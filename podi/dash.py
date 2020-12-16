#!/usr/bin/env python

# region

import plotly.express as px
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# endregion

########
# DEMO #
########

# region

# Load Data
df = px.data.tips()

# Build App
app = JupyterDash(__name__)
app.layout = html.Div(
    [
        html.H1("JupyterDash Demo"),
        dcc.Graph(id="graph"),
        html.Label(
            [
                "colorscale",
                dcc.Dropdown(
                    id="colorscale-dropdown",
                    clearable=False,
                    value="plasma",
                    options=[
                        {"label": c, "value": c} for c in px.colors.named_colorscales()
                    ],
                ),
            ]
        ),
    ]
)

# Define callback to update graph
@app.callback(Output("graph", "figure"), [Input("colorscale-dropdown", "value")])
def update_figure(colorscale):
    return px.scatter(
        df,
        x="total_bill",
        y="tip",
        color="size",
        color_continuous_scale=colorscale,
        render_mode="webgl",
        title="Tips",
    )


# Run app and display result
app.run_server(mode="inline")

# endregion

#####################################
# PROJECTED MARKET DIFFUSION CURVES #
#####################################

# region

# Build App
app = JupyterDash(__name__)
app.layout = html.Div(
    [
        html.H1("Projected Market Diffusion Curves"),
        dcc.Graph(id="graph"),
        html.Label(
            [
                "colorscale",
                dcc.Dropdown(
                    id="colorscale-dropdown",
                    clearable=False,
                    value="plasma",
                    options=[
                        {"label": c, "value": c} for c in px.colors.named_colorscales()
                    ],
                ),
            ]
        ),
    ]
)

# Define callback to update graph
@app.callback(Output("graph", "figure"), [Input("colorscale-dropdown", "value")])
def update_figure(colorscale):
    return px.scatter(
        fig,
        x="total_bill",
        y="tip",
        color="size",
        color_continuous_scale=colorscale,
        render_mode="webgl",
        title="Tips",
    )


# Run app and display result
app.run_server(mode="inline")

# endregion
