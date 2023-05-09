import itertools
import os

import dash
import dash_bootstrap_components as dbc
import numpy as np
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
    assets_folder="assets",
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
    "climate_output_concentration": "GHG Concentration",
    "climate_output_temperature": "Temperature Change",
    # "climate_output_forcing": "Radiative Forcing",
    "technology_adoption_output": "Technology Adoption Rates",
}

index_names = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "flow_category",
    "flow_long",
    "variable",
    "gas",
]

# make layout
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
            ],
        ),
        html.Div(
            children=[
                dbc.Container(
                    fluid=True,
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                html.Label(
                                                    "Model Output",
                                                    id="model-output",
                                                    className="select-label",
                                                ),
                                                dbc.Tooltip(
                                                    "Select the model output to view",
                                                    target="model-output",
                                                    placement="top",
                                                    style={
                                                        "font-size": "0.8rem"
                                                    },
                                                ),
                                                dcc.Dropdown(
                                                    id="model_output",
                                                    options=[
                                                        {
                                                            "label": model_output[
                                                                i
                                                            ],
                                                            "value": i,
                                                        }
                                                        for i in model_output
                                                    ],
                                                    value=list(
                                                        model_output.keys()
                                                    )[0],
                                                    clearable=False,
                                                    className="mb-2",
                                                ),
                                                html.Label(
                                                    "Date Range",
                                                    id="date-range",
                                                    className="select-label",
                                                ),
                                                dbc.Tooltip(
                                                    "Select the date range to view",
                                                    target="date-range",
                                                    placement="top",
                                                    style={
                                                        "font-size": "0.8rem"
                                                    },
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
                                                                str(year): {
                                                                    "label": str(
                                                                        year
                                                                    ),
                                                                    "style": {
                                                                        "color": "black",
                                                                        "font-size": "12px",
                                                                        "white-space": "nowrap",
                                                                        "transform": "rotate(45deg)",
                                                                        # "font-weight": "bold",
                                                                    },
                                                                }
                                                                for year in range(
                                                                    data_start_year,
                                                                    proj_end_year
                                                                    + 1,
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
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                    },
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.Tabs(
                                                    children=[
                                                        dbc.Tab(
                                                            label="Data",
                                                            tab_id="data-tab",
                                                            children=[
                                                                dbc.Card(
                                                                    html.Div(
                                                                        id="graph_controls"
                                                                    ),
                                                                    body=True,
                                                                ),
                                                                html.Br(),
                                                                dbc.Card(
                                                                    dcc.Graph(
                                                                        id="output_graph",
                                                                        figure={},
                                                                    ),
                                                                ),
                                                            ],
                                                        ),
                                                        dbc.Tab(
                                                            label="Additional",
                                                            tab_id="additional-tab",
                                                            children=[
                                                                html.Div(
                                                                    children=[
                                                                        html.Div(
                                                                            children=[
                                                                                html.Iframe(
                                                                                    src="https://www.metaculus.com/questions/embed/2563/?theme=theme-light",
                                                                                    style={
                                                                                        "width": "600px",
                                                                                        "height": "300px",
                                                                                        "border": "none",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "display": "inline-block",
                                                                                "vertical-align": "top",
                                                                                "margin-right": "10px",
                                                                            },
                                                                        ),
                                                                        html.Div(
                                                                            children=[
                                                                                html.Iframe(
                                                                                    src="https://www.metaculus.com/questions/embed/3742/?theme=theme-light",
                                                                                    style={
                                                                                        "width": "600px",
                                                                                        "height": "300px",
                                                                                        "border": "none",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "display": "inline-block",
                                                                                "vertical-align": "top",
                                                                            },
                                                                        ),
                                                                        html.Div(
                                                                            children=[
                                                                                html.Iframe(
                                                                                    src="https://forecasts.kalshi.com/events/GTEMP-23/forecast_card",
                                                                                    style={
                                                                                        "width": "600px",
                                                                                        "height": "400px",
                                                                                        "border": "none",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "display": "inline-block",
                                                                                "vertical-align": "top",
                                                                            },
                                                                        ),
                                                                        html.Div(
                                                                            children=[
                                                                                html.Iframe(
                                                                                    src="https://metaforecast.org/questions/embed/goodjudgmentopen-2590",
                                                                                    style={
                                                                                        "width": "600px",
                                                                                        "height": "300px",
                                                                                        "border": "none",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "display": "inline-block",
                                                                                "vertical-align": "top",
                                                                            },
                                                                        ),
                                                                    ],
                                                                    style={
                                                                        "textAlign": "center",
                                                                        "border": "none",
                                                                    },
                                                                )
                                                            ],
                                                        ),
                                                    ]
                                                )
                                            ]
                                        ),
                                        html.Br(),
                                        dbc.Card(
                                            children=[
                                                html.Div(
                                                    children=[
                                                        html.Iframe(
                                                            src="https://app.wonderchat.io/chatbot/clgo3z4gv00k1mc0kplyvv4j6",
                                                            style={
                                                                "width": "100%",
                                                                "height": "300px",
                                                                "border": "none",
                                                                "border-radius": "30px",
                                                            },
                                                        ),
                                                    ],
                                                )
                                            ],  # make the card corner radius larger and transparent background
                                            style={
                                                "border-radius": "10px",
                                                "background-color": "rgba(0,0,0,0)",
                                            },
                                        ),
                                    ],
                                    md=9,
                                    style={
                                        "display": "flex",
                                        "flexDirection": "column",
                                    },
                                ),
                            ],
                            style={"height": "100vh", "display": "flex"},
                        ),
                    ],
                ),
                # Add hidden divs for unused data controls
                html.Div(id="unused_data_controls", style={"display": "none"}),
            ],
            className="dbc",
            style={
                "height": "100vh",
                "display": "flex",
                "flexDirection": "column",
            },
        ),
    ],
    className="dbc",
    style={
        "height": "100vh",
        "display": "flex",
        "flexDirection": "column",
    },
)


# populate data and graph control options based on model output selection
@app.callback(
    output=[
        Output("data_controls", "children"),
        Output("unused_data_controls", "children"),
        Output("graph_controls", "children"),
    ],
    inputs=[Input("model_output", "value")],
)
def set_data_and_chart_control_options(model_output):
    # define graph output options
    graph_output_dict = {
        "energy_output": ["Energy Supply & Demand"],
        "emissions_output_co2e": ["Emissions", "Emissions Mitigated"],
        "climate_output_concentration": [
            "GHG Concentration",
            "CO2 Concentration Community Prediction",
        ],
        "climate_output_temperature": ["Temperature Change"],
        "climate_output_forcing": ["Radiative Forcing"],
        "technology_adoption_output": ["Technology Adoption Rates"],
    }

    # define graph output default value
    graph_output_default_dict = {
        "energy_output": "Energy Supply & Demand",
        "emissions_output_co2e": "Emissions",
        "climate_output_concentration": "GHG Concentration",
        "climate_output_temperature": "Temperature Change",
        "climate_output_forcing": "Radiative Forcing",
        "technology_adoption_output": "Technology Adoption Rates",
    }

    # define groupby_set options
    groupby_set_options_dict = {
        "energy_output": [
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Sector", "value": "sector"},
            {"label": "Product Category", "value": "product_category"},
            {"label": "Product", "value": "product_long"},
            {"label": "Flow", "value": "flow_long"},
        ],
        "emissions_output_co2e": [
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Sector", "value": "sector"},
            {"label": "Product Category", "value": "product_category"},
            {"label": "Product", "value": "product_long"},
            {"label": "Flow Category", "value": "flow_category"},
            {"label": "Flow", "value": "flow_long"},
        ],
        "afolu_output": [
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Sector", "value": "sector"},
            {"label": "Product Category", "value": "product_category"},
            {"label": "Product", "value": "product_long"},
            {"label": "Flow", "value": "flow_long"},
        ],
        "climate_output_concentration": [
            {"label": "Model", "value": "model"},
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Gas", "value": "gas"},
        ],
        "climate_output_temperature": [
            {"label": "Model", "value": "model"},
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Gas", "value": "gas"},
        ],
        "climate_output_forcing": [
            {"label": "Model", "value": "model"},
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Gas", "value": "gas"},
        ],
        "technology_adoption_output": [
            {"label": "Model", "value": "model"},
            {"label": "Scenario", "value": "scenario"},
            {"label": "Region", "value": "region"},
            {"label": "Sector", "value": "sector"},
            {"label": "Product Category", "value": "product_category"},
            {"label": "Product", "value": "product_long"},
            {"label": "Flow", "value": "flow_long"},
        ],
    }

    # define groupby_set default value
    groupby_set_default_dict = {
        "energy_output": ["sector", "product_long"],
        "emissions_output_co2e": ["sector", "product_long"],
        "afolu_output": "flow_long",
        "climate_output_concentration": ["scenario", "gas"],
        "climate_output_temperature": "scenario",
        "climate_output_forcing": "scenario",
        "technology_adoption_output": "product_long",
    }

    # define yaxis_type options
    yaxis_type_options_dict = {
        "energy_output": [
            "Linear",
            "Log",
            "Cumulative",
            "% of Cumulative at Final Year",
            "% of Annual Total",
            "% Change YOY",
            "% of Maximum Value",
            "% of Final Year Value",
        ],
        "emissions_output_co2e": [
            "Linear",
            "Log",
            "Cumulative",
            "% of Cumulative at Final Year",
            "% of Annual Total",
            "% Change YOY",
            "% of Maximum Value",
            "% of Final Year Value",
        ],
        "afolu_output": [
            "Linear",
            "Log",
            "Cumulative",
            "% of Cumulative at Final Year",
            "% of Annual Total",
            "% Change YOY",
            "% of Maximum Value",
            "% of Final Year Value",
        ],
        "climate_output_concentration": ["Linear", "Log", "% Change YOY"],
        "climate_output_temperature": ["Linear", "Log", "% Change YOY"],
        "climate_output_forcing": ["Linear", "Log", "% Change YOY"],
        "technology_adoption_output": [
            "Linear",
            "Log",
            "Cumulative",
            "% of Cumulative at Final Year",
            "% Change YOY",
            "% of Maximum Value",
            "% of Final Year Value",
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
        "technology_adoption_output": "% of Cumulative at Final Year",
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
        "technology_adoption_output": [
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
        "technology_adoption_output": "none",
    }

    graph_output_options = graph_output_dict[model_output]

    graph_output_default = graph_output_default_dict[model_output]

    groupby_set_options = groupby_set_options_dict[model_output]

    groupby_set_default = groupby_set_default_dict[model_output]

    yaxis_type_options = yaxis_type_options_dict[model_output]

    yaxis_type_default = yaxis_type_default_dict[model_output]

    graph_type_options = graph_type_options_dict[model_output]

    graph_type_default = graph_type_default_dict[model_output]

    # define custom default selections for data_controls
    df_index_custom_default_dict = {
        "energy_output": {"flow_category": ["Final consumption"]},
        # "emissions_output_co2e": {
        #     "region": [],
        #     "sector": [],
        #     "product_long": [],
        #     "flow_category": [],
        #     "flow_long": [],
        # },
        "climate_output_concentration": {
            "scenario": ["baseline", "pathway"],
            "gas": ["CO2", "CH4", "N2O"],
        },
        "climate_output_temperature": {
            "scenario": ["baseline", "pathway"],
            "gas": ["All"],
        },
        "climate_output_forcing": {
            "scenario": ["baseline", "pathway"],
            "gas": ["CO2", "CH4", "N2O"],
        },
    }

    # if model_output has a custom default value, use it
    if model_output in df_index_custom_default_dict:
        df_index_custom_default = df_index_custom_default_dict[model_output]
    else:
        df_index_custom_default = {}

    # read in data
    expanded_home_path = os.path.expanduser("~/positive-disruption/podi/data/")
    if os.path.isdir(expanded_home_path):
        data_path = expanded_home_path
    elif os.path.isdir("data/"):
        data_path = "data/"
    else:
        raise FileNotFoundError("Data directory not found")

    df = pd.read_parquet(os.path.join(data_path, model_output + ".parquet"))
    index_dtypes = {k: "category" for k in df.index.names}
    column_dtypes = {j: "float32" for j in df.columns}
    dtypes = {**index_dtypes, **column_dtypes}
    df = df.reset_index().astype(dtypes)

    df = pd.read_parquet(os.path.join(data_path, model_output + ".parquet"))
    index_dtypes = {k: "category" for k in df.index.names}
    column_dtypes = {j: "float32" for j in df.columns}
    dtypes = {**index_dtypes, **column_dtypes}
    df = df.reset_index().astype(dtypes)

    # define model_output index options that should not be used
    df_index_exclude_dict = {
        "energy_output": [
            "product_category",
            "flow_category",
            "product_short",
            "flow_short",
            "unit",
        ],
        "emissions_output_co2e": [
            "product_category",
            "flow_category",
            # "flow_long",
            "product_short",
            "flow_short",
            "unit",
        ],
        "afolu_output": ["product_short", "flow_short", "unit"],
        "climate_output_concentration": ["unit"],
        "climate_output_temperature": ["unit"],
        "climate_output_forcing": ["unit"],
        "technology_adoption_output": [
            "product_category",
            "flow_category",
            "flow_long",
            "product_short",
            "flow_short",
            "unit",
        ],
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
        "climate_output_concentration": ["GHG Concentration"],
        "climate_output_temperature": ["Temperature Change"],
        "climate_output_forcing": ["Radiative Forcing"],
        "technology_adoption_output": ["Technology Adoption Rates"],
    }

    # define tooltip descriptions of data controls and graph_controls dropdowns
    tooltip_dict = {
        "model": "Select the model to view",
        "scenario": "Select the scenario to view",
        "region": "Select the region to view",
        "sector": "A category of industries or ecosystems that share common characteristics.",
        "product_category": "The product category filter is offered to enable visualizations that are simplified by 'bundling up' products with similar characteristics into a smaller number of categories",
        "product_long": "A good or service, which may be tangible (e.g. coal) or intangible (e.g. avoided peat impacts)",
        "flow_category": "The flow category filter is offered to enable visualizations that are simplified by 'bundling up' flows with similar characteristics into a smaller number of categories.",
        "flow_long": "The path that a product takes. It can be thought of as 'where the product ends up when it is used'.",
        "variable": "<>",
        "gas": "Select the gas to view",
        "group-by": "The graph will display data aggregated by the items selected here",
        "yaxis-type": "Select the y-axis type to view",
        "graph-type": "Select the graph type to view",
        "graph-output": "Select the graph output to view",
    }

    # drop the columns that are numerical and not in the range of data_start_year to proj_end_year
    df.drop(
        columns=[
            col
            for col in df.columns
            if col.isdigit()
            and int(col) not in range(data_start_year, proj_end_year + 1)
        ],
        inplace=True,
    )

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

    # define list of data controls, labels, and tooltips
    div_elements = []

    for level in df.index.names:
        # if df_index_custom_default is defined and level is in
        # df_index_custom_default, use df_index_custom_default[level] as
        # default_value
        if df_index_custom_default and level in df_index_custom_default:
            default_value = df_index_custom_default[level]
        elif df_index_multi[level]:
            default_value = df.reset_index()[level].unique().tolist()
        else:
            default_value = df.reset_index()[level].unique().tolist()[-1]

        div_elements.append(
            html.Label(
                level.replace("_", " ").replace("long", "").title(),
                id=level + "-label",
                className="select-label",
            )
        )

        if not type(default_value) is list:
            default_value = [default_value]

        div_elements.append(
            html.Div(
                [
                    # dcc.Checklist(
                    #     id="all-or-none",
                    #     options=[{"label": "Select All", "value": "All"}],
                    #     value=[],
                    #     labelStyle={"display": "inline-block"},
                    # ),
                    dcc.Checklist(
                        id=level,
                        options=df.reset_index()[level].unique().tolist(),
                        value=default_value,
                        labelStyle={
                            "display": "block",
                            "color": "black"
                        },
                    ),
                ],
                style={
                    "maxHeight": "200px",
                    "overflow-y": "scroll",
                    "border": "1px solid #d6d6d6",
                }
            )
        )

        

        # div_elements.append(
        #     html.Div(
        #         [
        #             dcc.Dropdown(
        #                 df.reset_index()[level].unique().tolist(),
        #                 default_value,
        #                 id=level,
        #                 multi=True,
        #                 style={
        #                     # "maxHeight": "45px",
        #                     # "overflow-y": "scroll",
        #                     # "border": "1px solid #d6d6d6",
        #                     # "border-radius": "5px",
        #                     "outline": "none",
        #                 },
        #             ),
        #         ],
        #         className="mb-0" if level == df.index.names[-1] else "mb-3",
        #     )
        # )

        div_elements.append(
            dbc.Tooltip(
                tooltip_dict[level],
                target=level + "-label",
                placement="top",
                style={"font-size": "0.8rem"},
            )
        )

    # define data_controls layout
    data_controls = html.Div(
        div_elements
    )

    #

    # define graph controls layout
    graph_controls = html.Div(
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label(
                            "Graph Output",
                            id="graph-output",
                            className="select-label",
                        ),
                        dbc.Tooltip(
                            tooltip_dict["graph-output"],
                            target="graph-output",
                            placement="top",
                            style={"font-size": "0.8rem"},
                        ),
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
                        html.Label(
                            "Group By", id="group-by", className="select-label"
                        ),
                        dbc.Tooltip(
                            tooltip_dict["group-by"],
                            target="group-by",
                            placement="top",
                            style={"font-size": "0.8rem"},
                        ),
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
                        html.Label(
                            "Y-Axis Type",
                            id="yaxis-type",
                            className="select-label",
                        ),
                        dbc.Tooltip(
                            tooltip_dict["yaxis-type"],
                            target="yaxis-type",
                            placement="top",
                            style={"font-size": "0.8rem"},
                        ),
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
                        html.Label(
                            "Graph Type",
                            id="graph-type",
                            className="select-label",
                        ),
                        dbc.Tooltip(
                            tooltip_dict["graph-type"],
                            target="graph-type",
                            placement="top",
                            style={"font-size": "0.8rem"},
                        ),
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

    # define unused data controls layout as the values in index_names that are not in df.index.names
    unused_data_controls = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        [],
                        [],
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
                className="mb-0",
            )
            for level in index_names
            if level not in df.index.names
        ]
    )

    return (data_controls, unused_data_controls, graph_controls)


"""
# update data controls based on selections in other data controls
@app.callback(
    output=[
        Output("data_controls", "children", allow_duplicate=True),
        Output("unused_data_controls", "children", allow_duplicate=True),
    ],
    inputs=[
        Input("model_output", "value"),
        Input("data_controls", "children"),
    ],
    state=[*[State(f"{level}", "value") for level in index_names]],
    prevent_initial_call=True,
)
def update_data_controls(
    model_output,
    data_controls_values,
    *index_values,
):
    # read in data
    expanded_home_path = os.path.expanduser("~/positive-disruption/podi/data/")
    if os.path.isdir(expanded_home_path):
        data_path = expanded_home_path
    elif os.path.isdir("data/"):
        data_path = "data/"
    else:
        raise FileNotFoundError("Data directory not found")

    df = pd.read_parquet(
        os.path.join(data_path, model_output + ".parquet")
    )
    index_dtypes = {k: "category" for k in df.index.names}
    column_dtypes = {j: "float32" for j in df.columns}
    dtypes = {**index_dtypes, **column_dtypes}
    df = df.reset_index().astype(dtypes)


    # define tooltip descriptions of data controls and graph_controls dropdowns
    tooltip_dict = {
        "model": "Select the model to view",
        "scenario": "Select the scenario to view",
        "region": "Select the region to view",
        "sector": "A category of industries or ecosystems that share common characteristics.",
        "product_category": "The product category filter is offered to enable visualizations that are simplified by 'bundling up' products with similar characteristics into a smaller number of categories",
        "product_long": "A good or service, which may be tangible (e.g. coal) or intangible (e.g. avoided peat impacts)",
        "flow_category": "The flow category filter is offered to enable visualizations that are simplified by 'bundling up' flows with similar characteristics into a smaller number of categories.",
        "flow_long": "The path that a product takes. It can be thought of as 'where the product ends up when it is used'.",
        "variable": "<>",
        "gas": "Select the gas to view",
        "group-by": "The graph will display data aggregated by the items selected here",
        "yaxis-type": "Select the y-axis type to view",
        "graph-type": "Select the graph type to view",
        "graph-output": "Select the graph output to view",
    }

    # drop the columns that are numerical and not in the range of data_start_year to proj_end_year
    df.drop(
        columns=[
            col
            for col in df.columns
            if col.isdigit()
            and int(col) not in range(data_start_year, proj_end_year + 1)
        ],
        inplace=True,
    )

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

    # filter df based on index_values. Retain the old behavior, use `series.index.isin(sequence, level=1)` if `index_values` is a list of lists
    # drop empty arrays from index_values
    index_values = [x for x in index_values if x]

    # index_values is split into half its length since state values are stored there and not needed
    # df_selected = df.loc[tuple([*index_values[: len(index_values) // 2]])]
    df_selected = df.loc[tuple([*index_values])]

    # define list of data controls
    index_to_data_controls = []
    for level in df.index.names:
        # if df.reset_index()[level].unique().tolist() is one item, define default_value as the string inside the list:
        if len(df_selected.reset_index()[level].unique().tolist()) == 1:
            selected_values = (
                df_selected.reset_index()[level].unique().tolist()[0]
            )
        else:
            selected_values = (
                df_selected.reset_index()[level].unique().tolist()
            )

        index_to_data_controls.append(
            html.Div(
                [
                    dcc.Dropdown(
                        df.reset_index()[level].unique().tolist(),
                        selected_values,
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
                id=level + "-label",
                className="select-label",
            )
        )

    # make tooltips for each data control label
    index_to_data_controls_tooltips = []
    for level in df.index.names:
        index_to_data_controls_tooltips.append(
            dbc.Tooltip(
                tooltip_dict[level],
                target=level + "-label",
                placement="top",
                style={"font-size": "0.8rem"},
            )
        )

    # define data_controls layout
    data_controls = html.Div(
        [
            element
            for pair in zip(
                index_to_data_controls_labels,
                index_to_data_controls_tooltips,
                index_to_data_controls,
            )
            for element in pair
        ]
    )

    # define unused data controls layout as the values in index_names that are not in df.index.names
    unused_data_controls = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        [],
                        [],
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
                className="mb-0",
            )
            for level in index_names
            if level not in df.index.names
        ]
    )

    return (data_controls, unused_data_controls)
"""


# update graph
@app.callback(
    output=[Output("output_graph", "figure")],
    inputs=[
        Input("data_controls", "children"),
        Input("unused_data_controls", "children"),
        Input("model_output", "value"),
        Input("date_range", "value"),
        Input("graph_output", "value"),
        Input("groupby_set", "value"),
        Input("yaxis_type", "value"),
        Input("graph_type", "value"),
        *[Input(f"{level}", "value") for level in index_names],
    ],
)
def update_output_graph(
    data_controls_values,
    unused_data_controls_values,
    model_output,
    date_range,
    graph_output,
    groupby_set,
    yaxis_type,
    graph_type,
    *index_values,
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
            "<b>Year</b>: %{x}" + "<br><b>Value</b>: %{y:,.0f} " + "<br>"
        ),
    }

    model_output_dict = {
        "energy_output": "Energy Supply & Demand",
        "emissions_output_co2e": "GHG Emissions",
        "climate_output_concentration": "GHG Concentration",
        "climate_output_temperature": "Temperature Change",
        "climate_output_forcing": "Radiative Forcing",
        "technology_adoption_output": "Technology Adoption Rates",
    }

    # define model_output index options that should not be used
    df_index_exclude_dict = {
        "energy_output": [
            "product_category",
            "flow_category",
            "product_short",
            "flow_short",
            "unit",
        ],
        "emissions_output_co2e": [
            "product_category",
            "flow_category",
            # "flow_long",
            "product_short",
            "flow_short",
            "unit",
        ],
        "afolu_output": ["product_short", "flow_short", "unit"],
        "climate_output_concentration": ["unit"],
        "climate_output_temperature": ["unit"],
        "climate_output_forcing": ["unit"],
        "technology_adoption_output": [
            "product_category",
            "flow_category",
            "flow_long",
            "product_short",
            "flow_short",
            "unit",
        ],
    }

    # define dict of definitions of each subvertical
    subvertical_dict = {
        "Electric Power": "This is the electricity sector. It includes generation, transmission, and distribution of electricity. It also includes the use of electricity in the residential, commercial, and industrial sectors.",
        "Residential": "This is the residential sector. It includes the use of electricity in the residential sector.",
        "Commercial": "This is the commercial sector. It includes the use of electricity in the commercial sector.",
        "Industrial": "This is the industrial sector. It includes the use of electricity in the industrial sector.",
        "Transportation": "This is the transportation sector. It includes the use of electricity in the transportation sector.",
        "Agriculture": "This is the agriculture sector. It includes the use of electricity in the agriculture sector.",
        "Forests & Wetlands": "This is the forests & wetlands sector. It includes the use of electricity in the forests & wetlands sector.",
    }

    # drop empty index_values
    index_values = [value for value in index_values if value]

    # read in data
    expanded_home_path = os.path.expanduser("~/positive-disruption/podi/data/")
    if os.path.isdir(expanded_home_path):
        data_path = expanded_home_path
    elif os.path.isdir("data/"):
        data_path = "data/"
    else:
        raise FileNotFoundError("Data directory not found")

    df = pd.read_parquet(os.path.join(data_path, model_output + ".parquet"))
    index_dtypes = {k: "category" for k in df.index.names}
    column_dtypes = {j: "float32" for j in df.columns}
    dtypes = {**index_dtypes, **column_dtypes}
    df = df.reset_index().astype(dtypes)

    # store units before dropping
    units = df["unit"].unique().tolist()

    # drop the columns that are numerical and not in the range of data_start_year to proj_end_year
    df.drop(
        columns=[
            col
            for col in df.columns
            if col.isdigit()
            and int(col) not in range(data_start_year, proj_end_year + 1)
        ],
        inplace=True,
    )

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

    # check if df.loc[tuple([*index_values])] raises a KeyError, and if so, return an empty figure
    try:
        df.loc[tuple([*index_values])]
    except KeyError:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="No data available for the current set of dropdown selections",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    # prevent error if groupby_set is empty
    if not groupby_set:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="Select a variable to group by in the 'GROUP BY' menu above",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    # make groupby_set an array if it is not already
    if not isinstance(groupby_set, list):
        groupby_set = [groupby_set] if groupby_set else []

    # filter df based on index_values. Retain the old behavior, use `series.index.isin(sequence, level=1)` if `index_values` is a list of lists
    if isinstance(index_values[0], list):
        df = df[df.index.isin(index_values, level=1)]
    else:
        df = df.loc[tuple([*index_values])]

    # prevent error if all of the groupby_set selections each have less than 2 options
    try:
        all(
            len(df.index.get_level_values(groupby_name).unique()) < 2
            for groupby_name in groupby_set
        )
    except IndexError:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="At least one of the selections in the 'GROUP BY' menu must have more than one option with nonzero data.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    if all(
        len(index_values[df.index.names.index(groupby_name)]) < 2
        for groupby_name in groupby_set
    ):
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="At least one of the selections in the 'GROUP BY' menu must have more than one option with nonzero data.",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    # check if filtered_df.loc[tuple([*index_values])] raises a KeyError, and if so, return an empty figure
    try:
        filtered_df = (
            df.groupby(groupby_set)
            .sum(numeric_only=True)
            .loc[:, str(date_range[0]) : str(date_range[1])]
        ).T.fillna(0)
    except KeyError:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="No data available for the current set of dropdown selections",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    # choose graph_output
    filtered_df = (
        df.groupby(groupby_set)
        .sum(numeric_only=True)
        .loc[:, str(date_range[0]) : str(date_range[1])]
    ).T.fillna(0)

    # check if filtered_df raises an error
    if filtered_df.empty:
        fig = go.Figure()
        fig.update_layout(
            annotations=[
                dict(
                    text="No data available for the current set of dropdown selections",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(
                        size=24,
                        color="rgba(128, 128, 128, 0.5)",
                    ),
                    align="center",
                )
            ],
        )
        return (fig,)

    if yaxis_type == "Cumulative":
        filtered_df = filtered_df.cumsum()

    if yaxis_type == "% of Cumulative at Final Year":
        filtered_df = (
            filtered_df.cumsum()
            .div(filtered_df.sum(axis=0), axis=1)
            .replace([np.inf, -np.inf, 0], np.nan)
            * 100
        )

    if yaxis_type == "% of Annual Total":
        groupnorm = "percent"
        filtered_df[filtered_df < 0] = 0
        if graph_type == "Line":
            # Find the percent of the annual total for each year
            filtered_df = (
                filtered_df.div(filtered_df.sum(axis=1), axis=0).replace(
                    [np.inf, -np.inf, 0], np.nan
                )
                * 100
            )
    else:
        groupnorm = None

    if yaxis_type == "% Change YOY":
        filtered_df = (
            filtered_df.pct_change().replace([np.inf, -np.inf], np.nan) * 100
        )

    if yaxis_type == "% of Maximum Value":
        filtered_df = (
            filtered_df.div(filtered_df.max(axis=0), axis=1).replace(
                [np.inf, -np.inf, 0], np.nan
            )
            * 100
        )

    if yaxis_type == "% of Final Year Value":
        filtered_df = (
            filtered_df.div(filtered_df.iloc[-1], axis=1).replace(
                [np.inf, -np.inf, 0], np.nan
            )
            * 100
        )

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
                        align="center",
                    ),
                    cells=dict(
                        values=[filtered_df[k] for k in filtered_df.columns],
                        fill_color="lavender",
                        align="center",
                    ),
                )
            ]
        )

        return (fig,)

    # create graph based graph_output selection
    if graph_output == "Energy Supply & Demand":
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

            # Define trace_string as all of the values that match any string in subvertical_dict
            trace_string = [
                k for k in subvertical_dict.keys() if any(x in k for x in sub)
            ]

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year or the last year of historical data and dashdot after (if projections exist)
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub], : str(data_end_year)]["year"]
                        .values.dropna(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub], : str(data_end_year)]["value"]
                        .values.dropna(),
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"]
                        + f"{trace_string}",
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub], str(data_end_year) : str(proj_end_year)][
                            "year"
                        ]
                        .values,
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub], str(data_end_year) : str(proj_end_year)][
                            "value"
                        ]
                        .values,
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=False,
                        hovertemplate=graph_template["hovertemplate"]
                        + f"{trace_string}",
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub]]["value"]
                        .values,
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"]
                        + "<br>"
                        + f"{trace_string}",
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                    )
                )
            i += 1

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
            title=str(units[0]),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units[0]))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units[0])
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Emissions":
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

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=filtered_df["year"][
                            filtered_df["year"] <= data_end_year
                        ].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub], : str(data_end_year)]["value"]
                        .values,
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub]]["value"]
                        .values,
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=False,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
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
            title=str(units[0]),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units[0]))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units[0])
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Emissions Mitigated":
        # prevent confusing output if two scenarios are not selected
        if len(df.index.get_level_values("scenario").unique()) < 2:
            fig = go.Figure()
            fig.update_layout(
                annotations=[
                    dict(
                        text="Choose two scenarios to compare",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(
                            size=24,
                            color="rgba(128, 128, 128, 0.5)",
                        ),
                        align="center",
                    )
                ],
            )
            return (fig,)
        # prevent confusing output if groupby contains scenario
        if "scenario" in groupby_set:
            fig = go.Figure()
            fig.update_layout(
                annotations=[
                    dict(
                        text="Remove 'scenario' option from GROUP BY",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(
                            size=24,
                            color="rgba(128, 128, 128, 0.5)",
                        ),
                        align="center",
                    )
                ],
            )
            return (fig,)

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

        filtered_df2 = (
            df.groupby(groupby_set)
            .sum(numeric_only=True)
            .loc[:, str(date_range[0]) : str(date_range[1])]
        ).T.fillna(0)

        if yaxis_type == "Cumulative":
            filtered_df2 = filtered_df2.cumsum()

        if yaxis_type == "% of Cumulative at Final Year":
            filtered_df2 = (
                filtered_df2.div(filtered_df2.sum(axis=0), axis=1).replace(
                    [np.inf, -np.inf, 0], np.nan
                )
                * 100
            )

        if yaxis_type == "% of Annual Total":
            groupnorm = "percent"
            filtered_df2[filtered_df2 < 0] = 0
        else:
            groupnorm = None

        if yaxis_type == "% Change YOY":
            filtered_df2 = (
                filtered_df2.pct_change().replace([np.inf, -np.inf], np.nan)
                * 100
            )

        if yaxis_type == "% of Maximum Value":
            filtered_df2 = (
                filtered_df2.div(filtered_df2.max(axis=0), axis=1).replace(
                    [np.inf, -np.inf, 0], np.nan
                )
                * 100
            )

        if yaxis_type == "% of Final Year Value":
            filtered_df2 = (
                filtered_df2.div(filtered_df2.iloc[-1], axis=1).replace(
                    [np.inf, -np.inf, 0], np.nan
                )
                * 100
            )

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

        # if graph_type is 'Table', return a table
        if graph_type == "Table":
            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=list(filtered_df2.columns),
                            fill_color="paleturquoise",
                            align="left",
                        ),
                        cells=dict(
                            values=[
                                filtered_df2[k] for k in filtered_df2.columns
                            ],
                            fill_color="lavender",
                            align="left",
                        ),
                    )
                ]
            )

            return (fig,)

        fig = go.Figure()

        if yaxis_type not in ["Log", "Cumulative", "% of Annual Total"]:
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
                    name=name.replace("Co2", "CO<sub>2</sub>")
                    .replace("Ch4", "CH<sub>4</sub>")
                    .replace("N2o", "N<sub>2</sub>O"),
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

        if yaxis_type not in ["Log", "Cumulative", "% of Annual Total"]:
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
            title=str(units[0]),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units[0]))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units[0])
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "CO2 Concentration Community Prediction":
        fig = go.Figure()

        fig.add_layout_image(
            dict(
                source="https://www.metaculus.com/questions/embed/2563/",
                xref="x",
                yref="y",
                x=0,
                y=10,
                sizex=2,
                sizey=2,
                sizing="stretch",
                opacity=1,
                layer="above",
            )
        )

    elif graph_output == "Technology Adoption Rates":
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

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        mode="lines",
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=pd.DataFrame(
                            filtered_df[
                                filtered_df["year"]
                                >= max(data_end_year, date_range[0])
                            ]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"],
                        y=pd.DataFrame(
                            filtered_df[
                                filtered_df["year"]
                                >= max(data_end_year, date_range[0])
                            ]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        name=name,
                        mode="lines",
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=pd.DataFrame(
                            filtered_df[
                                filtered_df["year"]
                                <= min(data_end_year, date_range[1])
                            ]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"],
                        y=pd.DataFrame(
                            filtered_df[
                                filtered_df["year"]
                                <= min(data_end_year, date_range[1])
                            ]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=False,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )

                if i == 1:
                    fig.update_layout(legend=dict(traceorder="reversed"))

            else:
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"],
                        y=pd.DataFrame(filtered_df)
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                    )
                )
            i += 1

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
            title=str(units[0]),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units[0]))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units[0])
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    else:
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

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=pd.DataFrame(
                            filtered_df[filtered_df["year"] >= data_end_year]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"],
                        y=pd.DataFrame(
                            filtered_df[filtered_df["year"] >= data_end_year]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(
                            width=3,
                            color="black",
                            dash="solid",
                        ),
                        x=pd.DataFrame(
                            filtered_df[filtered_df["year"] <= data_end_year]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"],
                        y=pd.DataFrame(
                            filtered_df[filtered_df["year"] <= data_end_year]
                        )
                        .set_index(groupby_set)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True if i == 1 else False,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup="Historical",
                    )
                )

                if i == 1:
                    fig.update_layout(legend=dict(traceorder="reversed"))

            else:
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O"),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
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
            title=str(units[0]),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units[0]))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units[0])
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    return (fig,)


if __name__ == "__main__":
    app.run_server(
        debug=True, host="0.0.0.0", port=8050, dev_tools_hot_reload=False
    )
