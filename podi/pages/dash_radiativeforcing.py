import itertools

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(
    __name__,
    path="/RadiativeForcing",
    title="Radiative Forcing",
    name="Radiative Forcing",
)

# define year ranges of data and projections
data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100

# define dataset options
dataset = {"Radiative forcing": "forcing"}

# define chart output options
chart_output = ["Radiative forcing"]

# read in data
df = pd.DataFrame()
for i in dataset.values():
    df = pd.concat(
        [
            df,
            pd.read_parquet(
                "~/positive-disruption/podi/data/output/climate/climate_output_"
                + i
                + ".parquet"
            ),
        ]
    )


# combine_first for rows with same index
df = (
    df.groupby(level=df.index.names)
    .first()
    .combine_first(df)
    .drop_duplicates()
)

df = df.reset_index().astype(
    {k: "category" for k in df.index.names}
    | {j: "float32" for j in df.columns}
)

# define dataset index options that should not be used
index_exclude = ["variable", "unit"]

# define list of columns to use as index
clst = df.columns[
    (
        ~df.columns.isin(
            str(f"{i}") for i in range(data_start_year, proj_end_year + 1)
        )
    )
    & (~df.columns.isin(index_exclude))
].tolist()


# define dataset index options that should be default singular or
# multi-selected
clst_multi = {
    "model": False,
    "scenario": True,
    "region": True,
    "sector": True,
    "product_category": True,
    "product_long": True,
    "flow_category": True,
    "flow_long": True,
    "unit": False,
    "variable": False,
    "gas": True,
}

# set index
df.set_index(
    df.columns[
        (
            ~df.columns.isin(
                str(f"{i}") for i in range(data_start_year, proj_end_year + 1)
            )
        )
        & (~df.columns.isin(index_exclude))
    ].tolist(),
    inplace=True,
)

# drop unused columns
df.drop(columns=index_exclude, inplace=True)

# define list of data controls
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
                    df.reset_index()[level].unique().tolist()
                    if clst_multi[level]
                    else df.reset_index()[level].unique().tolist()[-1],
                    id=level,
                    multi=True,
                    style={
                        "maxHeight": "45.5px",
                        "overflow-y": "scroll",
                        "border": "1px solid #d6d6d6",
                        "border-radius": "5px",
                        "outline": "none",
                    },
                ),
            ],
            className="mb-3",
        )
    )

# define data_controls layout
data_controls = dbc.Card(
    [
        html.Label("Model Output", className="select-label"),
        html.Div(
            [
                dcc.Dropdown(
                    [{"label": i, "value": dataset[i]} for i in dataset],
                    [{"label": i, "value": dataset[i]} for i in dataset][0][
                        "value"
                    ],
                    id="dataset",
                ),
            ],
            className="mb-2",
        ),
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
                            data_start_year, proj_end_year + 1, 10
                        )
                    },
                ),
            ],
            className="mb-2",
        ),
        html.Div(lst),
    ],
    body=True,
)

# define chart controls layout
chart_controls = dbc.Card(
    dbc.Row(
        [
            dbc.Col(
                [
                    html.Label("Chart Output", className="select-label"),
                    html.Div(
                        [
                            dcc.Dropdown(
                                chart_output,
                                chart_output[0],
                                id="chart_output",
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Label("Group By", className="select-label"),
                    html.Div(
                        [
                            dcc.Dropdown(
                                clst,
                                id="groupby",
                                multi=True,
                            ),
                        ],
                        className="mb-2",
                    ),
                ]
            ),
            dbc.Col(
                [
                    html.Label("Y-Axis Type", className="select-label"),
                    html.Div(
                        [
                            dcc.Dropdown(
                                [
                                    "Linear",
                                    "Log",
                                    "Cumulative",
                                    "% of Total",
                                ],
                                "Linear",
                                id="yaxis_type",
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Label("Chart Type", className="select-label"),
                    html.Div(
                        [
                            dcc.Dropdown(
                                {"none": "line", "tonexty": "area"},
                                "none",
                                id="chart_type",
                            ),
                        ],
                        className="mb-2",
                    ),
                ]
            ),
        ]
    ),
    body=True,
)

# define layout
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(data_controls, md=3),
                dbc.Col(
                    [
                        dbc.Card(chart_controls),
                        html.Br(),
                        dbc.Card(
                            dcc.Graph(
                                id="graphic-radiativeforcing",
                                # style={"height": "100%"},
                            ),
                            style={"height": "77.2%"},
                        ),
                    ],
                    md=9,
                ),
            ],
        )
    ],
    fluid=True,
)


@callback(
    output=Output("graphic-radiativeforcing", "figure"),
    inputs=[
        Input("dataset", "value"),
        Input("date_range", "value"),
        Input("chart_output", "value"),
        Input("groupby", "value"),
        Input("yaxis_type", "value"),
        Input("chart_type", "value"),
    ]
    + [
        Input(component_id=i, component_property="value")
        for i in df.index.names
    ],
)
def update_graph(
    dataset,
    date_range,
    chart_output,
    groupby,
    yaxis_type,
    chart_type,
    *clst,
):
    # define dictionaries used for chart formatting
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
            "<b>Year</b>: %{x}" + "<br><b>Emissions</b>: %{y:,.0f} " + "<br>"
        ),
    }
    yaxis_title = {
        "Concentration": "PPM",
        "Temperature change": "C",
        "Radiative forcing": "W/m2",
    }

    # read in data
    df = pd.read_parquet(
        "~/positive-disruption/podi/data/output/climate/climate_output_"
        + dataset
        + ".parquet"
    ).reset_index()

    # set index
    df.set_index(
        df.columns[
            (
                ~df.columns.isin(
                    str(f"{i}")
                    for i in range(data_start_year, proj_end_year + 1)
                )
            )
            & (~df.columns.isin(index_exclude))
        ].tolist(),
        inplace=True,
    )

    # combine_first for rows with same index
    df = (
        df.groupby(level=df.index.names)
        .first()
        .combine_first(df)
        .drop_duplicates()
    )

    # drop unused columns
    df.drop(columns=index_exclude, inplace=True)

    # make groupby an array if it is not already
    if not isinstance(groupby, list):
        groupby = [groupby] if groupby else []

    # prevent error if groupby is empty
    if not groupby:
        groupby = ["scenario"]

    # choose chart_output
    filtered_df = (
        df.loc[clst, :]
        .groupby(groupby)
        .sum(numeric_only=True)
        .loc[:, str(date_range[0]) : str(date_range[1])]
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
        value_name="value",
    ).astype(
        {k: "category" for k in groupby} | {"year": "int", "value": "float32"}
    )

    fig = go.Figure()

    i = 0

    for sub in (
        filtered_df.sort_values("value", ascending=False)[groupby]
        .drop_duplicates()
        .values
    ):
        if isinstance(sub, str):
            name = str(sub).capitalize()
        else:
            name = ", ".join(str(x).capitalize() for x in sub)

        fig.add_trace(
            go.Scatter(
                name=name,
                line=dict(
                    width=3,
                    color=chart_template["linecolor"][i],
                    dash="dashdot",
                ),
                x=filtered_df[
                    (filtered_df["year"] >= data_end_year + 3)
                    & (filtered_df["year"] <= date_range[1])
                ]["year"].drop_duplicates(),
                y=pd.DataFrame(
                    filtered_df[
                        (filtered_df["year"] >= data_end_year + 3)
                        & (filtered_df["year"] <= date_range[1])
                    ]
                )
                .set_index(groupby)
                .loc[sub]["value"],
                fill=chart_type,
                stackgroup=stack_type[chart_type],
                showlegend=True,
                hovertemplate=chart_template["hovertemplate"],
                fillcolor=chart_template["fillcolor"][i],
                groupnorm=groupnorm,
            )
        )
        i += 1

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black", dash="solid"),
            x=filtered_df[
                (filtered_df["year"] >= date_range[0])
                & (filtered_df["year"] <= data_end_year + 3)
            ]["year"].drop_duplicates(),
            y=pd.Series(
                filtered_df[
                    (filtered_df.year >= date_range[0])
                    & (filtered_df.year <= data_end_year + 3)
                    & (filtered_df.scenario == "baseline")
                ]
                .groupby("year")
                .sum(numeric_only=True)["value"]
                .values,
                index=filtered_df[
                    (filtered_df["year"] >= date_range[0])
                    & (filtered_df["year"] <= data_end_year + 3)
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
        x0=max(data_end_year + 3, date_range[0]),
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
            "text": "<b>"
            + chart_output
            + "</b>, grouped by "
            + "<b>"
            + " & ".join(str(x).capitalize() for x in groupby),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        template="plotly_white",
        margin=dict(t=25, b=0, l=0, r=0),
    )

    fig.update_yaxes(
        title=yaxis_title[chart_output],
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
        fig.update_yaxes(title="Cumulative Climate")

    return fig
