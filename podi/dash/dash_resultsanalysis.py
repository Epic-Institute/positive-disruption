from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("~/positive-disruption/podi/data/historical_analogs_output.csv")
df2 = pd.read_csv("~/positive-disruption/podi/data/adoption_output.csv")
df3 = pd.read_csv("~/positive-disruption/podi/data/pdindex_output.csv")

app = Dash(__name__)

app.layout = html.Div(
    [
        # Historical Analogs
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
        # Adoption fit to energy demand growth rate
        html.Div(
            children=[
                html.Label("Dataset"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "adoption_output",
                            ],
                            "adoption_output",
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
                            df2.model.unique().tolist(),
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
                            df2.scenario.unique().tolist(),
                            df2.scenario.unique().tolist()[0],
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
                            df2.region.unique().tolist(),
                            df2.region.unique().tolist(),
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
                            df2.sector.unique().tolist(),
                            df2.sector.unique().tolist(),
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
                            df2.product_category.unique().tolist(),
                            df2.product_category.unique().tolist(),
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
                            df2.product_long.unique().tolist(),
                            df2.product_long.unique().tolist(),
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
                            df2.product_short.unique().tolist(),
                            df2.product_short.unique().tolist(),
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
                            df2.flow_category.unique().tolist(),
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
                            df2.flow_long.unique().tolist(),
                            df2.flow_long.unique().tolist(),
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
                            df2.flow_short.unique().tolist(),
                            df2.flow_short.unique().tolist(),
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
                            df2.unit.unique().tolist(),
                            df2.unit.unique().tolist()[0],
                            id="yaxis_unit2",
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log"],
                            "Linear",
                            id="yaxis_type2",
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
                            id="chart_type",
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        dcc.Graph(id="indicator-graphic2"),
        html.Br(),
        # PD Index
        html.Div(
            children=[
                html.Label("Dataset"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "pdindex_output",
                            ],
                            "pdindex_output",
                            id="dataset3",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Model"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df3.model.unique().tolist(),
                            df3.model.unique().tolist(),
                            id="model3",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Scenario"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df3.scenario.unique().tolist(),
                            df3.scenario.unique().tolist()[1],
                            id="scenario3",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df3.region.unique().tolist(),
                            df3.region.unique().tolist()[0],
                            id="region3",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Sector"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df3.sector.unique().tolist(),
                            df3.sector.unique().tolist()[0],
                            id="sector3",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df3.product_long.unique().tolist(),
                            df3.product_long.unique().tolist(),
                            id="product_long3",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Unit"),
                html.Div(
                    [
                        dcc.RadioItems(
                            df3.unit.unique().tolist(),
                            df3.unit.unique().tolist()[0],
                            id="yaxis_unit3",
                        ),
                    ],
                ),
                html.Br(),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log"],
                            "Linear",
                            id="yaxis_type3",
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
                                "product_long",
                            ],
                            "product_long",
                            id="groupby3",
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
                            id="chart_type3",
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        dcc.Graph(id="indicator-graphic3"),
    ]
)


@app.callback(
    Output("indicator-graphic", "figure"),
    Output("indicator-graphic2", "figure"),
    Output("indicator-graphic3", "figure"),
    Input("dataset", "value"),
    Input("label", "value"),
    Input("iso3c", "value"),
    Input("yaxis_unit", "value"),
    Input("yaxis_type", "value"),
    Input("groupby", "value"),
    Input("dataset2", "value"),
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
    Input("yaxis_unit2", "value"),
    Input("yaxis_type2", "value"),
    Input("groupby2", "value"),
    Input("chart_type", "value"),
    Input("dataset3", "value"),
    Input("model3", "value"),
    Input("scenario3", "value"),
    Input("region3", "value"),
    Input("sector3", "value"),
    Input("product_long3", "value"),
    Input("yaxis_unit3", "value"),
    Input("yaxis_type3", "value"),
    Input("groupby3", "value"),
    Input("chart_type3", "value"),
)
def update_graph(
    dataset,
    label,
    iso3c,
    yaxis_unit,
    yaxis_type,
    groupby,
    dataset2,
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
    yaxis_unit2,
    yaxis_type2,
    groupby2,
    chart_type,
    dataset3,
    model3,
    scenario3,
    region3,
    sector3,
    product_long3,
    yaxis_unit3,
    yaxis_type3,
    groupby3,
    chart_type3,
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

    # Chart #2

    stack_type = {"none": None, "tonexty": "1"}

    df2 = pd.read_csv("~/positive-disruption/podi/data/" + dataset2 + ".csv")

    fig2 = go.Figure()

    if yaxis_unit2 == "percent of total":
        filtered_df2 = (
            (
                pd.DataFrame(df2)
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
                .groupby([groupby2])
                .sum()
            )
        ).T.fillna(0)

        # calculate the percent of total for each groupby for each year
        filtered_df2 = filtered_df2.apply(
            lambda x: x / filtered_df2.sum(axis=0), axis=1
        )

        filtered_df2.index.name = "year"
        filtered_df2.reset_index(inplace=True)
        filtered_df2 = pd.melt(
            filtered_df2,
            id_vars="year",
            var_name=[groupby2],
            value_name=yaxis_unit2,
        )

        for sub in filtered_df2[groupby2].unique():
            fig2.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=filtered_df2["year"],
                    y=filtered_df2[filtered_df2[groupby2] == sub][yaxis_unit2],
                    fill=chart_type,
                    stackgroup=stack_type[chart_type],
                    showlegend=True,
                )
            )
    else:
        filtered_df2 = (
            (
                pd.DataFrame(df2)
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
            value_name=yaxis_unit2,
        )

        for sub in filtered_df2[groupby2].unique():
            fig2.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=filtered_df2["year"],
                    y=filtered_df2[filtered_df2[groupby2] == sub][yaxis_unit2],
                    fill=chart_type,
                    stackgroup=stack_type[chart_type],
                    showlegend=True,
                )
            )

    fig2.update_layout(
        title={
            "text": "Market Adoption Data Fit to Energy Demand Growth Rates",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": yaxis_unit2},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig2.update_yaxes(
        title=yaxis_unit2,
        type="linear" if yaxis_type2 == "Linear" else "log",
    )

    # Chart 3

    stack_type = {"none": None, "tonexty": "1"}

    df3 = pd.read_csv("~/positive-disruption/podi/data/" + dataset3 + ".csv")

    fig3 = go.Figure()

    if yaxis_unit2 == "percent of total":
        filtered_df3 = (
            (
                pd.DataFrame(df3)
                .set_index(
                    [
                        "model",
                        "scenario",
                        "region",
                        "sector",
                        "product_long",
                    ]
                )
                .loc[
                    model3,
                    scenario3,
                    region3,
                    sector3,
                    product_long3,
                ]
                .groupby([groupby3])
                .sum()
            )
        ).T.fillna(0)

        # calculate the percent of total for each groupby for each year
        filtered_df3 = filtered_df3.apply(
            lambda x: x / filtered_df3.sum(axis=0), axis=1
        )

        filtered_df3.index.name = "year"
        filtered_df3.reset_index(inplace=True)
        filtered_df3 = pd.melt(
            filtered_df3,
            id_vars="year",
            var_name=[groupby3],
            value_name=yaxis_unit3,
        )

        for sub in filtered_df3[groupby3].unique():
            fig3.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=filtered_df3["year"],
                    y=filtered_df3[filtered_df3[groupby3] == sub][yaxis_unit3],
                    fill=chart_type3,
                    stackgroup=stack_type[chart_type3],
                    showlegend=True,
                )
            )
    else:
        filtered_df3 = (
            (
                pd.DataFrame(df3)
                .set_index(
                    [
                        "model",
                        "scenario",
                        "region",
                        "sector",
                        "product_long",
                    ]
                )
                .loc[
                    model3,
                    scenario3,
                    region3,
                    sector3,
                    product_long3,
                ]
                .groupby([groupby3])
                .sum()
            )
        ).T.fillna(0)

        filtered_df3.index.name = "year"
        filtered_df3.reset_index(inplace=True)
        filtered_df3 = pd.melt(
            filtered_df3,
            id_vars="year",
            var_name=[groupby3],
            value_name=yaxis_unit3,
        )

        for sub in filtered_df3[groupby3].unique():
            fig3.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=2,
                    ),
                    x=filtered_df3["year"],
                    y=filtered_df3[filtered_df3[groupby3] == sub][yaxis_unit3],
                    fill=chart_type3,
                    stackgroup=stack_type[chart_type3],
                    showlegend=True,
                )
            )

    fig3.update_layout(
        title={
            "text": "Adoption as a Percent of Total",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": yaxis_unit3},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        xaxis1_rangeslider_visible=True,
    )

    fig3.update_yaxes(
        title=yaxis_unit3,
        type="linear" if yaxis_type3 == "Linear" else "log",
    )

    return fig, fig2, fig3


if __name__ == "__main__":
    app.run_server(debug=True)
