import dash
from dash import dcc, html, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd

dash.register_page(__name__, path="/Emissions", title="Emissions", name="Emissions")

data_end_year = 2020

df = pd.read_csv("~/positive-disruption/podi/data/emissions_output_co2e.csv")

layout = html.Div(
    [
        html.Div(
            children=[
                dcc.Graph(id="graphic-emissions"),
                dcc.Graph(id="graphic-emissions-2"),
                html.Label("Dataset"),
                html.Div(
                    [
                        dcc.RadioItems(
                            [
                                "emissions_output_co2e",
                            ],
                            "emissions_output_co2e",
                            id="dataset",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Unit"),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Mt", "Gt"],
                            "Mt",
                            id="yaxis_unit",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Y Axis Type"),
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
                            "product_long",
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
                            "pathway",
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
                            style={
                                "max-height": "100px",
                                "overflow-y": "scroll",
                            },
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
                            style={"max-height": "100px", "overflow-y": "scroll"},
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
            ]
        ),
    ],
    style={"padding": "10px", "flex": "1 1 auto"},
)


@callback(
    Output("graphic-emissions", "figure"),
    Output("graphic-emissions-2", "figure"),
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

    unit_val = {"Mt": 1, "Gt": 1e-3}
    stack_type = {"none": None, "tonexty": "1"}

    df = pd.read_csv("~/positive-disruption/podi/data/" + dataset + ".csv")

    df.drop(
        df.filter(["hydrogen", "flexible", "nonenergy", "unit"]), inplace=True, axis=1
    )

    hovertemplate = (
        "<b>Year</b>: %{x}" + "<br><b>Emissions</b>: %{y:,.0f} " + yaxis_unit + "<br>"
    )

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
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df, id_vars="year", var_name=[groupby], value_name=str(yaxis_unit)
    )

    filtered_df.year = filtered_df.year.astype(int)

    fig = go.Figure()

    for sub in filtered_df.sort_values(str(yaxis_unit), ascending=False)[
        groupby
    ].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                ),
                x=filtered_df["year"],
                y=filtered_df[filtered_df[groupby] == sub][str(yaxis_unit)],
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
                hovertemplate=hovertemplate,
            )
        )

    fig.add_trace(
        go.Scatter(
            name="Net Projected",
            line=dict(width=3, color="magenta", dash="dash"),
            x=filtered_df[filtered_df["year"] >= data_end_year]["year"],
            y=filtered_df[filtered_df["year"] >= data_end_year]
            .groupby("year")
            .sum()[str(yaxis_unit)],
            showlegend=True,
            hovertemplate=hovertemplate,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=filtered_df[filtered_df["year"] <= data_end_year]["year"],
            y=filtered_df[filtered_df["year"] <= data_end_year]
            .groupby("year")
            .sum()[str(yaxis_unit)],
            showlegend=True,
            hovertemplate=hovertemplate,
        )
    )

    fig.update_layout(
        title={
            "text": "EMISSIONS, " + str(dataset).upper(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
            # "font": dict(size=12),
        },
        xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        # legend=dict(font=dict(size=12)),
        # template="presentation",
    )

    fig.update_yaxes(
        title=str(yaxis_unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    # Wedges chart

    filtered_df2 = (
        (
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
                    "baseline",
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
                - (
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
                        "pathway",
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
            )
        )
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)

    filtered_df2.index.name = "year"
    filtered_df2.reset_index(inplace=True)
    filtered_df2 = pd.melt(
        filtered_df2, id_vars="year", var_name=[groupby], value_name=str(yaxis_unit)
    )

    filtered_df2.year = filtered_df2.year.astype(int)

    fig2 = go.Figure()

    spacer = (
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
            "pathway",
            region,
            sector,
            product_category,
            product_long,
            product_short,
            flow_category,
            flow_long,
            flow_short,
        ]
        .sum()
    )

    spacer.index = spacer.index.astype(int)

    fig2.add_trace(
        go.Scatter(
            name="",
            line=dict(width=0),
            x=spacer.index.values[spacer.index.values >= data_end_year],
            y=spacer[spacer.index.values >= data_end_year],
            fill="none",
            stackgroup="one",
            showlegend=False,
        )
    )

    for groupby_value in filtered_df2.sort_values(str(yaxis_unit), ascending=False)[
        groupby
    ].unique():

        fig2.add_trace(
            go.Scatter(
                name=groupby_value,
                line=dict(width=0.5),
                x=filtered_df2[filtered_df2["year"] > data_end_year]["year"].unique(),
                y=filtered_df2[
                    (filtered_df2[groupby] == groupby_value)
                    & (filtered_df2["year"] > data_end_year)
                ][yaxis_unit].values,
                fill="tonexty",
                stackgroup="one",
                legendgroup=groupby_value,
                hovertemplate=hovertemplate,
            )
        )

    fig2.add_trace(
        go.Scatter(
            name="Pathway",
            line=dict(width=3, color="magenta", dash="dash"),
            x=filtered_df[filtered_df["year"] >= data_end_year]["year"].unique(),
            y=pd.Series(
                filtered_df[filtered_df.year >= data_end_year]
                .groupby("year")
                .sum()[yaxis_unit]
                .values,
                index=filtered_df[filtered_df["year"] >= data_end_year][
                    "year"
                ].unique(),
            ).loc[data_end_year:],
            fill="none",
            stackgroup="pathway",
            showlegend=True,
            hovertemplate=hovertemplate,
        )
    )

    fig2.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=3, color="red", dash="dash"),
            x=filtered_df[filtered_df["year"] >= data_end_year]["year"].unique(),
            y=pd.Series(
                filtered_df[(filtered_df.year >= data_end_year)]
                .groupby("year")
                .sum()[yaxis_unit]
                .values
                * 0,
                index=filtered_df[filtered_df["year"] >= data_end_year][
                    "year"
                ].unique(),
            ).loc[data_end_year:],
            fill="none",
            stackgroup="one",
            showlegend=True,
            hovertemplate=hovertemplate,
        )
    )

    fig2.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=2, color="black"),
            x=filtered_df[filtered_df["year"] <= data_end_year]["year"].unique(),
            y=pd.Series(
                filtered_df[filtered_df.year <= data_end_year]
                .groupby("year")
                .sum()[yaxis_unit]
                .values,
                index=filtered_df[filtered_df["year"] <= data_end_year][
                    "year"
                ].unique(),
            ).loc[:data_end_year],
            fill="none",
            stackgroup="historical",
            showlegend=True,
            hovertemplate=hovertemplate,
        )
    )

    fig2.update_layout(
        title={
            "text": "EMISSIONS MITIGATED, " + str(dataset).upper(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
            # "font": dict(size=12),
        },
        xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        # legend=dict(font=dict(size=12)),
        # template="presentation",
        legend_traceorder="reversed",
    )

    fig2.update_yaxes(
        title=str(yaxis_unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return fig, fig2
