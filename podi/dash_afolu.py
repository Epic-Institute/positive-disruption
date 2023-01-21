from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("~/positive-disruption/podi/data/afolu_output.csv")
df2 = pd.read_csv("~/positive-disruption/podi/data/TNC/afolu_historical.csv")

app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("DATASET 1"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "afolu_output",
                            ],
                            "afolu_output",
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
                            df.flow_category.unique().tolist(),
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
                            ["Mha", "m3", "Percent adoption"],
                            "Mha",
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
        html.Br(),
        html.Label("DATASET 2", style={"font-weight": "bold"}),
        html.Br(),
        html.Div(
            [
                dcc.RadioItems(
                    [
                        "afolu_historical",
                        "flux_output",
                        "max_extent_output",
                    ],
                    "afolu_historical",
                    id="dataset2",
                ),
            ],
        ),
        html.Br(),
        html.Label("Model"),
        html.Div(
            [
                dcc.Dropdown(
                    df2.model.unique().tolist(),
                    df2.model.unique().tolist()[0],
                    id="model2",
                    multi=True,
                ),
            ],
        ),
        html.Br(),
        html.Label("Scenario"),
        html.Div(
            [
                dcc.Dropdown(
                    df2.scenario.unique().tolist(),
                    df2.scenario.unique().tolist()[0],
                    id="scenario2",
                    multi=True,
                ),
            ],
        ),
        html.Br(),
        html.Label("Region"),
        html.Div(
            [
                dcc.Dropdown(
                    df2.region.unique().tolist(),
                    df2.region.unique().tolist(),
                    id="region2",
                    multi=True,
                ),
            ],
        ),
        html.Br(),
        html.Label("Variable"),
        html.Div(
            [
                dcc.Dropdown(
                    df2.variable.unique().tolist(),
                    df2.variable.unique().tolist(),
                    id="variable",
                    multi=True,
                ),
            ],
        ),
        html.Br(),
        html.Label("Unit"),
        html.Div(
            [
                dcc.RadioItems(
                    df2.unit.unique().tolist()
                    + ["tCO2e/m3/yr", "tCO2e/percentile improvement", "tCO2e/Mha/yr"],
                    df2.unit.unique().tolist()[0],
                    id="unit",
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
                        "variable",
                        "unit",
                    ],
                    "unit",
                    id="groupby2",
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
                    id="chart_type2",
                ),
            ],
        ),
        dcc.Graph(id="indicator-graphic2"),
    ]
)


@app.callback(
    Output("indicator-graphic", "figure"),
    Output("indicator-graphic2", "figure"),
    Input("dataset", "value"),
    Input("dataset2", "value"),
    Input("model", "value"),
    Input("model2", "value"),
    Input("scenario", "value"),
    Input("scenario2", "value"),
    Input("region", "value"),
    Input("region2", "value"),
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
    Input("groupby2", "value"),
    Input("chart_type", "value"),
    Input("chart_type2", "value"),
    Input("variable", "value"),
    Input("unit", "value"),
)
def update_graph(
    dataset,
    dataset2,
    model,
    model2,
    scenario,
    scenario2,
    region,
    region2,
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
    groupby2,
    chart_type,
    chart_type2,
    variable,
    unit,
):

    # unit_val = {"Mha": 1, "ha": 1e6, "km2": 1e4}
    stack_type = {"none": None, "tonexty": "1"}

    df = pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")

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
                    "unit",
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
                yaxis_unit,
            ]
            .groupby([groupby])
            .sum()
        )
    ).T.fillna(0)

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df,
        id_vars="year",
        var_name=[groupby],
        value_name="Adoption, " + str(yaxis_unit),
    )

    fig = go.Figure()

    for sub in filtered_df[groupby].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df["year"],
                y=filtered_df[filtered_df[groupby] == sub][
                    "Adoption, " + str(yaxis_unit)
                ],
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Adoption",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "Adoption, " + str(yaxis_unit)},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig.update_yaxes(
        title="Adoption, " + str(yaxis_unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    df2 = pd.read_csv("~/positive-disruption/podi/data/TNC/" + dataset2 + ".csv")

    filtered_df2 = (
        (
            pd.DataFrame(df2)
            .set_index(["model", "scenario", "region", "variable", "unit"])
            .loc[model2, scenario2, region2, variable, unit]
            .groupby([groupby2])
            .sum()
        )
    ).T.fillna(0)

    filtered_df2.index.name = "year"
    filtered_df2.reset_index(inplace=True)
    filtered_df2 = pd.melt(
        filtered_df2,
        id_vars="year",
        var_name=[groupby2],
        value_name=unit,
    )

    fig2 = go.Figure()

    for sub in filtered_df2[groupby2].unique():
        fig2.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df2["year"],
                y=filtered_df2[filtered_df2[groupby2] == sub][unit],
                fill=chart_type2,
                stackgroup=stack_type[chart_type2],
                showlegend=True,
            )
        )

    fig2.update_layout(
        title={
            "text": dataset2,
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": str(unit)},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig2.update_yaxes(
        title=str(unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return fig, fig2


if __name__ == "__main__":
    app.run_server(debug=True)
