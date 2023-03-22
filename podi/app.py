import itertools

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

external_stylesheet = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

# Create Dash App
app = dash.Dash(
    __name__,
    use_pages=False,
    external_stylesheets=[external_stylesheet],
    title="Data Explorer",
)

# Expose Flask instance
server = app.server

# define year ranges of data and projections
data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100

# define dataset options
dataset = [
    "energy_output",
    "emissions_output_co2e",
    "afolu_output",
    "concentration",
    "temperature",
    "forcing",
    "adoption_output",
]

# make dictionary of dataset options that uses common names for keys
dataset_dict = {
    "energy_output": "Energy Supply & Demand",
    "emissions_output_co2e": "GHG Emissions",
    "afolu_output": "AFOLU Adoption",
    "concentration": "GHG Concentration",
    "temperature": "Temperature Change",
    "forcing": "Radiative Forcing",
    "adoption_output": "Adoption Rates",
}

# define chart output options
chart_output = ["Emissions", "Emissions Mitigated"]

# read in data
df = (
    pd.read_parquet(
        "~/positive-disruption/podi/data/" + dataset[0] + ".parquet"
    )
    .reset_index()
    .astype(
        {
            k: "category"
            for k in pd.read_parquet(
                "~/positive-disruption/podi/data/" + dataset[0] + ".parquet"
            ).index.names
        }
        | {
            j: "float32"
            for j in pd.read_parquet(
                "~/positive-disruption/podi/data/" + dataset[0] + ".parquet"
            ).columns
        }
    )
)

# define dataset index options that should not be used
index_exclude = ["product_short", "flow_short", "unit"]

# define list of columns to use as index
clst = df.columns[
    (
        ~df.columns.isin(
            str(f"{i}") for i in range(data_start_year, proj_end_year + 1)
        )
    )
    & (~df.columns.isin(index_exclude))
].tolist()

# make a dictionary of clst that uses common names for keys
clst_dict = {
    "model": "Model",
    "scenario": "Scenario",
    "region": "Region",
    "sector": "Sector",
    "product_category": "Product Category",
    "product_long": "Product",
    "flow_category": "Flow Category",
    "flow_long": "Flow",
    "unit": "Unit",
}


# define dataset index options that should be default singular or
# multi-selected
clst_multi = {
    "model": False,
    "scenario": False,
    "region": True,
    "sector": True,
    "product_category": True,
    "product_long": True,
    "flow_category": True,
    "flow_long": True,
    # "unit": False,
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
                        "maxHeight": "45px",
                        "overflow-y": "scroll",
                        "border": "1px solid #d6d6d6",
                        "border-radius": "5px",
                        "outline": "none",
                    },
                ),
            ],
            className="mb-0" if level == df.index.names[-1] else "mb-4",
        )
    )

# define data_controls layout
data_controls = dbc.Card(
    [
        html.Label("Model Output", className="select-label"),
        html.Div(
            [
                dcc.Dropdown(
                    [
                        {"label": dataset_dict[i], "value": i}
                        for i in dataset_dict
                    ],
                    value=list(dataset_dict.keys())[0],
                    id="dataset",
                ),
            ],
            className="mb-4",
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
            className="mb-4",
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
                                [
                                    {"label": clst_dict[i], "value": i}
                                    for i in clst
                                ],
                                value=list(clst_dict.keys())[3],
                                id="groupby",
                                multi=True,
                            )
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
                                "tonexty",
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

app.layout = html.Div(
    [
        html.Meta(
            charSet="utf-8",
        ),
        html.Meta(
            name="description",
            content="",
        ),
        html.Meta(
            name="viewport",
            content="width=device-width, initial-scale=1.0",
        ),
        html.Title("Data Explorer"),
        html.Link(rel="preconnect", href="https://fonts.googleapis.com"),
        html.Link(rel="preconnect", href="https://fonts.gstatic.com"),
        html.Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:ital,wght@0,200;0,300;0,400;0,600;0,700;0,900;1,200;1,300;1,400;1,600;1,700;1,900&family=Josefin+Sans:wght@100;200;300;400;500;600;700&display=swap",
        ),
        html.Link(rel="stylesheet", href="css/bootstrap.min.css"),
        html.Link(rel="stylesheet", href="css/homepage.css"),
        html.Meta(name="twitter:card", content="summary_large_image"),
        html.Meta(
            name="twitter:title", content="Positive Disruption Data Explorer"
        ),
        html.Meta(
            name="twitter:description",
            content="The Positive Disruption model examines how adoption of low- and no-carbon technologies and practices can be expected to grow over the next 30 years.",
        ),
        html.Meta(
            name="twitter:image",
            content="https://epic-institute.github.io/data-explorer/img/social-twitter.png",
        ),
        # make a header
        html.Div(
            className="row",
            id="data-explorer",
            children=[
                html.Div(
                    className="row header",
                    children=[
                        html.Div(
                            [
                                html.A(
                                    html.Img(
                                        src=app.get_asset_url(
                                            "img/epic-logo.png"
                                        ),
                                        style={
                                            "width": "auto",
                                            "height": "40%",
                                        },
                                    ),
                                    href="https://epicinstitute.org/",
                                    target="_blank",
                                )
                            ],
                            className="col-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Data Explorer", className="header-item"
                                )
                            ],
                            className="col-9",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    html.A(
                                        "github",
                                        href="https://github.com/Epic-Institute/data-explorer",
                                        target="_blank",
                                    ),
                                    className="header-item",
                                )
                            ],
                            className="col-1",
                        ),
                        html.Div(
                            className="col-1",
                            children=[
                                html.Div(
                                    id="dropdown-about",
                                    children=[
                                        html.Span(
                                            "about",
                                            id="about-button",
                                            className="header-item",
                                        ),
                                        html.Div(
                                            id="about-details",
                                            children=[
                                                dbc.Tooltip(
                                                    children=[
                                                        html.P(
                                                            "Positive Disruption Data Explorer",
                                                            className="about-subtitle",
                                                        ),
                                                        html.P(
                                                            "The Data Explorer is a web-based tool that allows for easy navigation through the Positive Disruption model results to examine how adoption of low- and no-carbon technologies and practices in the energy, agriculture, and land-use sectors can be expected to grow over the next 30 years, and the effect they will have on the process of reversing climate change."
                                                        ),
                                                    ],
                                                    target="about-button",
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(className="row ei-border-bottom"),
            ],
        ),
        html.Br(),
        dbc.Container(
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
                                        id="graphic-emissions",
                                        style={"height": "100%"},
                                    ),
                                    style={"height": "78.3%"},
                                ),
                            ],
                            md=9,
                        ),
                    ],
                )
            ],
            fluid=True,
        ),
    ],
    className="dbc",
)


@callback(
    output=Output("graphic-emissions", "figure"),
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

    # read in data
    df = pd.read_parquet(
        "~/positive-disruption/podi/data/" + dataset + ".parquet"
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

    # drop unused columns
    df.drop(columns=index_exclude, inplace=True)

    # make groupby an array if it is not already
    if not isinstance(groupby, list):
        groupby = [groupby] if groupby else []

    # prevent error if groupby is empty
    if not groupby:
        groupby = ["sector"]

    # choose chart_output
    filtered_df = (
        df.loc[df.index.isin(clst, level=1)]
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

    if chart_output == "Emissions":
        filtered_df = (
            df.loc[df.index.isin(clst, level=1)]
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
            {k: "category" for k in groupby}
            | {"year": "int", "value": "float32"}
        )

        fig = go.Figure()

        i = 0

        for sub in (
            filtered_df.sort_values("value", ascending=False)[groupby]
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
                    .loc[[sub]]["value"]
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
                        .sum(numeric_only=True)["value"]
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
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title="MtCO2e",
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
            fig.update_yaxes(title="Cumulative Emissions")
    elif chart_output == "Emissions Mitigated":
        filtered_df2 = (
            (
                (
                    df[(df.reset_index().scenario == "baseline").values]
                    .groupby(groupby)
                    .sum(numeric_only=True)
                    - (
                        df[(df.reset_index().scenario == "pathway").values]
                        .groupby(groupby)
                        .sum(numeric_only=True)
                    )
                )
            ).loc[:, str(date_range[0]) : str(date_range[1])]
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
            value_name="value",
        ).astype(
            {k: "category" for k in groupby}
            | {"year": "int", "value": "float32"}
        )

        fig = go.Figure()

        if yaxis_type not in ["Log", "Cumulative", "% of Total"]:
            spacer = (
                df[(df.reset_index().scenario == "pathway").values]
                .loc[:, str(date_range[0]) : str(date_range[1])]
                .sum()
            )

            spacer.index = spacer.index.astype(int)

            fig.add_trace(
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

            fig.add_trace(
                go.Scatter(
                    name="Pathway",
                    line=dict(width=5, color="magenta", dash="dashdot"),
                    x=filtered_df[
                        (filtered_df["year"] >= data_end_year)
                        & (filtered_df["year"] <= date_range[1])
                    ]["year"].drop_duplicates(),
                    y=spacer[
                        (spacer.index.values >= data_end_year)
                        & (spacer.index.values <= date_range[1])
                    ]
                    * 0,
                    fill="none",
                    stackgroup="one",
                    showlegend=True,
                    hovertemplate=chart_template["hovertemplate"],
                    groupnorm=groupnorm,
                )
            )

        i = 0

        for groupby_value in (
            filtered_df2.sort_values("value", ascending=False)[groupby]
            .drop_duplicates()
            .squeeze()
            .values
        ):
            if isinstance(groupby_value, str):
                name = str(groupby_value).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in groupby_value)

            fig.add_trace(
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
                    .loc[[groupby_value]]["value"]
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
            fig.add_trace(
                go.Scatter(
                    name="Baseline",
                    line=dict(width=5, color="red", dash="dashdot"),
                    x=filtered_df[filtered_df["year"] >= data_end_year][
                        "year"
                    ].drop_duplicates(),
                    y=pd.Series(
                        filtered_df[(filtered_df.year >= data_end_year)]
                        .groupby("year")
                        .sum(numeric_only=True)["value"]
                        .values
                        * 0,
                        index=filtered_df[
                            filtered_df["year"] >= data_end_year
                        ]["year"].drop_duplicates(),
                    ).loc[data_end_year:],
                    fill="none",
                    stackgroup="one",
                    showlegend=True,
                    hovertemplate=chart_template["hovertemplate"],
                    groupnorm=groupnorm,
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=3, color="black"),
                    x=filtered_df[filtered_df["year"] <= data_end_year][
                        "year"
                    ].drop_duplicates(),
                    y=spacer[spacer.index.values <= data_end_year],
                    fill="none",
                    stackgroup="historical",
                    showlegend=True,
                    hovertemplate=chart_template["hovertemplate"],
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
                "text": "<b>Emissions Mitigated</b>, grouped by "
                + "<b>"
                + " & ".join(str(x).capitalize() for x in groupby),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            legend_traceorder="reversed",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title="MtCO2e",
            type="linear"
            if yaxis_type == "Linear"
            or yaxis_type == "Cumulative"
            or yaxis_type == "% of Total"
            else "log",
        )

        if yaxis_type == "% of Total":
            fig.update_yaxes(title="% of Total")
        elif yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative Emissions Mitigated")

    # add watermark
    fig.add_layout_image(
        dict(
            source="podi/assets/img/epic-logo-dark.png",
            xref="x",
            yref="y",
            x=0,
            y=1,
            sizex=2,
            sizey=2,
            sizing="stretch",
            opacity=0.5,
            layer="above",
        )
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
