import itertools
import os

import dash
import dash_bootstrap_components as dbc
import dask.dataframe as dd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dcc, html

from furl import furl

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

# define data
data = {}
default_values = {}

REGION_NAMES = {
    'world': 'World',
    'albania': 'Albania',
    'algeria': 'Algeria',
    'angola': 'Angola',
    'argentina': 'Argentina',
    'armenia': 'Armenia',
    'australi': 'Australia',
    'austria': 'Austria',
    'azerbaijan': 'Azerbaijan',
    'bahrain': 'Bahrain',
    'bangladesh': 'Bangladesh',
    'belarus': 'Belarus',
    'belgium': 'Belgium',
    'benin': 'Benin',
    'bolivia': 'Bolivia',
    'bosniaherz': 'Bosnia and Herzegovina',
    'botswana': 'Botswana',
    'brazil': 'Brazil',
    'brunei': 'Brunei',
    'bulgaria': 'Bulgaria',
    'mburkinafa': 'Burkina Faso',
    'myanmar': 'Burma',
    'cambodia': 'Cambodia',
    'cameroon': 'Cameroon',
    'canada': 'Canada',
    'mchad': 'Chad',
    'chile': 'Chile',
    'china': 'China',
    'colombia': 'Colombia',
    'costarica': 'Costa Rica',
    'coteivoire': "Cote d'Ivoire",
    'croatia': 'Croatia',
    'cuba': 'Cuba',
    'curacao': 'Curacao',
    'cyprus': 'Cyprus',
    'czech': 'Czech Republic',
    'congorep': 'Democratic Republic of the Congo',
    'denmark': 'Denmark',
    'dominicanr': 'Dominican Republic',
    'ecuador': 'Ecuador',
    'egypt': 'Egypt',
    'elsalvador': 'El Salvador',
    'eqguinea': 'Equatorial Guinea',
    'eritrea': 'Eritrea',
    'estonia': 'Estonia',
    'eswatini': 'Eswatini',
    'ethiopia': 'Ethiopia',
    'finland': 'Finland',
    'france': 'France',
    'gabon': 'Gabon',
    'georgia': 'Georgia',
    'germany': 'Germany',
    'ghana': 'Ghana',
    'gibraltar': 'Gibraltar',
    'greece': 'Greece',
    'mgreenland': 'Greenland',
    'guatemala': 'Guatemala',
    'guyana': 'Guyana',
    'haiti': 'Haiti',
    'honduras': 'Honduras',
    'hongkong': 'Hong Kong',
    'hungary': 'Hungary',
    'iceland': 'Iceland',
    'india': 'India',
    'indonesia': 'Indonesia',
    'iran': 'Iran',
    'iraq': 'Iraq',
    'ireland': 'Ireland',
    'israel': 'Israel',
    'italy': 'Italy',
    'jamaica': 'Jamaica',
    'japan': 'Japan',
    'jordan': 'Jordan',
    'kazakhstan': 'Kazakhstan',
    'kenya': 'Kenya',
    'kosovo': 'Kosovo',
    'kuwait': 'Kuwait',
    'kyrgyzstan': 'Kyrgyzstan',
    'lao': 'Laos',
    'latvia': 'Latvia',
    'lebanon': 'Lebanon',
    'libya': 'Libya',
    'lithuania': 'Lithuania',
    'luxembou': 'Luxembourg',
    'madagascar': 'Madagascar',
    'malaysia': 'Malaysia',
    'mmali': 'Mali',
    'malta': 'Malta',
    'mmauritani': 'Mauritania',
    'mauritius': 'Mauritius',
    'mexico': 'Mexico',
    'moldova': 'Moldova',
    'mongolia': 'Mongolia',
    'montenegro': 'Montenegro',
    'morocco': 'Morocco',
    'mozambique': 'Mozambique',
    'namibia': 'Namibia',
    'nepal': 'Nepal',
    'nethland': 'Netherlands',
    'nz': 'New Zealand',
    'nicaragua': 'Nicaragua',
    'niger': 'Niger',
    'nigeria': 'Nigeria',
    'koreadpr': 'North Korea',
    'northmaced': 'North Macedonia',
    'norway': 'Norway',
    'oman': 'Oman',
    'pakistan': 'Pakistan',
    'panama': 'Panama',
    'paraguay': 'Paraguay',
    'peru': 'Peru',
    'philippine': 'Philippines',
    'poland': 'Poland',
    'portugal': 'Portugal',
    'qatar': 'Qatar',
    'congo': 'Republic of the Congo',
    'romania': 'Romania',
    'russia': 'Russia',
    'rwanda': 'Rwanda',
    'saudiarabi': 'Saudi Arabia',
    'senegal': 'Senegal',
    'serbia': 'Serbia',
    'singapore': 'Singapore',
    'slovakia': 'Slovakia',
    'slovenia': 'Slovenia',
    'southafric': 'South Africa',
    'korea': 'South Korea',
    'ssudan': 'South Sudan',
    'spain': 'Spain',
    'srilanka': 'Sri Lanka',
    'sudan': 'Sudan',
    'suriname': 'Suriname',
    'sweden': 'Sweden',
    'switland': 'Switzerland',
    'syria': 'Syria',
    'taipei': 'Taiwan',
    'tajikistan': 'Tajikistan',
    'tanzania': 'Tanzania',
    'thailand': 'Thailand',
    'togo': 'Togo',
    'trinidad': 'Trinidad and Tobago',
    'tunisia': 'Tunisia',
    'turkey': 'Turkey',
    'turkmenist': 'Turkmenistan',
    'uganda': 'Uganda',
    'ukraine': 'Ukraine',
    'uae': 'United Arab Emirates',
    'uk': 'United Kingdom',
    'usa': 'United States',
    'uruguay': 'Uruguay',
    'uzbekistan': 'Uzbekistan',
    'venezuela': 'Venezuela',
    'vietnam': 'Vietnam',
    'yemen': 'Yemen',
    'zambia': 'Zambia',
    'zimbabwe': 'Zimbabwe'
 }


# define year ranges of data and projections
data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100


# define empy figure
def get_empty_fig(label):
    fig = go.Figure()
    fig.update_layout(
        annotations=[
            dict(
                text=label,
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
    return fig


no_data_fig = get_empty_fig(
    "No data available for the current set of dropdown selections"
)


def clean_gas_name(gas_name):
    clean_name = (
        gas_name.replace("Co2", "CO<sub>2</sub>")
        .replace("Ch4", "CH<sub>4</sub>")
        .replace("N2o", "N<sub>2</sub>O")
        .replace("Nh3", "NH<sub>3</sub>")
        .replace("Nox", "NO<sub>x</sub>")
        .replace("So2", "SO<sub>2</sub>")
    )
    return clean_name


# make dictionary of model_output options that uses common names for keys
model_output = {
    "energy_output_supply": "Energy Supply",
    "energy_output_demand": "Energy Demand",
    "emissions_output_co2e": "GHG Emissions",
    "climate_output_concentration": "GHG Concentration",
    "climate_output_temperature": "Temperature Change",
    # "climate_output_forcing": "Radiative Forcing",
    "technology_adoption_output": "Technology Adoption Rates",
}

# list all possible index names from all model_outputs, to define unused_data_controls
all_possible_index_names = [
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
    "unit",
]

# define model_output index levels that should be included as dropdowns in data_controls
data_controls_dropdowns = {
    "energy_output_supply": [
        "model",
        "scenario",
        "region",
        "sector",
        # "product_category",
        "product_long",
        # "product_short",
        "flow_category",
        "flow_long",
        # "flow_short",
        # "unit",
    ],
    "energy_output_demand": [
        "model",
        "scenario",
        "region",
        "sector",
        # "product_category",
        "product_long",
        # "product_short",
        "flow_category",
        "flow_long",
        # "flow_short",
        # "unit",
    ],
    "emissions_output_co2e": [
        "model",
        "scenario",
        "region",
        "sector",
        # "product_category",
        "product_long",
        # "product_short",
        # "flow_category",
        "flow_long",
        # "flow_short",
        # "unit",
    ],
    "climate_output_concentration": [
        "model",
        "scenario",
        "region",
        "variable",
        "gas",
        # "unit"
    ],
    "climate_output_temperature": [
        "model",
        "scenario",
        "region",
        "variable",
        "gas",
        # "unit"
    ],
    "climate_output_forcing": [
        "model",
        "scenario",
        "region",
        "variable",
        "gas",
        "unit",
    ],
    "technology_adoption_output": [
        "model",
        "scenario",
        "region",
        "sector",
        # "product_category",
        "product_long",
        # "product_short",
        # "flow_category",
        "flow_long",
        # "flow_short",
        # "unit",
    ],
}

# define graph_output_dropdown_values
graph_output_dropdown_values_all = {
    "energy_output_supply": ["Energy Supply"],
    "energy_output_demand": ["Energy Demand"],
    "emissions_output_co2e": [
        "Emissions Sources",
        "Negative Emissions",
        "Net Emissions",
        "Emissions Mitigated",
    ],
    "climate_output_concentration": [
        "GHG Concentration",
    ],
    "climate_output_temperature": ["Temperature Change"],
    "climate_output_forcing": ["Radiative Forcing"],
    "technology_adoption_output": ["Technology Adoption Rates"],
}

# define graph_output_dropdown_values_default
graph_output_dropdown_values_default_all = {
    "energy_output_supply": "Energy Supply",
    "energy_output_demand": "Energy Demand",
    "emissions_output_co2e": "Emissions Sources",
    "climate_output_concentration": "GHG Concentration",
    "climate_output_temperature": "Temperature Change",
    "climate_output_forcing": "Radiative Forcing",
    "technology_adoption_output": "Technology Adoption Rates",
}

# define group_by_dropdown_values
group_by_dropdown_values_all = {
    "energy_output_supply": [
        {"label": "Scenario", "value": "scenario"},
        {"label": "Region", "value": "region"},
        {"label": "Sector", "value": "sector"},
        {"label": "Product Category", "value": "product_category"},
        {"label": "Product", "value": "product_long"},
        {"label": "Flow Category", "value": "flow_category"},
        {"label": "Flow", "value": "flow_long"},
    ],
    "energy_output_demand": [
        {"label": "Scenario", "value": "scenario"},
        {"label": "Region", "value": "region"},
        {"label": "Sector", "value": "sector"},
        {"label": "Product Category", "value": "product_category"},
        {"label": "Product", "value": "product_long"},
        {"label": "Flow Category", "value": "flow_category"},
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
        {"label": "Unit", "value": "unit"},
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

# define group_by_dropdown_values_default
group_by_dropdown_values_default_all = {
    "energy_output_supply": ["sector", "product_long"],
    "energy_output_demand": ["sector", "product_long"],
    "emissions_output_co2e": ["flow_long"],
    "climate_output_concentration": ["scenario", "gas"],
    "climate_output_temperature": "scenario",
    "climate_output_forcing": "scenario",
    "technology_adoption_output": "flow_long",
}

# define y_axis_type_dropdown_values
y_axis_type_dropdown_values_all = {
    "energy_output_supply": [
        "Linear",
        "Log",
        "Cumulative",
        "% of Cumulative at Final Year",
        "% of Annual Total",
        "% Change YOY",
        "% of Maximum Value",
        "% of Final Year Value",
    ],
    "energy_output_demand": [
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
        "PPM",
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

# define y_axis_type_dropdown_default
y_axis_type_dropdown_default_all = {
    "energy_output_supply": "Linear",
    "energy_output_demand": "Linear",
    "emissions_output_co2e": "Linear",
    "climate_output_concentration": "Linear",
    "climate_output_temperature": "Linear",
    "climate_output_forcing": "Linear",
    "technology_adoption_output": "% of Cumulative at Final Year",
}

# define graph_type_dropdown_values
graph_type_dropdown_values_all = {
    "energy_output_supply": [
        {"label": "Area", "value": "tonexty"},
        {"label": "Line", "value": "none"},
        {"label": "Table", "value": "Table"},
    ],
    "energy_output_demand": [
        {"label": "Area", "value": "tonexty"},
        {"label": "Line", "value": "none"},
        {"label": "Table", "value": "Table"},
    ],
    "emissions_output_co2e": [
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

# define graph_type_dropdown_default
graph_type_dropdown_default_all = {
    "energy_output_supply": "tonexty",
    "energy_output_demand": "tonexty",
    "emissions_output_co2e": "tonexty",
    "climate_output_concentration": "none",
    "climate_output_temperature": "none",
    "climate_output_forcing": "none",
    "technology_adoption_output": "none",
}

# define units_dropdown_values
units_dropdown_values_all = {
    "energy_output_supply": [
        {"label": "TJ", "value": "TJ"},
        {"label": "EJ", "value": "EJ"},
        {"label": "GWh", "value": "GWh"},
        {"label": "TWh", "value": "TWh"},
    ],
    "energy_output_demand": [
        {"label": "TJ", "value": "TJ"},
        {"label": "EJ", "value": "EJ"},
        {"label": "GWh", "value": "GWh"},
        {"label": "TWh", "value": "TWh"},
    ],
    "emissions_output_co2e": [
        {"label": "MtCO2e", "value": "MtCO2e"},
        {"label": "GtCO2e", "value": "GtCO2e"},
    ],
    "climate_output_concentration": [
        {"label": "PPM", "value": "PPM"},
        {"label": "PPB", "value": "PPB"},
    ],
    "climate_output_temperature": [
        {"label": "C", "value": "C"},
        {"label": "F", "value": "F"},
    ],
    "climate_output_forcing": [
        {"label": "W/m^2", "value": "W/m^2"},
    ],
    "technology_adoption_output": [
        {"label": "Multiple", "value": "Multiple"},
    ],
}

# define units_dropdown_default
units_dropdown_default_all = {
    "energy_output_supply": "TJ",
    "energy_output_demand": "TJ",
    "emissions_output_co2e": "MtCO2e",
        "climate_output_concentration": "PPM",
        "climate_output_temperature": "C",
        "climate_output_forcing": "W/m^2",
        "technology_adoption_output": "Multiple",
}

# define data_controls_default for a given model_output
data_controls_default = {
    "energy_output_supply": {},
    "energy_output_demand": {
        "flow_category": [
            "Final consumption",
            "Energy industry own use and Losses",
        ]
    },
    # "emissions_output_co2e": {
    #     "region": [],
    #     "sector": [],
    #     "product_long": [],
    #     "flow_category": [],
    #     "flow_long": [],
    # },
    "climate_output_concentration": {
        "scenario": ["baseline", "pathway"],
        "gas": ["CO2"],
    },
    "climate_output_temperature": {
        "scenario": ["baseline", "pathway"],
        "gas": ["All"],
    },
    "climate_output_forcing": {
        "scenario": ["baseline", "pathway"],
        "gas": ["CO2"],
    },
}


# make layout
app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
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
                                                        "fontSize": "0.8rem"
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
                                                    )[2],
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
                                                        "fontSize": "0.8rem"
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
                                                                        "fontSize": "12px",
                                                                        "whiteSpace": "nowrap",
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
                                                                                "verticalAlign": "top",
                                                                                "marginRight": "10px",
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
                                                                                "verticalAlign": "top",
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
                                                                                "verticalAlign": "top",
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
                                                                                "verticalAlign": "top",
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
                                                        # html.Iframe(
                                                        #     src="https://app.wonderchat.io/chatbot/clgo3z4gv00k1mc0kplyvv4j6",
                                                        #     style={
                                                        #         "width": "100%",
                                                        #         "height": "300px",
                                                        #         "border": "none",
                                                        #         "borderRadius": "30px",
                                                        #     },
                                                        # ),
                                                        html.Div(
                                                            [
                                                                dcc.Input(
                                                                    id="pandasai-input",
                                                                    value="",
                                                                    type="text",
                                                                    placeholder="Enter your question here",
                                                                    style={
                                                                        "width": "100%",
                                                                        "height": "50px",
                                                                        "lineHeight": "50px",
                                                                        "border": "2px solid #ccc",
                                                                        "borderRadius": "5px",
                                                                        "textAlign": "left",
                                                                        "fontSize": "18px",
                                                                        "fontFamily": "Arial",
                                                                        "marginBottom": "10px",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                )
                                            ],  # make the card corner radius larger and transparent background
                                            style={
                                                "borderRadius": "10px",
                                                "backgroundColor": "rgba(0,0,0,0)",
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

@app.callback(Output("model_output", "value"),
              Input('url', 'href'))
def get_url(href: str):
    f = furl(href)
    data['initial_load'] = True
    data['args'] = {}

    for key in f.args.keys():
        if ',' in f.args[key]:
            data['args'][key] = f.args[key].split(',')
        else:
            if (key == 'groupby'):
                data['args'][key] = [f.args[key]]
            else:
                data['args'][key] = f.args[key]

    if 'model' in f.args.keys():
        return f.args['model']
    else:
        return "energy_output_supply"

# given an input value for model_output, create lists for data_controls and graph_controls. unused_data_controls is needed to store the unused data controls in a hidden div
@app.callback(
    output=[
        Output("data_controls", "children"),
        Output("graph_controls", "children"),
    ],
    inputs=[Input("model_output", "value")],
    prevent_initial_call=True,
)
def set_data_and_chart_control_options(
    model_output, all_possible_index_names=all_possible_index_names
):
    
    graph_output_dropdown_values = graph_output_dropdown_values_all[model_output]
    if data['initial_load'] and ('graph_output' in data['args'].keys()):
        if data['args']['graph_output'] in graph_output_dropdown_values:
            graph_output_dropdown_values_default = data['args']['graph_output']
        else:
            graph_output_dropdown_values_default = (
                graph_output_dropdown_values_default_all[model_output]
            )
    else :
        graph_output_dropdown_values_default = (
            graph_output_dropdown_values_default_all[model_output]
        )

    group_by_dropdown_values = group_by_dropdown_values_all[model_output]
    if data['initial_load'] and ('groupby' in data['args'].keys()):
        valid_inputs = []
        for groupby_key in data['args']['groupby']:
            filtered = list(filter(lambda x: x['value'] == groupby_key, group_by_dropdown_values))
            if len(filtered) == 1:
                valid_inputs.append(groupby_key)

        if len(valid_inputs) > 0:
            group_by_dropdown_values_default = valid_inputs
        else:
            group_by_dropdown_values_default = group_by_dropdown_values_default_all[
                model_output
            ]
    else:
        group_by_dropdown_values_default = group_by_dropdown_values_default_all[
            model_output
        ]

    # remove group_by_dropdown_values that are not in data_controls_dropdowns[model_output]
    group_by_dropdown_values = [
        i
        for i in group_by_dropdown_values
        if i["value"] in data_controls_dropdowns[model_output]
    ]

    y_axis_type_dropdown_values = y_axis_type_dropdown_values_all[model_output]
    if data['initial_load'] and ('yaxis_type' in data['args'].keys()):
        if data['args']['yaxis_type'] in y_axis_type_dropdown_values:
            y_axis_type_dropdown_default = data['args']['yaxis_type']
        else:
            y_axis_type_dropdown_default = y_axis_type_dropdown_default_all[model_output]
    else :
        y_axis_type_dropdown_default = y_axis_type_dropdown_default_all[model_output]

    units_dropdown_values = units_dropdown_values_all[model_output]
    if data['initial_load'] and ('units' in data['args'].keys()):
        filtered = list(filter(lambda x: x['value'] == data['args']['units'], units_dropdown_values))
        if len(filtered) == 1:
            units_dropdown_default = data['args']['units']
        else:
            units_dropdown_default = units_dropdown_default_all[model_output]
    else:
        units_dropdown_default = units_dropdown_default_all[model_output]

    graph_type_dropdown_values = graph_type_dropdown_values_all[model_output]
    if data['initial_load'] and ('graph_type' in data['args'].keys()):
        filtered = list(filter(lambda x: x['value'] == data['args']['graph_type'], graph_type_dropdown_values))
        if len(filtered) == 1:
            graph_type_dropdown_default = data['args']['graph_type']
        else:
            graph_type_dropdown_default = graph_type_dropdown_default_all[model_output]
    else:
        graph_type_dropdown_default = graph_type_dropdown_default_all[model_output]

    # if model_output is in data_controls_default, use that, otherwise use empty dict
    if model_output in data_controls_default:
        df_index_custom_default = data_controls_default[model_output]
    else:
        df_index_custom_default = {}

    # read model_output data
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

    # store unit label for use in graph axis label
    data["units"] = df["unit"].unique().tolist()

    # define data_controls_dropdowns that should allow for multi-selection
    data_controls_dropdowns_multiselect = {
        "model": False,
        "scenario": False,
        "region": True,
        "sector": True,
        "product_category": True,
        "product_long": True,
        "flow_category": True,
        "flow_long": True,
        "variable": False,
        "gas": False,
        "unit": True,
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
        "unit": "Select the unit to view",
        "group-by": "The graph will display data aggregated by the items selected here",
        "yaxis-type": "Select the y-axis type to view",
        "graph-type": "Select the graph type to view",
        "graph-output": "Select the graph output to view",
        "units": "Select the unit to view",
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
            & (df.columns.isin(data_controls_dropdowns[model_output]))
        ].tolist(),
        inplace=True,
    )

    # drop unused columns (at this point all columns that are not numerical)
    df.drop(
        columns=df.columns[
            ~df.columns.isin(
                str(f"{i}") for i in range(data_start_year, proj_end_year + 1)
            )
        ].tolist(),
        inplace=True,
    )

    # set global dataframe
    data["df"] = df

    # define list of data controls, labels, and tooltips
    div_elements = []

    for level in all_possible_index_names:
        # if df_index_custom_default is defined and level is in
        # df_index_custom_default, use df_index_custom_default[level] as
        # default_value
        if level not in df.index.names:
            default_value = []
        elif df_index_custom_default and level in df_index_custom_default:
            default_value = df_index_custom_default[level]
        elif data_controls_dropdowns_multiselect[level]:
            default_value = df.reset_index()[level].unique().tolist()
        else:
            default_value = df.reset_index()[level].unique().tolist()[-1]

        values = (
            []
            if level not in df.index.names
            else df.reset_index()[level].unique().tolist()
        )
        display = "none" if level not in df.index.names else "block"

        div_elements.append(
            html.Label(
                level.replace("_", " ").replace("long", "").title(),
                id=level + "-label",
                className="select-label",
                style={"display": display},
            )
        )

        if not type(default_value) is list:
            default_value = [default_value]

        default_values[level] = default_value
        checklist_options = [{"label": REGION_NAMES[i], "value": i} for i in values] if level == 'region' else [{"label": i, "value": i} for i in values]

        div_elements.append(
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Input(
                                id=level + "-search-box",
                                value="",
                                type="text",
                                placeholder="Search...",
                                className="search-box-input",
                            ),
                            html.Button(
                                "X",
                                id=level + "-clear-search",
                                className="clear-search",
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "All",
                                        id=level + "-select-all",
                                        className="select-all-option",
                                    ),
                                    html.Button(
                                        "None",
                                        id=level + "-deselect-all",
                                        className="deselect-all-option",
                                    ),
                                ],
                                className="select-all-container",
                            )
                        ]
                    ),
                    dcc.Checklist(
                        id=level,
                        options=checklist_options,
                        value=default_value,
                        labelStyle={"display": "block", "color": "black"},
                    ),
                ],
                style={
                    "maxHeight": "200px",
                    "overflowY": "scroll",
                    "border": "1px solid #d6d6d6",
                    "display": display,
                },
            ),
        )

        div_elements.append(
            dbc.Tooltip(
                tooltip_dict[level],
                target=level + "-label",
                placement="top",
                style={"fontSize": "0.8rem"},
            )
        )

    # define data_controls layout
    data_controls = html.Div(div_elements)

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
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    graph_output_dropdown_values,
                                    value=graph_output_dropdown_values_default,
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
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    group_by_dropdown_values,
                                    value=group_by_dropdown_values_default,
                                    id="group_by_dropdown_values",
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
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    y_axis_type_dropdown_values,
                                    y_axis_type_dropdown_default,
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
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    graph_type_dropdown_values,
                                    graph_type_dropdown_default,
                                    id="graph_type",
                                    clearable=False,
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Units",
                                    id="units",
                                    className="select-label",
                                ),
                                dbc.Tooltip(
                                    tooltip_dict["units"],
                                    target="units",
                                    placement="top",
                                    style={"fontSize": "0.8rem"},
                                ),
                                dcc.Dropdown(
                                    units_dropdown_values,
                                    units_dropdown_default,
                                    id="units",
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

    data['initial_load'] = False

    return (data_controls, graph_controls)


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
    state=[*[State(f"{level}", "value") for level in all_possible_index_names]],
    prevent_initial_call=True,
)
def update_data_controls(
    model_output,
    data_controls_values,
    *index_values,
):

    # read model_output data
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
            & (df.columns.isin(data_controls_dropdowns[model_output]))
        ].tolist(),
        inplace=True,
    )

    # drop unused columns (at this point all columns that are not numerical)
    df.drop(
        columns=df.columns[
            ~df.columns.isin(
                str(f"{i}") for i in range(data_start_year, proj_end_year + 1)
            )
        ].tolist(),
        inplace=True,
    )

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
                            "overflowY": "scroll",
                            "border": "1px solid #d6d6d6",
                            "borderRadius": "5px",
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
                style={"fontSize": "0.8rem"},
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

    # define unused data controls layout as the values in all_possible_index_names that are not in df.index.names
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
                            "overflowY": "scroll",
                            "border": "1px solid #d6d6d6",
                            "borderRadius": "5px",
                            "outline": "none",
                        },
                    ),
                ],
                className="mb-0",
            )
            for level in all_possible_index_names
            if level not in df.index.names
        ]
    )

    return (data_controls, unused_data_controls)
"""

for level in all_possible_index_names:

    @app.callback(
        Output(f"{level}", "value"),
        [
            Input(f"{level}-select-all", "n_clicks"),
            Input(f"{level}-deselect-all", "n_clicks"),
        ],
        [State(f"{level}", "options")],
        prevent_initial_call=True,
    )
    def update_options(btn1, btn2, options):
        selected = default_values[level]
        if ctx.triggered_id.endswith("-select-all"):
            selected = [option["value"] for option in options]
        elif ctx.triggered_id.endswith("-select-all"):
            selected = []
        return selected


for level in all_possible_index_names:

    @app.callback(
        Output(f"{level}", "options"),
        Input(f"{level}-search-box", "value"),
        prevent_initial_call=True,
    )
    def update_checklist_values(search_value):
        this_level = ctx.triggered_id.split("-")[0]
        values = (
            []
            if this_level not in data["df"].index.names
            else data["df"].reset_index()[this_level].unique().tolist()
        )
        options = [
            {"label": i, "value": i}
            for i in values
            if search_value.lower() in i.lower()
        ]
        return options


for level in all_possible_index_names:

    @app.callback(
        Output(f"{level}-search-box", "value"),
        Input(f"{level}-clear-search", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_options(btn):
        return ""


# update graph
@app.callback(
    output=[Output("output_graph", "figure")],
    inputs=[
        Input("data_controls", "children"),
        Input("model_output", "value"),
        Input("date_range", "value"),
        Input("graph_output", "value"),
        Input("group_by_dropdown_values", "value"),
        Input("yaxis_type", "value"),
        Input("graph_type", "value"),
        Input("units", "value"),
        *[Input(f"{level}", "value") for level in all_possible_index_names],
    ],
)
def update_output_graph(
    data_controls_values,
    model_output,
    date_range,
    graph_output,
    group_by_dropdown_values,
    yaxis_type,
    graph_type,
    units,
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
        "energy_output_supply": "Energy Supply",
        "energy_output_demand": "Energy Demand",
        "emissions_output_co2e": "GHG Emissions",
        "climate_output_concentration": "GHG Concentration",
        "climate_output_temperature": "Temperature Change",
        "climate_output_forcing": "Radiative Forcing",
        "technology_adoption_output": "Technology Adoption Rates",
    }

    subvertical_dict = {
        "Electric Power": "This is the electricity sector. It includes generation, transmission, and distribution of electricity. It also includes the use of electricity in the residential, commercial, and industrial sectors.",
        "Residential": "This is the residential sector. It includes the use of electricity in the residential sector.",
        "Commercial": "This is the commercial sector. It includes the use of electricity in the commercial sector.",
        "Industrial": "This is the industrial sector. It includes the use of electricity in the industrial sector.",
        "Transportation": "This is the transportation sector. It includes the use of electricity in the transportation sector.",
        "Agriculture": "This is the agriculture sector. It includes the use of electricity in the agriculture sector.",
        "Forests & Wetlands": "This is the forests & wetlands sector. It includes the use of electricity in the forests & wetlands sector.",
    }

    units_dict = {
        "TJ": 1,
        "EJ": 1e-6,
        "GWh": 2.78e-1,
        "TWh": 2.78e-4,
        "MtCO2e": 1,
        "GtCO2e": 1e-3,
        "PPM": 1,
        "PPB": 1e3,
        "C": 1,
        "F": 9 / 5 + 32,
        "W/m2": 1,
        "Multiple": 1,
    }

    # drop empty index_values
    index_values = [value for value in index_values if value]

    # read model_output data
    expanded_home_path = os.path.expanduser("~/positive-disruption/podi/data/")
    if os.path.isdir(expanded_home_path):
        data_path = expanded_home_path
    elif os.path.isdir("data/"):
        data_path = "data/"
    else:
        raise FileNotFoundError("Data directory not found")

    df = data["df"]

    # remove index values at locations where df.index.names is not in data_controls_dropdowns[model_output]
    index_values = [
        value
        for value, name in zip(index_values, df.index.names)
        if name in data_controls_dropdowns[model_output]
    ]

    # check if df.loc[tuple([*index_values])] raises a KeyError, and if so, return an empty figure
    try:
        df.loc[tuple([*index_values])]
    except KeyError:
        return (no_data_fig,)

    # prevent error if group_by_dropdown_values is empty
    if not group_by_dropdown_values:
        return (
            get_empty_fig(
                "Select a variable to group by in the 'GROUP BY' menu above"
            ),
        )

    # make group_by_dropdown_values an array if it is not already
    if not isinstance(group_by_dropdown_values, list):
        group_by_dropdown_values = (
            [group_by_dropdown_values] if group_by_dropdown_values else []
        )

    # if index_values for scenario has more than one unique value, make graph_type = "none"
    if (
        pd.Series(index_values[1]).isin(["pathway"]).any()
        and len(index_values[1]) > 1
        and graph_type == "tonexty"
    ):
        return (
            get_empty_fig(
                "Reduce the number of scenarios or change the Graph Type away from 'Area'"
            ),
        )

    filtered_df = df.loc[tuple([*index_values])]
    df = df.loc[tuple([*index_values])]

    # update units based on units dropdown
    filtered_df = filtered_df * units_dict[units]
    df = df * units_dict[units]

    # check if filtered_df.loc[tuple([*index_values])] raises a KeyError, and if so, return an empty figure
    try:
        # Resetting the index
        df_reset = filtered_df.reset_index()

        # Now apply the Dask operations
        ddf = dd.from_pandas(df_reset, npartitions=16)

        filtered_df = (
            (
                ddf.groupby(group_by_dropdown_values)
                .sum(numeric_only=True)
                .loc[:, str(date_range[0]) : str(date_range[1])]
            )
            .compute()
            .T.fillna(0)
        )
    except KeyError:
        return (no_data_fig,)

    # check if filtered_df raises an error
    if filtered_df.empty:
        return (no_data_fig,)

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
        var_name=group_by_dropdown_values,
        value_name="value",
    ).astype(
        {k: "category" for k in group_by_dropdown_values}
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
    if graph_output == "Energy Supply" or graph_output == "Energy Demand":
        fig = go.Figure()

        i = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
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
                data_plot = (
                    pd.DataFrame(filtered_df)
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                )

                # if all values are zero, skip
                if data_plot["value"].sum() == 0:
                    continue

                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=data_plot[data_plot["year"] <= data_end_year][
                            "year"
                        ].values,
                        y=data_plot[data_plot["year"] <= data_end_year][
                            "value"
                        ].values,
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=data_plot[data_plot["year"] >= data_end_year][
                            "year"
                        ].values,
                        y=data_plot[data_plot["year"] >= data_end_year][
                            "value"
                        ].values,
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
                data_plot = (
                    pd.DataFrame(filtered_df)
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                )

                # if all values are zero, skip
                if data_plot["value"].sum() == 0:
                    continue

                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=data_plot["year"].values,
                        y=data_plot["value"].values,
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Emissions Sources":
        fig = go.Figure()

        i = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if all(
                x <= 0
                for x in pd.DataFrame(filtered_df)
                .set_index(group_by_dropdown_values)
                .loc[[sub]]["value"]
                .values
            ):
                continue

            if isinstance(sub, str):
                name = str(sub).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in sub)

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=filtered_df["year"][
                            filtered_df["year"] <= data_end_year
                        ].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
                        .loc[[sub], : str(data_end_year)]["value"]
                        .values.clip(lower=0),
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
                        .loc[[sub]]["value"]
                        .clip(lower=0)
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
                        .loc[[sub]]["value"]
                        .clip(lower=0)
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
            plot_data = filtered_df[
                (date_range[0] <= filtered_df["year"])
                & (filtered_df["year"] <= date_range[1])
            ]

            fig.add_trace(
                go.Scatter(
                    name="Net Emissions",
                    line=dict(width=5, color="magenta", dash="dashdot"),
                    x=plot_data["year"].drop_duplicates(),
                    y=pd.Series(
                        plot_data.groupby("year")
                        .sum(numeric_only=True)["value"]
                        .values
                        * 0,
                        index=plot_data["year"].drop_duplicates(),
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Negative Emissions":
        fig = go.Figure()

        i = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if all(
                x >= 0
                for x in pd.DataFrame(filtered_df)
                .set_index(group_by_dropdown_values)
                .loc[[sub]]["value"]
                .values
            ):
                continue

            if isinstance(sub, str):
                name = str(sub).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in sub)

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=filtered_df["year"][
                            filtered_df["year"] <= data_end_year
                        ].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
            data_plot = filtered_df[
                (date_range[0] <= filtered_df["year"])
                & (filtered_df["year"] <= date_range[1])
            ]
            fig.add_trace(
                go.Scatter(
                    name="Net Emissions",
                    line=dict(width=5, color="magenta", dash="dashdot"),
                    x=data_plot["year"].drop_duplicates(),
                    y=pd.Series(
                        data_plot.groupby("year")
                        .sum(numeric_only=True)["value"]
                        .values
                        * 0,
                        index=data_plot["year"].drop_duplicates(),
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Net Emissions":
        fig = go.Figure()

        i = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if isinstance(sub, str):
                name = str(sub).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in sub)

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=filtered_df["year"][
                            filtered_df["year"] <= data_end_year
                        ].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
            data_plot = filtered_df[
                (date_range[0] <= filtered_df["year"])
                & (filtered_df["year"] <= date_range[1])
            ]
            fig.add_trace(
                go.Scatter(
                    name="Net Emissions",
                    line=dict(width=5, color="magenta", dash="dashdot"),
                    x=data_plot["year"].drop_duplicates(),
                    y=pd.Series(
                        data_plot.groupby("year")
                        .sum(numeric_only=True)["value"]
                        .values
                        * 0,
                        index=data_plot["year"].drop_duplicates(),
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
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
        # make index_values a list if it is not already
        if not isinstance(index_values[1], list):
            index_values[1] = [index_values[1]]

        if len(index_values[1]) < 2:
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
        if "scenario" in group_by_dropdown_values:
            return (
                get_empty_fig(
                    "Remove 'scenario' option from GROUP BY",
                ),
            )

        if yaxis_type == "PPM":
            units = "PPM"
            df.update(
                df.loc[:, : str(data_end_year)].applymap(lambda x: x / 17.3e3)
            )

            df.update(
                df.loc[:, str(data_end_year + 1) :].applymap(
                    lambda x: x / 17.3e3
                    if isinstance(x, float) and x != int(x) and x > 0
                    else (
                        x / 7.8e3
                        if isinstance(x, float) and x != int(x) and x < 0
                        else x
                    )
                )
            )

        # calculate difference between baseline and pathway filtered_df
        filtered_df2 = (
            (
                (
                    df[(df.reset_index().scenario == "baseline").values]
                    .groupby(group_by_dropdown_values)
                    .sum(numeric_only=True)
                    - (
                        df[(df.reset_index().scenario == "pathway").values]
                        .groupby(group_by_dropdown_values)
                        .sum(numeric_only=True)
                    )
                )
            ).loc[:, str(date_range[0]) : str(date_range[1])]
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
            var_name=group_by_dropdown_values,
            value_name="value",
        ).astype(
            {k: "category" for k in group_by_dropdown_values}
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

            if yaxis_type == "PPM":
                # filter out negative values
                spacer[spacer < 0] = 0
                spacer = spacer.cumsum()
                spacer = spacer + (415 - spacer.loc[data_end_year])

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

        i = 0
        j = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df2.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        # if "Biochar" is in the name, then put it at the top of the list
        if any("Biochar" in x for x in sorted_df.iloc[:, 0].tolist()):
            sorted_df = sorted_df.iloc[
                sorted_df.iloc[:, 0].str.contains("Biochar").argsort()
            ]

        # reverse sorted_df
        sorted_df = sorted_df.iloc[::-1]

        for groupby_set_value in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if isinstance(groupby_set_value, str):
                name = str(groupby_set_value).capitalize()
            else:
                name = ", ".join(
                    str(x).capitalize() for x in groupby_set_value
                )

            # if name does not contain "Biochar", make name 'Carbon Removal from all other sources'
            if "Biochar" not in name:
                name = "Other Sources"
                y = (
                    -(
                        pd.DataFrame(
                            filtered_df2[
                                (filtered_df2.year > data_end_year)
                                & (filtered_df2.year <= date_range[1])
                            ]
                        )
                        .set_index(group_by_dropdown_values)
                        .loc[[groupby_set_value]]["value"]
                    )
                    * 0.1
                )
            else:
                name = (
                    name.replace("Biochar as ag soil amendment", "Biochar")
                    .replace("Biochar for water treatment", "Biochar")
                    .replace("Biochar as activated carbon", "Biochar")
                    .replace("Biochar for construction materials", "Biochar")
                    .replace(
                        "Biochar for carbon removal & sequestration", "Biochar"
                    )
                )

                y = -(
                    pd.DataFrame(
                        filtered_df2[
                            (filtered_df2.year > data_end_year)
                            & (filtered_df2.year <= date_range[1])
                        ]
                    )
                    .set_index(group_by_dropdown_values)
                    .loc[[groupby_set_value]]["value"]
                )

            if yaxis_type == "PPM":
                y = y.cumsum()
                fig.add_trace(
                    go.Scatter(
                        name="Carbon Removal from " + name,
                        line=dict(
                            width=3,
                            color="green"
                            if "Biochar" in name
                            else "goldenrod",
                        ),
                        x=filtered_df2[
                            (filtered_df2["year"] > data_end_year)
                            & ((filtered_df2["year"] <= date_range[1]))
                        ]["year"].drop_duplicates(),
                        y=y,
                        fill="tonexty",
                        stackgroup="one",
                        showlegend=True
                        if (i == 0) & ("Biochar" not in name)
                        or (j == 0) & ("Biochar" in name)
                        else False,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor="green"
                        if "Biochar" in name
                        else "goldenrod",
                        groupnorm=groupnorm,
                    )
                )

            else:
                fig.add_trace(
                    go.Scatter(
                        name=name.replace("Co2", "CO<sub>2</sub>")
                        .replace("Ch4", "CH<sub>4</sub>")
                        .replace("N2o", "N<sub>2</sub>O")
                        .replace("Nh3", "NH<sub>3</sub>")
                        .replace("Nox", "NO<sub>x</sub>")
                        .replace("So2", "SO<sub>2</sub>")
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
                        y=y,
                        fill="tonexty",
                        stackgroup="one",
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                    )
                )

            i += 1 if "Biochar" not in name else 0
            j += 1 if "Biochar" in name else 0

        if yaxis_type not in ["Log", "Cumulative", "% of Annual Total"]:
            baseline = (
                df[(df.reset_index().scenario == "baseline").values]
                .loc[:, str(date_range[0]) : str(date_range[1])]
                .sum()
            )
            baseline.index = baseline.index.astype(int)

            baseline[baseline.index.values == data_end_year] = baseline[
                baseline.index.values == data_end_year
            ].values + (
                spacer[spacer.index.values == data_end_year].values
                - baseline[baseline.index.values == data_end_year].values
            )

            if yaxis_type == "PPM":
                baseline = baseline.cumsum()
                baseline = baseline + (415 - baseline.loc[data_end_year])

            fig.add_trace(
                go.Scatter(
                    name="2. Remove Past Emissions",
                    line=dict(width=4, color="turquoise", dash="dashdot"),
                    x=spacer.index.values[
                        (spacer.index.values >= data_end_year)
                        & (spacer.index.values <= date_range[1])
                    ],
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

            fig.add_trace(
                go.Scatter(
                    name="1. Stop Current Emissions",
                    line=dict(width=4, color="red", dash="dashdot"),
                    x=spacer.index.values[
                        (spacer.index.values >= data_end_year)
                        & (spacer.index.values <= date_range[1])
                    ],
                    y=spacer[
                        (spacer.index.values >= data_end_year)
                        & (spacer.index.values <= date_range[1])
                    ],
                    fill="none",
                    stackgroup="three",
                    showlegend=True,
                    hovertemplate=graph_template["hovertemplate"],
                    groupnorm=groupnorm,
                )
            )

            # fig.add_trace(
            #     go.Scatter(
            #         name="Baseline",
            #         line=dict(width=4, color="red", dash="dashdot"),
            #         x=baseline.index.values[
            #             (baseline.index.values >= data_end_year)
            #             & (baseline.index.values <= date_range[1])
            #         ],
            #         y=baseline[
            #             (baseline.index.values >= data_end_year)
            #             & (baseline.index.values <= date_range[1])
            #         ],
            #         fill="none",
            #         stackgroup="two",
            #         showlegend=True,
            #         hovertemplate=graph_template["hovertemplate"],
            #         groupnorm=groupnorm,
            #     )
            # )

            for m in [0.1, 0.2, 0.35, 0.5, 0.75, 0.9]:
                fig.add_trace(
                    go.Scatter(
                        name="",
                        line=dict(width=2, color="lightgreen", dash="dashdot"),
                        x=baseline.index.values[
                            (baseline.index.values >= data_end_year)
                            & (baseline.index.values <= date_range[1])
                        ],
                        y=spacer[
                            (spacer.index.values >= data_end_year)
                            & (spacer.index.values <= date_range[1])
                        ].values
                        - (
                            pd.DataFrame(
                                filtered_df2[
                                    (filtered_df2.year >= data_end_year)
                                    & (filtered_df2.year <= date_range[1])
                                ]
                            )
                            .set_index(group_by_dropdown_values)
                            .loc[["Biochar as Ag Soil Amendment"]]["value"]
                        ).cumsum()
                        * (1 - m),
                        fill="none",
                        stackgroup=m,
                        showlegend=False,
                        hovertemplate=graph_template["hovertemplate"],
                        groupnorm=groupnorm,
                    )
                )

            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=3, color="black"),
                    x=spacer[
                        spacer.index.values <= data_end_year
                    ].index.values,
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
            )
        elif yaxis_type == "% of Annual Total":
            fig.update_yaxes(title="% of Annual Total")
        elif yaxis_type == "% Change YOY":
            fig.update_yaxes(title="% Change YOY")
        elif yaxis_type == "% of Maximum Value":
            fig.update_yaxes(title="% of Maximum Value")
        elif yaxis_type == "% of Final Year Value":
            fig.update_yaxes(title="% of Final Year Value")

    elif graph_output == "Technology Adoption Rates":
        fig = go.Figure()

        i = 0

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if isinstance(sub, str):
                name = str(sub).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in sub)

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                data_plot = (
                    pd.DataFrame(
                        filtered_df[filtered_df["year"] >= data_end_year]
                    )
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                    .replace(0, np.nan)
                    .dropna()
                )
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        mode="lines",
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=data_plot["year"],
                        y=data_plot["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        customdata=[units],
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )

                data_plot = (
                    pd.DataFrame(
                        filtered_df[filtered_df["year"] <= data_end_year]
                    )
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                    .replace(
                        0,
                        np.nan,
                        limit=(
                            filtered_df[filtered_df["year"] <= data_end_year]
                            == 0
                        ).idxmax(),
                    )
                    .dropna()
                )

                # replace all leading zeros with NaN

                fig.add_trace(
                    go.Scatter(
                        name=name,
                        mode="lines",
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="solid",
                        ),
                        x=data_plot["year"],
                        y=data_plot["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True
                        if pd.DataFrame(
                            filtered_df[
                                filtered_df["year"]
                                <= min(data_end_year, date_range[1])
                            ]
                        )
                        .set_index(group_by_dropdown_values)
                        .loc[[sub]]
                        .replace(0, np.nan)
                        .dropna()["year"]
                        .max()
                        < data_end_year
                        else False,
                        customdata=[units],
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup=name,
                    )
                )

                if i == 1:
                    fig.update_layout(legend=dict(traceorder="reversed"))

            else:
                data_plot = (
                    pd.DataFrame(filtered_df)
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                    .replace(0, np.nan)
                    .dropna()
                )
                fig.add_trace(
                    go.Scatter(
                        name=name,
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=data_plot["year"],
                        y=data_plot["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=False,
                        customdata=[str(units)],
                        hovertemplate=graph_template["hovertemplate"]
                        + "<b>Unit</b>: %{customdata[0]}<extra></extra>",
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
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

        # convert group_by_dropdown_values to list if it is a string, before using it in the for loop
        group_by_dropdown_values = (
            [group_by_dropdown_values]
            if isinstance(group_by_dropdown_values, str)
            else group_by_dropdown_values
        )
        sorted_df = filtered_df.sort_values("value", ascending=False)[
            group_by_dropdown_values
        ].drop_duplicates()

        for sub in (
            sorted_df.iloc[:, 0].tolist()
            if len(group_by_dropdown_values) == 1
            else sorted_df.to_records(index=False).tolist()
        ):
            if isinstance(sub, str):
                name = str(sub).capitalize()
            else:
                name = ", ".join(str(x).capitalize() for x in sub)

            # if the graph_type is line, add a trace to fig that is solid up to data_end_year and dashdot after
            if graph_type == "none":
                data_plot = (
                    pd.DataFrame(
                        filtered_df[filtered_df["year"] >= data_end_year]
                    )
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                    .replace(0, np.nan)
                    .dropna()
                )
                fig.add_trace(
                    go.Scatter(
                        name=clean_gas_name(name),
                        line=dict(
                            width=3,
                            color=graph_template["linecolor"][i],
                            dash="dashdot",
                        ),
                        x=data_plot["year"],
                        y=data_plot["value"],
                        fill=graph_type,
                        stackgroup=stack_type[graph_type],
                        showlegend=True,
                        hovertemplate=graph_template["hovertemplate"],
                        fillcolor=graph_template["fillcolor"][i],
                        groupnorm=groupnorm,
                        legendgroup="Biochar"
                        if "Biochar" in name
                        else "Total Emissions",
                    )
                )

                data_plot = (
                    pd.DataFrame(
                        filtered_df[filtered_df["year"] <= data_end_year]
                    )
                    .set_index(group_by_dropdown_values)
                    .loc[[sub]]
                    .replace(0, np.nan)
                    .dropna()
                )
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(
                            width=3,
                            color="black",
                            dash="solid",
                        ),
                        x=data_plot["year"],
                        y=data_plot["value"],
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
                        name=clean_gas_name(name),
                        line=dict(
                            width=3, color=graph_template["linecolor"][i]
                        ),
                        x=filtered_df["year"].drop_duplicates(),
                        y=pd.DataFrame(filtered_df)
                        .set_index(group_by_dropdown_values)
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
                    for x in group_by_dropdown_values
                ),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            template="plotly_white",
            margin=dict(t=25, b=0, l=0, r=0),
        )

        fig.update_yaxes(
            title=str(units),
            type="log" if yaxis_type == "Log" else "linear",
            spikemode="toaxis",
        )

        fig.update_xaxes(spikemode="toaxis")

        if yaxis_type == "Cumulative":
            fig.update_yaxes(title="Cumulative " + str(units))
        elif yaxis_type == "% of Cumulative at Final Year":
            fig.update_yaxes(
                title="% of Cumulative at Final Year " + str(units)
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


# # pandas ai
# @app.callback(
#     output= [Output("pandasai-output", "children")],
#     input= [Input("pandasai-input", "value")],
# )
# def pandasai(input):


#     return (input,)

if __name__ == "__main__":
    app.run_server(
        debug=True, host="0.0.0.0", port=8050, dev_tools_hot_reload=False
    )
