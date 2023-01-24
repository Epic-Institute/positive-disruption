from dash import Dash, dcc, html, Output
import pandas as pd
import plotly.graph_objects as go


datasets = ["energy_output"]

df = (
    pd.read_csv("~/positive-disruption/podi/data/energy_output.csv")
    .melt(
        id_vars=[
            "model",
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "product_short",
            "flow_category",
            "flow_long",
            "flow_short",
            "unit",
        ],
        var_name="year",
        value_name="value",
    )
    .drop(columns=["product_short", "flow_short"])
)

app = Dash(__name__)

lst = [
    html.Label("Dataset"),
    html.Div([dcc.RadioItems(datasets, datasets[0], id="dataset")]),
    html.Br(),
]

for column in df.columns.drop(["value"]):
    lst.append(html.Label(column))
    lst.append(
        html.Div([dcc.Dropdown(df[column].unique(), df[column].unique(), id=column)])
    )
    lst.append(html.Br())

app.layout = html.Div(
    children=[
        html.Div(lst),
        html.Br(),
        html.Label("Y-Axis Type"),
        html.Div([dcc.RadioItems(["Linear", "Log"], "Linear", id="yaxis_type")]),
        html.Br(),
        html.Label("Group By"),
        html.Div([dcc.RadioItems(df.columns, id="Group By")]),
        html.Br(),
        html.Label("Chart Type"),
        html.Div(
            [
                dcc.RadioItems(
                    {"none": "line", "tonexty": "area"}, "tonexty", id="chart_type"
                )
            ]
        ),
        html.Br(),
        dcc.Graph(id="indicator-graphic"),
    ]
)

clst = []
for column in [
    ["dataset"]
    + df.columns.drop(["value"]).tolist()
    + ["yaxis_type", "groupby", "chart_type"],
][0]:
    clst.append('Input("' + column + '", ' + '"value")')


@app.callback(
    Output("indicator-graphic", "figure"),
    clst,
)
def update_graph(clst):

    unit_val = {"TJ": 1, "TWh": 0.0002777, "percent of total": 1}
    stack_type = {"none": None, "tonexty": "1"}

    df = (
        pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")
        .melt(
            id_vars=[
                "model",
                "scenario",
                "region",
                "sector",
                "product_category",
                "product_long",
                "product_short",
                "flow_category",
                "flow_long",
                "flow_short",
                "unit",
            ],
            var_name="year",
            value_name="value",
        )
        .drop(columns=["product_short", "flow_short"])
    )

    fig = go.Figure()

    filtered_df = (
        (
            pd.DataFrame(df)
            .set_index(
                [
                    "model",
                    "scenario",
                    "region",
                    "sector",
                    "product_category",
                    "product_long",
                    "flow_category",
                    "flow_long",
                ]
            )
            .loc[
                dlst.model,
                dlst.scenario,
                dlst.region,
                dlst.sector,
                dlst.product_category,
                dlst.product_long,
                dlst.flow_category,
                dlst.flow_long,
            ]
            .groupby([dlst.groupby])
            .sum()
        )
        * unit_val[dlst.yaxis_unit]
    ).T.fillna(0)

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df,
        id_vars="year",
        var_name=[dlst.groupby],
        value_name="TFC, " + str(dlst.yaxis_unit),
    )

    for sub in filtered_df[dlst.groupby].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df["year"],
                y=filtered_df[filtered_df[dlst.groupby] == sub][
                    "TFC, " + str(dlst.yaxis_unit)
                ],
                fill=dlst.chart_type,
                stackgroup=stack_type[dlst.chart_type],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Final Consumption",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "TFC, " + str(dlst.yaxis_unit)},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig.update_yaxes(
        title="TFC, " + str(dlst.yaxis_unit),
        type="linear" if dlst.yaxis_type == "Linear" else "log",
    )

    return fig


"""
app.layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Dataset"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "energy_post_upstream",
                                "energy_post_addtl_eff",
                                "energy_electrified",
                                "energy_reduced_electrified",
                                "energy_output",
                                "energy_percent",
                            ],
                            "energy_output",
                            id="dataset",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Model"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.model.unique().tolist(),
                            df.model.unique().tolist(),
                            id="model",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Scenario"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.scenario.unique().tolist(),
                            df.scenario.unique().tolist()[0],
                            id="scenario",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.region.unique().tolist(),
                            df.region.unique().tolist(),
                            id="region",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Sector"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.sector.unique().tolist(),
                            df.sector.unique().tolist(),
                            id="sector",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product Category"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_category.unique().tolist(),
                            df.product_category.unique().tolist(),
                            id="product_category",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_long.unique().tolist(),
                            df.product_long.unique().tolist(),
                            id="product_long",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product Short"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_short.unique().tolist(),
                            df.product_short.unique().tolist(),
                            id="product_short",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow Category"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_category.unique().tolist(),
                            "Final consumption",
                            id="flow_category",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_long.unique().tolist(),
                            df.flow_long.unique().tolist(),
                            id="flow_long",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow Short"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_short.unique().tolist(),
                            df.flow_short.unique().tolist(),
                            id="flow_short",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Unit"),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["TJ", "TWh"],
                            "TJ",
                            id="yaxis_unit",
                        ),
                    ],
                ),
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
                                "model",
                                "scenario",
                                "region",
                                "sector",
                                "product_category",
                                "product_long",
                                "product_short",
                                "flow_category",
                                "flow_long",
                                "flow_short",
                            ],
                            "flow_short",
                            id="groupby",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Chart Type"),
                html.Div(
                    [
                        dcc.RadioItems(
                            {"none": "line", "tonexty": "area"},
                            "tonexty",
                            id="chart_type",
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        dcc.Graph(id="indicator-graphic"),
    ]
)

@app.callback(
    Output("indicator-graphic", "figure"),
    Input("dataset", "value"),
    Input("model", "value"),
    Input("scenario", "value"),
    Input("region", "value"),
    Input("sector", "value"),
    Input("product_category", "value"),
    Input("product_long", "value"),
    Input("product_short", "value"),
    Input("flow_category", "value"),
    Input("flow_long", "value"),
    Input("flow_short", "value"),
    Input("yaxis_unit", "value"),
    Input("yaxis_type", "value"),
    Input("groupby", "value"),
    Input("chart_type", "value"),
)
def update_graph(
    dataset,
    model,
    scenario,
    region,
    sector,
    product_category,
    product_long,
    product_short,
    flow_category,
    flow_long,
    flow_short,
    yaxis_unit,
    yaxis_type,
    groupby,
    chart_type,
):

    unit_val = {"TJ": 1, "TWh": 0.0002777, "percent of total": 1}
    stack_type = {"none": None, "tonexty": "1"}

    df = pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")

    df.drop(
        df.filter(["hydrogen", "flexible", "nonenergy", "unit"]), inplace=True, axis=1
    )

    fig = go.Figure()

    if yaxis_unit == "percent of total":
        filtered_df = (
            (
                pd.DataFrame(df)
                .set_index(
                    [
                        "model",
                        "scenario",
                        "region",
                        "sector",
                        "product_category",
                        "product_long",
                        "product_short",
                        "flow_category",
                        "flow_long",
                        "flow_short",
                    ]
                )
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    product_short,
                    flow_category,
                    flow_long,
                    flow_short,
                ]
                .groupby([groupby])
                .sum()
            )
            * unit_val[yaxis_unit]
        ).T.fillna(0)

        # calculate the percent of total for each groupby for each year
        filtered_df = filtered_df.apply(lambda x: x / filtered_df.sum(axis=0), axis=1)

        filtered_df.index.name = "year"
        filtered_df.reset_index(inplace=True)
        filtered_df = pd.melt(
            filtered_df,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + str(yaxis_unit),
        )

        for sub in filtered_df[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=filtered_df["year"],
                    y=filtered_df[filtered_df[groupby] == sub][
                        "TFC, " + str(yaxis_unit)
                    ],
                    fill=chart_type,
                    stackgroup=stack_type[chart_type],
                    showlegend=True,
                )
            )
    else:
        filtered_df = (
            (
                pd.DataFrame(df)
                .set_index(
                    [
                        "model",
                        "scenario",
                        "region",
                        "sector",
                        "product_category",
                        "product_long",
                        "product_short",
                        "flow_category",
                        "flow_long",
                        "flow_short",
                    ]
                )
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    product_short,
                    flow_category,
                    flow_long,
                    flow_short,
                ]
                .groupby([groupby])
                .sum()
            )
            * unit_val[yaxis_unit]
        ).T.fillna(0)

        filtered_df.index.name = "year"
        filtered_df.reset_index(inplace=True)
        filtered_df = pd.melt(
            filtered_df,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + str(yaxis_unit),
        )

        for sub in filtered_df[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=filtered_df["year"],
                    y=filtered_df[filtered_df[groupby] == sub][
                        "TFC, " + str(yaxis_unit)
                    ],
                    fill=chart_type,
                    stackgroup=stack_type[chart_type],
                    showlegend=True,
                )
            )

    fig.update_layout(
        title={
            "text": "Total Final Consumption",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "TFC, " + str(yaxis_unit)},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig.update_yaxes(
        title="TFC, " + str(yaxis_unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return fig
"""

if __name__ == "__main__":
    app.run_server(debug=True)
