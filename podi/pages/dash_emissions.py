import itertools

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(
    __name__, path="/Emissions", title="Emissions", name="Emissions"
)

data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100

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
                html.Label("Dataset", className="select-label"),
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
                html.Label("Date Range", className="select-label"),
                html.Div(
                    [
                        dcc.RangeSlider(
                            id="date_range",
                            min=data_start_year,
                            max=proj_end_year,
                            value=[data_start_year, proj_end_year],
                            marks={
                                str(year): str(year)
                                for year in range(
                                    data_start_year, proj_end_year + 1, 5
                                )
                            },
                        ),
                    ],
                ),
                html.Label("Unit", className="select-label"),
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
                html.Label("Y Axis Type", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log", "Cumulative", "% of Total"],
                            "Linear",
                            id="yaxis_type",
                            inline=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Chart Type", className="select-label"),
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
                html.Label("Group by", className="select-label"),
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
                html.Label("Model", className="select-label"),
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
                html.Label("Scenario", className="select-label"),
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
                html.Label("Region", className="select-label"),
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
                html.Label("Sector", className="select-label"),
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
                html.Label("Product Category", className="select-label"),
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
                html.Label("Product", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_long.unique().tolist(),
                            df.product_long.unique().tolist(),
                            id="product_long",
                            multi=True,
                            style={
                                "max-height": "100px",
                                "overflow-y": "scroll",
                            },
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product Short", className="select-label"),
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
                html.Label("Flow Category", className="select-label"),
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
                html.Label("Flow", className="select-label"),
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
                html.Label("Flow Short", className="select-label"),
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
    Input("date_range", "value"),
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
    date_range,
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
            + yaxis_unit.replace(
                yaxis_unit, "%" if yaxis_type == "% of Total" else yaxis_unit
            )
            + "<br>"
        ),
    }

    df = pd.read_parquet(
        "~/positive-disruption/podi/data/" + dataset + ".parquet"
    )

    # make groupby an array if it is not already
    if not isinstance(groupby, list):
        groupby = [groupby] if groupby else []

    # prevent error if groupby is empty
    if not groupby:
        groupby = ["sector"]

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
        ).loc[:, str(date_range[0]) : str(date_range[1])]
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)
    
    if yaxis_type == "Cumulative":
        filtered_df = filtered_df.loc[
            str(date_range[0]) : str(date_range[1])
        ].cumsum()

    if yaxis_type == "% of Total":
        groupnorm = "percent"
        filtered_df[filtered_df < 0] = 0
    else:
        groupnorm = None

    if yaxis_type == "Log":
        filtered_df[filtered_df < 0] = 0

    filtered_df.index.name = "year"
    filtered_df.reset_index(inplace=True)
    filtered_df = pd.melt(
        filtered_df,
        id_vars="year",
        var_name=groupby,
        value_name=str(yaxis_unit),
    ).astype(
        {k: "category" for k in groupby}
        | {"year": "int", yaxis_unit: "float32"}
    )

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
                line=dict(width=3, color=chart_template["linecolor"][i]),
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
                groupnorm=groupnorm,
            )
        )
        i += 1

    if chart_type not in ["none"]:
        fig.add_trace(
            go.Scatter(
                name="Net Emissions",
                line=dict(width=5, color="magenta", dash="dashdot"),
                x=filtered_df[
                    (filtered_df["year"] >= date_range[0])
                    & (filtered_df["year"] <= date_range[1])
                ]["year"].drop_duplicates(),
                y=pd.Series(
                    filtered_df[
                        (filtered_df.year >= date_range[0])
                        & (filtered_df.year <= date_range[1])
                    ]
                    .groupby("year")
                    .sum(numeric_only=True)[yaxis_unit]
                    .values
                    * 0,
                    index=filtered_df[
                        (filtered_df["year"] >= date_range[0])
                        & (filtered_df["year"] <= date_range[1])
                    ]["year"].drop_duplicates(),
                ),
                fill="none",
                stackgroup=stack_type[chart_type],
                showlegend=True,
                hovertemplate=chart_template["hovertemplate"],
                groupnorm=groupnorm,
            )
        )

    # add shaded region to indicate Projection
    fig.add_vrect(
        x0=max(data_end_year, date_range[0]),
        x1=date_range[1],
        y0=0,
        y1=1,
        fillcolor="LightGrey",
        opacity=0.25,
        layer="above",
        line_width=0,
        annotation_text="Projection",
        annotation_position="top left",
    )

    fig.update_layout(
        title={
            "text": "<b>Emissions</b>, grouped by "
            + "<b>"
            + " & ".join(str(x).capitalize() for x in groupby),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        # xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        template="presentation",
    )

    fig.update_yaxes(
        title=str(yaxis_unit) + "CO2e",
        type="linear"
        if yaxis_type == "Linear"
        or yaxis_type == "Cumulative"
        or yaxis_type == "% of Total"
        else "log",
        spikemode="toaxis",
    )
    
    fig.update_xaxes(spikemode="toaxis")

    if yaxis_type == "% of Total":
        fig.update_yaxes(title="% of Total")
    elif yaxis_type == "Cumulative":
        fig.update_yaxes(title="Cumulative Emissions, " + str(yaxis_unit))

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
                .sum(numeric_only=True)
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
                    .sum(numeric_only=True)
                )
            )
        ).loc[:, str(date_range[0]) : str(date_range[1])]
        * unit_val[str(yaxis_unit)]
    ).T.fillna(0)

    if yaxis_type == "Cumulative":
        filtered_df2 = filtered_df2.loc[
            str(date_range[0]) : str(date_range[1])
        ].cumsum()

    if yaxis_type == "% of Total":
        groupnorm = "percent"
        filtered_df2[filtered_df2 < 0] = 0
    else:
        groupnorm = None

    if yaxis_type == "Log":
        filtered_df2[filtered_df2 < 0] = 0

    filtered_df2.index.name = "year"
    filtered_df2.reset_index(inplace=True)
    filtered_df2 = pd.melt(
        filtered_df2,
        id_vars="year",
        var_name=groupby,
        value_name=str(yaxis_unit),
    ).astype(
        {k: "category" for k in groupby}
        | {"year": "int", yaxis_unit: "float32"}
    )

    fig2 = go.Figure()

    if yaxis_type not in ["Log", "Cumulative", "% of Total"]:
        spacer = (
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
            .loc[:, str(date_range[0]) : str(date_range[1])]
            .sum()
        )

        spacer.index = spacer.index.astype(int)

        fig2.add_trace(
            go.Scatter(
                name="",
                line=dict(width=0),
                x=spacer.index.values[
                    (spacer.index.values >= data_end_year)
                    & (spacer.index.values <= date_range[1])
                ],
                y=spacer[
                    (spacer.index.values >= data_end_year)
                    & (spacer.index.values <= date_range[1])
                ],
                fill="none",
                stackgroup="one",
                showlegend=False,
                groupnorm=groupnorm,
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
                    width=3,
                    color=chart_template["linecolor"][i],
                ),
                x=filtered_df2[
                    (filtered_df2["year"] > data_end_year)
                    & ((filtered_df2["year"] <= date_range[1]))
                ]["year"].drop_duplicates(),
                y=pd.DataFrame(
                    filtered_df2[
                        (filtered_df2.year > data_end_year)
                        & (filtered_df2.year <= date_range[1])
                    ]
                )
                .set_index(groupby)
                .loc[[groupby_value]][yaxis_unit]
                .values,
                fill="tonexty",
                stackgroup="one",
                hovertemplate=chart_template["hovertemplate"],
                fillcolor=chart_template["fillcolor"][i],
                groupnorm=groupnorm,
            )
        )
        i += 1

    if yaxis_type not in ["Log", "Cumulative", "% of Total"]:
        fig2.add_trace(
            go.Scatter(
                name="Pathway",
                line=dict(width=5, color="magenta", dash="dashdot"),
                x=filtered_df[
                    (filtered_df["year"] >= data_end_year)
                    & (filtered_df["year"] <= date_range[1])
                ]["year"].drop_duplicates(),
                y=pd.Series(
                    filtered_df[
                        (filtered_df.year >= data_end_year)
                        & (filtered_df.year <= date_range[1])
                    ]
                    .groupby("year")
                    .sum(numeric_only=True)[yaxis_unit]
                    .values,
                    index=filtered_df[
                        (filtered_df["year"] >= data_end_year)
                        & (filtered_df["year"] <= date_range[1])
                    ]["year"].drop_duplicates(),
                ).loc[data_end_year : date_range[1]],
                fill="none",
                stackgroup="pathway",
                showlegend=True,
                hovertemplate=chart_template["hovertemplate"],
                groupnorm=groupnorm,
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
                    .sum(numeric_only=True)[yaxis_unit]
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
                groupnorm=groupnorm,
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
                    .sum(numeric_only=True)[yaxis_unit]
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

    # add shaded region to indicate Projection
    fig2.add_vrect(
        x0=max(data_end_year, date_range[0]),
        x1=date_range[1],
        y0=0,
        y1=1,
        fillcolor="LightGrey",
        opacity=0.25,
        layer="above",
        line_width=0,
        annotation_text="Projection",
        annotation_position="top left",
    )

    fig2.update_layout(
        title={
            "text": "<b>Emissions Mitigated</b>, grouped by "
            + "<b>"
            + " & ".join(str(x).capitalize() for x in groupby),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        # xaxis1_rangeslider_visible=True,
        width=1850,
        height=950,
        template="presentation",
        legend_traceorder="reversed",
    )

    fig2.update_yaxes(
        title=str(yaxis_unit) + "CO2e",
        type="linear"
        if yaxis_type == "Linear"
        or yaxis_type == "Cumulative"
        or yaxis_type == "% of Total"
        else "log",
    )

    if yaxis_type == "% of Total":
        fig2.update_yaxes(title="% of Total")
    elif yaxis_type == "Cumulative":
        fig2.update_yaxes(
            title="Cumulative Emissions Mitigated, " + str(yaxis_unit)
        )

    return fig, fig2
