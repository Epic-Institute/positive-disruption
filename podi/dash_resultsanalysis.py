from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("~/positive-disruption/podi/data/historical_analogs_output.csv")

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Dataset"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "historical_analogs_output",
                            ],
                            "historical_analogs_output",
                            id="dataset",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Technology"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.label.unique().tolist(),
                            df.label.unique().tolist(),
                            id="label",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.iso3c.unique().tolist(),
                            df.iso3c.unique().tolist(),
                            id="iso3c",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Unit"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.unit.unique().tolist(),
                            df.unit.unique().tolist()[0],
                            id="yaxis_unit",
                            multi=False,
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log"],
                            "Linear",
                            id="yaxis_type",
                            inline=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Group by"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "label",
                                "iso3c",
                                "unit",
                            ],
                            "label",
                            id="groupby",
                        ),
                    ],
                ),
                html.Br(),
            ]
        ),
        html.Br(),
        dcc.Graph(id="indicator-graphic"),
    ]
)


@app.callback(
    Output("indicator-graphic", "figure"),
    Input("dataset", "value"),
    Input("label", "value"),
    Input("iso3c", "value"),
    Input("yaxis_unit", "value"),
    Input("yaxis_type", "value"),
    Input("groupby", "value"),
)
def update_graph(
    dataset,
    label,
    iso3c,
    yaxis_unit,
    yaxis_type,
    groupby,
):

    {"none": None, "tonexty": "1"}

    df = pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")

    fig = go.Figure()

    # pivot df by year
    df = df.pivot_table(
        index=["label", "iso3c", "unit"],
        columns=["year"],
        values=["value"],
    ).interpolate(method="linear", limit_area="inside", axis=1)

    filtered_df = (
        (
            pd.DataFrame(df)
            .loc[
                label,
                iso3c,
                yaxis_unit,
            ]
            .groupby([groupby])
            .sum()
        )
    ).T.replace(0, None)

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df,
        id_vars="year",
        var_name=[groupby],
        value_name=yaxis_unit,
    )

    for sub in filtered_df[groupby].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df["year"].unique().astype(int),
                y=filtered_df[filtered_df[groupby] == sub][yaxis_unit].values,
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Technology adoption, by " + str(groupby),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": str(groupby) + ", " + str(yaxis_unit)},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig.update_yaxes(
        type="linear" if yaxis_type == "Linear" else "log",
        title=(
            str(yaxis_unit)
            if yaxis_type == "Linear"
            else "Log ( " + str(yaxis_unit) + " )"
        ),
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
