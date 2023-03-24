import itertools

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

external_stylesheet = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

# Create Dash App
app = dash.Dash(
    __name__,
    use_pages=False,
    external_stylesheets=[external_stylesheet],
    title="Data Explorer",
    suppress_callback_exceptions=True,
)

# Expose Flask instance
server = app.server

# define year ranges of data and projections
data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100


# make dictionary of model_output options that uses common names for keys
model_output = {
    "energy_output": "Energy Supply & Demand",
    "emissions_output_co2e": "GHG Emissions",
    "afolu_output": "AFOLU Adoption",
    "climate_output_concentration": "GHG Concentration",
    "climate_output_temperature": "Temperature Change",
    "climate_output_forcing": "Radiative Forcing",
    "adoption_output_historical": "Adoption Rates",
}

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
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        html.Label(
                                            "Model Output",
                                            className="select-label",
                                        ),
                                        dcc.Dropdown(
                                            id="model_output",
                                            options=[
                                                {
                                                    "label": model_output[i],
                                                    "value": i,
                                                }
                                                for i in model_output
                                            ],
                                            value=list(model_output.keys())[0],
                                            clearable=False,
                                            className="mb-2",
                                        ),
                                        html.Label(
                                            "Date Range",
                                            className="select-label",
                                        ),
                                        html.Div(
                                            [
                                                dcc.RangeSlider(
                                                    id="date_range",
                                                    min=data_start_year,
                                                    max=proj_end_year,
                                                    value=[
                                                        data_start_year,
                                                        proj_end_year,
                                                    ],
                                                    marks={
                                                        str(year): str(year)
                                                        for year in range(
                                                            data_start_year,
                                                            proj_end_year + 1,
                                                            10,
                                                        )
                                                    },
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                        html.Div(id="data_controls"),
                                    ],
                                    className="mb-2",
                                    body=True,
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    html.Div(id="graph_controls"), body=True
                                ),
                                html.Br(),
                                dbc.Card(
                                    dcc.Graph(
                                        id="output_graph",
                                        style={"height": "100%"},
                                    ),
                                    style={"height": "77%"},
                                ),
                            ],
                            md=9,
                        ),
                    ],
                )
            ],
            fluid=True,
        ),
        dcc.Store(id="df_index_names", storage_type="session"),
    ],
    className="dbc",
)


@app.callback(
    output=[
        Output("data_controls", "children"),
        Output("graph_controls", "children"),
        Output("df_index_names", "data"),
    ],
    inputs=[Input("model_output", "value")],
)
def set_data_and_chart_control_options(model_output):
    # define graph output options
    graph_output_dict = {
        "energy_output": ["Energy Supply & Demand"],
        "emissions_output_co2e": ["Emissions", "Emissions Mitigated"],
        "afolu_output": ["AFOLU Adoption"],
        "climate_output_concentration": ["GHG Concentration"],
        "climate_output_temperature": ["Temperature Change"],
        "climate_output_forcing": ["Radiative Forcing"],
        "adoption_output_historical": ["Adoption Rates"],
    }

    # define graph output default value
    graph_output_default_dict = {
        "energy_output": "Energy Supply & Demand",
        "emissions_output_co2e": "Emissions",
        "afolu_output": "AFOLU Adoption",
        "climate_output_concentration": "GHG Concentration",
        "climate_output_temperature": "Temperature Change",
        "climate_output_forcing": "Radiative Forcing",
        "adoption_output_historical": "Adoption Rates",
    }

    # define groupby_set options
    groupby_set_options_dict = {
        "energy_output": [
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "flow_long",
        ],
        "emissions_output_co2e": [
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "flow_long",
        ],
        "afolu_output": [
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "flow_long",
        ],
        "climate_output_concentration": [
            "model",
            "scenario",
            "region",
            "variable",
            "gas",
        ],
        "climate_output_temperature": [
            "model",
            "scenario",
            "region",
            "variable",
            "gas",
        ],
        "climate_output_forcing": [
            "model",
            "scenario",
            "region",
            "variable",
            "gas",
        ],
        "adoption_output_historical": [
            "model",
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "flow_long",
        ],
    }

    # define groupby_set default value
    groupby_set_default_dict = {
        "energy_output": ["sector", "product_long"],
        "emissions_output_co2e": ["sector", "product_long"],
        "afolu_output": "flow_long",
        "climate_output_concentration": "scenario",
        "climate_output_temperature": "scenario",
        "climate_output_forcing": "scenario",
        "adoption_output_historical": "product_long",
    }

    # define yaxis_type options
    yaxis_type_options_dict = {
        "energy_output": ["Linear", "Log", "Cumulative", "% of Total"],
        "emissions_output_co2e": ["Linear", "Log", "Cumulative", "% of Total"],
        "afolu_output": ["Linear", "Log", "Cumulative", "% of Total"],
        "climate_output_concentration": ["Linear", "Log"],
        "climate_output_temperature": ["Linear", "Log"],
        "climate_output_forcing": ["Linear", "Log"],
        "adoption_output_historical": [
            "Linear",
            "Log",
            "Cumulative",
            "% of Total",
        ],
    }

    # define yaxis_type default value
    yaxis_type_default_dict = {
        "energy_output": "Linear",
        "emissions_output_co2e": "Linear",
        "afolu_output": "Linear",
        "climate_output_concentration": "Linear",
        "climate_output_temperature": "Linear",
        "climate_output_forcing": "Linear",
        "adoption_output_historical": "Linear",
    }

    # define graph_type options
    graph_type_options_dict = {
        "energy_output": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "emissions_output_co2e": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "afolu_output": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "climate_output_concentration": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "climate_output_temperature": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "climate_output_forcing": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
        "adoption_output_historical": [
            {"label": "Area", "value": "tonexty"},
            {"label": "Line", "value": "none"},
            {"label": "Table", "value": "Table"},
        ],
    }

    # define graph_type default value
    graph_type_default_dict = {
        "energy_output": "tonexty",
        "emissions_output_co2e": "tonexty",
        "afolu_output": "tonexty",
        "climate_output_concentration": "none",
        "climate_output_temperature": "none",
        "climate_output_forcing": "none",
        "adoption_output_historical": "none",
    }

    graph_output_options = graph_output_dict[model_output]

    graph_output_default = graph_output_default_dict[model_output]

    groupby_set_options = groupby_set_options_dict[model_output]

    groupby_set_default = groupby_set_default_dict[model_output]

    yaxis_type_options = yaxis_type_options_dict[model_output]

    yaxis_type_default = yaxis_type_default_dict[model_output]

    graph_type_options = graph_type_options_dict[model_output]

    graph_type_default = graph_type_default_dict[model_output]

    # read in data
    df = (
        pd.read_parquet(
            "~/positive-disruption/podi/data/" + model_output + ".parquet"
        )
        .reset_index()
        .astype(
            {
                k: "category"
                for k in pd.read_parquet(
                    "~/positive-disruption/podi/data/"
                    + model_output
                    + ".parquet"
                ).index.names
            }
            | {
                j: "float32"
                for j in pd.read_parquet(
                    "~/positive-disruption/podi/data/"
                    + model_output
                    + ".parquet"
                ).columns
            }
        )
    )

    # define model_output index options that should not be used
    df_index_exclude_dict = {
        "energy_output": ["product_short", "flow_short", "unit"],
        "emissions_output_co2e": ["product_short", "flow_short", "unit"],
        "afolu_output": ["product_short", "flow_short", "unit"],
        "climate_output_concentration": ["unit"],
        "climate_output_temperature": ["unit"],
        "climate_output_forcing": ["unit"],
        "adoption_output_historical": ["product_short", "flow_short", "unit"],
    }

    # define model_output index options that should be default singular or
    # multi-selected
    df_index_multi = {
        "model": False,
        "scenario": False,
        "region": True,
        "sector": True,
        "product_category": True,
        "product_long": True,
        "flow_category": True,
        "flow_long": True,
        "variable": False,
        "gas": True,
    }

    # define graph output options
    graph_output_dict = {
        "energy_output": ["Energy Supply & Demand"],
        "emissions_output_co2e": ["Emissions", "Emissions Mitigated"],
        "afolu_output": ["AFOLU Adoption"],
        "climate_output_concentration": ["GHG Concentration"],
        "climate_output_temperature": ["Temperature Change"],
        "climate_output_forcing": ["Radiative Forcing"],
        "adoption_output_historical": ["Adoption Rates"],
    }

    # store units before dropping
    units = df["unit"].unique().tolist()

    # set index
    df.set_index(
        df.columns[
            (
                ~df.columns.isin(
                    str(f"{i}")
                    for i in range(data_start_year, proj_end_year + 1)
                )
            )
            & (~df.columns.isin(df_index_exclude_dict[model_output]))
        ].tolist(),
        inplace=True,
    )

    # drop unused columns
    df.drop(columns=df_index_exclude_dict[model_output], inplace=True)

    # define list of data controls
    index_to_data_controls = []
    for level in df.index.names:
        index_to_data_controls.append(
            html.Div(
                [
                    dcc.Dropdown(
                        df.reset_index()[level].unique().tolist(),
                        df.reset_index()[level].unique().tolist()
                        if df_index_multi[level]
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
                className="mb-0" if level == df.index.names[-1] else "mb-3",
            )
        )

    index_to_data_controls_labels = []
    for level in df.index.names:
        index_to_data_controls_labels.append(
            html.Label(
                level.replace("_", " ").replace("long", "").title(),
                className="select-label",
            )
        )

    # define data_controls layout
    data_controls = html.Div(
        [
            element
            for pair in zip(
                index_to_data_controls_labels, index_to_data_controls
            )
            for element in pair
        ]
    )

    # define graph controls layout
    graph_controls = html.Div(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Graph Output", className="select-label"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    graph_output_options,
                                    value=graph_output_default,
                                    id="graph_output",
                                    clearable=False,
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.Label("Group By", className="select-label"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    groupby_set_options,
                                    value=groupby_set_default,
                                    id="groupby_set",
                                    multi=True,
                                    clearable=False,
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
                                    yaxis_type_options,
                                    yaxis_type_default,
                                    id="yaxis_type",
                                    clearable=False,
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.Label("Graph Type", className="select-label"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    graph_type_options,
                                    graph_type_default,
                                    id="graph_type",
                                    clearable=False,
                                ),
                            ],
                            className="mb-2",
                        ),
                    ]
                ),
            ]
        ),
    )

    return (data_controls, graph_controls, df.index.names)


@app.callback(
    output=[
        Output("output_graph", "figure"),
    ],
    inputs=[
        Input("data_controls", "children"),
        # Input("graph_controls", "children"),
        Input("model_output", "value"),
        Input("date_range", "value"),
        Input("graph_output", "value"),
        Input("groupby_set", "value"),
        Input("yaxis_type", "value"),
        Input("graph_type", "value"),
        # Input("df_index_names", "data"),
    ],
)
def update_output_graph(
    data_controls_values,
    # graph_controls_children,
    model_output,
    date_range,
    graph_output,
    groupby_set,
    yaxis_type,
    graph_type,
    # df_index_names,
):
    # define dictionaries used for graph formatting
    stack_type = {"none": None, "tonexty": "1"}
    graph_template = {
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

    model_output_dict = {
        "energy_output": "Energy Supply & Demand",
        "emissions_output_co2e": "GHG Emissions",
        "afolu_output": "AFOLU Adoption",
        "climate_output_concentration": "GHG Concentration",
        "climate_output_temperature": "Temperature Change",
        "climate_output_forcing": "Radiative Forcing",
        "adoption_output_historical": "Adoption Rates",
    }

    # define model_output index options that should not be used
    df_index_exclude_dict = {
        "energy_output": ["product_short", "flow_short", "unit"],
        "emissions_output_co2e": ["product_short", "flow_short", "unit"],
        "afolu_output": ["product_short", "flow_short", "unit"],
        "climate_output_concentration": ["unit"],
        "climate_output_temperature": ["unit"],
        "climate_output_forcing": ["unit"],
        "adoption_output_historical": ["product_short", "flow_short", "unit"],
    }

    # read in data
    df = pd.read_parquet(
        "~/positive-disruption/podi/data/" + model_output + ".parquet"
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
            & (~df.columns.isin(df_index_exclude_dict[model_output]))
        ].tolist(),
        inplace=True,
    )

    # drop unused columns
    df.drop(columns=df_index_exclude_dict[model_output], inplace=True)

    # prevent error if groupby_set is empty
    if not groupby_set:
        groupby_set = [""]

    # make groupby_set an array if it is not already
    if not isinstance(groupby_set, list):
        groupby_set = [groupby_set] if groupby_set else []

    # filter df based on data_controls_values
    data_controls_selection = []

    for child in data_controls_values["props"]["children"]:
        # check if the child has its own children
        if "children" in child["props"]:
            # loop through the child's children
            for grandchild in child["props"]["children"]:
                # check if the grandchild is a dropdown component
                if (
                    isinstance(grandchild, dict)
                    and grandchild.get("type") == "Dropdown"
                ):
                    # extract the value of the dropdown
                    value = grandchild["props"]["value"]
                    # append the value to the array of arrays
                    data_controls_selection.append(value)

    # filter df based on data_controls_values
    df = df.loc[tuple([*data_controls_selection])]

    # choose graph_output
    filtered_df = (
        df.groupby(groupby_set)
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
        var_name=groupby_set,
        value_name="value",
    ).astype(
        {k: "category" for k in groupby_set}
        | {"year": "int", "value": "float32"}
    )

    # if graph_type is 'Table', return a table
    if graph_type == "Table":
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(filtered_df.columns),
                        fill_color="paleturquoise",
                        align="left",
                    ),
                    cells=dict(
                        values=[filtered_df[k] for k in filtered_df.columns],
                        fill_color="lavender",
                        align="left",
                    ),
                )
            ]
        )

        return (fig,)

    # create graph based graph_output selection
    if graph_output == "Emissions":
        filtered_df = (
            df.groupby(groupby_set)
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
            var_name=groupby_set,
            value_name="value",
        ).astype(
            {k: "category" for k in groupby_set}
            | {"year": "int", "value": "float32"}
        )

        fig = go.Figure()

        i = 0

        for sub in (
            filtered_df.sort_values("value", ascending=False)[groupby_set]
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
                    line=dict(width=3, color=graph_template["linecolor"][i]),
                    x=filtered_df["year"].drop_duplicates(),
                    y=pd.DataFrame(filtered_df)
                    .set_index(groupby_set)
                    .loc[[sub]]["value"]
                    .values,
                    fill=graph_type,
                    stackgroup=stack_type[graph_type],
                    showlegend=True,
                    hovertemplate=graph_template["hovertemplate"],
                    fillcolor=graph_template["fillcolor"][i],
                    groupnorm=groupnorm,
                )
            )
            i += 1

        if graph_type not in ["none"]:
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
                    stackgroup=stack_type[graph_type],
                    showlegend=True,
                    hovertemplate=graph_template["hovertemplate"],
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
                "text": "<b>"
                + model_output_dict[model_output]
                + "</b>, grouped by "
                + "<b>"
                + " & ".join(
                    str(x.replace("_long", "")).capitalize()
                    for x in groupby_set
                ),
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
    elif graph_output == "Emissions Mitigated":
        filtered_df2 = (
            (
                (
                    df[(df.reset_index().scenario == "baseline").values]
                    .groupby(groupby_set)
                    .sum(numeric_only=True)
                    - (
                        df[(df.reset_index().scenario == "pathway").values]
                        .groupby(groupby_set)
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
            var_name=groupby_set,
            value_name="value",
        ).astype(
            {k: "category" for k in groupby_set}
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
                    hovertemplate=graph_template["hovertemplate"],
                    groupnorm=groupnorm,
                )
            )

        i = 0

        for groupby_set_value in (
            filtered_df2.sort_values("value", ascending=False)[groupby_set]
            .drop_duplicates()
            .squeeze()
            .values
        ):
            if isinstance(groupby_set_value, str):
                name = str(groupby_set_value).capitalize()
            else:
                name = ", ".join(
                    str(x).capitalize() for x in groupby_set_value
                )

            fig.add_trace(
                go.Scatter(
                    name=name,
                    line=dict(
                        width=3,
                        color=graph_template["linecolor"][i],
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
                    .set_index(groupby_set)
                    .loc[[groupby_set_value]]["value"]
                    .values,
                    fill="tonexty",
                    stackgroup="one",
                    hovertemplate=graph_template["hovertemplate"],
                    fillcolor=graph_template["fillcolor"][i],
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
                    hovertemplate=graph_template["hovertemplate"],
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
                    hovertemplate=graph_template["hovertemplate"],
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
                "text": "<b>"
                + graph_output
                + "</b>, grouped by "
                + "<b>"
                + " & ".join(
                    str(x.replace("_long", "")).capitalize()
                    for x in groupby_set
                ),
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
        )

        if yaxis_type == "% of Total":
            fig.update_yaxes(title="% of Total")
        elif yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative Emissions Mitigated")
    else:
        filtered_df = (
            df.groupby(groupby_set)
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
            var_name=groupby_set,
            value_name="value",
        ).astype(
            {k: "category" for k in groupby_set}
            | {"year": "int", "value": "float32"}
        )

        fig = go.Figure()

        i = 0

        for sub in (
            filtered_df.sort_values("value", ascending=False)[groupby_set]
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
                    line=dict(width=3, color=graph_template["linecolor"][i]),
                    x=filtered_df["year"].drop_duplicates(),
                    y=pd.DataFrame(filtered_df)
                    .set_index(groupby_set)
                    .loc[[sub]]["value"]
                    .values,
                    fill=graph_type,
                    stackgroup=stack_type[graph_type],
                    showlegend=True,
                    hovertemplate=graph_template["hovertemplate"],
                    fillcolor=graph_template["fillcolor"][i],
                    groupnorm=groupnorm,
                )
            )
            i += 1

        if graph_type not in ["none"]:
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
                    stackgroup=stack_type[graph_type],
                    showlegend=True,
                    hovertemplate=graph_template["hovertemplate"],
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
                "text": "<b>"
                + model_output_dict[model_output]
                + "</b>, grouped by "
                + "<b>"
                + " & ".join(
                    str(x.replace("_long", "")).capitalize()
                    for x in groupby_set
                ),
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

    return (fig,)


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
