import dash
from dash import dcc, html, callback, Output, Input
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import itertools

dash.register_page(__name__, path="/Energy", title="Energy", name="Energy")

data_start_year = 1990
data_end_year = 2100

dataset = ["energy_output"]

df = pd.read_parquet(
    "~/positive-disruption/podi/data/" + dataset[0] + ".parquet"
).reset_index()

clst = df.columns[
    (~df.columns.isin(f"{i}" for i in range(data_start_year, data_end_year + 1)))
    & (~df.columns.isin(["product_short", "flow_short"]))
].tolist()

df.set_index(
    df.columns[
        (~df.columns.isin(f"{i}" for i in range(data_start_year, data_end_year + 1)))
        & (~df.columns.isin(["product_short", "flow_short"]))
    ].tolist(),
    inplace=True,
)

lst = []
for level in df.index.names:
    lst.append(
        html.Label(
            level.replace("_", " ").replace("long", "").title(),
            className="select-label",
        )
    )
    lst.append(
        html.Div(
            [
                dcc.Dropdown(
                    df.reset_index()[level].unique().tolist(),
                    df.reset_index()[level].unique().tolist(),
                    id=level,
                    multi=True,
                ),
            ],
        )
    )
    lst.append(html.Br())


layout = html.Div(
    children=[
        html.Label("Dataset", className="select-label"),
        html.Div(
            dcc.RadioItems(
                dataset,
                dataset[0],
                id="dataset",
                style={"margin-right": "20px"},
            )
        ),
        html.Br(),
        html.Div(lst),
        html.Label("Y-Axis Type", className="select-label"),
        html.Div([dcc.RadioItems(["Linear", "Log"], "Linear", id="yaxis_type")]),
        html.Br(),
        html.Label("Y-Axis Unit", className="select-label"),
        html.Div(
            [
                dcc.RadioItems(
                    df.reset_index().unit.unique().tolist() + ["TWh"],
                    df.reset_index().unit.unique().tolist()[0],
                    id="yaxis_unit",
                )
            ]
        ),
        html.Br(),
        html.Label("Group By", className="select-label"),
        html.Div(
            [
                dcc.RadioItems(
                    df.index.names,
                    df.index.names[-3],
                    id="groupby",
                )
            ]
        ),
        html.Br(),
        html.Label("Chart Type", className="select-label"),
        html.Div(
            [
                dcc.RadioItems(
                    {"none": "line", "tonexty": "area"},
                    "tonexty",
                    id="chart_type",
                )
            ]
        ),
        html.Br(),
        dcc.Graph(id="graphic-energy"),
        html.Br(),
    ],
)


@callback(
    output=Output("graphic-energy", "figure"),
    inputs=[
        Input("dataset", "value"),
        Input("yaxis_type", "value"),
        Input("yaxis_unit", "value"),
        Input("groupby", "value"),
        Input("chart_type", "value"),
    ]
    + [Input(component_id=i, component_property="value") for i in df.index.names],
)
def update_graph(
    dataset,
    yaxis_type,
    yaxis_unit,
    groupby,
    chart_type,
    *clst,
    data_start_year=1990,
    data_end_year=2100,
):

    unit_val = {"TJ": 1, "TWh": 0.0002777, "percent of total": 1}
    stack_type = {"none": None, "tonexty": "1"}

    fig = go.Figure()

    df = pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")
    df.set_index(
        df.columns[
            (
                ~df.columns.isin(
                    f"{i}" for i in range(data_start_year, data_end_year + 1)
                )
            )
            & (~df.columns.isin(["product_short", "flow_short"]))
        ].tolist(),
        inplace=True,
    )

    filtered_df = (
        df.loc[clst, :].groupby([groupby]).sum(numeric_only=True) * unit_val[yaxis_unit]
    )

    for sub in filtered_df.reset_index()[groupby].unique().tolist():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df.columns.astype(int),
                y=filtered_df.loc[sub],
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
                fillcolor=list(
                    itertools.chain.from_iterable(
                        itertools.repeat(
                            px.colors.qualitative.Prism
                            + px.colors.qualitative.Antique
                            + px.colors.qualitative.Dark24
                            + px.colors.qualitative.Pastel1
                            + px.colors.qualitative.Pastel2
                            + px.colors.qualitative.Set1
                            + px.colors.qualitative.Set2
                            + px.colors.qualitative.Set3,
                            10,
                        )
                    )
                )[filtered_df.reset_index()[groupby].unique().tolist().index(sub)],
            )
        )

    fig.update_layout(
        title={
            "text": "<b>"
            + dataset
            + "</b>, grouped by "
            + "<b>"
            + groupby
            + "</b> , in <b>"
            + yaxis_unit
            + "</b>",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": yaxis_unit},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig.update_yaxes(
        title=yaxis_unit,
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return fig
