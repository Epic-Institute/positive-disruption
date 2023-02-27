import dash
from dash import dcc, html, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import itertools
import plotly.express as px

dash.register_page(__name__, path="/Emissions", title="Emissions", name="Emissions")

data_end_year = 2020

df = pd.read_parquet(
    "~/positive-disruption/podi/data/emissions_output_co2e.parquet"
).reset_index()

layout = html.Div(
    [
        html.Div(
            children=[
                dcc.Graph(id="graphic-emissions"),
                dcc.Graph(id="graphic-emissions-2"),
                html.Br(),
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
                            ["Linear", "Log", "Cumulative"],
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
                        dcc.Dropdown(
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
                            ["sector", "product_category"],
                            id="groupby",
                            multi=True,
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

    chart_template = {
        "linecolor": list(
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
                    200,
                )
            )
        ),
        "fillcolor": list(
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
                    200,
                )
            )
        ),
        "hovertemplate": (
            "<b>Year</b>: %{x}"
            + "<br><b>Emissions</b>: %{y:,.0f} "
            + yaxis_unit
            + "<br>"
        ),
    }

    df = pd.read_parquet("~/positive-disruption/podi/data/" + dataset + ".parquet")

    # make groupby an array if it is not already
    if not isinstance(groupby, list):
        groupby = [groupby] if groupby else []

    filtered_df = (
        (
            df.loc[
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
            .groupby(groupby)
            .sum()
        )
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)

    if yaxis_type == "Cumulative":
        filtered_df = filtered_df.loc[str(data_end_year) :].cumsum()

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df, id_vars="year", var_name=groupby, value_name=str(yaxis_unit)
    ).astype({k: "category" for k in groupby} | {"year": "int", yaxis_unit: "float32"})

    fig = go.Figure()

    i = 0

    for sub in (
        filtered_df.sort_values(str(yaxis_unit), ascending=False)[groupby]
        .drop_duplicates()
        .squeeze()
        .values
    ):

        if isinstance(sub, str):
            name = str(sub).capitalize()
        else:
            name = ", ".join(str(x).capitalize() for x in sub)

        fig.add_trace(
            go.Scatter(
                name=name,
                line=dict(width=0.5, color=chart_template["linecolor"][i]),
                x=filtered_df["year"].drop_duplicates(),
                y=pd.DataFrame(filtered_df)
                .set_index(groupby)
                .loc[[sub]][yaxis_unit]
                .values,
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
                hovertemplate=chart_template["hovertemplate"],
                fillcolor=chart_template["fillcolor"][i],
            )
        )
        i += 1

    fig.add_trace(
        go.Scatter(
            name="Net Projected",
            line=dict(width=5, color="magenta", dash="dashdot"),
            x=filtered_df[filtered_df["year"] >= data_end_year]["year"],
            y=filtered_df[filtered_df["year"] >= data_end_year]
            .groupby("year")
            .sum()[str(yaxis_unit)],
            showlegend=True,
            hovertemplate=chart_template["hovertemplate"],
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
            hovertemplate=chart_template["hovertemplate"],
        )
    )

    fig.update_layout(
        title={
            "text": "EMISSIONS, " + str(dataset).upper(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        template="presentation",
    )

    fig.update_yaxes(
        title=str(yaxis_unit),
        type="linear"
        if yaxis_type == "Linear" or yaxis_type == "Cumulative"
        else "log",
    )

    # Wedges chart

    filtered_df2 = (
        (
            (
                df.loc[
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
                .groupby(groupby)
                .sum()
                - (
                    df.loc[
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
                    .groupby(groupby)
                    .sum()
                )
            )
        )
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)

    if yaxis_type == "Cumulative":
        filtered_df2 = filtered_df2.loc[str(data_end_year) :].cumsum()

    filtered_df2.index.name = "year"
    filtered_df2.reset_index(inplace=True)
    filtered_df2 = pd.melt(
        filtered_df2, id_vars="year", var_name=groupby, value_name=str(yaxis_unit)
    ).astype({k: "category" for k in groupby} | {"year": "int", yaxis_unit: "float32"})

    fig2 = go.Figure()

    spacer = df.loc[
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
    ].sum()

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

    i = 0

    for groupby_value in (
        filtered_df2.sort_values(str(yaxis_unit), ascending=False)[groupby]
        .drop_duplicates()
        .squeeze()
        .values
    ):

        if isinstance(groupby_value, str):
            name = str(groupby_value).capitalize()
        else:
            name = ", ".join(str(x).capitalize() for x in groupby_value)

        fig2.add_trace(
            go.Scatter(
                name=name,
                line=dict(
                    width=0.5,
                    color=chart_template["linecolor"][i],
                ),
                x=filtered_df2[filtered_df2["year"] > data_end_year][
                    "year"
                ].drop_duplicates(),
                y=pd.DataFrame(filtered_df2[filtered_df2.year > data_end_year])
                .set_index(groupby)
                .loc[[groupby_value]][yaxis_unit]
                .values,
                fill="tonexty",
                stackgroup="one",
                hovertemplate=chart_template["hovertemplate"],
                fillcolor=chart_template["fillcolor"][i],
            )
        )
        i += 1

    fig2.add_trace(
        go.Scatter(
            name="Pathway",
            line=dict(width=5, color="magenta", dash="dashdot"),
            x=filtered_df[filtered_df["year"] >= data_end_year][
                "year"
            ].drop_duplicates(),
            y=pd.Series(
                filtered_df[filtered_df.year >= data_end_year]
                .groupby("year")
                .sum()[yaxis_unit]
                .values,
                index=filtered_df[filtered_df["year"] >= data_end_year][
                    "year"
                ].drop_duplicates(),
            ).loc[data_end_year:],
            fill="none",
            stackgroup="pathway",
            showlegend=True,
            hovertemplate=chart_template["hovertemplate"],
        )
    )

    fig2.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=5, color="red", dash="dashdot"),
            x=filtered_df[filtered_df["year"] >= data_end_year][
                "year"
            ].drop_duplicates(),
            y=pd.Series(
                filtered_df[(filtered_df.year >= data_end_year)]
                .groupby("year")
                .sum()[yaxis_unit]
                .values
                * 0,
                index=filtered_df[filtered_df["year"] >= data_end_year][
                    "year"
                ].drop_duplicates(),
            ).loc[data_end_year:],
            fill="none",
            stackgroup="one",
            showlegend=True,
            hovertemplate=chart_template["hovertemplate"],
        )
    )

    fig2.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=filtered_df[filtered_df["year"] <= data_end_year][
                "year"
            ].drop_duplicates(),
            y=pd.Series(
                filtered_df[filtered_df.year <= data_end_year]
                .groupby("year")
                .sum()[yaxis_unit]
                .values,
                index=filtered_df[filtered_df["year"] <= data_end_year][
                    "year"
                ].drop_duplicates(),
            ).loc[:data_end_year],
            fill="none",
            stackgroup="historical",
            showlegend=True,
            hovertemplate=chart_template["hovertemplate"],
        )
    )

    fig2.update_layout(
        title={
            "text": "EMISSIONS MITIGATED, " + str(dataset).upper(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        template="presentation",
        legend_traceorder="reversed",
    )

    fig2.update_yaxes(
        title=str(yaxis_unit),
        type="linear" if yaxis_type == "Linear" else "log",
    )

    return (
        fig,
        fig2,
    )
