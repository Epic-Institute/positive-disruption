#!/usr/bin/env python

# region

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from podi.energy_demand import data_end_year, data_start_year
from podi.energy_supply import (
    near_proj_start_year,
    near_proj_end_year,
    long_proj_start_year,
    long_proj_end_year,
)
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import chain, zip_longest
from math import ceil, pi, nan
from kneed import DataGenerator, KneeLocator
from podi.curve_smooth import curve_smooth
from numpy import NaN
import fair
from fair.forward import fair_scm
from fair.RCPs import rcp26, rcp45, rcp60, rcp85, rcp3pd
from fair.constants import radeff

annotation_source = [
    "Historical data is from IEA WEO 2020, projections are based on PD21 growth rate assumptions applied to IEA WEO projections for 2020-2040 and GCAM scenario x for 2040-2100"
]

unit_name = ["TWh", "EJ", "TJ", "Mtoe", "Ktoe"]
unit_val = [1, 0.00360, 3600, 0.086, 86]
unit = [unit_name[0], unit_val[0]]

region_list = pd.read_csv("podi/data/region_list.csv", header=None, squeeze=True)

save_figs = True
show_figs = True
start_year = 2000
scenario = 'pathway'

# endregion

###################
# ADOPTION CURVES #
###################

# region

scenario = scenario
start_year = start_year

for i in range(0, len(region_list)):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, start_year:
        ]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="one",
            legendgroup="Electricity",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Transport")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="two",
            legendgroup="Transport",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Buildings")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="three",
            legendgroup="Buildings",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Industry")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="four",
            legendgroup="Industry",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V5: Regenerative Agriculture",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020) & (fig2["Sector"] == "Regenerative Agriculture")
            ]["% Adoption"],
            fill="none",
            stackgroup="five",
            legendgroup="Regenerative Agriculture",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Forests & Wetlands")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="six",
            legendgroup="Forests & Wetlands",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V8: Other Gases",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Other Gases")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="othergases",
            legendgroup="Other Gases",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=3, color="#B279A2", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="eight",
            legendgroup="Electricity",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=3, color="#7AA8B8", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Transport")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="nine",
            legendgroup="Transport",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=3, color="#F58518", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Buildings")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="ten",
            legendgroup="Buildings",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=3, color="#60738C", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Industry")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="eleven",
            legendgroup="Industry",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V5: Regenerative Agriculture",
            line=dict(width=3, color="#EECA3B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020) & (fig2["Sector"] == "Regenerative Agriculture")
            ]["% Adoption"],
            fill="none",
            stackgroup="twelve",
            legendgroup="Regenerative Agriculture",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=3, color="#54A24B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Forests & Wetlands")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="thirteen",
            legendgroup="Forests & Wetlands",
        )
    )

    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="V7: Mariculture",
                line=dict(width=3, color="black"),
                x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] <= 2020)
                    & (fig2["Sector"] == "Mariculture")
                ]["% Adoption"],
                fill="none",
                stackgroup="mariculture2",
                legendgroup="mariculture",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name="V7: Mariculture",
                line=dict(width=3, color="#2FDDCE", dash="dot"),
                x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] >= 2020)
                    & (fig2["Sector"] == "Mariculture")
                ]["% Adoption"],
                fill="none",
                stackgroup="mariculture",
                legendgroup="mariculture",
            )
        )
    '''
    fig.add_trace(
        go.Scatter(
            name="V8: Other Gases",
            line=dict(width=3, color="#E45756", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Other Gases")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="othergases2",
            legendgroup="Other Gases",
        )
    )
    '''
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="V9: Carbon Dioxide Removal",
                line=dict(width=3, color="black"),
                x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] <= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
                fill="none",
                stackgroup="seven",
                legendgroup="Carbon Dioxide Removal",
                showlegend=False,
            )
        )
        if scenario == 'pathway':
            fig.add_trace(
                go.Scatter(
                    name="V9: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"].cumsum().divide((fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]).cumsum().max())*100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    name="V9: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"].cumsum().divide((fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]))*100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + scenario.title() + ', ' + region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands, Mariculture, Other Gases</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.18,
        y=1.15,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    """
    fig.add_vrect(x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)
    """
    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/scurves-" + region_list[i] + "-" + scenario + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

#############################
# ADOPTION CURVES DASHBOARD #
#############################

# region

scenario = scenario
start_year = start_year

for i in range(0, len(region_list)):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, start_year:
        ]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    fig = make_subplots(rows=2, cols=4, start_cell='top-left', subplot_titles=('Electricity', 'Transport', 'Buildings', 'Industry', 'Regenerative Agriculture', 'Forests & Wetlands', 'Other Gases', 'CDR'))
    fig.update_annotations(font_size=10)

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="one",
            legendgroup="Electricity",
            showlegend=False, 
        ), row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Transport")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="two",
            legendgroup="Transport",
            showlegend=False,
        ), row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Buildings")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="three",
            legendgroup="Buildings",
            showlegend=False,
        ), row=1, col=3
    )

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Industry")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="four",
            legendgroup="Industry",
            showlegend=False,
        ), row=1, col=4
    )

    fig.add_trace(
        go.Scatter(
            name="V5: Regenerative Agriculture",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020) & (fig2["Sector"] == "Regenerative Agriculture")
            ]["% Adoption"],
            fill="none",
            stackgroup="five",
            legendgroup="Regenerative Agriculture",
            showlegend=False,
        ), row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Forests & Wetlands")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="six",
            legendgroup="Forests & Wetlands",
            showlegend=False,
        ), row=2, col=2
    )

    fig.add_trace(
        go.Scatter(
            name="V7: Other Gases",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Other Gases")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="othergases",
            legendgroup="Other Gases",
            showlegend=False,
        ), row=2, col=3
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=3, color="#B279A2", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="eight",
            legendgroup="Electricity",
        ), row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=3, color="#7AA8B8", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Transport")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="nine",
            legendgroup="Transport",
        ), row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=3, color="#F58518", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Buildings")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="ten",
            legendgroup="Buildings",
        ), row=1, col=3
    )

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=3, color="#60738C", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Industry")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="eleven",
            legendgroup="Industry",
        ), row=1, col=4
    )

    fig.add_trace(
        go.Scatter(
            name="V5: Regenerative Agriculture",
            line=dict(width=3, color="#EECA3B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020) & (fig2["Sector"] == "Regenerative Agriculture")
            ]["% Adoption"],
            fill="none",
            stackgroup="twelve",
            legendgroup="Regenerative Agriculture",
        ), row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=3, color="#54A24B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Forests & Wetlands")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="thirteen",
            legendgroup="Forests & Wetlands",
        ), row=2, col=2
    )
    '''
    fig.add_trace(
        go.Scatter(
            name="V7: Other Gases",
            line=dict(width=3, color="#E45756", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Other Gases")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="othergases2",
            legendgroup="Other Gases",
        ), row=2, col=3
    )
    '''
    
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="black"),
                x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] <= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
                fill="none",
                stackgroup="seven",
                legendgroup="Carbon Dioxide Removal",
                showlegend=False,
            ), row=2, col=4
        )

        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="#FF9DA6", dash="dot"),
                x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] >= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
                fill="none",
                stackgroup="fourteen",
                legendgroup="Carbon Dioxide Removal",
            ), row=2, col=4
        )
    
    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + scenario.title() + ', ' + region_list[i],
            "xanchor": "center",
            "x": 0.5,
        }, showlegend=False
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/scurves2-" + region_list[i] + "-" + scenario + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

#############################
# SUBVECTOR ADOPTION CURVES #
#############################

# region

scenario = scenario
start_year = start_year

colors = px.colors.qualitative.Vivid

for i in range(0, len(region_list)):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, start_year:
        ]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig3 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    for j in ['Electricity', 'Transport', 'Buildings', 'Industry', 'Regenerative Agriculture', 'Forests & Wetlands']:

        fig = (
            sadoption_curves.loc[region_list[i], j, slice(None), scenario, :].loc[
                :, start_year:
            ]
            * 100
        )

        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="% Adoption")

        fig = go.Figure()

        for x in fig2['Metric'].unique():
            fig.add_trace(
                go.Scatter(
                    name=x,
                    line=dict(width=0, color=colors[pd.DataFrame(fig2['Metric'].unique()).set_index(0).index.get_loc(x)]),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == x][
                        "% Adoption"
                    ],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=x,
                )
            )

        fig.add_trace(
            go.Scatter(
                name=j,
                line=dict(width=3, color="black"),
                x=fig2[fig2["Year"] <= 2020]['Year'],
                y=fig3[(fig3["Year"] <= 2020) & (fig3["Sector"] == j)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="three",
                legendgroup=j, showlegend=False
            )
        )

        fig.add_trace(
            go.Scatter(
                name=j,
                line=dict(width=3, color="#7AA8B8", dash="dot"),
                x=fig2[fig2["Year"] >= 2020]['Year'],
                y=fig3[(fig3["Year"] >= 2020) & (fig3["Sector"] == j)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="four",
                legendgroup=j, showlegend=True
            )
        )

        fig.update_layout(
            title={
                "text": "Percent of Total PD Adoption, " + scenario.title() + ', ' + j + ', ' + region_list[i],
                "xanchor": "center",
                "x": 0.5,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"}, legend={'traceorder':'reversed'}
        )

        fig.add_annotation(
            text="",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=1.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_vrect(x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0)

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/scurvessub-" + region_list[i] + "-" + j + "-" + scenario + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

# endregion

#######################################
# SUBVECTOR ADOPTION CURVES UNSTACKED #
#######################################

# region

scenario = scenario
start_year = start_year

colors = px.colors.qualitative.Vivid

for i in range(0, len(region_list)):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, start_year:
        ]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig3 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    for j in ['Electricity', 'Transport', 'Buildings', 'Industry', 'Regenerative Agriculture', 'Forests & Wetlands']:

        fig = (
            sadoption_curves.loc[region_list[i], j, slice(None), scenario, :].loc[
                :, start_year:
            ]
            * 100
        )

        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="% Adoption")

        fig = go.Figure()

        for x in fig2['Metric'].unique():
            fig.add_trace(
                go.Scatter(
                    name=x,
                    line=dict(width=3, color=colors[pd.DataFrame(fig2['Metric'].unique()).set_index(0).index.get_loc(x)]),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == x][
                        "% Adoption"
                    ],
                    fill="none",
                    stackgroup=x,
                    legendgroup=x,
                )
            )

        fig.add_trace(
            go.Scatter(
                name=j,
                line=dict(width=3, color="black"),
                x=fig2[fig2["Year"] <= 2020]['Year'],
                y=fig3[(fig3["Year"] <= 2020) & (fig3["Sector"] == j)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup='2',
                legendgroup='2', showlegend=False
            )
        )

        fig.add_trace(
            go.Scatter(
                name=j,
                line=dict(width=3, color="#7AA8B8", dash="dot"),
                x=fig2[fig2["Year"] >= 2020]['Year'],
                y=fig3[(fig3["Year"] >= 2020) & (fig3["Sector"] == j)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup='none',
                legendgroup='2', showlegend=True
            )
        )

        fig.update_layout(
            title={
                "text": "Percent of Total PD Adoption, " + scenario.title() + ', ' + j + ', ' + region_list[i],
                "xanchor": "center",
                "x": 0.5,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"}, legend={'traceorder':'reversed'}
        )

        fig.add_annotation(
            text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture and Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=1.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_vrect(x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0)

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/scurvessub-" + region_list[i] + "-" + j + "-" + scenario + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

# endregion

#######################################
# ENERGY DEMAND BY SECTOR AND END-USE #
#######################################

# region

scenario = scenario
start_year = 2000

for i in range(0, len(region_list)):
    energy_demand_i = (
        energy_demand.loc[region_list[i], slice(None), slice(None), scenario]
        * unit[1]
    ).loc[:, start_year:]

    if region_list[i] == "World ":
        energy_demand_i.loc["Transport", "Other fuels"] = energy_demand_i.loc[
            "Transport", ["International bunkers", "Other fuels"], :
        ].sum()

    fig = (
        energy_demand_i.loc[(slice(None), "Electricity"), :]
        .groupby(["Sector"])
        .sum()
        .drop("TFC")
        .rename(
            index={
                "Buildings": "Buildings-Electricity",
                "Industry": "Industry-Electricity",
                "Transport": "Transport-Electricity",
            }
        )
        .append(
            pd.DataFrame(
                energy_demand_i.loc["Transport", slice(None)]
                .groupby(["Metric"])
                .sum()
                .loc[
                    [
                        "Oil",
                        "Bioenergy",
                        "Other fuels",
                    ],
                    :,
                ]
                .sum()
            ).T.rename(index={0: "Transport-Nonelectric"})
        )
        .append(
            pd.DataFrame(
                energy_demand_i.loc["Buildings", slice(None)]
                .groupby(["Metric"])
                .sum()
                .loc[
                    [
                        "Heat",
                    ],
                    :,
                ]
                .sum()
            ).T.rename(index={0: "Buildings-Heat"})
        )
        .append(
            pd.DataFrame(
                energy_demand_i.loc["Industry", slice(None)]
                .groupby(["Metric"])
                .sum()
                .loc[
                    [
                        "Heat",
                    ],
                    :,
                ]
                .sum()
            ).T.rename(index={0: "Industry-Heat"})
        )
        .reindex(
            [
                "Transport-Nonelectric",
                "Transport-Electricity",
                "Buildings-Heat",
                "Buildings-Electricity",
                "Industry-Heat",
                "Industry-Electricity",
            ]
        )
    ).loc[:, start_year:long_proj_end_year]
    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Transport-Nonelectric",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Nonelectric"]["TFC, " + unit[0]],
            fill="tozeroy",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport-Electricity",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Electricity"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings-Heat",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings-Heat"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings-Electricity",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings-Electricity"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry-Heat",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry-Heat"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry-Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry-Electricity"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.update_layout(
        title={
            "text": "Energy Demand, " + region_list[i].replace(" ","") + ", " + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
            'y':.93,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(
        x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0
    )

    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to <br>IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline <br>Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/demand-" + scenario + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

#####################################
# ENERGY SUPPLY BY SOURCE & END-USE #
#####################################

# region

scenario = scenario
start_year = 2000

tech_list = [
    "Electricity-Solar",
    "Electricity-Wind",
    "Electricity-Nuclear",
    "Electricity-Other ren",
    "Heat-Solar thermal",
    "Heat-Bioenergy",
    "Heat-Fossil fuels",
    "Transport-Fossil fuels",
    "Electricity-Fossil fuels",
    "Transport-Bioenergy & H2",
]

group_keys = {
    ("Electricity", "Biomass and waste"): "Electricity-Other ren",
    ("Electricity", "Fossil fuels"): "Electricity-Fossil fuels",
    ("Electricity", "Geothermal"): "Electricity-Other ren",
    ("Electricity", "Hydroelectricity"): "Electricity-Other ren",
    ("Electricity", "Tide and wave"): "Electricity-Other ren",
    ("Electricity", "Nuclear"): "Electricity-Nuclear",
    ("Electricity", "Solar"): "Electricity-Solar",
    ("Electricity", "Wind"): "Electricity-Wind",
    ("Heat", "Fossil fuels"): "Heat-Fossil fuels",
    ("Heat", "Bioenergy"): "Heat-Bioenergy",
    ("Heat", "Coal"): "Heat-Fossil fuels2",
    ("Heat", "Geothermal"): "Heat-Bioenergy",
    ("Heat", "Natural gas"): "Heat-Fossil fuels2",
    ("Heat", "Nuclear"): "Heat-Fossil fuels2",
    ("Heat", "Oil"): "Heat-Fossil fuels2",
    ("Heat", "Other sources"): "Heat-Bioenergy",
    ("Heat", "Solar thermal"): "Heat-Solar thermal",
    ("Heat", "Waste"): "Heat-Bioenergy",
    ("Transport", "Oil"): "Transport-Fossil fuels2",
    ("Transport", "Bioenergy"): "Transport-Bioenergy & H2",
    ("Transport", "Other fuels"): "Transport-Bioenergy & H2",
    ("Transport", "Fossil fuels"): "Transport-Fossil fuels",
}

for i in range(0, len(region_list)):
    elec_consump_i = (
        elec_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    elec_consump_i = pd.concat([elec_consump_i], keys=["Electricity"], names=["Sector"])
    heat_consump_i = (
        heat_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    heat_consump_i = pd.concat([heat_consump_i], keys=["Heat"], names=["Sector"])
    transport_consump_i = (
        transport_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    transport_consump_i = pd.concat(
        [transport_consump_i], keys=["Transport"], names=["Sector"]
    )
    fig = (
        pd.DataFrame(
            (elec_consump_i.append(heat_consump_i).append(transport_consump_i)).loc[
                :, start_year:long_proj_end_year
            ]
        )
        * unit[1]
    )
    fig = fig.groupby(group_keys).sum()
    fig = fig.reindex(tech_list)

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Electricity-Solar",
            line=dict(width=0.5, color="rgb(136,204,238)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Solar"]["TFC, " + unit[0]],
            fill="tozeroy",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Wind",
            line=dict(width=0.5, color="rgb(204,102,119)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Wind"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Nuclear",
            line=dict(width=0.5, color="rgb(221,204,119)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Nuclear"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Other ren",
            line=dict(width=0.5, color="rgb(17,119,51)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Other ren"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Fossil fuels",
            line=dict(width=0.5, color="rgb(51,34,136)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Fossil fuels"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Solar thermal",
            line=dict(width=0.5, color="rgb(170,168,153)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Solar thermal"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Biochar",
            line=dict(width=0.5, color="rgb(136,204,238)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Biochar"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Bioenergy",
            line=dict(width=0.5, color="rgb(68,170,153)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Bioenergy"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Fossil fuels",
            line=dict(width=0.5, color="rgb(153,153,51)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Fossil fuels"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport-Fossil fuels",
            line=dict(width=0.5, color="rgb(136,34,85)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Fossil fuels"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport-Bioenergy & H2",
            line=dict(width=0.5, color="rgb(102,17,0)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Bioenergy & H2"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.update_layout(
        title={
            "text": "Energy Supply, " + region_list[i] + ", " + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(
        x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to <br>IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline <br>Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/supply-"
                + scenario
                + "-"
                + region_list[i].replace(" ", "")
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

##########################################
# ELECTRICITY SUPPLY BY SOURCE & END-USE #
##########################################

# region

scenario = scenario
start_year = start_year

tech_list = [
    "Electricity-Solar",
    "Electricity-Wind",
    "Electricity-Nuclear",
    "Electricity-Other ren",
    "Electricity-Fossil fuels",
]

group_keys = {
    ("Electricity", "Biomass and waste"): "Electricity-Other ren",
    ("Electricity", "Fossil fuels"): "Electricity-Fossil fuels",
    ("Electricity", "Geothermal"): "Electricity-Other ren",
    ("Electricity", "Hydroelectricity"): "Electricity-Other ren",
    ("Electricity", "Tide and wave"): "Electricity-Other ren",
    ("Electricity", "Nuclear"): "Electricity-Nuclear",
    ("Electricity", "Solar"): "Electricity-Solar",
    ("Electricity", "Wind"): "Electricity-Wind",
    ("Heat", "Fossil fuels"): "Heat-Fossil fuels",
    ("Heat", "Bioenergy"): "Heat-Bioenergy",
    ("Heat", "Coal"): "Heat-Fossil fuels2",
    ("Heat", "Geothermal"): "Heat-Bioenergy",
    ("Heat", "Natural gas"): "Heat-Fossil fuels2",
    ("Heat", "Nuclear"): "Heat-Fossil fuels2",
    ("Heat", "Oil"): "Heat-Fossil fuels2",
    ("Heat", "Other sources"): "Heat-Bioenergy",
    ("Heat", "Solar thermal"): "Heat-Solar thermal",
    ("Heat", "Waste"): "Heat-Biochar",
    ("Transport", "Oil"): "Transport-Fossil fuels2",
    ("Transport", "Bioenergy"): "Transport-Bioenergy & H2",
    ("Transport", "Other fuels"): "Transport-Bioenergy & H2",
    ("Transport", "Fossil fuels"): "Transport-Fossil fuels",
}


for i in range(0, len(region_list)):
    elec_consump_i = (
        elec_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    elec_consump_i = pd.concat(
        [elec_consump_i], keys=["Electricity"], names=["Sector"]
    )
    heat_consump_i = (
        heat_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    heat_consump_i = pd.concat([heat_consump_i], keys=["Heat"], names=["Sector"])
    transport_consump_i = (
        transport_consump.loc[region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    transport_consump_i = pd.concat(
        [transport_consump_i], keys=["Transport"], names=["Sector"]
    )
    fig = (
        pd.DataFrame(
            (elec_consump_i.append(heat_consump_i).append(transport_consump_i)).loc[
                :, start_year:long_proj_end_year
            ]
        )
        * unit[1]
    )
    fig = fig.groupby(group_keys).sum()
    fig = fig.reindex(tech_list)
    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0]
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Electricity-Solar",
            line=dict(width=0.5, color="rgb(136,204,238)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Solar"]["TFC, " + unit[0]],
            fill="tozeroy",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Wind",
            line=dict(width=0.5, color="rgb(204,102,119)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Wind"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Nuclear",
            line=dict(width=0.5, color="rgb(221,204,119)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Nuclear"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Other ren",
            line=dict(width=0.5, color="rgb(17,119,51)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Other ren"][
                "TFC, " + unit[0]
            ],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity-Fossil fuels",
            line=dict(width=0.5, color="rgb(51,34,136)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity-Fossil fuels"][
                "TFC, " + unit[0]
            ],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Solar thermal",
            line=dict(width=0.5, color="rgb(170,168,153)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Solar thermal"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Biochar",
            line=dict(width=0.5, color="rgb(136,204,238)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Biochar"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Bioenergy",
            line=dict(width=0.5, color="rgb(68,170,153)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Bioenergy"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Heat-Fossil fuels",
            line=dict(width=0.5, color="rgb(153,153,51)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Heat-Fossil fuels"]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport-Fossil fuels",
            line=dict(width=0.5, color="rgb(136,34,85)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Fossil fuels"][
                "TFC, " + unit[0]
            ],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport-Bioenergy & H2",
            line=dict(width=0.5, color="rgb(102,17,0)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport-Bioenergy & H2"][
                "TFC, " + unit[0]
            ],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.update_layout(
        title={
            "text": "Electricity Supply, "
            + region_list[i].replace(" ", "")
            + ", "
            + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(x0=start_year, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to <br>IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline <br>Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/supply2-"
                + scenario
                + "-"
                + region_list[i]
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

###################
# EMISSIONS (OLD) #
###################

# region

scenario = scenario
start_year = 2000

for i in range(0, len(region_list)):
    if scenario == "baseline":
        em = em_baseline
    else:
        em = em_pathway

    em_electricity = (
        em.loc[region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        em.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None),
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fw = (
        em.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None),
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_othergas = (
        em.loc[region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    if region_list[i] == "World ":
        em_cdr = -cdr.loc['World ','Carbon Dioxide Removal', scenario, :].squeeze()

        em = pd.DataFrame(
            [
                em_electricity,
                em_transport,
                em_buildings,
                em_industry,
                em_othergas,
                em_ra,
                em_fw,
                em_cdr,
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Other",
                "Unnamed 5": "Agriculture",
                "Unnamed 6": "Forests & Wetlands",
                "0": "CDR",
            }
        )
    else:
        em = pd.DataFrame(
            [
                em_electricity,
                em_transport,
                em_buildings,
                em_industry,
                em_othergas,
                em_ra,
                em_fw,
            ]
        ).rename(
            index={
                0: "Electricity",
                1: "Transport",
                2: "Buildings",
                3: "Industry",
                4: "Other",
                5: "Agriculture",
                6: "Forests & Wetlands",
            }
        )

    fig = ((em) / 1000).loc[:, start_year:]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()
    """
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tozeroy",
                stackgroup="one",
            )
        )
    """
    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="fw",
        )
    )

    if (
        fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
    ).any() == True:
        if (
            fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
        ).all() == True:
            fill = "tozeroy"
            stackgroup = "two"
        else:
            fill = "tonexty"
            stackgroup = "fw"
    else:
        fill = "tonexty"
        stackgroup = "fw"

    fig.add_trace(
        go.Scatter(
            name="Agriculture",
            line=dict(width=0.5, color="#EECA3B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

    fig.add_trace(
        go.Scatter(
            name="Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup2,
        )
    )

    """
    fig.add_trace(
        go.Scatter(
            name="CH4",
            line=dict(width=0.5, color="#B82E2E"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "CH4"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="N2O",
            line=dict(width=0.5, color="#77453b"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "N2O"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="F-gases",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "F-gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )
    """
    fig.add_trace(
        go.Scatter(
            name="Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    if em_fw.loc[2000] < 0:
        histfill = "tozeroy"
        stackgroup = "hist"
    else:
        histfill = "tozeroy"
        stackgroup = "hist"

    fig.add_trace(
        go.Scatter(
            name="Historical Net Emissions",
            line=dict(width=2, color="black"),
            x=pd.Series(em_hist.loc[:, start_year:].columns.values),
            y=pd.Series(
                em_hist.loc[region_list[i]].loc[:, start_year:].values[0] / 1000
            ),
            fill=histfill,
            stackgroup=stackgroup,
        )
    )
    """
    fig.add_trace(
        go.Scatter(
            name="PD-DAU Net Emissions",
            line=dict(width=2, color="green", dash='dot'),
            x=fig2[fig2["Year"] >= data_end_year]['Year'],
            y=fig2[(fig2["Year"] >= data_end_year)].append(),
        )
    )
    """

    fig.update_layout(
        title={
            "text": "Emissions, " + scenario.title() + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA <br>World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario <br>for 2040-2100; emissions factors are from IEA Emissions Factors 2020",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=6,
        bgcolor="#ffffff",
        opacity=1,
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/em2-" + scenario + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

################
# EMISSIONS # V2 collapses 'other gases' into sectors
################

# region

scenario = scenario
start_year = 2000

for i in range(0, len(region_list)):

    em_electricity = (
        em.loc[region_list[i], ["Electricity"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_electricity = em_electricity.loc[~(em_electricity==0).all(axis=1)]

    em_transport = (
        em.loc[region_list[i], ["Transport"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_transport = em_transport.loc[~(em_transport==0).all(axis=1)]

    em_buildings = (
        em.loc[region_list[i], ["Buildings"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_buildings = em_buildings.loc[~(em_buildings==0).all(axis=1)]

    em_industry = (
        em.loc[
            region_list[i],
            ["Industry"],
            slice(None), slice(None), scenario
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_industry = em_industry.loc[~(em_industry==0).all(axis=1)]

    em_ra = (
        em.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_ra = em_ra.loc[~(em_ra==0).all(axis=1)]

    em_fw = (
        em.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_fw = em_fw.loc[~(em_fw==0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc['World ', ['Carbon Dioxide Removal'], scenario, :]
        em_cdr = pd.concat([pd.concat([em_cdr], names=['Gas'], keys=['CO2'])], names=['Metric'], keys=['Carbon Dioxide Removal']).reorder_levels(['Region', 'Sector', 'Metric', 'Gas', 'Scenario'])

        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)

    else:
        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)

    fig = ((em2.groupby('Sector').sum()) / 1000).loc[:, start_year:]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

    """
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tozeroy",
                stackgroup="one",
            )
        )
    """

    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="fw",
        )
    )

    if (
        fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
    ).any() == True:
        if (
            fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
        ).all() == True:
            fill = "tozeroy"
            stackgroup = "two"
        else:
            fill = "tonexty"
            stackgroup = "fw"
    else:
        fill = "tonexty"
        stackgroup = "fw"

    fig.add_trace(
        go.Scatter(
            name="V5: Agriculture",
            line=dict(width=0.5, color="#EECA3B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Regenerative Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

    """
    fig.add_trace(
        go.Scatter(
            name="Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="CH4",
            line=dict(width=0.5, color="#B82E2E"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "CH4"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="N2O",
            line=dict(width=0.5, color="#77453b"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "N2O"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="F-gases",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "F-gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )
    """

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    if em_fw.loc[:,2000].values[0] < 0:
        histfill = "tozeroy"
        stackgroup = "hist"
    else:
        histfill = "tozeroy"
        stackgroup = "hist"

    fig.add_trace(
        go.Scatter(
            name="Historical Net Emissions",
            line=dict(width=2, color="black"),
            x=pd.Series(em_hist.loc[:, start_year:].columns.values),
            y=pd.Series(
                em_hist.loc[region_list[i]].loc[:, start_year:].values[0] / 1000
            ),
            fill=histfill,
            stackgroup=stackgroup,
        )
    )

    fig.update_layout(
        title={
            "text": "Emissions, " + scenario.title() + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA <br>World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario <br>for 2040-2100; emissions factors are from IEA Emissions Factors 2020",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=6,
        bgcolor="#ffffff",
        opacity=1,
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/em2-" + scenario + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

################
# EMISSIONS V3 # One chart per sector, gas breakdown
################

# region

scenario = scenario
start_year = 2000

colors = px.colors.qualitative.Safe

for i in range(0, len(region_list)):

    em_electricity = (
        em.loc[region_list[i], ["Electricity"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_electricity = em_electricity.loc[~(em_electricity==0).all(axis=1)]

    em_transport = (
        em.loc[region_list[i], ["Transport"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_transport = em_transport.loc[~(em_transport==0).all(axis=1)]

    em_buildings = (
        em.loc[region_list[i], ["Buildings"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_buildings = em_buildings.loc[~(em_buildings==0).all(axis=1)]

    em_industry = (
        em.loc[
            region_list[i],
            ["Industry"],
            slice(None), slice(None), scenario
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_industry = em_industry.loc[~(em_industry==0).all(axis=1)]

    '''
    em_industry.loc[region_list[i], 'Industry', 'Fossil fuels', slice(None), scenario] = em_industry.loc[slice(None), slice(None), ['Fossil fuels', 'Cement'],:].sum()

    em_industry = em_industry.loc[region_list[i], 'Industry', ['Fossil fuels', 'CH4', 'N2O', 'F-gases']]
    '''

    em_ra = (
        em.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_ra = em_ra.loc[~(em_ra==0).all(axis=1)]

    em_fw = (
        em.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_fw = em_fw.loc[~(em_fw==0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc['World ', ['Carbon Dioxide Removal'], scenario, :]
        em_cdr = pd.concat([pd.concat([em_cdr], names=['Gas'], keys=['CO2'])], names=['Metric'], keys=['Carbon Dioxide Removal']).reorder_levels(['Region', 'Sector', 'Metric', 'Gas', 'Scenario'])

        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)

    else:
        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)

    for j in pd.Series(em2.index.get_level_values(1).unique()):

        fig = ((em2.loc[slice(None), j,:].groupby('Gas').sum()) / 1000).loc[:, start_year:]
        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e"
        )

        fig = go.Figure()

        for gas in fig2['Metric'].unique():
            fig.add_trace(
                go.Scatter(
                    name=gas,
                    line=dict(width=0.5, color=colors[pd.DataFrame(fig2['Metric'].unique()).set_index(0).index.get_loc(gas)]),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == gas]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup='1',
                )
            )

        fig.update_layout(
            title={
                "text": "Emissions by Type in " + str(j) + ", " + scenario.title() + ", " + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"}, showlegend=True
        )

        fig.add_annotation(
            text="Historical data is from Global Carbon Project and Community Emissions Data System; projections are based on PD21 technology adoption rate assumptions<br>applied to IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model for 2040-2100; emissions factors are from IEA<br>Emissions Factors 2020.",
            xref="paper",
            yref="paper",
            x=-0.16,
            y=1.17,
            showarrow=False,
            font=dict(size=9, color="#2E3F5C"),
            align="left",
            borderpad=6,
            bgcolor="#ffffff",
            opacity=1,
        )

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/em3-" + scenario + "-" + region_list[i] + "-" + str(j) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )
        plt.clf()

# endregion

################
# EMISSIONS V4 # One chart per gas, sector breakdown
################

# region

scenario = scenario
start_year = 2000

colors = px.colors.qualitative.Safe

for i in range(0, len(region_list)):

    em_electricity = (
        em.loc[region_list[i], ["Electricity"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_electricity = em_electricity.loc[~(em_electricity==0).all(axis=1)]

    em_transport = (
        em.loc[region_list[i], ["Transport"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_transport = em_transport.loc[~(em_transport==0).all(axis=1)]

    em_buildings = (
        em.loc[region_list[i], ["Buildings"], slice(None), slice(None), scenario]
        .loc[:,start_year:long_proj_end_year]
    )
    em_buildings = em_buildings.loc[~(em_buildings==0).all(axis=1)]

    em_industry = (
        em.loc[
            region_list[i],
            ["Industry"],
            slice(None), slice(None), scenario
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_industry = em_industry.loc[~(em_industry==0).all(axis=1)]

    em_ra = (
        em.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_ra = em_ra.loc[~(em_ra==0).all(axis=1)]

    em_fw = (
        em.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None), slice(None),
            scenario,
        ]
        .loc[:,start_year:long_proj_end_year]
    )
    em_fw = em_fw.loc[~(em_fw==0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc['World ', ['Carbon Dioxide Removal'], scenario, :]
        em_cdr = pd.concat([pd.concat([em_cdr], names=['Gas'], keys=['CO2'])], names=['Metric'], keys=['Carbon Dioxide Removal']).reorder_levels(['Region', 'Sector', 'Metric', 'Gas', 'Scenario'])

        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)

    else:
        em2 = em_electricity.append(em_transport).append(em_buildings).append(em_industry).append(em_ra).append(em_fw)
  

    for gas in em2.index.get_level_values(3).unique():

        fig = ((em2.loc[region_list[i], slice(None), slice(None), gas, scenario, :].groupby('Sector').sum()) / 1000).loc[:, start_year:]
        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e"
        )

        fig = go.Figure()

        for j in pd.Series(em2.index.get_level_values(1).unique()).iloc[::-1]:
            fig.add_trace(
                go.Scatter(
                    name=j,
                    line=dict(width=0.5, color=colors[pd.DataFrame(em2.index.get_level_values(1).unique()).set_index('Sector').index.get_loc(j)]),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == j]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup='1',
                )
            )

        fig.update_layout(
            title={
                "text": "Emissions by Sector in " + str(gas) + ", " + scenario.title() + ", " + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"}, showlegend=True
        )

        fig.add_annotation(
            text="Historical data is from Global Carbon Project and Community Emissions Data System; projections are based on PD21 technology adoption rate assumptions<br>applied to IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model for 2040-2100; emissions factors are from IEA<br>Emissions Factors 2020.",
            xref="paper",
            yref="paper",
            x=-0.16,
            y=1.17,
            showarrow=False,
            font=dict(size=9, color="#2E3F5C"),
            align="left",
            borderpad=6,
            bgcolor="#ffffff",
            opacity=1,
        )

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/em4-" + scenario + "-" + region_list[i] + "-" + str(j) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )
        plt.clf()

# endregion

###########################
# EMISSIONS AS RELATIVE % #
###########################

# region

scenario = scenario
start_year = 2000

for i in range(0, len(region_list)):
    if scenario == "baseline":
        em = em_baseline.clip(lower=0)
    else:
        em = em_pathway.clip(lower=0)

    em_electricity = (
        em.loc[region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        em.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None),
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fw = (
        em.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None),
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_othergas = (
        em.loc[region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    if region_list[i] == "World ":
        em_cdr = -cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :].squeeze()

        em = pd.DataFrame(
            [
                em_electricity,
                em_transport,
                em_buildings,
                em_industry,
                em_othergas,
                em_ra,
                em_fw,
                em_cdr,
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Other",
                "Unnamed 5": "Agriculture",
                "Unnamed 6": "Forests & Wetlands",
                "0": "CDR",
            }
        )
    else:
        em = pd.DataFrame(
            [
                em_electricity,
                em_transport,
                em_buildings,
                em_industry,
                em_othergas,
                em_ra,
                em_fw,
            ]
        ).rename(
            index={
                0: "Electricity",
                1: "Transport",
                2: "Buildings",
                3: "Industry",
                4: "Other",
                5: "Agriculture",
                6: "Forests & Wetlands",
            }
        )

    fig = ((em) / 1000).loc[:, start_year:]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()
    """
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tozeroy",
                stackgroup="one",
            )
        )
    """
    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="fw",
            groupnorm="percent",
        )
    )

    if (
        fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
    ).any() == True:
        if (
            fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"] < 0
        ).all() == True:
            fill = "tozeroy"
            stackgroup = "two"
        else:
            fill = "tonexty"
            stackgroup = "fw"
    else:
        fill = "tonexty"
        stackgroup = "fw"

    fig.add_trace(
        go.Scatter(
            name="V5: Agriculture",
            line=dict(width=0.5, color="#EECA3B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
            groupnorm="percent",
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

    fig.add_trace(
        go.Scatter(
            name="V8: Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup2,
            groupnorm="percent",
        )
    )

    """
    fig.add_trace(
        go.Scatter(
            name="CH4",
            line=dict(width=0.5, color="#B82E2E"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "CH4"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="N2O",
            line=dict(width=0.5, color="#77453b"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "N2O"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="F-gases",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "F-gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )
    """
    fig.add_trace(
        go.Scatter(
            name="Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
        )
    )

    fig.update_layout(
        title={
            "text": "Emissions as Relative %, " + scenario.title() + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% of Total Emissions"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA <br>World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario <br>for 2040-2100; emissions factors are from IEA Emissions Factors 2020",
        xref="paper",
        yref="paper",
        x=-0.17,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.add_vrect(x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0)

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/em3-" + scenario + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

###########################
# MITIGATION WEDGES CURVE #
###########################

# region

scenario = 'pathway'
start_year = start_year

ndcs = [
    [(2030, 2050), (25, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2025, 2050, 2030, 2050),
        (4.86, 2.84, 2.84, 0),
        ("NDC", "NDC 2050 est.", "50% reduction by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.3, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.49),
    (3, 3),
    [(2030, 2030, 2050), (12.96, 6.15, 0), ('NDC', "50% reduction by 2030", "Net-zero by 2050")],
    (2030, 5.88),
    (2030, 1),
    (3, 3),
    (3, 3),
]

ndc_commit = [
    ("x",),
    ("x",),
    ("reduce emissions to 25% below 2005 levels by 2025.",),
    ("x",),
    ("reduce emissions to 1.3 GtCO2e by 2025 and 1.2 by 2030.",),
    ("x",),
    ("x",),
    ("reduce emissions to 398-614 MtCO2e over the period 2025-2030.",),
    ("x",),
    ("reduce emissions to 25-30% below 1990 by 2030",),
    ("x",),
    ("reach a GDP carbon intensity 60-65% below 2005 levels by 2030.",),
    ("reach a GDP carbon intensity of 33-35% below 2005 by 2030.",),
    (
        "reduce emissions to 26% emissions below 2013 levels in 2030 and reach net 0 by 2050.",
    ),
    ("x",),
    ("x",),
]

for i in range(0, len(region_list)):
    em_mit_electricity = em_mitigated.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated.loc[
        region_list[i],
        [
            "Biochar",
            "Cropland Soil Health",
            "Improved Rice",
            "Nitrogen Fertilizer Management",
            "Trees in Croplands",
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Regenerative Agriculture",
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_fw = em_mitigated.loc[
        region_list[i],
        [
            "Avoided Coastal Impacts",
            "Avoided Forest Conversion",
            "Avoided Peat Impacts",
            "Coastal Restoration",
            "Improved Forest Mgmt",
            "Peat Restoration",
            "Natural Regeneration",
            "Forests & Wetlands",
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_othergas = em_mitigated.loc[region_list[i], "Other", :].sum()

    em_mit_ch4 = em_mitigated.loc[region_list[i], "Other", "CH4"].rename("CH4")

    em_mit_n2o = em_mitigated.loc[region_list[i], "Other", "N2O"].rename("N2O")

    em_mit_fgas = em_mitigated.loc[region_list[i], "Other", "F-gases"].rename(
        "F-gases"
    )

    if region_list[i] in ["World "]:
        em_mit_mar = em_mitigated.loc[region_list[i], "Mariculture"].squeeze()
        
        em_mit_cdr = cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :].squeeze().rename("CDR")
        em_mit = pd.DataFrame(
            [
                em_mit_electricity,
                em_mit_transport,
                em_mit_buildings,
                em_mit_industry,
                em_mit_ra,
                em_mit_fw,
                em_mit_othergas,
                em_mit_cdr, em_mit_mar
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Forests & Wetlands",
                "Unnamed 5": "Agriculture",
                "Unnamed 6": "Other Gases",
                "CDR": "CDR", "Mariculture": "Mariculture"
            }
        ).clip(lower=0)
    elif region_list[i] in ["US ", "CHINA ", "EUR "]:
        em_mit_cdr = cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :].squeeze().rename("CDR")
        em_mit = pd.DataFrame(
            [
                em_mit_electricity,
                em_mit_transport,
                em_mit_buildings,
                em_mit_industry,
                em_mit_ra,
                em_mit_fw,
                em_mit_othergas,
                em_mit_cdr,
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Forests & Wetlands",
                "Unnamed 5": "Agriculture",
                "Unnamed 6": "Other Gases",
                "CDR": "CDR",
            }
        ).clip(lower=0)
    else:
        em_mit = (
            pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                    em_mit_othergas,
                ]
            )
            .clip(lower=0)
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Forests & Wetlands",
                    5: "Agriculture",
                    6: "Other Gases",
                }
            )
        ).clip(lower=0)

    spacer = (
        pd.Series(
            em_baseline.groupby("Region").sum().loc[region_list[i]] - em_mit.sum()
        )
        .replace(nan, 0)
        .rename("")
        .T
    )

    em_targets = (
        em_targets_pathway.loc[
            "MESSAGE-GLOBIOM 1.0", "World ", slice(None), "Emissions|Kyoto Gases"
        ]
        .loc[:, data_start_year:]
        .div(1000)
    )

    fig = (
        ((em_mit.append(spacer)) / 1000)
        .reindex(
            [
                "Electricity",
                "Transport",
                "Buildings",
                "Industry",
                "Forests & Wetlands",
                "Agriculture",
                "Other Gases",
                "CDR", 'Mariculture',
                spacer.name,
            ]
        )
        .loc[:, data_end_year:]
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="",
            line=dict(width=0.5, color="rgba(230, 236, 245, 0)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == ""]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="one",
            showlegend=False,
        )
    )

    if region_list[i] in ["World ", 'US ', 'CHINA ', 'EUR ']:
        fig.add_trace(
            go.Scatter(
                name="V9: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR in 2100: " + str(fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)) + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.05,
            y=0.05,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    """
    fig.add_trace(
        go.Scatter(
            name="CH4",
            line=dict(width=0.5, color="#B82e2e"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "CH4"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="N2O",
            line=dict(width=0.5, color="#77453b"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "N2O"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="F-gases",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "F-gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    """

    fig.add_trace(
        go.Scatter(
            name="V8: Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other Gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )

    if region_list[i] in ["World "]:
        fig.add_trace(
            go.Scatter(
                name="V7: Mariculture",
                line=dict(width=0.5, color="#2FDDCE"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Mariculture"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

    fig.add_trace(
        go.Scatter(
            name="V5: Agriculture",
            line=dict(width=0.5, color="#EECA3B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=2, color="black"),
            x=pd.Series(em_hist.columns.values),
            y=pd.Series(em_hist.loc[region_list[i], :].values[0] / 1000),
            fill="none",
            stackgroup="two", showlegend=False
        )
    )

    # Targets/NDCS

    # region
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="SSP2-1.9",
                line=dict(width=2, color="#17BECF", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-19", near_proj_start_year:].index.values
                ),
                y=pd.Series(em_targets.loc["SSP2-19", near_proj_start_year:].values),
                fill="none",
                stackgroup="three",
            )
        )
        '''
        fig.add_trace(
            go.Scatter(
                name="SSP2-2.6",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(em_targets.loc["SSP2-26", near_proj_start_year:].values),
                fill="none",
                stackgroup="four",
            )
        )
        '''
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        fig.add_trace(
            go.Scatter(
                name="PD21-DAU",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
            )
        )

        fig.add_trace(
            go.Scatter(
                name="PD21+CDR",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="pd21+cdr",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][0]],
                y=[ndcs[i][1][0]],
                marker_color="#f71be9",
                name=ndcs[i][2][0],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#211df2",
                name=ndcs[i][2][1],
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                name="PD21-DAU",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name='50% reduction by 2030',
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name='Net-zero by 2050',
            )
        )

        fig.add_annotation(
            text="50% reduction and net-zero goals compare regional alignment with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=2, color="red", dash="dot"),
            x=pd.Series(em_targets.loc["SSP2-26", near_proj_start_year:].index.values),
            y=pd.Series(
                em_baseline.loc[:, near_proj_start_year:]
                .groupby("Region")
                .sum()
                .loc[region_list[i]]
                / 1000
            ),
            fill="none",
            stackgroup="six",
        )
    )

    if region_list[i] in ["US "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][3]],
                y=[ndcs[i][1][3]],
                marker_color="#05a118",
                name=ndcs[i][2][3],
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.2,
            y=-0.25,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )
    elif region_list[i] in [
        "SAFR ",
        "RUS ",
        "JPN ",
        "BRAZIL ",
        "INDIA ",
    ]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0]],
                y=[ndcs[i][1]],
                marker_color="#FC0080",
                name="NDC " + str(ndcs[i][0]),
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="center",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    # endregion

    fig.add_annotation(
        text="Historical data (black) is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to <br>IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario <br>for 2040-2100; emissions factors are from IEA Emissions Factors 2020",
        xref="paper",
        yref="paper",
        x=-0.18,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        title={
            "text": "Emissions Mitigated, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"}, legend=dict(font=dict(size=11))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-" + "pathway" + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    plt.clf()

# endregion

##############################
# MITIGATION WEDGES CURVE V2 # collapses 'other gases'
##############################

# region

scenario = 'pathway'
start_year = start_year

ndcs = [
    [(2030, 2050), (25, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2025, 2050, 2030, 2050),
        (4.86, 2.84, 2.84, 0),
        ("NDC", "NDC 2050 est.", "50% reduction by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.3, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.49),
    (3, 3),
    [(2030, 2030, 2050), (12.96, 6.15, 0), ('NDC', "50% reduction by 2030", "Net-zero by 2050")],
    (2030, 5.88),
    (2030, 1),
    (3, 3),
    (3, 3),
]

ndc_commit = [
    ("x",),
    ("x",),
    ("reduce emissions to 25% below 2005 levels by 2025.",),
    ("x",),
    ("reduce emissions to 1.3 GtCO2e by 2025 and 1.2 by 2030.",),
    ("x",),
    ("x",),
    ("reduce emissions to 398-614 MtCO2e over the period 2025-2030.",),
    ("x",),
    ("reduce emissions to 25-30% below 1990 by 2030",),
    ("x",),
    ("reach a GDP carbon intensity 60-65% below 2005 levels by 2030.",),
    ("reach a GDP carbon intensity of 33-35% below 2005 by 2030.",),
    (
        "reduce emissions to 26% emissions below 2013 levels in 2030 and reach net 0 by 2050.",
    ),
    ("x",),
    ("x",),
]

for i in range(0, len(region_list)):
    em_mit_electricity = em_mitigated.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated.loc[
        region_list[i],
        [
            "Biochar",
            "Cropland Soil Health",
            "Improved Rice",
            "Nitrogen Fertilizer Management",
            "Trees in Croplands",
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Regenerative Agriculture",
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_fw = em_mitigated.loc[
        region_list[i],
        [
            "Avoided Coastal Impacts",
            "Avoided Forest Conversion",
            "Avoided Peat Impacts",
            "Coastal Restoration",
            "Improved Forest Mgmt",
            "Peat Restoration",
            "Natural Regeneration",
            "Forests & Wetlands",
        ],
        slice(None),
        slice(None),
    ].sum()

    '''
    em_mit_ch4 = em_mitigated.loc[region_list[i], "Other", "CH4"].rename("CH4")

    em_mit_n2o = em_mitigated.loc[region_list[i], "Other", "N2O"].rename("N2O")

    em_mit_fgas = em_mitigated.loc[region_list[i], "Other", "F-gases"].rename(
        "F-gases"
    )
    '''

    if region_list[i] in ["World "]:
        em_mit_mar = em_mitigated.loc[region_list[i], "Mariculture"].squeeze()
        
        em_mit_cdr = cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :].squeeze().rename("CDR")
        em_mit = pd.DataFrame(
            [
                em_mit_electricity,
                em_mit_transport,
                em_mit_buildings,
                em_mit_industry,
                em_mit_ra,
                em_mit_fw,
                em_mit_cdr, em_mit_mar
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Forests & Wetlands",
                "Unnamed 5": "Agriculture",
                "CDR": "CDR", "Mariculture": "Mariculture"
            }
        ).clip(lower=0)
    elif region_list[i] in ["US ", "CHINA ", "EUR "]:
        em_mit_cdr = cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :].squeeze().rename("CDR")
        em_mit = pd.DataFrame(
            [
                em_mit_electricity,
                em_mit_transport,
                em_mit_buildings,
                em_mit_industry,
                em_mit_ra,
                em_mit_fw,
                em_mit_cdr,
            ]
        ).rename(
            index={
                "Unnamed 0": "Electricity",
                "Unnamed 1": "Transport",
                "Unnamed 2": "Buildings",
                "Unnamed 3": "Industry",
                "Unnamed 4": "Forests & Wetlands",
                "Unnamed 5": "Agriculture",
                "CDR": "CDR",
            }
        ).clip(lower=0)
    else:
        em_mit = (
            pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                ]
            )
            .clip(lower=0)
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Forests & Wetlands",
                    5: "Agriculture",
                }
            )
        ).clip(lower=0)

    spacer = (
        pd.Series(
            em_baseline.groupby("Region").sum().loc[region_list[i]] - em_mit.sum()
        )
        .replace(nan, 0)
        .rename("")
        .T
    )

    em_targets = (
        em_targets_pathway.loc[
            "MESSAGE-GLOBIOM 1.0", "World ", slice(None), "Emissions|Kyoto Gases"
        ]
        .loc[:, data_start_year:]
        .div(1000)
    )

    fig = (
        ((em_mit.append(spacer)) / 1000)
        .reindex(
            [
                "Electricity",
                "Transport",
                "Buildings",
                "Industry",
                "Forests & Wetlands",
                "Agriculture",
                "CDR", 'Mariculture',
                spacer.name,
            ]
        )
        .loc[:, data_end_year:]
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="",
            line=dict(width=0.5, color="rgba(230, 236, 245, 0)"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == ""]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="one",
            showlegend=False,
        )
    )

    if region_list[i] in ["World ", 'US ', 'CHINA ', 'EUR ']:
        fig.add_trace(
            go.Scatter(
                name="V9: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR in 2100: " + str(fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)) + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.05,
            y=0.05,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    """
    fig.add_trace(
        go.Scatter(
            name="CH4",
            line=dict(width=0.5, color="#B82e2e"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "CH4"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="N2O",
            line=dict(width=0.5, color="#77453b"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "N2O"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="F-gases",
            line=dict(width=0.5, color="#bbe272"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "F-gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other Gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    """

    if region_list[i] in ["World "]:
        fig.add_trace(
            go.Scatter(
                name="V7: Mariculture",
                line=dict(width=0.5, color="#2FDDCE"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Mariculture"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

    fig.add_trace(
        go.Scatter(
            name="V5: Agriculture",
            line=dict(width=0.5, color="#EECA3B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V6: Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=2, color="black"),
            x=pd.Series(em_hist.columns.values),
            y=pd.Series(em_hist.loc[region_list[i], :].values[0] / 1000),
            fill="none",
            stackgroup="two", showlegend=False
        )
    )

    # Targets/NDCS

    # region
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="SSP2-1.9",
                line=dict(width=2, color="#17BECF", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-19", near_proj_start_year:].index.values
                ),
                y=pd.Series(em_targets.loc["SSP2-19", near_proj_start_year:].values),
                fill="none",
                stackgroup="three",
            )
        )
        '''
        fig.add_trace(
            go.Scatter(
                name="SSP2-2.6",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(em_targets.loc["SSP2-26", near_proj_start_year:].values),
                fill="none",
                stackgroup="four",
            )
        )
        '''
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        fig.add_trace(
            go.Scatter(
                name="PD21-DAU",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
            )
        )

        fig.add_trace(
            go.Scatter(
                name="PD21+CDR",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="pd21+cdr",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][0]],
                y=[ndcs[i][1][0]],
                marker_color="#f71be9",
                name=ndcs[i][2][0],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#211df2",
                name=ndcs[i][2][1],
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                name="PD21-DAU",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name='50% reduction by 2030',
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name='Net-zero by 2050',
            )
        )

        fig.add_annotation(
            text="50% reduction and net-zero goals compare regional alignment with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=2, color="red", dash="dot"),
            x=pd.Series(em_targets.loc["SSP2-26", near_proj_start_year:].index.values),
            y=pd.Series(
                em_baseline.loc[:, near_proj_start_year:]
                .groupby("Region")
                .sum()
                .loc[region_list[i]]
                / 1000
            ),
            fill="none",
            stackgroup="six",
        )
    )

    if region_list[i] in ["US "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][3]],
                y=[ndcs[i][1][3]],
                marker_color="#05a118",
                name=ndcs[i][2][3],
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.2,
            y=-0.25,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )
    elif region_list[i] in [
        "SAFR ",
        "RUS ",
        "JPN ",
        "BRAZIL ",
        "INDIA ",
    ]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0]],
                y=[ndcs[i][1]],
                marker_color="#FC0080",
                name="NDC " + str(ndcs[i][0]),
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0] + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
            xref="paper",
            yref="paper",
            x=-0.17,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="center",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    # endregion

    fig.add_annotation(
        text="Historical data (black) is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to <br>IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario <br>for 2040-2100; emissions factors are from IEA Emissions Factors 2020",
        xref="paper",
        yref="paper",
        x=-0.18,
        y=1.17,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        title={
            "text": "Emissions Mitigated, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"}, legend=dict(font=dict(size=11))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-" + "pathway" + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    plt.clf()

# endregion

#################################
# EMISSIONS MITIGATION BARCHART #
#################################

# region

bar_emissions_goal = [
    ("of 50% reduction in the year 2030.", "of net-zero emissions in the year 2050."),
    ("x",),
    ("determined through linear extrapolation using the U.S’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2025.", "of net zero emissions, which was set in President Biden’s climate plan."),
    ("x",),
    ("set in Brazil’s 2015 NDC.", "determined through linear extrapolation using Brazil’s 2025 and <br>2030 emissions goals set in their 2015 NDC."), ("of 50% reduction in the year 2030.", "of net-zero emissions in the year 2050."),
    ("x",),
    ("set in South Africa’s 2015 NDC.", "determined through linear extrapolation using South Africa’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030. South Africa submitted a Low Emission <br>Development Scenario in 2020, but the scenario does not specify a 2050 emissions goal."),
    ("x",),
    ("set in Russia’s 2015 NDC.", "determined through linear extrapolation using Russia’s 1990 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030."),
    ("x",),
    ("determined by China’s 2020 NDC update to peak emissions before <br>2030.", "of net zero emissions, which was announced by President Xi Jinping in <br>September 2020."),
    ("set in India’s 2015 NDC.", 
    "determined through linear extrapolation using India’s 2017 emissions <br>and the NDC set in 2015, which set an emissions goal for 2030."),
    ("set in Japan’s 2015 NDC.", 
    "of net zero emissions, which was announced in Prime Minister Yoshihide <br>Suga's speech on October 26th, 2020."),
    ("x",),
    ("x",),
]

ndcs = [
    [(2030, 2050), (25, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    [(2030, 2050), (2.84, 0), ("NDC", "Net-zero by 2050")],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.3, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.17),
    (3, 3),
    [(2030, 2050), (12.96, 0), ('NDC', "Net-zero by 2050")],
    (2030, 9.14),
    (2030, 1),
    (3, 3),
    (3, 3),
]

scenario = 'pathway'

for year in [2030]:
    for i in range(0, len(region_list)):
        em_mit_electricity = em_mitigated.loc[
            region_list[i], "Electricity", slice(None)
        ].sum()

        em_mit_transport = em_mitigated.loc[
            region_list[i], "Transport", slice(None)
        ].sum()

        em_mit_buildings = em_mitigated.loc[
            region_list[i], "Buildings", slice(None)
        ].sum()

        em_mit_industry = em_mitigated.loc[
            region_list[i], "Industry", slice(None)
        ].sum()

        em_mit_ra = em_mitigated.loc[
            region_list[i],
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            slice(None),
            slice(None),
        ].sum()

        em_mit_fw = em_mitigated.loc[
            region_list[i],
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            slice(None),
            slice(None),
        ].sum()

        em_mit_othergas = em_mitigated.loc[region_list[i], slice(None), ['CH4', 'N2O', 'F-gases'], :].sum()

        if region_list[i] in ['World ', 'US ', 'CHINA ', 'EUR ']:
            em_mit_cdr = pd.Series(
                cdr.loc[region_list[i], 'Carbon Dioxide Removal', scenario].sum(), index=np.arange(data_start_year, long_proj_end_year + 1)
            ) / 100

            em_mit = pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                    em_mit_othergas,
                    em_mit_cdr,
                ]
            ).rename(
                index={
                    0: "V1: Electricity",
                    1: "V2: Transport",
                    2: "V3: Buildings",
                    3: "V4: Industry",
                    4: "V5: Forests & Wetlands",
                    5: "V6: Agriculture",
                    6: "V7: Mariculture",
                    7: "V8: Other Gases",
                    8: "V9: CDR"
                }
            )
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "V9: CDR",
                        "V8: Other Gases",
                        "V6: Agriculture",
                        "V5: Forests & Wetlands",
                        "V4: Industry",
                        "V3: Buildings",
                        "V2: Transport",
                        "V1: Electricity",
                    ]
                )
                .round(decimals=4)
                .clip(lower=0)
            )
            data = {
                "V1: Electricity": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V1: Electricity", year],
                    fig.loc["V1: Electricity", year],
                ],
                "V2: Transport": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V2: Transport", year],
                    0,
                    fig.loc["V2: Transport", year],
                ],
                "V3: Buildings": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V3: Buildings", year],
                    0,
                    0,
                    fig.loc["V3: Buildings", year],
                ],
                "V4: Industry": [
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                    0,
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                ],
                "V5: Forests & Wetlands": [
                    0,
                    0,
                    0,
                    fig.loc["V5: Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V5: Forests & Wetlands", year],
                ],
                "V6: Agriculture": [
                    0,
                    0,
                    fig.loc["V6: Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V6: Agriculture", year],
                ],
                "V8: Other Gases": [
                    0,
                    fig.loc["V8: Other Gases", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V8: Other Gases", year],
                ],
                "V9: CDR": [
                    fig.loc["V9: CDR", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V9: CDR", year],
                ],
                "Total": [
                    0,
                    fig.loc["V1: Electricity", year],
                    fig.loc["V2: Transport", year],
                    fig.loc["V3: Buildings", year],
                    fig.loc["V4: Industry", year],
                    fig.loc["V5: Forests & Wetlands", year],
                    fig.loc["V6: Agriculture", year],
                    fig.loc["V8: Other Gases", year],
                    fig.loc["V9: CDR", year],
                ],
                "labels": [
                    "V9: CDR",
                    "V8: Other Gases",
                    "V6: Agriculture",
                    "V5: Forests & Wetlands",
                    "V4: Industry",
                    "V3: Buildings",
                    "V2: Transport",
                    "V1: Electricity",
                    "Total",
                ],
            }
        else:
            em_mit = pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                    em_mit_othergas,
                ]
            ).rename(
                index={
                    0: "V1: Electricity",
                    1: "V2: Transport",
                    2: "V3: Buildings",
                    3: "V4: Industry",
                    4: "V5: Forests & Wetlands",
                    5: "V6: Agriculture",
                    6: "V7: Mariculture",
                    7: "V8: Other Gases",
                }
            )
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "V8: Other Gases",
                        "V6: Agriculture",
                        "V5: Forests & Wetlands",
                        "V4: Industry",
                        "V3: Buildings",
                        "V2: Transport",
                        "V1: Electricity",
                    ]
                )
                .round(decimals=4)
                .clip(lower=0)
            )
            data = {
                "V1: Electricity": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V1: Electricity", year],
                    fig.loc["V1: Electricity", year],
                ],
                "V2: Transport": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V2: Transport", year],
                    0,
                    fig.loc["V2: Transport", year],
                ],
                "V3: Buildings": [
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V3: Buildings", year],
                    0,
                    0,
                    fig.loc["V3: Buildings", year],
                ],
                "V4: Industry": [
                    0,
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                    0,
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                ],
                "V5: Forests & Wetlands": [
                    0,
                    0,
                    fig.loc["V5: Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V5: Forests & Wetlands", year],
                ],
                "V6: Agriculture": [
                    0,
                    fig.loc["V6: Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V6: Agriculture", year],
                ],
                "V8: Other Gases": [
                    fig.loc["V8: Other Gases", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V8: Other Gases", year],
                ],
                "Total": [
                    0,
                    fig.loc["V1: Electricity", year],
                    fig.loc["V2: Transport", year],
                    fig.loc["V3: Buildings", year],
                    fig.loc["V4: Industry", year],
                    fig.loc["V5: Forests & Wetlands", year],
                    fig.loc["V6: Agriculture", year],
                    fig.loc["V8: Other Gases", year],
                ],
                "labels": [
                    "V8: Other Gases",
                    "V6: Agriculture",
                    "V5: Forests & Wetlands",
                    "V4: Industry",
                    "V3: Buildings",
                    "V2: Transport",
                    "V1: Electricity",
                    "Total",
                ],
            }
        
        em_mit.loc[:, :2020] = 0
        opacity = 0.5

        if year == 2030:
            j = 0
        else:
            j = 1

        if region_list[i] in ["World ", 'US ', 'CHINA ', 'EUR ']:
            
            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["V9: CDR"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#FF9DA6",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V8: Other Gases"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#E45756",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V6: Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#EECA3B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V5: Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V4: Industry"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#60738C",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V3: Buildings"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#F58518",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V2: Transport"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#7AA8B8",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V1: Electricity"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#B279A2",
                        opacity=opacity,
                    ),
                ]
            )
            
            figure.add_shape(
                type="line",
                x0=pd.Series(data['Total']).sum(),
                y0=-0.5,
                x1=pd.Series(data['Total']).sum(),
                y1=8.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="NDC",
            )

            figure.add_annotation(
                text="The blue dotted line represents an emissions mitigation goal " + bar_emissions_goal[i][j],
                xref="paper",
                yref="paper",
                x=0,
                y=1.14,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="center",
                borderpad=4,
                bgcolor="#ffffff",
                opacity=1,
            )
        
        else:
            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["V8: Other Gases"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#E45756",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V6: Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#EECA3B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V5: Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V4: Industry"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#60738C",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V3: Buildings"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#F58518",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V2: Transport"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#7AA8B8",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V1: Electricity"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#B279A2",
                        opacity=opacity,
                    ),
                ]
            )

        if (region_list[i] in [
            "SAFR ",
            "RUS ",
            "JPN ",
            "BRAZIL ",
            "INDIA ",
        ]) & (year==2030):
            figure.add_shape(
                type="line",
                x0=(pd.Series(em_baseline.groupby("Region").sum().loc[region_list[i]][year]/1e3 - ndcs[i][1]).values[0]).clip(min=0),
                y0=-0.5,
                x1=(pd.Series(em_baseline.groupby("Region").sum().loc[region_list[i]][year]/1e3 - ndcs[i][1]).values[0]).clip(min=0),
                y1=7.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="NDC",
            )

            figure.add_annotation(
                text="The blue dotted line represents an emissions mitigation goal " + bar_emissions_goal[i][j],
                xref="paper",
                yref="paper",
                x=0,
                y=1.14,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="center",
                borderpad=4,
                bgcolor="#ffffff",
                opacity=1,
            )

        if region_list[i] in ['World ', 'US ', 'CHINA ', 'EUR ', "SAFR ", "RUS ", "JPN ", "BRAZIL ", "INDIA ", ]:

            ei = em_mit.loc[:, year].values.sum()/1e3 / (em_mit_ndc[(em_mit_ndc["Region"] == region_list[i]) & (em_mit_ndc.index == year)]["em_mit"].values[0])

            figure.add_annotation(
                text="Epic Index = PD Projected Mitigation Potential / Target Mitigation = "
                + str((em_mit.loc[:, year].values.sum()/1e3).round(decimals=2))
                + " GtCO2e"
                + "  /  "
                + str(((em_mit_ndc[(em_mit_ndc["Region"] == region_list[i]) & (em_mit_ndc.index == year)]["em_mit"].values[0])).round(decimals=2))
                + " GtCO2e = " + str(ei.round(decimals=2)),
                xref="paper",
                yref="paper",
                x=0,
                y=-0.25,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="left",
                borderpad=4,
                borderwidth=2,
                bgcolor="#ffffff",
                opacity=1,
            )
        '''
        figure.add_annotation(
            text="Mitigation potential is defined as the difference between baseline emissions and pathway emissions in a given year.",
            xref="paper",
            yref="paper",
            x=-0.2,
            y=-0.25,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )
        '''  
        figure.update_layout(
            title="Climate Mitigation Potential, "
            + str(year)
            + ", "
            + region_list[i],
            title_x=0.5,
            xaxis={"title": "GtCO2e mitigated in " + str(year)},
            barmode="stack",
            legend=dict(
                x=0.7,
                y=0,
                bgcolor="rgba(255, 255, 255, 0)",
                bordercolor="rgba(255, 255, 255, 0)",
            ),
            showlegend=False,
        )

        if show_figs is True:
            figure.show()
        if save_figs is True:
            pio.write_html(
                figure,
                file=(
                    "./charts/em1-"
                    + "pathway"
                    + "-"
                    + str(year)
                    + "-"
                    + region_list[i]
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

# endregion

#################################
# CO2 ATMOSPHERIC CONCENTRATION #
#################################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp60.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)

hist = pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv")).set_index(
    ["Region", "Metric", "Units", "Scenario"]
)
hist.columns = hist.columns.astype(int)
hist = hist.loc["World ", "Atm conc CO2", "ppm", "pathway"].T.dropna()

results = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
results.columns = results.columns.astype(int)
results19 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4",
            "SSP2-19",
            "World", "Diagnostics|MAGICC6|Concentration|CO2"].loc[2010:]).T , "quadratic", 3)

results19 = results19 * (hist[2021] / results19.loc[:,2021].values[0])

#CO2
em_b.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values - (cdr.loc['World ', 'Carbon Dioxide Removal', 'pathway'] / 3670).values


em_b.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values


#CH4
em_b.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_pd.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_cdr.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values

#N2O
em_b.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_pd.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_cdr.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)

Cb = (pd.DataFrame(Cb).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Cpd = (pd.DataFrame(Cpd).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Ccdr = (pd.DataFrame(Ccdr).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))

# CO2e conversion (not needed here for just CO2)
Cb['CO2'] = Cb.loc[:,0]
Cpd['CO2'] = Cpd.loc[:,0]
Ccdr['CO2'] = Ccdr.loc[:,0]

C19 = results19 * (hist[2021] / results19.loc[:,2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021,'CO2'])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021,'CO2'])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021,'CO2'])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, 'CO2'],
        fill="none",
        stackgroup="hist",
        legendgroup="hist",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cb.loc[data_end_year:, 'CO2'],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21-DAU",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, 'CO2'],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, 'CO2'],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={
        "text": "Atmospheric CO2 Concentration",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2"},
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FaIR climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=1.15,
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="center",
    borderpad=4,
    borderwidth=2,
    bgcolor="#ffffff",
    opacity=1,
)

if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/co2conc-" + "World " + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

#################################
# GHG ATMOSPHERIC CONCENTRATION #
#################################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp60.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)

hist = pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv")).set_index(
    ["Region", "Metric", "Units", "Scenario"]
)
hist.columns = hist.columns.astype(int)
hist = hist.loc["World ", "Equivalent CO2", "ppm", "pathway"].T.dropna()

results = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
results.columns = results.columns.astype(int)
results19 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            [
                "Diagnostics|MAGICC6|Concentration|CO2",
                "Diagnostics|MAGICC6|Concentration|CH4",
                "Diagnostics|MAGICC6|Concentration|N2O",
            ],
        ].loc[:,2010:].multiply([1, 25e-3, 298e-3], axis=0).sum()
    ).T,
    "quadratic",
    6,
)
results19 = results19 * (hist[2021] / results19.loc[:,2021].values[0])

#CO2
em_b.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values - (cdr.loc['World ', 'Carbon Dioxide Removal', 'pathway'] / 3670).values


em_b.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values


#CH4
em_b.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_pd.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_cdr.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values

#N2O
em_b.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_pd.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_cdr.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)

Cb = (pd.DataFrame(Cb).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Cpd = (pd.DataFrame(Cpd).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Ccdr = (pd.DataFrame(Ccdr).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))

# CO2e conversion
Cb['CO2e'] = Cb.loc[:,0] + Cb.loc[:,1] * 25e-3 + Cb.loc[:,2] * 298e-3
Cpd['CO2e'] = Cpd.loc[:,0] + Cpd.loc[:,1] * 25e-3 + Cpd.loc[:,2] * 298e-3
Ccdr['CO2e'] = Ccdr.loc[:,0] + Ccdr.loc[:,1] * 25e-3 + Ccdr.loc[:,2] * 298e-3

C19 = results19 * (hist[2021] / results19.loc[:,2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021,'CO2e'])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021,'CO2e'])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021,'CO2e'])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, 'CO2e'],
        fill="none",
        stackgroup="hist",
        legendgroup="hist",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cb.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21-DAU",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={
        "text": "Atmospheric GHG Concentration",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2e"},
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FaIR climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=1.15,
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="center",
    borderpad=4,
    borderwidth=2,
    bgcolor="#ffffff",
    opacity=1,
)

if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/ghgconc-" + "World " + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

#####################
# RADIATIVE FORCING #
#####################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp85.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)

hist = (pd.read_csv('podi/data/forcing.csv'))
hist.columns = hist.columns.astype(int)

F = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
F.columns = F.columns.astype(int)

F19 = curve_smooth(pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:]
    ), 'quadratic', 6)

#CO2
em_b.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values - (cdr.loc['World ', 'Carbon Dioxide Removal', 'pathway'] / 3670).values


em_b.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values


#CH4
em_b.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_pd.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_cdr.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values

#N2O
em_b.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_pd.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_cdr.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
'''
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
'''
Fb = (pd.DataFrame(Fb).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Fpd = (pd.DataFrame(Fpd).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Fcdr = (pd.DataFrame(Fcdr).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))

# CO2e conversion

Fb['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Fb, axis=1)).T, 'quadratic', 6).T
Fpd['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Fpd, axis=1)).T, 'quadratic', 6).T
Fcdr['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Fcdr, axis=1)).T, 'quadratic', 6).T
'''
Fb['CO2e'] = np.sum(Fb, axis=1)
Fpd['CO2e'] = np.sum(Fpd, axis=1)
Fcdr['CO2e'] = np.sum(Fcdr, axis=1)
'''

F19 = F19 * (hist.loc[:,2020].values[0] / F19.loc[:,2020].values[0])
Fb = Fb * (hist.loc[:, data_end_year].values[0] / Fb.loc[data_end_year,'CO2e'])
Fpd = Fpd * (hist.loc[:, data_end_year].values[0] / Fpd.loc[data_end_year,'CO2e'])
Fcdr = Fcdr * (hist.loc[:, data_end_year].values[0] / Fcdr.loc[data_end_year,'CO2e'])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:,data_start_year:long_proj_end_year].squeeze(),
        fill="none",
        stackgroup="hist",
        legendgroup="hist",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fb.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21-DAU",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fpd.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=F19.loc[:, 2020:2100].columns,
        y=F19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fcdr.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={
        "text": "Radiative Forcing",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "W/m2"},
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FaIR climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=1.15,
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="center",
    borderpad=4,
    borderwidth=2,
    bgcolor="#ffffff",
    opacity=1,
)

if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/forcing-" + 'World' + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

######################
# TEMPERATURE CHANGE #
######################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp85.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)

hist = (pd.read_csv('podi/data/temp.csv'))
hist.columns = hist.columns.astype(int)

T = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
T.columns = T.columns.astype(int)

T19 = curve_smooth(
    pd.DataFrame(
        T.loc[
            "GCAM4",
            "SSP1-19",
            "World",
            ["Diagnostics|MAGICC6|Temperature|Global Mean"],
        ].loc[:, 2010:]
    ),
    "quadratic",
    6,
)

#CO2
em_b.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 1] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Electricity', 'Transport', 'Buildings', 'Industry'], slice(None), 'pathway'].sum() / 3670).values - (cdr.loc['World ', 'Carbon Dioxide Removal', 'pathway'] / 3670).values


em_b.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'baseline'].sum() / 3670).values
em_pd.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values
em_cdr.loc[225:335, 2] = (em[~em.index.get_level_values(2).isin(['CH4', 'N2O', 'F-gases'])].loc['World ', ['Forests & Wetlands', 'Regenerative Agriculture'], slice(None), 'pathway'].sum() / 3670).values


#CH4
em_b.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_pd.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values
em_cdr.loc[225:335, 3] = (em[em.index.get_level_values(2).isin(['CH4'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (25)).values

#N2O
em_b.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_pd.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values
em_cdr.loc[225:335, 4] = (em[em.index.get_level_values(2).isin(['N2O'])].loc['World ', slice(None), slice(None), 'pathway'].sum() / (298)).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
'''
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
'''
Tb = (pd.DataFrame(Tb).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Tpd = (pd.DataFrame(Tpd).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))
Tcdr = (pd.DataFrame(Tcdr).loc[225:335].set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1)))

# CO2e conversion

Tb['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Tb, axis=1)).T, 'quadratic', 6).T
Tpd['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Tpd, axis=1)).T, 'quadratic', 6).T
Tcdr['CO2e'] = curve_smooth(pd.DataFrame(np.sum(Tcdr, axis=1)).T, 'quadratic', 6).T

T19 = T19 * (hist.loc[:,2020].values[0] / T19.loc[:,2020].values[0])
Tb = Tb * (hist.loc[:, data_end_year].values[0] / Tb.loc[data_end_year,'CO2e'])
Tpd = Tpd * (hist.loc[:, data_end_year].values[0] / Tpd.loc[data_end_year,'CO2e'])
Tcdr = Tcdr * (hist.loc[:, data_end_year].values[0] / Tcdr.loc[data_end_year,'CO2e'])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:,data_start_year:long_proj_end_year].squeeze(),
        fill="none",
        stackgroup="hist",
        legendgroup="hist",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tb.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21-DAU",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=T19.loc[:, 2020:2100].columns,
        y=T19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, 'CO2e'],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={
        "text": "Global Mean Temperature",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the Hector climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=1.15,
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="center",
    borderpad=4,
    borderwidth=2,
    bgcolor="#ffffff",
    opacity=1,
)

if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/temp-" + 'World' + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion


########################################
#//////////// NOT YET USED ////////////#
########################################


##########################
# EPIC INDEX ALL REGIONS #
##########################

# region

scenario = 'pathway'
start_year = 1990

# calculate

# region
em_total = em_hist

"""
em_total = pd.read_csv(
    "podi/data/CO2_CEDS_emissions_by_sector_country_2021_02_05.csv"
).drop(columns=["Em", "Units"])

em_total = pd.DataFrame(em_total).set_index(["Country", "Sector"]) / 1000

em_total.columns = em_total.columns.astype(int)

em_total = em_total.groupby("Country").sum()

region_categories = pd.read_csv(
    "podi/data/region_categories.csv", usecols=["ISO", "IEA Region"]
)

em_total = em_total.merge(region_categories, right_on=["ISO"], left_on=["Country"])

em_total = em_total.groupby("IEA Region").sum()

# split into various levels of IEA regional grouping
em_total["IEA Region 1"] = em_total.apply(lambda x: x.name.split()[2] + " ", axis=1)
em_total["IEA Region 2"] = em_total.apply(lambda x: x.name.split()[4] + " ", axis=1)
em_total["IEA Region 3"] = em_total.apply(
    lambda x: x.name.split()[-1] + " ", axis=1
)

em_total.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

# make new row for world level data
em_total_world = pd.DataFrame(em_total.sum()).T.rename(index={0: "World "})

# make new rows for OECD/NonOECD regions
em_total_oecd = pd.DataFrame(em_total.groupby("IEA Region 1").sum()).rename(
    index={"OECD ": " OECD "}
)

# make new rows for IEA regions
em_total_regions = pd.DataFrame(em_total.groupby("IEA Region 2").sum())
em_total_regions2 = pd.DataFrame(em_total.groupby("IEA Region 3").sum())

# combine all
em_total = em_total_world.append(
    [em_total_oecd, em_total_regions.combine_first(em_total_regions2)]
)
em_total.index.name = "IEA Region"

em_total = pd.concat([em_total], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Gas"]
)
em_total3 = pd.concat(
    [em_total], keys=["baseline"], names=["Scenario"]
).reorder_levels(["IEA Region", "Gas", "Scenario"])
em_total = em_total3.append(
    pd.concat([em_total], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Gas", "Scenario"]
    )
)
"""
# endregion

if scenario == "baseline":
    em = em_baseline
    afolu_em = afolu_em_baseline
else:
    em = em_pathway
    afolu_em = afolu_em_pathway

em_electricity = (
    em.loc[region_list[i], "Electricity", slice(None)]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_transport = (
    em.loc[region_list[i], "Transport", slice(None)]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_buildings = (
    em.loc[region_list[i], "Buildings", slice(None)]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_industry = (
    em.loc[
        region_list[i],
        ["Industry"],
        slice(None),
    ]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_ra = (
    afolu_em.loc[
        region_list[i],
        [
            "Regenerative Agriculture",
        ],
        slice(None),
        slice(None),
    ]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_fw = (
    afolu_em.loc[
        region_list[i],
        [
            "Forests & Wetlands",
        ],
        slice(None),
        slice(None),
    ]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_othergas = (
    em.loc[region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_ch4 = (
    em.loc[region_list[i], slice(None), ["CH4"]]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_n2o = (
    em.loc[region_list[i], slice(None), ["N2O"]]
    .sum()
    .loc[start_year:long_proj_end_year]
)

em_fgas = (
    em.loc[region_list[i], slice(None), ["F-gases"]]
    .sum()
    .loc[start_year:long_proj_end_year]
)
"""
em_total = em_total.loc[region_list[i], "CO2", scenario]
"""

em_total = em_total.loc[region_list[i], slice(None), slice(None), scenario]

if region_list[i] == "World ":
    em_cdr = -cdr.loc[slice(None), scenario, :].squeeze()

    em = pd.DataFrame(
        [
            em_electricity,
            em_transport,
            em_buildings,
            em_industry,
            em_othergas,
            em_ra,
            em_fw,
            em_cdr,
        ]
    ).rename(
        index={
            "Unnamed 0": "Electricity",
            "Unnamed 1": "Transport",
            "Unnamed 2": "Buildings",
            "Unnamed 3": "Industry",
            "Unnamed 4": "Other",
            "Unnamed 5": "Agriculture",
            "Unnamed 6": "Forests & Wetlands",
            0: "CDR",
        }
    )
else:
    em = pd.DataFrame(
        [
            em_electricity,
            em_transport,
            em_buildings,
            em_industry,
            em_othergas,
            em_ra,
            em_fw,
        ]
    ).rename(
        index={
            0: "Electricity",
            1: "Transport",
            2: "Buildings",
            3: "Industry",
            4: "Other",
            5: "Agriculture",
            6: "Forests & Wetlands",
        }
    )

ei = em_total.loc[:, data_end_year].values / (em.sum().loc[data_end_year])

fig2 = ei

fig = go.Figure()

fig.add_trace(
    go.bar(
        name="EI",
        line=dict(width=4, color="#EECA3B"),
        x=pd.Series(data_end_year),
        y=pd.Series(fig2),
    )
)

"""
fig.add_trace(
    go.Scatter(
        name="GCP",
        line=dict(width=2, color="black"),
        x=pd.Series(em_total.loc[start_year:data_end_year].index),
        y=pd.Series(em_total.loc[start_year:data_end_year].values),
    )
)
"""
fig.update_layout(
    title={
        "text": "Epic Index, " + scenario.title() + ", " + region_list[i],
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "Index"},
)

fig.update_layout(margin=dict())
fig.add_annotation(
    text="Epic Index = Measured Emissions  /  PD Projected Emissions"
    + "<br>"
    + "EI = "
    + str((em_total.loc[:, data_end_year].values[0] / 1000).round(decimals=3))
    + " GtCO2e"
    + "  /  "
    + str((em.sum().loc[data_end_year] / 1000).round(decimals=3))
    + " GtCO2e",
    xref="paper",
    yref="paper",
    x=0.4,
    y=1.15
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="left",
    borderpad=4,
    borderwidth=2,
    bgcolor="#ffffff",
    opacity=1,
)

fig.update_shapes(dict(xref="x", yref="y"))

if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=(
            "./charts/ei2-" + "-" + region_list[i] + ".html"
        ).replace(" ", ""),
        auto_open=False,
    )
plt.clf()


# endregion

########################################
# ACTUAL VS. PROJECTED ADOPTION CURVES #
########################################

# region

actual = (
    pd.read_csv("podi/data/adoption_curves_PD20.csv")
    .set_index(["Region", "Sector", "Units", "Scenario"])
    .droplevel(["Region", "Units"])
)
actual.columns = actual.columns.astype(int)
actual = actual.loc[:, 2015:2025] * 100
actual.columns.name = "Year"

for i in range(0, 1):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[:, 2015:2025]
        * 100
    )
    fig = pd.concat([fig], keys=["PD21"], names=["Scenario"]).reorder_levels(
        ["Sector", "Scenario"]
    )

    hf = 1 / (
        actual.loc[:, 2018].values / (fig.loc[:, 2018].append(fig.loc[:, 2018]).values)
    )

    actual = actual.multiply(hf, axis=0)

    fig = fig.append(actual)

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name=["Sector", "Scenario"], value_name="% Adoption"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Electricity")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="one",
            legendgroup="Electricity",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Transport")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="two",
            legendgroup="Transport",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Buildings")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="three",
            legendgroup="Buildings",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Industry")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="four",
            legendgroup="Industry",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Regenerative Agriculture",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Regenerative Agriculture")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="five",
            legendgroup="Regenerative Agriculture",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands",
            line=dict(width=3, color="black"),
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] <= 2020)
                & (fig2["Sector"] == "Forests & Wetlands")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="six",
            legendgroup="Forests & Wetlands",
            showlegend=False,
        )
    )

    # PD21

    # region

    fig.add_trace(
        go.Scatter(
            name="Electricity PD21",
            line=dict(width=3, color="#B279A2", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Electricity")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="eight",
            legendgroup="Electricity",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport PD21",
            line=dict(width=3, color="#7AA8B8", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Transport")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="nine",
            legendgroup="Transport",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings PD21",
            line=dict(width=3, color="#F58518", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Buildings")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="ten",
            legendgroup="Buildings",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry PD21",
            line=dict(width=3, color="#60738C", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Industry")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="eleven",
            legendgroup="Industry",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Regenerative Agriculture PD21",
            line=dict(width=3, color="#EECA3B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Regenerative Agriculture")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="twelve",
            legendgroup="Regenerative Agriculture",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands PD21",
            line=dict(width=3, color="#54A24B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2020)
                & (fig2["Sector"] == "Forests & Wetlands")
                & (fig2["Scenario"] == "PD21")
            ]["% Adoption"],
            fill="none",
            stackgroup="thirteen",
            legendgroup="Forests & Wetlands",
        )
    )

    # endregion

    # PD20

    # region

    fig.add_trace(
        go.Scatter(
            name="Electricity PD20",
            line=dict(width=3, color="#B279A2", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Electricity")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="14",
            legendgroup="Electricity",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport PD20",
            line=dict(width=3, color="#7AA8B8", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Transport")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="15",
            legendgroup="Transport",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings PD20",
            line=dict(width=3, color="#F58518", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Buildings")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="16",
            legendgroup="Buildings",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry PD20",
            line=dict(width=3, color="#60738C", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Industry")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="17",
            legendgroup="Industry",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Regenerative Agriculture PD20",
            line=dict(width=3, color="#EECA3B", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Regenerative Agriculture")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="18",
            legendgroup="Regenerative Agriculture",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands PD20",
            line=dict(width=3, color="#54A24B", dash="dashdot"),
            x=fig2[(fig2["Year"] >= 2018) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2018)
                & (fig2["Sector"] == "Forests & Wetlands")
                & (fig2["Scenario"] == "PD20")
            ]["% Adoption"],
            fill="none",
            stackgroup="19",
            legendgroup="Forests & Wetlands",
        )
    )

    # endregion

    # PD17
    """
    # region

    fig.add_trace(
        go.Scatter(
            name="Electricity PD17",
            line=dict(width=3, color="#B279A2", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity") & (fig2["Scenario"] == "PD17")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="20",
            legendgroup="Electricity",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport PD17",
            line=dict(width=3, color="#7AA8B8", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Transport") & (fig2["Scenario"] == "PD17")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="21",
            legendgroup="Transport",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings PD17",
            line=dict(width=3, color="#F58518", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Buildings") & (fig2["Scenario"] == "PD17")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="22",
            legendgroup="Buildings",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Industry PD17",
            line=dict(width=3, color="#60738C", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Industry") & (fig2["Scenario"] == "PD17")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="23",
            legendgroup="Industry",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Regenerative Agriculture PD17",
            line=dict(width=3, color="#EECA3B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[
                (fig2["Year"] >= 2016) & (fig2["Sector"] == "Regenerative Agriculture") & (fig2["Scenario"] == "PD17")
            ]["% Adoption"],
            fill="none",
            stackgroup="24",
            legendgroup="Regenerative Agriculture",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands PD17",
            line=dict(width=3, color="#54A24B", dash="dot"),
            x=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Electricity")]["Year"],
            y=fig2[(fig2["Year"] >= 2016) & (fig2["Sector"] == "Forests & Wetlands") & (fig2["Scenario"] == "PD17")][
                "% Adoption"
            ],
            fill="none",
            stackgroup="25",
            legendgroup="Forests & Wetlands",
        )
    )

    # endregion
    """
    """
    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="black"),
                x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] <= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
                fill="none",
                stackgroup="seven",
                legendgroup="Carbon Dioxide Removal",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="#FF9DA6", dash="dot"),
                x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[
                    (fig2["Year"] >= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
                fill="none",
                stackgroup="fourteen",
                legendgroup="Carbon Dioxide Removal",
            )
        )
    """

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    """
    fig.add_vrect(x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)
    """

    fig.show()

# endregion

##############################
# ADOPTION CURVES STAR CHART #
##############################

# region

# code adapted from Joao Palmeiro, matplotblog

fig_type = "plotly"
year = 2020


def round_up(value):
    return int(ceil(value / 10.0)) * 10


def even_odd_merge(even, odd, filter_none=True):
    if filter_none:
        return filter(None.__ne__, chain.from_iterable(zip_longest(even, odd)))

    return chain.from_iterable(zip_longest(even, odd))


def prepare_angles(N):
    angles = [n / N * 2 * pi for n in range(N)]
    angles += angles[:1]

    return angles


def prepare_data(data):
    labels = [d[0] for d in data]
    values = [d[1] for d in data]
    values += values[:1]
    N = len(labels)
    angles = prepare_angles(N)
    return labels, values, angles, N


def prepare_stellar_aux_data(angles, ymax, N):
    angle_midpoint = pi / N
    stellar_angles = [angle + angle_midpoint for angle in angles[:-1]]
    stellar_values = [0.05 * ymax] * N
    return stellar_angles, stellar_values


def draw_peripherals(ax, labels, angles, ymax, outer_color, inner_color):
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=outer_color, size=8)
    ax.set_yticks(range(10, ymax, 10))
    ax.set_yticklabels(range(10, ymax, 10), color=inner_color, size=7)
    ax.set_ylim(0, ymax)
    ax.set_rlabel_position(0)
    ax.set_axisbelow(True)
    ax.spines["polar"].set_color(outer_color)
    ax.xaxis.grid(True, color=inner_color, linestyle="-")
    ax.yaxis.grid(True, color=inner_color, linestyle="-")


def draw_stellar(
    ax,
    labels,
    values,
    angles,
    N,
    shape_color="tab:blue",
    outer_color="slategrey",
    inner_color="lightgrey",
):

    ymax = round_up(max(values))
    stellar_angles, stellar_values = prepare_stellar_aux_data(angles, ymax, N)
    all_angles = list(even_odd_merge(angles, stellar_angles))
    all_values = list(even_odd_merge(values, stellar_values))
    draw_peripherals(ax, labels, angles, ymax, outer_color, inner_color)
    ax.plot(
        all_angles,
        all_values,
        linewidth=1,
        linestyle="solid",
        solid_joinstyle="round",
        color=shape_color,
    )

    ax.fill(all_angles, all_values, shape_color)
    ax.plot(0, 0, marker="o", color="white", markersize=3)


for i in range(0, len(region_list)):
    fig = adoption_curves.loc[region_list[i], slice(None), scenario] * 100

    data = [
        ("Electricity", fig.loc["Electricity", year]),
        ("Industry", fig.loc["Industry", year]),
        ("Buildings", fig.loc["Buildings", year]),
        ("Transport", fig.loc["Transport", year]),
        (
            "Regenerative Agriculture",
            fig.loc["Regenerative Agriculture", year],
        ),
        ("Forests & Wetlands", fig.loc["Forests & Wetlands", year]),
        (
            "Carbon Dioxide Removal",
            fig.loc["Carbon Dioxide Removal", year],
        ),
    ]

    fig = plt.figure(dpi=100)
    ax = fig.add_subplot(111, polar=True)
    draw_stellar(ax, *prepare_data(data))
    plt.title(
        "V7 Adoption, "
        + region_list[i].replace(" ", "")
        + ", "
        + str(data_end_year)
    )
    plt.show()

    # Plotly version
    if fig_type == "plotly":
        categories = [
            "Grid",
            "Transport",
            "Buildings",
            "Industry",
            "Regenerative Agriculture",
            "Forests & Wetlands",
            "Carbon Dioxide Removal",
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 0, 50], theta=categories, fill="toself", name="A"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="B"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="C"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="D"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="E"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="F"
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[0, 0, 0, 0, 0, 30, 0], theta=categories, fill="toself", name="G"
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
        )

        fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=("./charts/star-" + region_list[i] + ".html").replace(" ", ""),
                auto_open=False,
            )

# endregion

##############################
# ADOPTION CURVES KNEE/ELBOW #
##############################

# region

for i in range(0, len(region_list)):
    fig = adoption_curves.loc[region_list[i], slice(None), scenario] * 100
    kneedle = KneeLocator(
        fig.columns.values,
        fig.loc["Electricity"].values,
        S=1.0,
        curve="concave",
        direction="increasing",
    )

# endregion

########################################################
# REGENERATIVE AGRICULTURE SUBVECTOR MITIGATION WEDGES #
########################################################

# region

# region

color = (
    (0.999, 0.999, 0.999),
    (0.584, 0.804, 0.756),
    (0.526, 0.724, 0.680),
    (0.473, 0.651, 0.612),
    (0.426, 0.586, 0.551),
    (0.356, 0.356, 0.356),
    (0.720, 0.348, 0.324),
    (0.840, 0.688, 0.680),
    (0.804, 0.852, 0.704),
    (0.736, 0.708, 0.796),
    (0.712, 0.168, 0.136),
    (0.384, 0.664, 0.600),
)

# endregion

# region

custom_legend = [
    Line2D([0], [0], color=color[1], linewidth=4),
    Line2D([0], [0], color=color[2], linewidth=4),
    Line2D([0], [0], color=color[3], linewidth=4),
    Line2D([0], [0], color=color[4], linewidth=4),
    Line2D([0], [0], color=color[5], linewidth=4),
    Line2D([0], [0], color=color[6], linewidth=4),
    Line2D([0], [0], color=color[7], linewidth=4),
    Line2D([0], [0], color=color[8], linewidth=4),
    Line2D([0], [0], color=color[9], linewidth=4),
    Line2D([0], [0], color=color[10], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
    Line2D([0], [0], color=color[11], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
]

# endregion

for i in range(0, len(region_list)):
    em_mit = (
        (
            em_mitigated.loc[
                region_list[i],
                [
                    "Animal Mgmt",
                    "Legumes",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Biochar",
                    "Cropland Soil Health",
                    "Trees in Croplands",
                    "Nitrogen Fertilizer Management",
                    "Improved Rice",
                ],
                slice(None),
                slice(None),
            ]
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_targets_pathway = (
        pd.read_csv()
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            ["Agriculture Net Emissions", "Agriculture baseline Emissions"],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    em_mit.loc["Improved Rice"] = em_targets_pathway.loc[
        "World ", "Agriculture baseline Emissions"
    ].subtract(
        em_mit.drop(labels="Improved Rice")
        .append(spacer.drop(index="Agriculture baseline Emissions"))
        .sum()
    )

    em_mit.loc[:, :2020] = 0

    fig = (
        (em_mit.append(spacer.drop(index="Agriculture baseline Emissions"))) / 1000
    ).reindex(
        [
            spacer.index[1],
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Biochar",
            "Cropland Soil Health",
            "Trees in Croplands",
            "Nitrogen Fertilizer Management",
            "Improved Rice",
        ]
    )
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig,
        labels=fig.index,
        colors=color,
    )
    plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
    plt.legend(
        loc=2,
        fontsize="small",
    )
    plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
    plt.ylabel("GtCO2e/yr")
    plt.xlim([2020, 2100])
    plt.grid(which="major", linestyle=":", axis="y")
    plt.legend(
        custom_legend,
        [
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Biochar",
            "Cropland Soil Health",
            "Trees in Croplands",
            "Nitrogen Fertilizer Management",
            "Improved Rice",
            "Agriculture baseline Emissions",
            "Agriculture Net Emissions",
        ],
        bbox_to_anchor=(1.05, 1),
        loc=2,
        borderaxespad=0.0,
    )
    plt.xticks(np.arange(2020, 2110, 10))
    plt.yticks(np.arange(-3, 9, 1))
    plt.title(
        "Regenerative Agriculture Subvector Mitigation Wedges, " + region_list[i]
    )
    plt.show()
    plt.clf()

# endregion

##################################################
# FORESTS & WETLANDS SUBVECTOR MITIGATION WEDGES #
##################################################

# region

# region

color = (
    (0.999, 0.999, 0.999),
    (0.156, 0.472, 0.744),
    (0.804, 0.868, 0.956),
    (0.152, 0.152, 0.152),
    (0.780, 0.756, 0.620),
    (0.776, 0.504, 0.280),
    (0.320, 0.560, 0.640),
    (0.404, 0.332, 0.520),
    (0.676, 0.144, 0.112),
    (0.384, 0.664, 0.600),
)

custom_legend = [
    Line2D([0], [0], color=color[1], linewidth=4),
    Line2D([0], [0], color=color[2], linewidth=4),
    Line2D([0], [0], color=color[3], linewidth=4),
    Line2D([0], [0], color=color[4], linewidth=4),
    Line2D([0], [0], color=color[5], linewidth=4),
    Line2D([0], [0], color=color[6], linewidth=4),
    Line2D([0], [0], color=color[7], linewidth=4),
    Line2D([0], [0], color=color[8], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
    Line2D([0], [0], color=color[9], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
]

# endregion

for i in range(0, len(region_list)):
    em_mit = (
        (
            em_mitigated.loc[
                [" OECD ", "NonOECD "],
                [
                    "Coastal Restoration",
                    "Avoided Coastal Impacts",
                    "Peat Restoration",
                    "Avoided Peat Impacts",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Avoided Forest Conversion",
                ],
                slice(None),
                slice(None),
            ]
            * 0.95
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_mit.loc[:, :2020] = 0

    em_targets_pathway = (
        pd.read_csv()
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            [
                "Forests & Wetlands Net Emissions",
                "Forests & Wetlands baseline Emissions",
            ],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    fig = (
        (em_mit.append(spacer.drop(index="Forests & Wetlands baseline Emissions")))
        / 1000
    ).reindex(
        [
            spacer.index[1],
            "Coastal Restoration",
            "Avoided Coastal Impacts",
            "Peat Restoration",
            "Avoided Peat Impacts",
            "Improved Forest Mgmt",
            "Natural Regeneration",
            "Avoided Forest Conversion",
        ]
    )
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig,
        labels=fig.index,
        colors=color,
    )
    plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
    plt.legend(
        loc=2,
        fontsize="small",
    )
    plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
    plt.ylabel("GtCO2e/yr")
    plt.xlim([2020, 2100])
    plt.grid(which="major", linestyle=":", axis="y")
    plt.legend(
        custom_legend,
        [
            "Coastal Restoration",
            "Avoided Coastal Impacts",
            "Peat Restoration",
            "Avoided Peat Impacts",
            "Forest Management",
            "Reforestation",
            "Avoided Forest Conversion",
            "Forests & Wetlands baseline Emissions",
            "Forests & Wetlands Net Emissions",
        ],
        bbox_to_anchor=(1.05, 1),
        loc=2,
        borderaxespad=0.0,
    )
    plt.xticks(np.arange(2020, 2110, 10))
    plt.title("Forests & Wetlands Subvector Mitigation Wedges, " + region_list[i])
    plt.savefig(
        fname=("podi/data/figs/fw_pathway-" + region_list[i]).replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

#####################################
# AFOLU SUBVECTOR MITIGATION WEDGES #
#####################################

# region

# region

color = (
    (0.999, 0.999, 0.999),
    (0.156, 0.472, 0.744),
    (0.804, 0.868, 0.956),
    (0.152, 0.152, 0.152),
    (0.780, 0.756, 0.620),
    (0.776, 0.504, 0.280),
    (0.320, 0.560, 0.640),
    (0.404, 0.332, 0.520),
    (0.356, 0.356, 0.356),
    (0.584, 0.804, 0.756),
    (0.526, 0.724, 0.680),
    (0.473, 0.651, 0.612),
    (0.426, 0.586, 0.551),
    (0.720, 0.348, 0.324),
    (0.840, 0.688, 0.680),
    (0.804, 0.852, 0.704),
    (0.736, 0.708, 0.796),
    (0.704, 0.168, 0.120),
    (0.384, 0.664, 0.600),
)

custom_legend = [
    Line2D([0], [0], color=color[1], linewidth=4),
    Line2D([0], [0], color=color[2], linewidth=4),
    Line2D([0], [0], color=color[3], linewidth=4),
    Line2D([0], [0], color=color[4], linewidth=4),
    Line2D([0], [0], color=color[5], linewidth=4),
    Line2D([0], [0], color=color[6], linewidth=4),
    Line2D([0], [0], color=color[7], linewidth=4),
    Line2D([0], [0], color=color[8], linewidth=4),
    Line2D([0], [0], color=color[9], linewidth=4),
    Line2D([0], [0], color=color[10], linewidth=4),
    Line2D([0], [0], color=color[11], linewidth=4),
    Line2D([0], [0], color=color[12], linewidth=4),
    Line2D([0], [0], color=color[13], linewidth=4),
    Line2D([0], [0], color=color[14], linewidth=4),
    Line2D([0], [0], color=color[15], linewidth=4),
    Line2D([0], [0], color=color[16], linewidth=4),
    Line2D([0], [0], color=color[17], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
    Line2D([0], [0], color=color[18], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)),
]

# endregion

for i in range(0, len(region_list)):
    em_mit = (
        (
            em_mitigated.loc[
                [" OECD ", "NonOECD "],
                [
                    "Coastal Restoration",
                    "Avoided Coastal Impacts",
                    "Peat Restoration",
                    "Avoided Peat Impacts",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Avoided Forest Conversion",
                    "Animal Mgmt",
                    "Legumes",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Biochar",
                    "Cropland Soil Health",
                    "Trees in Croplands",
                    "Nitrogen Fertilizer Management",
                    "Improved Rice",
                ],
                slice(None),
                slice(None),
            ]
            * 0.95
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_mit.loc[:, :2020] = 0

    em_targets_pathway = (
        pd.read_csv()
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            [
                "AFOLU Net Emissions",
                "AFOLU baseline Emissions",
            ],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    fig = (
        (em_mit.append(spacer.drop(index="AFOLU baseline Emissions"))) / 1000
    ).reindex(
        [
            spacer.index[1],
            "Coastal Restoration",
            "Avoided Coastal Impacts",
            "Peat Restoration",
            "Avoided Peat Impacts",
            "Improved Forest Mgmt",
            "Natural Regeneration",
            "Avoided Forest Conversion",
            "Biochar",
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Cropland Soil Health",
            "Trees in Croplands",
            "Nitrogen Fertilizer Management",
            "Improved Rice",
        ]
    )
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig,
        labels=fig.index,
        colors=color,
    )
    plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
    plt.legend(
        loc=2,
        fontsize="small",
    )
    plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
    plt.ylabel("GtCO2e/yr")
    plt.xlim([2020, 2100])
    plt.grid(which="major", linestyle=":", axis="y")
    plt.legend(
        custom_legend,
        [
            "Coastal Restoration",
            "Avoided Coastal Impacts",
            "Peat Restoration",
            "Avoided Peat Impacts",
            "Forest Management",
            "Reforestation",
            "Avoided Forest Conversion",
            "Biochar",
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
            "Cropland Soil Health",
            "Trees in Croplands",
            "Nitrogen Fertilizer Management",
            "Improved Rice",
            "AFOLU baseline Emissions",
            "AFOLU Net Emissions",
        ],
        bbox_to_anchor=(1.05, 1),
        loc=2,
        borderaxespad=0.0,
    )
    plt.xticks(np.arange(2020, 2110, 10))
    plt.yticks(np.arange(-17, 10, 5))
    plt.title("AFOLU Subvector Mitigation Wedges, " + region_list[i])
    plt.show()
    plt.clf()

    # endregion

##############################
# AFOLU ADOPTION CURVE CHECK #
##############################

# region

for i in range(0, len(afolu_per_adoption_baseline)):
    fig1 = afolu_per_adoption_baseline.iloc[i].dropna() * 100
    fig2 = afolu_per_adoption_baseline.iloc[i] * 100

    fig1.index.name = "Year"
    fig2.index.name = "Year"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name=fig1.name[0],
            line=dict(width=3, color="black"),
            x=fig1.index.values,
            y=fig1.values,
            fill="none",
            stackgroup="one",
            legendgroup="one",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="PD Projection",
            line=dict(width=2, color="red", dash="dot"),
            x=fig2.index.values,
            y=fig2.values,
            fill="none",
            stackgroup="two",
            legendgroup="two",
            showlegend=True,
        )
    )

    fig.update_layout(
        title={
            "text": "Logistic Curve Fit, " + fig1.name[0],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.show()

# endregion

##############################
# ANNUAL CO2 REMOVED VIA CDR #
##############################

# region

color = (
    (0.804, 0.868, 0.956),
    (0.404, 0.332, 0.520),
    (0.156, 0.472, 0.744),
)

custom_legend = [
    Line2D([0], [0], color=color[0], linewidth=4),
    Line2D([0], [0], color=color[1], linewidth=4),
    Line2D([0], [0], color=color[2], linewidth=4),
]

for i in range(0, len(region_list)):
    fig = cdr_pathway / 1000
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig,
        labels=fig.index,
        colors=color,
    )
    plt.ylabel("GtCO2e/yr")
    plt.xlim([2020, 2100])
    plt.legend(
        custom_legend,
        [
            "ExSitu Enhanced Weathering",
            "Low-Temp Solid Sorbent DAC",
            "High-temp Liquid Sorbent DAC",
        ],
        bbox_to_anchor=(1.05, 1),
        fontsize="small",
        loc=2,
        borderaxespad=0.0,
    )
    plt.xticks(np.arange(2020, 2110, 10))
    plt.title("CO2 Removed via CDR, " + region_list[i])
    plt.savefig(
        fname=("podi/data/figs/cdr_pathway-" + region_list[i]).replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

################################
# ENERGY INTENSITY PROJECTIONS #
################################

# region
# https://github.com/iiasa/ipcc_sr15_scenario_analysis/blob/master/further_analysis/iamc15_energy_intensity.ipynb

# endregion

###############################
# ECONOMIC GROWTH PROJECTIONS #
###############################

# region
# https://github.com/iiasa/ipcc_sr15_scenario_analysis/blob/master/further_analysis/iamc15_gdp_per_capita.ipynb
# endregion

##############################
# ELECTRICITY PERCENT ADOPTION
##############################

# region

scenario = scenario
start_year = start_year

for i in range(0, len(region_list)):
    fig = elec_per_adoption.loc[region_list[i], slice(None), scenario]
    plt.figure(i)
    plt.plot(fig.T)
    plt.legend(fig.T)
    plt.title(region_list[i])
    elec_per_adoption.loc[region_list[i], slice(None), scenario].loc[:, 2019]

# endregion

#######################
# HEAT PERCENT ADOPTION
#######################

# region
scenario = scenario

for i in range(0, len(region_list)):
    plt.figure(i)
    plt.plot(heat_per_adoption.loc[region_list[i], slice(None), scenario].T)
    plt.legend(heat_per_adoption.loc[region_list[i], slice(None), scenario].T)
    plt.title(region_list[i])

# endregion

####################################
# NONELEC TRANSPORT PERCENT ADOPTION
####################################

# region
scenario = scenario

for i in range(0, len(region_list)):
    plt.figure(i)
    plt.plot(transport_per_adoption.loc[region_list[i], slice(None), scenario].T)
    plt.legend(transport_per_adoption.loc[region_list[i], slice(None), scenario].T)
    plt.title(region_list[i])

# endregion
