# region

import matplotlib.pyplot as plt
import numpy as np
from numpy.random import random_integers
import pandas as pd
from matplotlib.lines import Line2D
from scipy import interpolate
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
from numpy import NaN, triu_indices_from
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
scenario = "pathway"

# endregion

###################
# ADOPTION CURVES #
###################

# region

scenario = scenario
start_year = start_year
i = 0

for i in range(0, len(region_list)):

    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[:, start_year:]
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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )
        """
        else:
            fig.add_trace(
            go.Scatter(
                name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
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
        """

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, "
            + scenario.title()
            + ", "
            + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[:, start_year:]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    fig = make_subplots(
        rows=2,
        cols=4,
        start_cell="top-left",
        subplot_titles=(
            "Electricity",
            "Transport",
            "Buildings",
            "Industry",
            "Regenerative Agriculture",
            "Forests & Wetlands",
            "CDR",
        ),
    )
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
        ),
        row=1,
        col=1,
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
        ),
        row=1,
        col=2,
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
        ),
        row=1,
        col=3,
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
        ),
        row=1,
        col=4,
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
        ),
        row=2,
        col=1,
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
        ),
        row=2,
        col=2,
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
        ),
        row=1,
        col=1,
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
        ),
        row=1,
        col=2,
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
        ),
        row=1,
        col=3,
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
        ),
        row=1,
        col=4,
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
        ),
        row=2,
        col=1,
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
        ),
        row=2,
        col=2,
    )

    if region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="black"),
                x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Transport")][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="seven",
                legendgroup="Carbon Dioxide Removal",
                showlegend=False,
            ),
            row=2,
            col=3,
        )

        fig.add_trace(
            go.Scatter(
                name="Carbon Dioxide Removal",
                line=dict(width=3, color="#FF9DA6", dash="dot"),
                x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                    "Year"
                ],
                y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Transport")][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="fourteen",
                legendgroup="Carbon Dioxide Removal",
            ),
            row=2,
            col=3,
        )

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, "
            + scenario.title()
            + ", "
            + region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        showlegend=False,
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
i = 0

colors = px.colors.qualitative.Vivid

for i in range(0, len(region_list)):

    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[:, start_year:]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig3 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    for sector in [
        "Electricity",
        "Transport",
        "Buildings",
        "Industry",
        "Regenerative Agriculture",
        "Forests & Wetlands",
    ]:

        fig = (
            sadoption_curves.loc[region_list[i], sector, slice(None), scenario, :].loc[
                :, start_year:
            ]
            * 100
        )

        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="% Adoption")

        fig = go.Figure()

        for x in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=x,
                    line=dict(
                        width=0,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(x)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == x]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=x,
                )
            )

        fig.add_trace(
            go.Scatter(
                name=sector,
                line=dict(width=3, color="black"),
                x=fig2[fig2["Year"] <= 2020]["Year"],
                y=fig3[(fig3["Year"] <= 2020) & (fig3["Sector"] == sector)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="three",
                legendgroup=sector,
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name=sector,
                line=dict(width=3, color="#7AA8B8", dash="dot"),
                x=fig2[fig2["Year"] >= 2020]["Year"],
                y=fig3[(fig3["Year"] >= 2020) & (fig3["Sector"] == sector)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="four",
                legendgroup=sector,
                showlegend=True,
            )
        )

        fig.update_layout(
            title={
                "text": "Percent of Total PD Adoption, "
                + scenario.title()
                + ", "
                + sector
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"},
            legend={"traceorder": "reversed"},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)
            ),
            margin_t=120,
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

        fig.add_vrect(
            x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0
        )

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/scurvessub-"
                    + region_list[i]
                    + "-"
                    + sector
                    + "-"
                    + scenario
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

# endregion

#############################
# ADOPTION CURVES BY REGION #
#############################

# region

scenario = scenario
start_year = start_year
i = 0

data = []
sector = "Regenerative Agriculture"

for i in range(0, len(region_list)):

    fig = (
        adoption_curves.loc[region_list[i], sector, scenario].loc[:, start_year:] * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    data = pd.DataFrame(data).append(fig2)

fig2 = data
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == sector)]["Year"],
        y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == sector)]["% Adoption"],
        fill="none",
        stackgroup="one",
        legendgroup="Electricity",
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        name="V1: Electricity",
        line=dict(width=3, color="#B279A2", dash="dot"),
        x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == sector)]["Year"],
        y=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == sector)]["% Adoption"],
        fill="none",
        stackgroup="eight",
        legendgroup="Electricity",
    )
)

fig.update_layout(
    title={
        "text": "Percent of Total PD Adoption, " + scenario.title() + ", " + sector,
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "% Adoption"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=100,
)

fig.add_annotation(
    text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
    xref="paper",
    yref="paper",
    x=-0.12,
    y=-0.36,
    showarrow=False,
    font=dict(size=10, color="#2E3F5C"),
    align="left",
    borderpad=4,
    bgcolor="#ffffff",
    opacity=1,
)

if show_figs is True:
    fig.show()

# endregion

###############################################
# ADOPTION CURVES BY REGION SNAPSHOT BARCHART #
###############################################

# region

scenario = scenario
start_year = start_year
i = 0

data = []
sector = "Regenerative Agriculture"

for i in range(0, len(region_list)):

    fig = (
        adoption_curves.loc[region_list[i], sector, scenario].loc[:, start_year:] * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    data = pd.DataFrame(data).append(fig2)


figure = go.Figure(
    data=[
        go.Bar(
            name="V6: Forests & Wetlands",
            x=data["labels"],
            y=data["V6: Forests & Wetlands"],
            offsetgroup=0,
            orientation="v",
            marker_color="#54A24B",
            opacity=0.5,
        ),
        go.Bar(
            name="V5: Agriculture",
            x=data["labels"],
            y=data["V5: Agriculture"],
            offsetgroup=0,
            orientation="v",
            marker_color="#EECA3B",
            opacity=0.5,
        ),
    ]
)

figure.add_trace(
    go.Scatter(
        mode="markers",
        name="Emissions gap, after energy sector mitigation",
        x=data["labels"],
        y=data["spacer"],
        fill="none",
    )
)

figure.add_trace(
    go.Scatter(
        mode="markers",
        opacity=0,
        name="Emissions gap, after energy sector mitigation",
        x=data["labels"],
        y=-data["spacer"],
        fill="none",
        showlegend=False,
    )
)

figure.update_layout(
    title="Vector Adoption in " + str(year),
    title_x=0.5,
    title_y=0.99,
    yaxis={"title": "GtCO2e"},
    barmode="stack",
    showlegend=True,
    legend=dict(
        orientation="h",
        x=0.2,
        y=1.25,
        bgcolor="rgba(255, 255, 255, 0)",
        bordercolor="rgba(255, 255, 255, 0)",
    ),
    xaxis={"categoryorder": "total descending"},
)

figure.update_yaxes(range=[0, 35])

if show_figs is True:
    figure.show()

# endregion

#######################################
# SUBVECTOR ADOPTION CURVES UNSTACKED #
#######################################

# region

scenario = scenario
start_year = start_year
i = 0

colors = px.colors.qualitative.Vivid

for i in range(0, len(region_list)):
    fig = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[:, start_year:]
        * 100
    )

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig3 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="% Adoption")

    for sector in [
        "Electricity",
        "Transport",
        "Buildings",
        "Industry",
        "Regenerative Agriculture",
        "Forests & Wetlands",
    ]:

        fig = (
            sadoption_curves.loc[region_list[i], sector, slice(None), scenario, :].loc[
                :, start_year:
            ]
            * 100
        )

        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="% Adoption")

        fig = go.Figure()

        for x in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=x,
                    line=dict(
                        width=3,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(x)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == x]["% Adoption"],
                    fill="none",
                    stackgroup=x,
                    legendgroup=x,
                )
            )

        fig.add_trace(
            go.Scatter(
                name=sector,
                line=dict(width=3, color="black"),
                x=fig2[fig2["Year"] <= 2020]["Year"],
                y=fig3[(fig3["Year"] <= 2020) & (fig3["Sector"] == sector)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="2",
                legendgroup="2",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name=sector,
                line=dict(width=3, color="#7AA8B8", dash="dot"),
                x=fig2[fig2["Year"] >= 2020]["Year"],
                y=fig3[(fig3["Year"] >= 2020) & (fig3["Sector"] == sector)][
                    "% Adoption"
                ],
                fill="none",
                stackgroup="none",
                legendgroup="2",
                showlegend=True,
            )
        )

        fig.update_layout(
            title={
                "text": "Percent of Total PD Adoption, "
                + scenario.title()
                + ", "
                + sector
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"},
            legend={"traceorder": "reversed"},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)
            ),
            margin_b=100,
        )

        fig.add_annotation(
            text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture and Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available",
            xref="paper",
            yref="paper",
            x=-0.12,
            y=-0.38,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_vrect(
            x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0
        )

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/scurvessub-"
                    + region_list[i]
                    + "-"
                    + sector
                    + "-"
                    + scenario
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

# endregion

#################################################
# AFOLU SUBVECTOR ADOPTION CURVES AS MAX EXTENT #
#################################################

# region

scenario = scenario
start_year = start_year
i = 0

colors = px.colors.qualitative.Vivid

max_extent_units = {
    "Biochar": "Tgdm/yr",
    "Coastal Restoration": "Mha",
    "Cropland Soil Health": "Mha",
    "Improved Forest Mgmt": "m^3",
    "Improved Rice": "Mha",
    "Natural Regeneration": "Mha",
    "Nitrogen Fertilizer Management": "Mha",
    "Optimal Intensity": "Mha",
    "Peat Restoration": "Mha",
    "Silvopasture": "Mha",
    "Trees in Croplands": "Mha",
    "Avoided Forest Conversion": "Mha",
    "Avoided Coastal Impacts": "Mha",
    "Avoided Peat Impacts": "Mha",
}

for i in range(0, len(region_list)):

    fig = afolu_per_max.loc[region_list[i], slice(None), slice(None), scenario].loc[
        :, start_year:
    ]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig3 = pd.melt(fig, id_vars="Year", var_name="Sector", value_name="Adoption")

    for sector in [
        "Regenerative Agriculture",
        "Forests & Wetlands",
    ]:

        fig = afolu_per_max.loc[region_list[i], sector, slice(None), scenario, :].loc[
            :, start_year:
        ]

        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="Adoption")

        for x in fig2["Metric"].unique():
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    name=x,
                    line=dict(
                        width=0,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(x)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == x]["Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=x,
                )
            )

            """
            fig.add_trace(
                go.Scatter(
                    name=sector,
                    line=dict(width=3, color="black"),
                    x=fig2[fig2["Year"] <= 2020]["Year"],
                    y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == sector)][
                        "Adoption"
                    ],
                    fill="none",
                    stackgroup="three",
                    legendgroup=sector,
                    showlegend=False,
                )
            )


            fig.add_trace(
                go.Scatter(
                    name=sector,
                    line=dict(width=3, color="#7AA8B8", dash="dot"),
                    x=fig2[fig2["Year"] >= 2020]["Year"],
                    y=fig3[(fig3["Year"] >= 2020) & (fig3["Sector"] == sector)][
                        "Adoption"
                    ],
                    fill="none",
                    stackgroup="four",
                    legendgroup=sector,
                    showlegend=True,
                )
            )
            """

            fig.update_layout(
                title={
                    "text": "Total PD Adoption, "
                    + scenario.title()
                    + ", "
                    + sector
                    + ", "
                    + x
                    + ", "
                    + region_list[i],
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                xaxis={"title": "Year"},
                yaxis={"title": max_extent_units[x]},
                legend={"traceorder": "reversed"},
            )

            fig.update_layout(
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)
                ),
                margin_t=120,
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

            fig.add_vrect(
                x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0
            )

            if show_figs is True:
                fig.show()
            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/scurvessubafolu-"
                        + region_list[i]
                        + "-"
                        + sector
                        + "-"
                        + scenario
                        + "-"
                        + x
                        + ".html"
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
        energy_demand.loc[region_list[i], slice(None), slice(None), scenario] * unit[1]
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
            "text": "Energy Demand, "
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
        elec_consump.loc[region_list[i], slice(None), scenario].groupby("Metric").sum()
    )
    elec_consump_i = pd.concat([elec_consump_i], keys=["Electricity"], names=["Sector"])
    heat_consump_i = (
        heat_consump.loc[region_list[i], slice(None), scenario].groupby("Metric").sum()
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
        elec_consump.loc[region_list[i], slice(None), scenario].groupby("Metric").sum()
    )
    elec_consump_i = pd.concat([elec_consump_i], keys=["Electricity"], names=["Sector"])
    heat_consump_i = (
        heat_consump.loc[region_list[i], slice(None), scenario].groupby("Metric").sum()
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
                "./charts/supply2-" + scenario + "-" + region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

#############
# EMISSIONS #
#############

# region

scenario = scenario
start_year = 2000
i = 0

for i in range(0, len(region_list)):

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc["World ", ["Carbon Dioxide Removal"], scenario, :]
        em_cdr = pd.concat(
            [pd.concat([em_cdr], names=["Gas"], keys=["CO2"])],
            names=["Metric"],
            keys=["Carbon Dioxide Removal"],
        ).reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    else:
        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    fig = ((em2.groupby("Sector").sum()) / 1000).loc[:, start_year:]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

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

    if em_fw.loc[:, 2000].values[0] < 0:
        histfill = "tozeroy"
        stackgroup = "hist"
    else:
        histfill = "tozeroy"
        stackgroup = "hist"

    fig.add_trace(
        go.Scatter(
            name="Historical Net Emissions",
            line=dict(width=2, color="black"),
            x=pd.Series(
                em.loc[region_list[i], slice(None), slice(None), slice(None), scenario]
                .loc[:, start_year:data_end_year]
                .columns.values
            ),
            y=pd.Series(
                em.loc[region_list[i], slice(None), slice(None), slice(None), scenario]
                .loc[:, start_year:data_end_year]
                .sum()
            )
            / 1000,
            fill=histfill,
            stackgroup=stackgroup,
        )
    )

    fig.update_layout(
        title={
            "text": "Emissions, " + scenario.title() + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10)),
        margin_b=90,
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.31,
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
            file=("./charts/em2-" + scenario + "-" + region_list[i] + ".html").replace(
                " ", ""
            ),
            auto_open=False,
        )
    plt.clf()

# endregion

########################
# EMISSIONS SUBVECTORS #
########################

# region

scenario = scenario
start_year = 2000

colors = [
    "#AA0DFE",
    "#3283FE",
    "#85660D",
    "#565656",
    "#1C8356",
    "#16FF32",
    "#F7E1A0",
    "#C4451C",
    "#325A9B",
    "#FEAF16",
    "#F8A19F",
    "#90AD1C",
    "#F6222E",
    "#1CFFCE",
    "#2ED9FF",
    "#B10DA1",
    "#C075A6",
    "#FC1CBF",
    "#B00068",
    "#FBE426",
    "#FA0087",
    "#FD3216",
    "#00FE35",
    "#6A76FC",
    "#FED4C4",
    "#FE00CE",
    "#0DF9FF",
    "#F6F926",
    "#FF9616",
    "#479B55",
    "#EEA6FB",
    "#DC587D",
    "#D626FF",
    "#6E899C",
    "#00B5F7",
    "#B68E00",
    "#C9FBE5",
    "#FF0092",
    "#22FFA7",
    "#E3EE9E",
    "#86CE00",
    "#BC7196",
    "#7E7DCD",
    "#FC6955",
    "#E48F72",
]
i = 0

for i in range(0, len(region_list)):

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    em2 = (
        em_electricity.append(em_transport)
        .append(em_buildings)
        .append(em_industry)
        .append(em_ra)
        .append(em_fw)
    )

    for sector in pd.Series(em2.index.get_level_values(1).unique()):
        fig = (
            (
                em2.loc[region_list[i], sector, slice(None), slice(None), scenario]
                .groupby(["Metric"])
                .sum()
            )
            / 1000
        ).loc[:, start_year:]
        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e"
        )

        if sector == "Industry":
            fig3 = fig2[fig2["Metric"] == "Fossil Fuel Heat"]
            fig2 = fig3.append(fig2[fig2["Metric"] != "Fossil Fuel Heat"])

        if sector == "Regenerative Agriculture":
            fig3 = fig2[
                (fig2["Metric"] != "Cropland Soil Health")
                & (fig2["Metric"] != "Trees in Croplands")
                & (fig2["Metric"] != "Silvopasture")
                & (fig2["Metric"] != "Optimal Intensity")
                & (fig2["Metric"] != "Improved Rice")
                & (fig2["Metric"] != "Biochar")
                & (fig2["Metric"] != "Nitrogen Fertilizer Management")
            ]

            fig4 = fig2[
                (fig2["Metric"] == "Cropland Soil Health")
                | (fig2["Metric"] == "Trees in Croplands")
                | (fig2["Metric"] == "Silvopasture")
                | (fig2["Metric"] == "Optimal Intensity")
                | (fig2["Metric"] == "Improved Rice")
                | (fig2["Metric"] == "Biochar")
                | (fig2["Metric"] == "Nitrogen Fertilizer Management")
            ]

            fig2 = fig3.append(fig4)

        if sector == "Forests & Wetlands":
            fig3 = fig2[fig2["Metric"] == "Deforestation"]

            fig4 = fig2[fig2["Metric"] != "Deforestation"]

            fig2 = fig3.append(fig4)

        fig = go.Figure()

        for sub in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(sub)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == sub]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": " Emissions in "
                + str(sector)
                + ", "
                + scenario.title()
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            showlegend=True,
        )

        fig.add_annotation(
            text="Historical data is from Global Carbon Project and Community Emissions Data System; projections are based on PD21 technology adoption rate assumptions<br>applied to IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model for 2040-2100.",
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
                    "./charts/emsub-"
                    + scenario
                    + "-"
                    + region_list[i]
                    + "-"
                    + str(sector)
                    + ".html"
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
i = 0

colors = px.colors.qualitative.Safe

for i in range(0, len(region_list)):

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    """
    em_industry.loc[region_list[i], 'Industry', 'Fossil fuels', slice(None), scenario] = em_industry.loc[slice(None), slice(None), ['Fossil fuels', 'Cement'],:].sum()

    em_industry = em_industry.loc[region_list[i], 'Industry', ['Fossil fuels', 'CH4', 'N2O', 'F-gases']]
    """

    em_ra = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc["World ", ["Carbon Dioxide Removal"], scenario, :]
        em_cdr = pd.concat(
            [pd.concat([em_cdr], names=["Gas"], keys=["CO2"])],
            names=["Metric"],
            keys=["Carbon Dioxide Removal"],
        ).reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    else:
        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    for sector in pd.Series(em2.index.get_level_values(1).unique()):

        fig = ((em2.loc[slice(None), sector, :].groupby("Gas").sum()) / 1000).loc[
            :, start_year:
        ]
        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e"
        )

        fig = go.Figure()

        for gas in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=gas,
                    line=dict(
                        width=0.5,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(gas)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == gas]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Emissions by Type in "
                + str(sector)
                + ", "
                + scenario.title()
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            showlegend=True,
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
                    "./charts/em3-"
                    + scenario
                    + "-"
                    + region_list[i]
                    + "-"
                    + str(sector)
                    + ".html"
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
i = 0

colors = px.colors.qualitative.Safe

for i in range(0, len(region_list)):

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    if region_list[i] == "World ":
        em_cdr = -cdr.loc["World ", ["Carbon Dioxide Removal"], scenario, :]
        em_cdr = pd.concat(
            [pd.concat([em_cdr], names=["Gas"], keys=["CO2"])],
            names=["Metric"],
            keys=["Carbon Dioxide Removal"],
        ).reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    else:
        em2 = (
            em_electricity.append(em_transport)
            .append(em_buildings)
            .append(em_industry)
            .append(em_ra)
            .append(em_fw)
        )

    for gas in em2.index.get_level_values(3).unique():

        fig = (
            (
                em2.loc[region_list[i], slice(None), slice(None), gas, scenario, :]
                .groupby("Sector")
                .sum()
            )
            / 1000
        ).loc[:, start_year:]
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
                    line=dict(
                        width=0.5,
                        color=colors[
                            pd.DataFrame(em2.index.get_level_values(1).unique())
                            .set_index("Sector")
                            .index.get_loc(j)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == j]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": str(gas)
                + " Emissions by Sector, "
                + scenario.title()
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            showlegend=True,
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
                    "./charts/em4-"
                    + scenario
                    + "-"
                    + region_list[i]
                    + "-"
                    + str(gas)
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )
        plt.clf()

# endregion

###########################################
# EMISSIONS INDUSTRY FF HEAT REGION STACK #
###########################################

# region

scenario = scenario
start_year = 2000

colors = [
    "#AA0DFE",
    "#3283FE",
    "#85660D",
    "#565656",
    "#1C8356",
    "#16FF32",
    "#F7E1A0",
    "#C4451C",
    "#325A9B",
    "#FEAF16",
    "#F8A19F",
    "#90AD1C",
    "#F6222E",
    "#1CFFCE",
    "#2ED9FF",
    "#B10DA1",
    "#C075A6",
    "#FC1CBF",
    "#B00068",
    "#FBE426",
    "#FA0087",
    "#FD3216",
    "#00FE35",
    "#6A76FC",
    "#FED4C4",
    "#FE00CE",
    "#0DF9FF",
    "#F6F926",
    "#FF9616",
    "#479B55",
    "#EEA6FB",
    "#DC587D",
    "#D626FF",
    "#6E899C",
    "#00B5F7",
    "#B68E00",
    "#C9FBE5",
    "#FF0092",
    "#22FFA7",
    "#E3EE9E",
    "#86CE00",
    "#BC7196",
    "#7E7DCD",
    "#FC6955",
    "#E48F72",
]

em2 = em.loc[
    [
        "US ",
        "SAFR ",
        "RUS ",
        "ME ",
        "JPN ",
        "INDIA ",
        "EUR ",
        "CSAM ",
        "CHINA ",
        "AFRICA ",
    ],
    ["Industry"],
    slice(None),
    slice(None),
    scenario,
].loc[:, start_year:long_proj_end_year]
em2 = em2.loc[~(em2 == 0).all(axis=1)]

fig = (
    (
        em2.loc[slice(None), slice(None), ["Fossil Fuel Heat"], slice(None), scenario]
        .groupby(["Region", "Metric"])
        .sum()
    )
    / 1000
).loc[:, start_year:]
fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e")

fig = go.Figure()

for sub in fig2["Metric"].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2["Metric"].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Metric"] == sub]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": " Emissions in Industry Fossil Fuel Heat, " + scenario.title(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.93,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "GtCO2e/yr"},
    showlegend=True,
)

fig.add_annotation(
    text="Historical data is from Global Carbon Project and Community Emissions Data System; projections are based on PD21 technology adoption rate assumptions<br>applied to IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model for 2040-2100.",
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
        file=("./charts/emsubind-" + scenario + ".html").replace(" ", ""),
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

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    em2 = (
        em_electricity.append(em_transport)
        .append(em_buildings)
        .append(em_industry)
        .append(em_ra)
        .append(em_fw)
    )

    fig = ((em2.groupby("Sector").sum()) / 1000).loc[:, start_year:]
    fig = fig.clip(lower=0)

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

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
            y=fig2[fig2["Sector"] == "Regenerative Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
            groupnorm="percent",
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

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

    fig.update_layout(
        title={
            "text": "Emissions as Relative %, "
            + scenario.title()
            + ", "
            + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.93,
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

    fig.add_vrect(
        x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=("./charts/emr-" + scenario + "-" + region_list[i] + ".html").replace(
                " ", ""
            ),
            auto_open=False,
        )
    plt.clf()

# endregion

###########################
# MITIGATION WEDGES CURVE #
###########################

# region

scenario = "pathway"
start_year = start_year
altscen = str()

ndcs = [
    [(2030, 2050), (24, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2025, 2050, 2030, 2050),
        (4.86, 2.84, 2.84, 0),
        ("NDC", "NDC 2050 est.", "50% reduction by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.4, 0), ("50% reduction by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.17),
    (3, 3),
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("50% reduction by 2030", "NDC", "Net-zero by 2050"),
    ],
    (2030, 9.14),
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
i = 0

for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[region_list[i], "Transport", slice(None)].sum()

    em_mit_buildings = em_mitigated.loc[region_list[i], "Buildings", slice(None)].sum()

    em_mit_industry = em_mitigated.loc[region_list[i], "Industry", slice(None)].sum()

    em_mit_ra = em_mitigated.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:
        """
        em_mit_mar = em_mitigated.loc[region_list[i], "Mariculture"].squeeze()
        """
        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

        em_mit = (
            pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                    em_mit_cdr,
                ]
            )
            .rename(
                index={
                    "Unnamed 0": "Electricity",
                    "Unnamed 1": "Transport",
                    "Unnamed 2": "Buildings",
                    "Unnamed 3": "Industry",
                    "Unnamed 4": "Agriculture",
                    "Unnamed 5": "Forests & Wetlands",
                    "CDR": "CDR",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:
        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

        em_mit = (
            pd.DataFrame(
                [
                    em_mit_electricity,
                    em_mit_transport,
                    em_mit_buildings,
                    em_mit_industry,
                    em_mit_ra,
                    em_mit_fw,
                    em_mit_cdr,
                ]
            )
            .rename(
                index={
                    "Unnamed 0": "Electricity",
                    "Unnamed 1": "Transport",
                    "Unnamed 2": "Buildings",
                    "Unnamed 3": "Industry",
                    "Unnamed 4": "Agriculture",
                    "Unnamed 5": "Forests & Wetlands",
                    "CDR": "CDR",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
                "CDR",
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

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.05,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )

        fig.add_trace(
            go.Scatter(
                name="DAU21+CDR",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
        )
        """
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
        """
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            x=0,
            font=dict(size=10),
            traceorder="reversed",
        )
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + str(altscen)
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    plt.clf()

# endregion

######################################
# SUBVECTOR MITIGATION WEDGES CURVES #
######################################

# region

scenario = "pathway"
start_year = start_year
altscen = str()
i = 0

for i in range(0, len(region_list)):
    em_mit_electricity = em_mitigated.loc[region_list[i], "Electricity", slice(None)]

    em_mit_transport = em_mitigated.loc[region_list[i], "Transport", slice(None)]

    em_mit_buildings = em_mitigated.loc[region_list[i], "Buildings", slice(None)]

    em_mit_industry = em_mitigated.loc[region_list[i], "Industry", slice(None)]

    em_mit_ra = em_mitigated.loc[
        region_list[i], "Regenerative Agriculture", slice(None), slice(None)
    ]

    em_mit_fw = em_mitigated.loc[
        region_list[i], "Forests & Wetlands", slice(None), slice(None)
    ]

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
                4: "Agriculture",
                5: "Forests & Wetlands",
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

    for sector in pd.Series(em2.index.get_level_values(1).unique()):
        fig = (
            ((em_mit.append(spacer)) / 1000)
            .reindex(
                [
                    "Electricity",
                    "Transport",
                    "Buildings",
                    "Industry",
                    "Agriculture",
                    "Forests & Wetlands",
                    "CDR",
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

        for sub in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(sub)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == sub]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=2, color="black"),
                x=pd.Series(em_hist.columns.values),
                y=pd.Series(em_hist.loc[region_list[i], :].values[0] / 1000),
                fill="none",
                stackgroup="two",
                showlegend=False,
            )
        )

        fig.update_layout(
            margin_b=100,
            margin_t=125,
            title={
                "text": "Emissions Mitigated, " + sector + ", " + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            legend={"traceorder": "reversed"},
        )

        fig.add_annotation(
            text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
            xref="paper",
            yref="paper",
            x=-0.15,
            y=-0.4,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=5,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
        )

        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/mwedgessub-"
                    + "pathway"
                    + "-"
                    + sector
                    + "-"
                    + region_list[i]
                    + str(altscen)
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        plt.clf()

# endregion

#################################
# EMISSIONS MITIGATION BARCHART #
#################################

# region

ndcs = [
    [(2030, 2050), (24, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [
        (2030, 2050),
        (3.32, 0),
        (
            "determined through linear extrapolation using the<br>U.S’s 2005 emissions and the NDC set in 2015, which set an emissions goal for 2025.",
            "of net zero emissions, <br>which was set in President Biden’s climate plan.",
        ),
    ],
    (0, 0),
    [
        (2030, 2050),
        (0.94, 0),
        (
            "set in Brazil’s 2015 NDC.",
            "determined through linear extrapolation using Brazil’s 2025 and <br>2030 emissions goals set in their 2015 NDC.",
        ),
    ],
    [(2030, 2050), (2.4, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [
        (2030, 2050),
        (0.398, 0),
        (
            "set in South Africa’s 2015 NDC.",
            "determined through linear extrapolation using South Africa’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030. South Africa submitted a Low Emission <br>Development Scenario in 2020, but the scenario does not specify a 2050 emissions goal.",
        ),
    ],
    (0, 0),
    [
        (2030, 2050),
        (2.17, 0),
        (
            "set in Russia’s 2015 NDC.",
            "determined through linear extrapolation using Russia’s 1990 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030.",
        ),
    ],
    (0, 0),
    [
        (2030, 2050),
        (12.96, 0),
        (
            "determined by China’s 2020<br>NDC update to peak emissions before 2030.",
            "of net zero emissions, which<br>was announced by President Xi Jinping in September 2020.",
        ),
    ],
    [
        (2030, 2050),
        (9.14, 0),
        (
            "set in India’s 2015 NDC.",
            "determined through linear extrapolation using India’s 2017 emissions <br>and the NDC set in 2015, which set an emissions goal for 2030.",
        ),
    ],
    [
        (2030, 2050),
        (1, 0),
        (
            "set in Japan’s 2015 NDC.",
            "of net zero emissions, which was announced in Prime Minister Yoshihide <br>Suga's speech on October 26th, 2020.",
        ),
    ],
    (0, 0),
    (0, 0),
]

ipcc = [
    [(2030, 2050), (24, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (2.99, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (0.69, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (2.39, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (0.26, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (1.02, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (12, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (1.75, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (0.55, 0), ("of 50% reduction by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    (0, 0),
]

scenario = "pathway"

for year in [2030, 2050]:
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
            region_list[i], "Regenerative Agriculture", slice(None), slice(None)
        ].sum()

        em_mit_fw = em_mitigated.loc[
            region_list[i], "Forests & Wetlands", slice(None), slice(None)
        ].sum()

        if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
            em_mit_cdr = (
                pd.Series(
                    cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario],
                    index=np.arange(data_start_year, long_proj_end_year + 1),
                )
            ).rename(index="Unnamed 6")

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
                    "Unnamed 0": "V1: Electricity",
                    "Unnamed 1": "V2: Transport",
                    "Unnamed 2": "V3: Buildings",
                    "Unnamed 3": "V4: Industry",
                    "Unnamed 4": "V5: Agriculture",
                    "Unnamed 5": "V6: Forests & Wetlands",
                    "Unnamed 6": "V7: CDR",
                }
            )
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "V7: CDR",
                        "V6: Forests & Wetlands",
                        "V5: Agriculture",
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
                "V5: Agriculture": [
                    0,
                    0,
                    fig.loc["V5: Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V5: Agriculture", year],
                ],
                "V6: Forests & Wetlands": [
                    0,
                    fig.loc["V6: Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V6: Forests & Wetlands", year],
                ],
                "V7: CDR": [
                    fig.loc["V7: CDR", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V7: CDR", year],
                ],
                "Total": [
                    fig.loc["V7: CDR", year],
                    fig.loc["V6: Forests & Wetlands", year],
                    fig.loc["V5: Agriculture", year],
                    fig.loc["V4: Industry", year],
                    fig.loc["V3: Buildings", year],
                    fig.loc["V2: Transport", year],
                    fig.loc["V1: Electricity", year],
                    0,
                ],
                "labels": [
                    "V7: CDR",
                    "V6: Forests & Wetlands",
                    "V5: Agriculture",
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
                ]
            ).rename(
                index={
                    0: "V1: Electricity",
                    1: "V2: Transport",
                    2: "V3: Buildings",
                    3: "V4: Industry",
                    4: "V5: Agriculture",
                    5: "V6: Forests & Wetlands",
                }
            )
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "V6: Forests & Wetlands",
                        "V5: Agriculture",
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
                    fig.loc["V1: Electricity", year],
                    fig.loc["V1: Electricity", year],
                ],
                "V2: Transport": [
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
                    fig.loc["V3: Buildings", year],
                    0,
                    0,
                    fig.loc["V3: Buildings", year],
                ],
                "V4: Industry": [
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                    0,
                    0,
                    0,
                    fig.loc["V4: Industry", year],
                ],
                "V5: Agriculture": [
                    0,
                    fig.loc["V5: Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V5: Agriculture", year],
                ],
                "V6: Forests & Wetlands": [
                    fig.loc["V6: Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["V6: Forests & Wetlands", year],
                ],
                "Total": [
                    fig.loc["V6: Forests & Wetlands", year],
                    fig.loc["V5: Agriculture", year],
                    fig.loc["V4: Industry", year],
                    fig.loc["V3: Buildings", year],
                    fig.loc["V2: Transport", year],
                    fig.loc["V1: Electricity", year],
                    0,
                ],
                "labels": [
                    "V6: Forests & Wetlands",
                    "V5: Agriculture",
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

        if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:

            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["V7: CDR"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#FF9DA6",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V6: Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V5: Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#EECA3B",
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

            # IPCC target line
            figure.add_shape(
                type="line",
                x0=pd.Series(data["Total"]).sum(),
                y0=-0.5,
                x1=pd.Series(data["Total"]).sum(),
                y1=7.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="NDC",
            )

            figure.add_annotation(
                text="The blue dotted line represents an emissions mitigation goal "
                + ipcc[i][2][j],
                xref="paper",
                yref="paper",
                x=0,
                y=1.16,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="left",
                borderpad=4,
                bgcolor="#ffffff",
                opacity=1,
            )

            # NDC target line
            if region_list[i] in ["US ", "CHINA "]:

                figure.add_shape(
                    type="line",
                    x0=(
                        pd.Series(
                            em_baseline.groupby("Region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ndcs[i][1][j]
                        ).values[0]
                    ).clip(min=0),
                    y0=-0.5,
                    x1=(
                        pd.Series(
                            em_baseline.groupby("Region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ndcs[i][1][j]
                        ).values[0]
                    ).clip(min=0),
                    y1=7.5,
                    line=dict(color="green", width=3, dash="dot"),
                    name="NDC",
                )

                figure.add_annotation(
                    text="The blue dotted line represents an emissions mitigation goal "
                    + ipcc[i][2][j]
                    + "<br>The green dotted line represents an emissions mitigation goal "
                    + ndcs[i][2][j],
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1.2,
                    showarrow=False,
                    font=dict(size=10, color="#2E3F5C"),
                    align="left",
                    borderpad=4,
                    bgcolor="#ffffff",
                    opacity=1,
                )

        else:
            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["V6: Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["V5: Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#EECA3B",
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

        # IPCC & NDC target lines & (year == 2030)
        if region_list[i] in [
            "SAFR ",
            "RUS ",
            "JPN ",
            "BRAZIL ",
            "INDIA ",
        ]:
            figure.add_shape(
                type="line",
                x0=(
                    pd.Series(
                        em_baseline.groupby("Region").sum().loc[region_list[i]][year]
                        / 1e3
                        - ndcs[i][1][j]
                    ).values[0]
                ).clip(min=0),
                y0=-0.5,
                x1=(
                    pd.Series(
                        em_baseline.groupby("Region").sum().loc[region_list[i]][year]
                        / 1e3
                        - ndcs[i][1][j]
                    ).values[0]
                ).clip(min=0),
                y1=6.5,
                line=dict(color="green", width=3, dash="dot"),
                name="NDC",
            )

            figure.add_annotation(
                text="The green dotted line represents an emissions mitigation goal "
                + ndcs[i][2][j]
                + "<br>The blue dotted line represents an emissions mitigation goal of 50% emissions reduction by 2030",
                xref="paper",
                yref="paper",
                x=0,
                y=1.16,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="left",
                borderpad=4,
                bgcolor="#ffffff",
                opacity=1,
            )

            figure.add_shape(
                type="line",
                x0=em_hist.loc[region_list[i], 2019].values[0] / 2000,
                y0=-0.5,
                x1=em_hist.loc[region_list[i], 2019].values[0] / 2000,
                y1=6.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="NDC",
            )

        # EI
        if region_list[i] in [
            "World ",
            "US ",
            "CHINA ",
            "EUR ",
            "SAFR ",
            "RUS ",
            "JPN ",
            "BRAZIL ",
            "INDIA ",
        ]:

            #  & (year == 2030)
            if region_list[i] in [
                "US ",
                "CHINA ",
                "SAFR ",
                "RUS ",
                "JPN ",
                "BRAZIL ",
                "INDIA ",
            ]:
                ei = (
                    em_mit.loc[
                        [
                            "V6: Forests & Wetlands",
                            "V5: Agriculture",
                            "V4: Industry",
                            "V3: Buildings",
                            "V2: Transport",
                            "V1: Electricity",
                        ],
                        year,
                    ].values.sum()
                    / 1e3
                ) / (
                    em_baseline.groupby("Region").sum().loc[region_list[i]][year] / 1e3
                    - ndcs[i][1][j]
                )

                ndcan = (
                    "<br>EI (NDC Target) = "
                    + str(
                        (
                            em_mit.loc[
                                [
                                    "V6: Forests & Wetlands",
                                    "V5: Agriculture",
                                    "V4: Industry",
                                    "V3: Buildings",
                                    "V2: Transport",
                                    "V1: Electricity",
                                ],
                                year,
                            ].values.sum()
                            / 1e3
                        ).round(decimals=2)
                    )
                    + " GtCO2e  /  "
                    + str(
                        (
                            em_baseline.groupby("Region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ndcs[i][1][j]
                        ).round(decimals=2)
                    )
                    + " GtCO2e = "
                    + str(ei.round(decimals=2))
                )
            else:
                ndcan = str("")

            ei = (
                em_mit.loc[
                    [
                        "V6: Forests & Wetlands",
                        "V5: Agriculture",
                        "V4: Industry",
                        "V3: Buildings",
                        "V2: Transport",
                        "V1: Electricity",
                    ],
                    year,
                ].values.sum()
                / 1e3
            ) / (
                em_baseline.groupby("Region").sum().loc[region_list[i]][year] / 1e3
                - ipcc[i][1][j]
            )

            figure.add_annotation(
                text="Epic Index = PD Projected Mitigation Potential / Target Mitigation<br>EI (IPCC Target) = "
                + str(
                    (
                        em_mit.loc[
                            [
                                "V6: Forests & Wetlands",
                                "V5: Agriculture",
                                "V4: Industry",
                                "V3: Buildings",
                                "V2: Transport",
                                "V1: Electricity",
                            ],
                            year,
                        ].values.sum()
                        / 1e3
                    ).round(decimals=2)
                )
                + " GtCO2e"
                + "  /  "
                + str(
                    (
                        em_baseline.groupby("Region").sum().loc[region_list[i]][year]
                        / 1e3
                        - ipcc[i][1][j]
                    ).round(decimals=2)
                )
                + " GtCO2e = "
                + str(ei.round(decimals=2))
                + str(ndcan),
                xref="paper",
                yref="paper",
                x=0,
                y=-0.4,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="left",
                borderpad=4,
                borderwidth=2,
                bgcolor="#ffffff",
                opacity=1,
            )

        figure.update_layout(
            title="Climate Mitigation Potential, " + str(year) + ", " + region_list[i],
            title_x=0.5,
            title_y=0.95,
            xaxis={"title": "GtCO2e mitigated in " + str(year)},
            barmode="stack",
            legend=dict(
                x=0.7,
                y=0,
                bgcolor="rgba(255, 255, 255, 0)",
                bordercolor="rgba(255, 255, 255, 0)",
            ),
            showlegend=False,
            margin_b=120,
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

############################
# NCS OPPORTUNITY BARCHART #
############################

# region

bar_emissions_goal = [
    ("of 50% reduction in the year 2030.", "of net-zero emissions in the year 2050."),
    ("x",),
    (
        "determined through linear extrapolation using the U.S’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2025.",
        "of net zero emissions, which was set in President Biden’s climate plan.",
    ),
    ("x",),
    (
        "set in Brazil’s 2015 NDC.",
        "determined through linear extrapolation using Brazil’s 2025 and <br>2030 emissions goals set in their 2015 NDC.",
    ),
    ("of 50% reduction in the year 2030.", "of net-zero emissions in the year 2050."),
    ("x",),
    (
        "set in South Africa’s 2015 NDC.",
        "determined through linear extrapolation using South Africa’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030. South Africa submitted a Low Emission <br>Development Scenario in 2020, but the scenario does not specify a 2050 emissions goal.",
    ),
    ("x",),
    (
        "set in Russia’s 2015 NDC.",
        "determined through linear extrapolation using Russia’s 1990 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030.",
    ),
    ("x",),
    (
        "determined by China’s 2020 NDC update to peak emissions before <br>2030.",
        "of net zero emissions, which was announced by President Xi Jinping in <br>September 2020.",
    ),
    (
        "set in India’s 2015 NDC.",
        "determined through linear extrapolation using India’s 2017 emissions <br>and the NDC set in 2015, which set an emissions goal for 2030.",
    ),
    (
        "set in Japan’s 2015 NDC.",
        "of net zero emissions, which was announced in Prime Minister Yoshihide <br>Suga's speech on October 26th, 2020.",
    ),
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
    [(2030, 2050), (12.96, 0), ("NDC", "Net-zero by 2050")],
    (2030, 9.14),
    (2030, 1),
    (3, 3),
    (3, 3),
]

scenario = "pathway"
year = 2050

data = []

for i in range(0, len(region_list)):
    em_mit_electricity = em_mitigated.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[region_list[i], "Transport", slice(None)].sum()

    em_mit_buildings = em_mitigated.loc[region_list[i], "Buildings", slice(None)].sum()

    em_mit_industry = em_mitigated.loc[region_list[i], "Industry", slice(None)].sum()

    em_mit_ra = em_mitigated.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    em_mit = pd.DataFrame(
        [
            em_mit_electricity,
            em_mit_transport,
            em_mit_buildings,
            em_mit_industry,
            em_mit_ra,
            em_mit_fw,
        ]
    ).rename(
        index={
            0: "V1: Electricity",
            1: "V2: Transport",
            2: "V3: Buildings",
            3: "V4: Industry",
            4: "V5: Agriculture",
            5: "V6: Forests & Wetlands",
        }
    )

    spacer = (
        pd.Series(
            em_baseline.groupby("Region").sum().loc[region_list[i]]
            - em_mit.loc[
                ["V1: Electricity", "V2: Transport", "V3: Buildings", "V4: Industry"], :
            ].sum()
        )
        .replace(nan, 0)
        .rename("")
        .T
    )

    fig = (
        ((em_mit) / 1000)
        .reindex(
            [
                "V6: Forests & Wetlands",
                "V5: Agriculture",
                "V4: Industry",
                "V3: Buildings",
                "V2: Transport",
                "V1: Electricity",
            ]
        )
        .round(decimals=4)
        .clip(lower=0)
    )

    data = pd.DataFrame(data).append(
        {
            "V5: Agriculture": fig.loc["V5: Agriculture", year],
            "V6: Forests & Wetlands": fig.loc["V6: Forests & Wetlands", year],
            "labels": region_list[i],
            "spacer": spacer[2050] / 1000,
        },
        ignore_index=True,
    )

figure = go.Figure(
    data=[
        go.Bar(
            name="V6: Forests & Wetlands",
            x=data["labels"],
            y=data["V6: Forests & Wetlands"],
            offsetgroup=0,
            orientation="v",
            marker_color="#54A24B",
            opacity=0.5,
        ),
        go.Bar(
            name="V5: Agriculture",
            x=data["labels"],
            y=data["V5: Agriculture"],
            offsetgroup=0,
            orientation="v",
            marker_color="#EECA3B",
            opacity=0.5,
        ),
    ]
)

figure.add_trace(
    go.Scatter(
        mode="markers",
        name="Emissions gap, after energy sector mitigation",
        x=data["labels"],
        y=data["spacer"],
        fill="none",
    )
)

figure.add_trace(
    go.Scatter(
        mode="markers",
        opacity=0,
        name="Emissions gap, after energy sector mitigation",
        x=data["labels"],
        y=-data["spacer"],
        fill="none",
        showlegend=False,
    )
)

figure.update_layout(
    title="Opportunity for NCS Mitigation after Energy Markets, " + str(year),
    title_x=0.5,
    title_y=0.99,
    yaxis={"title": "GtCO2e"},
    barmode="stack",
    showlegend=True,
    legend=dict(
        orientation="h",
        x=0.2,
        y=1.25,
        bgcolor="rgba(255, 255, 255, 0)",
        bordercolor="rgba(255, 255, 255, 0)",
    ),
    xaxis={"categoryorder": "total descending"},
)

figure.update_yaxes(range=[0, 35])

if show_figs is True:
    figure.show()
if save_figs is True:
    pio.write_html(
        figure,
        file=(
            "./charts/ncsbar-" + "pathway" + "-" + str(year) + "-" + "World" + ".html"
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
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    3,
)

results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values


# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

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

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion (not needed here for just CO2)
Cb["CO2"] = Cb.loc[:, 0]
Cpd["CO2"] = Cpd.loc[:, 0]
Ccdr["CO2"] = Ccdr.loc[:, 0]

C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2"],
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
        y=Cb.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, "CO2"],
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
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
"""
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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    6,
)
"""
results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values


# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

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

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion
Cb["CO2e"] = Cb.loc[:, 0] + Cb.loc[:, 1] * 25e-3 + Cb.loc[:, 2] * 298e-3
Cpd["CO2e"] = Cpd.loc[:, 0] + Cpd.loc[:, 1] * 25e-3 + Cpd.loc[:, 2] * 298e-3
Ccdr["CO2e"] = Ccdr.loc[:, 0] + Ccdr.loc[:, 1] * 25e-3 + Ccdr.loc[:, 2] * 298e-3

C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2e"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2e"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2e"],
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
        y=Cb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, "CO2e"],
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
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2e"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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

hist = pd.read_csv("podi/data/forcing.csv")
hist.columns = hist.columns.astype(int)

F = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
F.columns = F.columns.astype(int)

F19 = curve_smooth(
    pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:]
    ),
    "quadratic",
    6,
)

"""
F19 = pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:])
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values


# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
"""
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
"""
Fb = (
    pd.DataFrame(Fb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fpd = (
    pd.DataFrame(Fpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fcdr = (
    pd.DataFrame(Fcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Fb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fb, axis=1)).T, "quadratic", 6).T
Fpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fpd, axis=1)).T, "quadratic", 6).T
Fcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fcdr, axis=1)).T, "quadratic", 6).T
"""
Fb['CO2e'] = np.sum(Fb, axis=1)
Fpd['CO2e'] = np.sum(Fpd, axis=1)
Fcdr['CO2e'] = np.sum(Fcdr, axis=1)
"""

F19 = F19 * (hist.loc[:, 2020].values[0] / F19.loc[:, 2020].values[0])
Fb = Fb * (hist.loc[:, data_end_year].values[0] / Fb.loc[data_end_year, "CO2e"])
Fpd = Fpd * (hist.loc[:, data_end_year].values[0] / Fpd.loc[data_end_year, "CO2e"])
Fcdr = Fcdr * (hist.loc[:, data_end_year].values[0] / Fcdr.loc[data_end_year, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Fb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=F19.loc[:, 2020:2100].columns,
        y=F19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={"text": "Radiative Forcing", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "W/m2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)


fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/forcing-" + "World" + ".html").replace(" ", ""),
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

hist = pd.read_csv("podi/data/temp.csv")
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

"""
T19 = T.loc[
            "GCAM4",
            "SSP1-19",
            "World",
            ["Diagnostics|MAGICC6|Temperature|Global Mean"],
        ].loc[:, 2010:]
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values


# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
"""
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
"""
Tb = (
    pd.DataFrame(Tb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tpd = (
    pd.DataFrame(Tpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tcdr = (
    pd.DataFrame(Tcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Tb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tb, axis=1)).T, "quadratic", 6).T
Tpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tpd, axis=1)).T, "quadratic", 6).T
Tcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tcdr, axis=1)).T, "quadratic", 6).T
"""
Tb['CO2e'] = np.sum(Tb, axis=1)
Tpd['CO2e'] = np.sum(Tpd, axis=1)
Tcdr['CO2e'] = np.sum(Tcdr, axis=1)
"""

T19 = T19 * (hist.loc[:, 2020].values[0] / T19.loc[:, 2020].values[0])
Tb = Tb * (hist.loc[:, data_end_year].values[0] / Tb.loc[data_end_year, "CO2e"])
Tpd = Tpd * (hist.loc[:, data_end_year].values[0] / Tpd.loc[data_end_year, "CO2e"])
Tcdr = Tcdr * (hist.loc[:, data_end_year].values[0] / Tcdr.loc[data_end_year, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Tb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=T19.loc[:, 2020:2100].columns,
        y=T19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={"text": "Global Mean Temperature", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the Hector climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/temp-" + "World" + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion


###################################
# //////////// DAU-LP ////////////# 2x
###################################

# region

##########################
# DAU-LP ADOPTION CURVES #
##########################

# region

scenario = scenario
start_year = start_year
i = 0
accel = 2

for i in range(0, len(region_list)):
    fig_hist = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, :data_end_year
        ]
        * 100
    )

    fig_alt = (
        adoption_curves.loc[region_list[i], slice(None), scenario]
        .loc[:, data_end_year + 1 :]
        .loc[:, ::accel]
        * 100
    )
    fig_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

    fig_end = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, long_proj_end_year - int(80 / accel - 1) :
        ]
        * 0
    )
    fig_end.loc[:, :] = fig_alt.iloc[:, -1].values[:, None]

    fig = (fig_hist.join(fig_alt).join(fig_end)).loc[:, start_year:]

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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )
        """
        else:
            fig.add_trace(
            go.Scatter(
                name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
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
        """

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + "DAU-LP" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
                "./charts/scurves-"
                + region_list[i]
                + "-"
                + scenario
                + "-daulp"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

####################
# DAU-LP EMISSIONS #
####################

# region

scenario = scenario
start_year = 2000
i = 0
accel = 2

em_pathway_alt = em_pathway.loc[:, data_end_year + 1 :].loc[:, ::accel]
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

em_pathway_end = em_pathway.loc[:, long_proj_end_year - int(80 / accel - 1) :] * 0
em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(em_pathway.loc[:, data_end_year])
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

em_alt = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

# for use in climate charts
em_alt_lp = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

for i in range(0, len(region_list)):

    em_electricity = em_alt.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em_alt.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em_alt.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em_alt.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em_alt.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em_alt.loc[
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
        scenario,
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    em2 = (
        em_electricity.append(em_transport)
        .append(em_buildings)
        .append(em_industry)
        .append(em_ra)
        .append(em_fw)
    )

    fig = ((em2.groupby("Sector").sum()) / 1000).loc[:, start_year:]

    fig = fig.T
    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name="Sector", value_name="Emissions, GtCO2e"
    )

    fig = go.Figure()

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

    if em_fw.loc[:, 2000].values[0] < 0:
        histfill = "tozeroy"
        stackgroup = "hist"
    else:
        histfill = "tozeroy"
        stackgroup = "hist"

    fig.add_trace(
        go.Scatter(
            name="Historical Net Emissions",
            line=dict(width=2, color="black"),
            x=pd.Series(
                em.loc[region_list[i], slice(None), slice(None), slice(None), scenario]
                .loc[:, start_year:data_end_year]
                .columns.values
            ),
            y=pd.Series(
                em.loc[region_list[i], slice(None), slice(None), slice(None), scenario]
                .loc[:, start_year:data_end_year]
                .sum()
            )
            / 1000,
            fill=histfill,
            stackgroup=stackgroup,
        )
    )

    fig.update_layout(
        title={
            "text": "Emissions, " + "DAU-LP" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10)),
        margin_b=90,
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.31,
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
                "./charts/em2-" + scenario + "-" + region_list[i] + "-daulp" + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

###############################
# DAU-LP EMISSIONS SUBVECTORS #
###############################

# region

scenario = scenario
start_year = 2000

colors = [
    "#AA0DFE",
    "#3283FE",
    "#85660D",
    "#565656",
    "#1C8356",
    "#16FF32",
    "#F7E1A0",
    "#C4451C",
    "#325A9B",
    "#FEAF16",
    "#F8A19F",
    "#90AD1C",
    "#F6222E",
    "#1CFFCE",
    "#2ED9FF",
    "#B10DA1",
    "#C075A6",
    "#FC1CBF",
    "#B00068",
    "#FBE426",
    "#FA0087",
    "#FD3216",
    "#00FE35",
    "#6A76FC",
    "#FED4C4",
    "#FE00CE",
    "#0DF9FF",
    "#F6F926",
    "#FF9616",
    "#479B55",
    "#EEA6FB",
    "#DC587D",
    "#D626FF",
    "#6E899C",
    "#00B5F7",
    "#B68E00",
    "#C9FBE5",
    "#FF0092",
    "#22FFA7",
    "#E3EE9E",
    "#86CE00",
    "#BC7196",
    "#7E7DCD",
    "#FC6955",
    "#E48F72",
]
i = 0
accel = 2

em_pathway_alt = em_pathway.loc[:, data_end_year + 1 :].loc[:, ::accel]
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

em_pathway_end = em_pathway.loc[:, long_proj_end_year - int(80 / accel - 1) :] * 0
em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(em_pathway.loc[:, data_end_year])
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

em_alt = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

# for use in climate charts
em_alt_lp = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

for i in range(0, len(region_list)):

    em_electricity = em_alt.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = em_electricity.loc[~(em_electricity == 0).all(axis=1)]

    em_transport = em_alt.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)]

    em_buildings = em_alt.loc[
        region_list[i], ["Buildings"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_buildings = em_buildings.loc[~(em_buildings == 0).all(axis=1)]

    em_industry = em_alt.loc[
        region_list[i], ["Industry"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_industry = em_industry.loc[~(em_industry == 0).all(axis=1)]

    em_ra = em_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_ra = em_ra.loc[~(em_ra == 0).all(axis=1)]

    em_fw = em_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_fw = em_fw.loc[~(em_fw == 0).all(axis=1)]

    em2 = (
        em_electricity.append(em_transport)
        .append(em_buildings)
        .append(em_industry)
        .append(em_ra)
        .append(em_fw)
    )

    for sector in pd.Series(em2.index.get_level_values(1).unique()):
        fig = (
            (
                em2.loc[region_list[i], sector, slice(None), slice(None), scenario]
                .groupby(["Metric"])
                .sum()
            )
            / 1000
        ).loc[:, start_year:]
        fig = fig.T
        fig.index.name = "Year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="Year", var_name="Metric", value_name="Emissions, GtCO2e"
        )

        if sector == "Industry":
            fig3 = fig2[fig2["Metric"] == "Fossil Fuel Heat"]
            fig2 = fig3.append(fig2[fig2["Metric"] != "Fossil Fuel Heat"])

        if sector == "Regenerative Agriculture":
            fig3 = fig2[
                (fig2["Metric"] != "Cropland Soil Health")
                & (fig2["Metric"] != "Trees in Croplands")
                & (fig2["Metric"] != "Silvopasture")
                & (fig2["Metric"] != "Optimal Intensity")
                & (fig2["Metric"] != "Improved Rice")
                & (fig2["Metric"] != "Biochar")
                & (fig2["Metric"] != "Nitrogen Fertilizer Management")
            ]

            fig4 = fig2[
                (fig2["Metric"] == "Cropland Soil Health")
                | (fig2["Metric"] == "Trees in Croplands")
                | (fig2["Metric"] == "Silvopasture")
                | (fig2["Metric"] == "Optimal Intensity")
                | (fig2["Metric"] == "Improved Rice")
                | (fig2["Metric"] == "Biochar")
                | (fig2["Metric"] == "Nitrogen Fertilizer Management")
            ]

            fig2 = fig3.append(fig4)

        if sector == "Forests & Wetlands":
            fig3 = fig2[fig2["Metric"] == "Deforestation"]

            fig4 = fig2[fig2["Metric"] != "Deforestation"]

            fig2 = fig3.append(fig4)

        fig = go.Figure()

        for sub in fig2["Metric"].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                        color=colors[
                            pd.DataFrame(fig2["Metric"].unique())
                            .set_index(0)
                            .index.get_loc(sub)
                        ],
                    ),
                    x=fig2["Year"],
                    y=fig2[fig2["Metric"] == sub]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": " Emissions in "
                + str(sector)
                + ", "
                + scenario.title()
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.93,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            showlegend=True,
        )

        fig.add_annotation(
            text="Historical data is from Global Carbon Project and Community Emissions Data System; projections are based on PD21 technology adoption rate assumptions<br>applied to IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model for 2040-2100.",
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
                    "./charts/emsub-"
                    + scenario
                    + "-"
                    + region_list[i]
                    + "-"
                    + str(sector)
                    + "-daulp"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )
        plt.clf()

# endregion

##################################
# DAU-LP MITIGATION WEDGES CURVE #
##################################

# region

scenario = "pathway"
start_year = start_year
i = 0
accel = 2

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
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("NDC", "50% reduction by 2030", "Net-zero by 2050"),
    ],
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

em_baseline_alt = em_baseline

em_pathway_alt = em_pathway.loc[:, data_end_year + 1 :].loc[:, ::accel]
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

em_pathway_end = em_pathway.loc[:, long_proj_end_year - int(80 / accel - 1) :] * 0
em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(em_pathway.loc[:, data_end_year])
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

# for use in climate charts
em_alt_lp = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

em_mitigated_alt = (
    em_baseline_alt.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway_alt.groupby(["Region", "Sector", "Metric"]).sum()
)


for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated_alt.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated_alt.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated_alt.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated_alt.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
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

    """
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21-LP",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, DAU-LP, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
        legend={"traceorder": "reversed"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + "-daulp"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

# endregion


###################################
# //////////// DAU-WE ////////////# 3X
###################################

# region

##########################
# DAU-WE ADOPTION CURVES #
##########################

# region

scenario = scenario
start_year = start_year
i = 0
accel = 3

for i in range(0, len(region_list)):

    fig_hist = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, :data_end_year
        ]
        * 100
    )

    fig_alt = (
        adoption_curves.loc[region_list[i], slice(None), scenario]
        .loc[:, data_end_year + 1 :]
        .loc[:, ::accel]
        * 100
    )
    fig_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

    fig_end = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, long_proj_end_year - int(80 / accel - 1) :
        ]
        * 0
    )
    fig_end.loc[:, :] = fig_alt.iloc[:, -1].values[:, None]

    fig = (fig_hist.join(fig_alt).join(fig_end)).loc[:, start_year:]

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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )
        """
        else:
            fig.add_trace(
            go.Scatter(
                name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
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
        """

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + "DAU-WE" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
                "./charts/scurves-"
                + region_list[i]
                + "-"
                + scenario
                + "-dauwe"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

##################################
# DAU-WE MITIGATION WEDGES CURVE #
##################################

# region

scenario = "pathway"
start_year = start_year
i = 0
accel = 3

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
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("NDC", "50% reduction by 2030", "Net-zero by 2050"),
    ],
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

"""
em_baseline_alt = em_baseline.loc[:, data_end_year + 1 :].loc[:, ::accel]
em_baseline_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

em_baseline_end = em_baseline.loc[:, long_proj_end_year - int(80 / accel - 1) :] * 0
em_baseline_end.loc[:, :] = em_baseline_alt.iloc[:, -1].values[:, None]

em_baseline_alt = pd.DataFrame(em_baseline.loc[:,data_end_year]).join(em_baseline_alt).join(em_baseline_end)
"""

em_baseline_alt = em_baseline

em_pathway_alt = em_pathway.loc[:, data_end_year + 1 :].loc[:, ::accel]
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

em_pathway_end = em_pathway.loc[:, 2047:] * 0
em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(em_pathway.loc[:, data_end_year])
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

# for use in climate charts
em_alt_we = em_pathway.loc[:, : data_end_year - 1].join(em_pathway_alt)

em_mitigated_alt = (
    em_baseline_alt.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway_alt.groupby(["Region", "Sector", "Metric"]).sum()
)


for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated_alt.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated_alt.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated_alt.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated_alt.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
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

    """
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21-WE",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, DAU-WE, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
        legend={"traceorder": "reversed"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + "-dauwe"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

# endregion


###################################
# //////////// DAU-RA ////////////# RA 2x
###################################

# region

##########################
# DAU-RA ADOPTION CURVES #
##########################

# region

scenario = scenario
start_year = start_year
i = 0
accel = 2

for i in range(0, len(region_list)):

    fig_hist = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, :data_end_year
        ]
        * 100
    )

    fig_alt = (
        adoption_curves.loc[region_list[i], slice(None), scenario]
        .loc[:, data_end_year + 1 :]
        .loc[:, ::accel]
        * 100
    )
    fig_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

    fig_end = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, long_proj_end_year - int(80 / accel - 1) :
        ]
        * 0
    )
    fig_end.loc[:, :] = fig_alt.iloc[:, -1].values[:, None]

    fig = (fig_hist.join(fig_alt).join(fig_end)).loc[:, start_year:]

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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )
        """
        else:
            fig.add_trace(
            go.Scatter(
                name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
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
        """

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + "DAU-RA" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
                "./charts/scurves-"
                + region_list[i]
                + "-"
                + scenario
                + "-daura"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

##################################
# DAU-RA MITIGATION WEDGES CURVE #
##################################

# region

scenario = "pathway"
start_year = start_year
i = 0
accel = 2

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
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("NDC", "50% reduction by 2030", "Net-zero by 2050"),
    ],
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

em_baseline_alt = em_baseline

em_pathway_alt = (
    em_pathway.loc[slice(None), ["Regenerative Agriculture"], :]
    .loc[:, data_end_year + 1 :]
    .loc[:, ::accel]
)
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)
"""
em_pathway_end = (
    em_pathway.loc[slice(None), ["Regenerative Agriculture"], :].loc[:, 2047:] * 0
)
"""
em_pathway_end = (
    em_pathway.loc[slice(None), ["Regenerative Agriculture"], :].loc[
        :, long_proj_end_year - int(80 / accel - 1) :
    ]
    * 0
)

em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(
        em_pathway.loc[slice(None), ["Regenerative Agriculture"], :].loc[
            :, data_end_year
        ]
    )
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

em_pathway_alt2 = em_pathway.loc[
    slice(None),
    ["Buildings", "Electricity", "Forests & Wetlands", "Industry", "Transport"],
    :,
].append(em_pathway_alt)
em_pathway_alt = em_pathway_alt2

# for use in climate charts
em_alt_ra = em_pathway_alt

em_mitigated_alt = (
    em_baseline_alt.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway_alt.groupby(["Region", "Sector", "Metric"]).sum()
)

for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated_alt.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated_alt.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated_alt.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated_alt.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
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

    """
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21-RA",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, DAU-RA, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
        legend={"traceorder": "reversed"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + "-daura"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

# endregion


###################################
# //////////// DAU-FW ////////////# FW 2x
###################################

# region

##########################
# DAU-FW ADOPTION CURVES #
##########################

# region

scenario = scenario
start_year = start_year
i = 0
accel = 2

for i in range(0, len(region_list)):

    fig_hist = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, :data_end_year
        ]
        * 100
    )

    fig_alt = (
        adoption_curves.loc[region_list[i], slice(None), scenario]
        .loc[:, data_end_year + 1 :]
        .loc[:, ::accel]
        * 100
    )
    fig_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

    fig_end = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, long_proj_end_year - int(80 / accel - 1) :
        ]
        * 0
    )
    fig_end.loc[:, :] = fig_alt.iloc[:, -1].values[:, None]

    fig = (fig_hist.join(fig_alt).join(fig_end)).loc[:, start_year:]

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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + "DAU-FW" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
                "./charts/scurves-"
                + region_list[i]
                + "-"
                + scenario
                + "-daufw"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

##################################
# DAU-FW MITIGATION WEDGES CURVE #
##################################

# region

scenario = "pathway"
start_year = start_year
i = 0
accel = 2

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
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("NDC", "50% reduction by 2030", "Net-zero by 2050"),
    ],
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

em_baseline_alt = em_baseline

em_pathway_alt = (
    em_pathway.loc[slice(None), ["Forests & Wetlands"], :]
    .loc[:, data_end_year + 1 :]
    .loc[:, ::accel]
)
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)
"""
em_pathway_end = (
    em_pathway.loc[slice(None), ["Forests & Wetlands"], :].loc[:, 2047:] * 0
)
"""
em_pathway_end = (
    em_pathway.loc[slice(None), ["Forests & Wetlands"], :].loc[
        :, long_proj_end_year - int(80 / accel - 1) :
    ]
    * 0
)

em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(
        em_pathway.loc[slice(None), ["Forests & Wetlands"], :].loc[:, data_end_year]
    )
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

em_pathway_alt2 = em_pathway.loc[
    slice(None),
    ["Buildings", "Electricity", "Regenerative Agriculture", "Industry", "Transport"],
    :,
].append(em_pathway_alt)
em_pathway_alt = em_pathway_alt2

# for use in climate charts
em_alt_fw = em_pathway_alt

em_mitigated_alt = (
    em_baseline_alt.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway_alt.groupby(["Region", "Sector", "Metric"]).sum()
)


for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated_alt.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated_alt.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated_alt.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated_alt.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
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

    """
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21-FW",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, DAU-FW, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
        legend={"traceorder": "reversed"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + "-daufw"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

# endregion


###################################
# //////////// DAU-RAFW ////////////# RA&FW 2x
###################################

# region

##########################
# DAU-FW ADOPTION CURVES #
##########################

# region

scenario = scenario
start_year = start_year
i = 0
accel = 2

for i in range(0, len(region_list)):

    fig_hist = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, :data_end_year
        ]
        * 100
    )

    fig_alt = (
        adoption_curves.loc[region_list[i], slice(None), scenario]
        .loc[:, data_end_year + 1 :]
        .loc[:, ::accel]
        * 100
    )
    fig_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)

    fig_end = (
        adoption_curves.loc[region_list[i], slice(None), scenario].loc[
            :, long_proj_end_year - int(80 / accel - 1) :
        ]
        * 0
    )
    fig_end.loc[:, :] = fig_alt.iloc[:, -1].values[:, None]

    fig = (fig_hist.join(fig_alt).join(fig_end)).loc[:, start_year:]

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
        if scenario == "pathway":
            fig.add_trace(
                go.Scatter(
                    name="V7: Carbon Dioxide Removal",
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
                    name="V7: Carbon Dioxide Removal",
                    line=dict(width=3, color="#FF9DA6", dash="dot"),
                    x=fig2[(fig2["Year"] >= 2020) & (fig2["Sector"] == "Electricity")][
                        "Year"
                    ],
                    y=fig2[
                        (fig2["Year"] >= 2020)
                        & (fig2["Sector"] == "Carbon Dioxide Removal")
                    ]["% Adoption"]
                    .cumsum()
                    .divide(
                        (
                            fig2[
                                (fig2["Year"] >= 2020)
                                & (fig2["Sector"] == "Carbon Dioxide Removal")
                            ]["% Adoption"]
                        )
                        .cumsum()
                        .max()
                    )
                    * 100,
                    fill="none",
                    stackgroup="fourteen",
                    legendgroup="Carbon Dioxide Removal",
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, "
            + "DAU-RAFW"
            + ", "
            + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
        margin_b=100,
    )

    fig.add_annotation(
        text="Adoption rates are represented as: <b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources; <br><b>Regenerative Agriculture, Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available; <br><b>CDR</b>: percent of total mitigation needed to meet net emissions targets.",
        xref="paper",
        yref="paper",
        x=-0.12,
        y=-0.36,
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
                "./charts/scurves-"
                + region_list[i]
                + "-"
                + scenario
                + "-daurafw"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

####################################
# DAU-RAFW MITIGATION WEDGES CURVE #
####################################

# region

scenario = "pathway"
start_year = start_year
i = 0
accel = 2

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
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("NDC", "50% reduction by 2030", "Net-zero by 2050"),
    ],
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

em_baseline_alt = em_baseline

em_pathway_alt = (
    em_pathway.loc[slice(None), ["Regenerative Agriculture", "Forests & Wetlands"], :]
    .loc[:, data_end_year + 1 :]
    .loc[:, ::accel]
)
em_pathway_alt.columns = np.arange(2020, int(2020 + 80 / accel + 1), 1)
"""
em_pathway_end = (
    em_pathway.loc[slice(None), ["Regenerative Agriculture", "Forests & Wetlands"], :].loc[:, 2047:] * 0
)
"""
em_pathway_end = (
    em_pathway.loc[
        slice(None), ["Regenerative Agriculture", "Forests & Wetlands"], :
    ].loc[:, long_proj_end_year - int(80 / accel - 1) :]
    * 0
)

em_pathway_end.loc[:, :] = em_pathway_alt.iloc[:, -1].values[:, None]

em_pathway_alt = (
    pd.DataFrame(
        em_pathway.loc[
            slice(None), ["Regenerative Agriculture", "Forests & Wetlands"], :
        ].loc[:, data_end_year]
    )
    .join(em_pathway_alt)
    .join(em_pathway_end)
)

em_pathway_alt2 = em_pathway.loc[
    slice(None),
    ["Buildings", "Electricity", "Industry", "Transport"],
    :,
].append(em_pathway_alt)
em_pathway_alt = em_pathway_alt2

# for use in climate charts
em_alt_rafw = em_pathway_alt

em_mitigated_alt = (
    em_baseline_alt.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway_alt.groupby(["Region", "Sector", "Metric"]).sum()
)


for i in range(0, len(region_list)):

    em_mit_electricity = em_mitigated_alt.loc[
        region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated_alt.loc[
        region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated_alt.loc[
        region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated_alt.loc[
        region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated_alt.loc[
        region_list[i], ["Regenerative Agriculture"], slice(None), slice(None)
    ].sum()

    em_mit_fw = em_mitigated_alt.loc[
        region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
    ].sum()

    if region_list[i] in ["World "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

    elif region_list[i] in ["US ", "CHINA ", "EUR "]:

        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .squeeze()
            .rename("CDR")
        )

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
            .rename(
                index={
                    0: "Electricity",
                    1: "Transport",
                    2: "Buildings",
                    3: "Industry",
                    4: "Agriculture",
                    5: "Forests & Wetlands",
                }
            )
            .clip(lower=0)
        )

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
                    4: "Agriculture",
                    5: "Forests & Wetlands",
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
                "Agriculture",
                "Forests & Wetlands",
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

    """
    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        
        fig.add_trace(
            go.Scatter(
                name="V7: CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2100: "
            + str(
                fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"].values.sum().round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.15,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2100: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] > 2049)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.02,
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
            stackgroup="two",
            showlegend=False,
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
                legendgroup="two",
            )
        )

    if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        """
        fig.add_trace(
            go.Scatter(
                name="DAU21-RA",
                line=dict(width=2, color="yellow", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values) / 1000,
                fill="none",
                stackgroup="DAU21+CDR",
                legendgroup="two",
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
                name="DAU21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series((spacer.loc[near_proj_start_year:].values) / 1000),
                fill="none",
                stackgroup="five",
                legendgroup="two",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% reduction by 2030",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=pd.Series(2050),
                y=pd.Series(0),
                marker_color="#211df2",
                name="Net-zero by 2050",
            )
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
            legendgroup="two",
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    elif region_list[i] in ["CHINA "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#eb742f",
                name=ndcs[i][2][2],
            )
        )
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
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
        """
        fig.add_annotation(
            text="The NDC commitment is to "
            + ndc_commit[i][0]
            + " 50% reduction and net-zero goals compare regional alignment <br>with global-level IPCC recommendations.",
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
        """
    # endregion

    fig.update_layout(
        margin_b=100,
        margin_t=125,
        title={
            "text": "Emissions Mitigated, DAU-RAFW, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
        legend={"traceorder": "reversed"},
    )

    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to IEA World Energy <br>Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100.",
        xref="paper",
        yref="paper",
        x=-0.15,
        y=-0.4,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=5,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10))
    )

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/mwedges-"
                + "pathway"
                + "-"
                + region_list[i]
                + "-daurafw"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

# endregion


#############################################################
# //////////// MULTI-SCENARIO CLIMATE OUTCOMES  ////////////#
#############################################################

# region

#################################
# CO2 ATMOSPHERIC CONCENTRATION #
#################################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp60.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)
em_lp = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_we = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)

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
"""
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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    6,
)
"""
results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_lp.loc[225:335, 1] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 1] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_lp.loc[225:335, 2] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 2] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_lp.loc[225:335, 3] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_we.loc[225:335, 3] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values


# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_lp.loc[225:335, 4] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_we.loc[225:335, 4] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_lp = em_lp.values
em_we = em_we.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_lp, other_rf=other_rf)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_we, other_rf=other_rf)

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Clp = (
    pd.DataFrame(Clp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cwe = (
    pd.DataFrame(Cwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)


# CO2e conversion (not needed here for just CO2)
Cb["CO2"] = Cb.loc[:, 0]
Cpd["CO2"] = Cpd.loc[:, 0]
Ccdr["CO2"] = Ccdr.loc[:, 0]
Clp["CO2"] = Clp.loc[:, 0]
Cwe["CO2"] = Cwe.loc[:, 0]


C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2"])
Clp = Clp * (hist[2021] / Clp.loc[2021, "CO2"])
Cwe = Cwe * (hist[2021] / Cwe.loc[2021, "CO2"])


fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2"],
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
        y=Cb.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="DAU21-LP",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Clp.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)
fig.add_trace(
    go.Scatter(
        name="DAU21-WE",
        line=dict(width=3, color="light blue", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cwe.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="we",
        legendgroup="we",
    )
)


fig.update_layout(
    title={
        "text": "Atmospheric CO2 Concentration",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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


# endregion

#################################
# GHG ATMOSPHERIC CONCENTRATION #
#################################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp60.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)
em_lp = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_we = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)

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
"""
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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    6,
)
"""
results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_lp.loc[225:335, 1] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 1] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_lp.loc[225:335, 2] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 2] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_lp.loc[225:335, 3] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_we.loc[225:335, 3] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values


# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_lp.loc[225:335, 4] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_we.loc[225:335, 4] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_lp = em_lp.values
em_we = em_we.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_lp, other_rf=other_rf)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_we, other_rf=other_rf)

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Clp = (
    pd.DataFrame(Clp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cwe = (
    pd.DataFrame(Cwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)


# CO2e conversion
Cb["CO2e"] = Cb.loc[:, 0] + Cb.loc[:, 1] * 25e-3 + Cb.loc[:, 2] * 298e-3
Cpd["CO2e"] = Cpd.loc[:, 0] + Cpd.loc[:, 1] * 25e-3 + Cpd.loc[:, 2] * 298e-3
Ccdr["CO2e"] = Ccdr.loc[:, 0] + Ccdr.loc[:, 1] * 25e-3 + Ccdr.loc[:, 2] * 298e-3
Clp["CO2e"] = Clp.loc[:, 0] + Clp.loc[:, 1] * 25e-3 + Clp.loc[:, 2] * 298e-3
Cwe["CO2e"] = Cwe.loc[:, 0] + Cwe.loc[:, 1] * 25e-3 + Cwe.loc[:, 2] * 298e-3

C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2e"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2e"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2e"])
Clp = Clp * (hist[2021] / Clp.loc[2021, "CO2e"])
Cwe = Cwe * (hist[2021] / Cwe.loc[2021, "CO2e"])


fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2e"],
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
        y=Cb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="DAU21-LP",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Clp.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)
fig.add_trace(
    go.Scatter(
        name="DAU21-WE",
        line=dict(width=3, color="light blue", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cwe.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="we",
        legendgroup="we",
    )
)


fig.update_layout(
    title={
        "text": "Atmospheric GHG Concentration",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2e"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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


# endregion

#####################
# RADIATIVE FORCING #
#####################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp85.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)
em_lp = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_we = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)

hist = pd.read_csv("podi/data/forcing.csv")
hist.columns = hist.columns.astype(int)

F = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
F.columns = F.columns.astype(int)

F19 = curve_smooth(
    pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:]
    ),
    "quadratic",
    6,
)

"""
F19 = pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:])
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_lp.loc[225:335, 1] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 1] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_lp.loc[225:335, 2] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 2] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_lp.loc[225:335, 3] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_we.loc[225:335, 3] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_lp.loc[225:335, 4] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_we.loc[225:335, 4] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_lp = em_lp.values
em_we = em_we.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_lp)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_we)

"""
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
"""
Fb = (
    pd.DataFrame(Fb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fpd = (
    pd.DataFrame(Fpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fcdr = (
    pd.DataFrame(Fcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Flp = (
    pd.DataFrame(Flp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fwe = (
    pd.DataFrame(Fwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Fb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fb, axis=1)).T, "quadratic", 6).T
Fpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fpd, axis=1)).T, "quadratic", 6).T
Fcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fcdr, axis=1)).T, "quadratic", 6).T
Flp["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Flp, axis=1)).T, "quadratic", 6).T
Fwe["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fwe, axis=1)).T, "quadratic", 6).T

"""
Fb['CO2e'] = np.sum(Fb, axis=1)
Fpd['CO2e'] = np.sum(Fpd, axis=1)
Fcdr['CO2e'] = np.sum(Fcdr, axis=1)
"""

F19 = F19 * (hist.loc[:, 2020].values[0] / F19.loc[:, 2020].values[0])
Fb = Fb * (hist.loc[:, data_end_year].values[0] / Fb.loc[data_end_year, "CO2e"])
Fpd = Fpd * (hist.loc[:, data_end_year].values[0] / Fpd.loc[data_end_year, "CO2e"])
Fcdr = Fcdr * (hist.loc[:, data_end_year].values[0] / Fcdr.loc[data_end_year, "CO2e"])
Flp = Flp * (hist.loc[:, data_end_year].values[0] / Flp.loc[data_end_year, "CO2e"])
Fwe = Fwe * (hist.loc[:, data_end_year].values[0] / Fwe.loc[data_end_year, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Fb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=F19.loc[:, 2020:2100].columns,
        y=F19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="DAU21-LP",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Flp.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)
fig.add_trace(
    go.Scatter(
        name="DAU21-WE",
        line=dict(width=3, color="light blue", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fwe.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="we",
        legendgroup="we",
    )
)

fig.update_layout(
    title={"text": "Radiative Forcing", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "W/m2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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


# endregion

######################
# TEMPERATURE CHANGE #
######################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp85.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)
em_lp = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_we = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)

hist = pd.read_csv("podi/data/temp.csv")
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

"""
T19 = T.loc[
            "GCAM4",
            "SSP1-19",
            "World",
            ["Diagnostics|MAGICC6|Temperature|Global Mean"],
        ].loc[:, 2010:]
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_lp.loc[225:335, 1] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 1] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_lp.loc[225:335, 2] = (
    em_alt_lp[~em_alt_lp.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_we.loc[225:335, 2] = (
    em_alt_we[~em_alt_we.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_lp.loc[225:335, 3] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_we.loc[225:335, 3] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_lp.loc[225:335, 4] = (
    em_alt_lp[em_alt_lp.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_we.loc[225:335, 4] = (
    em_alt_we[em_alt_we.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_lp = em_lp.values
em_we = em_we.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_lp)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_we)

"""
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
"""
Tb = (
    pd.DataFrame(Tb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tpd = (
    pd.DataFrame(Tpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tcdr = (
    pd.DataFrame(Tcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tlp = (
    pd.DataFrame(Tlp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Twe = (
    pd.DataFrame(Twe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Tb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tb, axis=1)).T, "quadratic", 6).T
Tpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tpd, axis=1)).T, "quadratic", 6).T
Tcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tcdr, axis=1)).T, "quadratic", 6).T
Tlp["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tlp, axis=1)).T, "quadratic", 6).T
Twe["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Twe, axis=1)).T, "quadratic", 6).T

"""
Tb['CO2e'] = np.sum(Tb, axis=1)
Tpd['CO2e'] = np.sum(Tpd, axis=1)
Tcdr['CO2e'] = np.sum(Tcdr, axis=1)
"""

T19 = T19 * (hist.loc[:, 2020].values[0] / T19.loc[:, 2020].values[0])
Tb = Tb * (hist.loc[:, data_end_year].values[0] / Tb.loc[data_end_year, "CO2e"])
Tpd = Tpd * (hist.loc[:, data_end_year].values[0] / Tpd.loc[data_end_year, "CO2e"])
Tcdr = Tcdr * (hist.loc[:, data_end_year].values[0] / Tcdr.loc[data_end_year, "CO2e"])
Tlp = Tlp * (hist.loc[:, data_end_year].values[0] / Tlp.loc[data_end_year, "CO2e"])
Twe = Twe * (hist.loc[:, data_end_year].values[0] / Twe.loc[data_end_year, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Tb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=T19.loc[:, 2020:2100].columns,
        y=T19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="DAU21-LP",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tlp.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21-WE",
        line=dict(width=3, color="light blue", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Twe.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="we",
        legendgroup="we",
    )
)

fig.update_layout(
    title={"text": "Global Mean Temperature", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the Hector climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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

# endregion


# endregion

#################################################################
# //////////// MULTI-ALT-SCENARIO CLIMATE OUTCOMES  ////////////#
#################################################################

# region

altscen = "daurafw"
show_ra = False
show_fw = False
show_rafw = True

#################################
# CO2 ATMOSPHERIC CONCENTRATION #
#################################

# region

# Load RCP data, then swap in PD for main GHGs
em_b = pd.DataFrame(rcp60.Emissions.emissions)
em_pd = pd.DataFrame(rcp3pd.Emissions.emissions)
em_cdr = pd.DataFrame(rcp3pd.Emissions.emissions * 1.001)
em_ra = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_fw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)
em_rafw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.999)

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
"""
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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    6,
)
"""
results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_ra.loc[225:335, 1] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 1] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 1] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_ra.loc[225:335, 2] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 2] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 2] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_ra.loc[225:335, 3] = (
    em_alt_ra[em_alt_ra.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_fw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_rafw.loc[225:335, 3] = (
    em_alt_rafw[em_alt_rafw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_ra.loc[225:335, 4] = (
    em_alt_ra[em_alt_ra.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_fw.loc[225:335, 4] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_rafw.loc[225:335, 4] = (
    em_alt_rafw[em_alt_rafw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_ra = em_ra.values
em_fw = em_fw.values
em_rafw = em_rafw.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_ra, other_rf=other_rf)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_fw, other_rf=other_rf)
Crafw, Frafw, Trafw = fair.forward.fair_scm(emissions=em_rafw, other_rf=other_rf)

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Clp = (
    pd.DataFrame(Clp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cwe = (
    pd.DataFrame(Cwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Crafw = (
    pd.DataFrame(Crafw)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion (not needed here for just CO2)
Cb["CO2"] = Cb.loc[:, 0]
Cpd["CO2"] = Cpd.loc[:, 0]
Ccdr["CO2"] = Ccdr.loc[:, 0]
Clp["CO2"] = Clp.loc[:, 0]
Cwe["CO2"] = Cwe.loc[:, 0]
Crafw["CO2"] = Crafw.loc[:, 0]

C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2"])
Clp = Clp * (hist[2021] / Clp.loc[2021, "CO2"])
Cwe = Cwe * (hist[2021] / Cwe.loc[2021, "CO2"])
Crafw = Crafw * (hist[2021] / Crafw.loc[2021, "CO2"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2"],
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
        y=Cb.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="cdr",
        legendgroup="cdr",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)
if show_ra == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RA",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Clp.loc[data_end_year:, "CO2"],
            fill="none",
            stackgroup="26",
            legendgroup="26",
        )
    )

if show_fw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-FW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Cwe.loc[data_end_year:, "CO2"],
            fill="none",
            stackgroup="we",
            legendgroup="we",
        )
    )

if show_rafw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RAFW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Crafw.loc[data_end_year:, "CO2"],
            fill="none",
            stackgroup="rafw",
            legendgroup="rafw",
        )
    )


fig.update_layout(
    title={
        "text": "Atmospheric CO2 Concentration",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/co2conc-" + "World " + "-" + str(altscen) + ".html").replace(
            " ", ""
        ),
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
em_ra = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_fw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)
em_rafw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.999)

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
"""
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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    6,
)
"""
results19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_ra.loc[225:335, 1] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 1] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 1] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_ra.loc[225:335, 2] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 2] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 2] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_ra.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_fw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_rafw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_ra.loc[225:335, 4] = (
    em_alt_ra[em_alt_ra.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_fw.loc[225:335, 4] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_rafw.loc[225:335, 4] = (
    em_alt_rafw[em_alt_rafw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_ra = em_ra.values
em_fw = em_fw.values
em_rafw = em_rafw.values

other_rf = np.zeros(em_pd.shape[0])
for x in range(0, em_pd.shape[0]):
    other_rf[x] = 0.5 * np.sin(2 * np.pi * (x) / 14.0)


# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b, other_rf=other_rf)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd, other_rf=other_rf)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr, other_rf=other_rf)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_ra, other_rf=other_rf)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_fw, other_rf=other_rf)
Crafw, Frafw, Trafw = fair.forward.fair_scm(emissions=em_rafw, other_rf=other_rf)

Cb = (
    pd.DataFrame(Cb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cpd = (
    pd.DataFrame(Cpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Ccdr = (
    pd.DataFrame(Ccdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Clp = (
    pd.DataFrame(Clp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Cwe = (
    pd.DataFrame(Cwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Crafw = (
    pd.DataFrame(Crafw)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion
Cb["CO2e"] = Cb.loc[:, 0] + Cb.loc[:, 1] * 25e-3 + Cb.loc[:, 2] * 298e-3
Cpd["CO2e"] = Cpd.loc[:, 0] + Cpd.loc[:, 1] * 25e-3 + Cpd.loc[:, 2] * 298e-3
Ccdr["CO2e"] = Ccdr.loc[:, 0] + Ccdr.loc[:, 1] * 25e-3 + Ccdr.loc[:, 2] * 298e-3
Clp["CO2e"] = Clp.loc[:, 0] + Clp.loc[:, 1] * 25e-3 + Clp.loc[:, 2] * 298e-3
Cwe["CO2e"] = Cwe.loc[:, 0] + Cwe.loc[:, 1] * 25e-3 + Cwe.loc[:, 2] * 298e-3
Crafw["CO2e"] = Crafw.loc[:, 0] + Crafw.loc[:, 1] * 25e-3 + Crafw.loc[:, 2] * 298e-3

C19 = results19 * (hist[2021] / results19.loc[:, 2021].values[0])
Cb = Cb * (hist[2021] / Cb.loc[2021, "CO2e"])
Cpd = Cpd * (hist[2021] / Cpd.loc[2021, "CO2e"])
Ccdr = Ccdr * (hist[2021] / Ccdr.loc[2021, "CO2e"])
Clp = Clp * (hist[2021] / Clp.loc[2021, "CO2e"])
Cwe = Cwe * (hist[2021] / Cwe.loc[2021, "CO2e"])
Crafw = Crafw * (hist[2021] / Crafw.loc[2021, "CO2e"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=Cpd.loc[:, "CO2e"],
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
        y=Cb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Ccdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="cdr",
        legendgroup="cdr",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

if show_ra == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RA",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Clp.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="26",
            legendgroup="26",
        )
    )

if show_fw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-FW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Cwe.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="we",
            legendgroup="we",
        )
    )

if show_rafw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RAFW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Crafw.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="rafw",
            legendgroup="rafw",
        )
    )

fig.update_layout(
    title={
        "text": "Atmospheric GHG Concentration",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.95,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2e"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/ghgconc-" + "World " + "-" + str(altscen) + ".html").replace(
            " ", ""
        ),
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
em_ra = pd.DataFrame(rcp3pd.Emissions.emissions * 1.002)
em_fw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)
em_rafw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.999)


hist = pd.read_csv("podi/data/forcing.csv")
hist.columns = hist.columns.astype(int)

F = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
F.columns = F.columns.astype(int)

F19 = curve_smooth(
    pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:]
    ),
    "quadratic",
    6,
)

"""
F19 = pd.DataFrame(
        F.loc[
            "GCAM4",
            "SSP2-19",
            "World",
            ["Diagnostics|MAGICC6|Forcing"],
        ].loc[:, 2010:])
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_ra.loc[225:335, 1] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 1] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 1] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_ra.loc[225:335, 2] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 2] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 2] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_ra.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_fw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_rafw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_ra.loc[225:335, 4] = (
    em_alt_ra[em_alt_ra.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_fw.loc[225:335, 4] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_rafw.loc[225:335, 4] = (
    em_alt_rafw[em_alt_rafw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_ra = em_ra.values
em_fw = em_fw.values
em_rafw = em_rafw.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_ra)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_fw)
Crafw, Frafw, Trafw = fair.forward.fair_scm(emissions=em_rafw)

Fb = (
    pd.DataFrame(Fb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fpd = (
    pd.DataFrame(Fpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fcdr = (
    pd.DataFrame(Fcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Flp = (
    pd.DataFrame(Flp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Fwe = (
    pd.DataFrame(Fwe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Frafw = (
    pd.DataFrame(Frafw)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Fb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fb, axis=1)).T, "quadratic", 6).T
Fpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fpd, axis=1)).T, "quadratic", 6).T
Fcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fcdr, axis=1)).T, "quadratic", 6).T
Flp["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Flp, axis=1)).T, "quadratic", 6).T
Fwe["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Fwe, axis=1)).T, "quadratic", 6).T
Frafw["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Frafw, axis=1)).T, "quadratic", 6).T


F19 = F19 * (hist.loc[:, 2020].values[0] / F19.loc[:, 2020].values[0])
Fb = Fb * (hist.loc[:, data_end_year].values[0] / Fb.loc[data_end_year, "CO2e"])
Fpd = Fpd * (hist.loc[:, data_end_year].values[0] / Fpd.loc[data_end_year, "CO2e"])
Fcdr = Fcdr * (hist.loc[:, data_end_year].values[0] / Fcdr.loc[data_end_year, "CO2e"])
Flp = Flp * (hist.loc[:, data_end_year].values[0] / Flp.loc[data_end_year, "CO2e"])
Fwe = Fwe * (hist.loc[:, data_end_year].values[0] / Fwe.loc[data_end_year, "CO2e"])
Frafw = Frafw * (
    hist.loc[:, data_end_year].values[0] / Frafw.loc[data_end_year, "CO2e"]
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Fb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="cdr",
        legendgroup="cdr",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=F19.loc[:, 2020:2100].columns,
        y=F19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

if show_ra == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RA",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Flp.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="26",
            legendgroup="26",
        )
    )

if show_fw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-FW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Fwe.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="we",
            legendgroup="we",
        )
    )

if show_rafw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RAFW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Frafw.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="rafw",
            legendgroup="rafw",
        )
    )

fig.update_layout(
    title={"text": "Radiative Forcing", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "W/m2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the FAIR v1.3 climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/forcing-" + "World" + "-" + str(altscen) + ".html").replace(
            " ", ""
        ),
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
em_ra = pd.DataFrame(rcp3pd.Emissions.emissions * 0.995)
em_fw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.998)
em_rafw = pd.DataFrame(rcp3pd.Emissions.emissions * 0.999)

hist = pd.read_csv("podi/data/temp.csv")
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

"""
T19 = T.loc[
            "GCAM4",
            "SSP1-19",
            "World",
            ["Diagnostics|MAGICC6|Temperature|Global Mean"],
        ].loc[:, 2010:]
"""

# CO2
em_b.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 1] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values - (cdr.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values
em_ra.loc[225:335, 1] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 1] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 1] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Electricity", "Transport", "Buildings", "Industry"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

em_b.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "baseline",
    ]
    .sum()
    / 3670
).values
em_pd.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_cdr.loc[225:335, 2] = (
    em[~em.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_ra.loc[225:335, 2] = (
    em_alt_ra[~em_alt_ra.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_fw.loc[225:335, 2] = (
    em_alt_fw[~em_alt_fw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values
em_rafw.loc[225:335, 2] = (
    em_alt_rafw[~em_alt_rafw.index.get_level_values(3).isin(["CH4", "N2O", "F-gases"])]
    .loc[
        "World ",
        ["Forests & Wetlands", "Regenerative Agriculture"],
        slice(None),
        "CO2",
        "pathway",
    ]
    .sum()
    / 3670
).values

# CH4
em_b.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_pd.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_cdr.loc[225:335, 3] = (
    em[em.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_ra.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_fw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values
em_rafw.loc[225:335, 3] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["CH4"])]
    .loc["World ", slice(None), slice(None), "CH4", "pathway"]
    .sum()
    / (25)
).values

# N2O
em_b.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_pd.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_cdr.loc[225:335, 4] = (
    em[em.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_ra.loc[225:335, 4] = (
    em_alt_ra[em_alt_ra.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_fw.loc[225:335, 4] = (
    em_alt_fw[em_alt_fw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values
em_rafw.loc[225:335, 4] = (
    em_alt_rafw[em_alt_rafw.index.get_level_values(3).isin(["N2O"])]
    .loc["World ", slice(None), slice(None), "N2O", "pathway"]
    .sum()
    / (298)
).values

em_b = em_b.values
em_pd = em_pd.values
em_cdr = em_cdr.values
em_ra = em_ra.values
em_fw = em_fw.values
em_rafw = em_rafw.values

other_rf = np.zeros(em_pd.shape[0])

# run the model
Cb, Fb, Tb = fair.forward.fair_scm(emissions=em_b)
Cpd, Fpd, Tpd = fair.forward.fair_scm(emissions=em_pd)
Ccdr, Fcdr, Tcdr = fair.forward.fair_scm(emissions=em_cdr)
Clp, Flp, Tlp = fair.forward.fair_scm(emissions=em_ra)
Cwe, Fwe, Twe = fair.forward.fair_scm(emissions=em_fw)
Crafw, Frafw, Trafw = fair.forward.fair_scm(emissions=em_rafw)

Tb = (
    pd.DataFrame(Tb)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tpd = (
    pd.DataFrame(Tpd)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tcdr = (
    pd.DataFrame(Tcdr)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Tlp = (
    pd.DataFrame(Tlp)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Twe = (
    pd.DataFrame(Twe)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)
Trafw = (
    pd.DataFrame(Trafw)
    .loc[225:335]
    .set_index(np.arange(data_start_year, (long_proj_end_year + 1), 1))
)

# CO2e conversion

Tb["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tb, axis=1)).T, "quadratic", 6).T
Tpd["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tpd, axis=1)).T, "quadratic", 6).T
Tcdr["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tcdr, axis=1)).T, "quadratic", 6).T
Tlp["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Tlp, axis=1)).T, "quadratic", 6).T
Twe["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Twe, axis=1)).T, "quadratic", 6).T
Trafw["CO2e"] = curve_smooth(pd.DataFrame(np.sum(Trafw, axis=1)).T, "quadratic", 6).T

T19 = T19 * (hist.loc[:, 2020].values[0] / T19.loc[:, 2020].values[0])
Tb = Tb * (hist.loc[:, data_end_year].values[0] / Tb.loc[data_end_year, "CO2e"])
Tpd = Tpd * (hist.loc[:, data_end_year].values[0] / Tpd.loc[data_end_year, "CO2e"])
Tcdr = Tcdr * (hist.loc[:, data_end_year].values[0] / Tcdr.loc[data_end_year, "CO2e"])
Tlp = Tlp * (hist.loc[:, data_end_year].values[0] / Tlp.loc[data_end_year, "CO2e"])
Twe = Twe * (hist.loc[:, data_end_year].values[0] / Twe.loc[data_end_year, "CO2e"])
Trafw = Trafw * (
    hist.loc[:, data_end_year].values[0] / Trafw.loc[data_end_year, "CO2e"]
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
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
        y=Tb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color="green", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="DAU21+CDR",
        line=dict(width=3, color="yellow", dash="dot"),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="cdr",
        legendgroup="cdr",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="#17BECF", dash="dot"),
        x=T19.loc[:, 2020:2100].columns,
        y=T19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

if show_ra == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RA",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Tlp.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="26",
            legendgroup="26",
        )
    )

if show_fw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-FW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Twe.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="we",
            legendgroup="we",
        )
    )

if show_rafw == True:
    fig.add_trace(
        go.Scatter(
            name="DAU21-RAFW",
            line=dict(width=3, color="purple", dash="dot"),
            x=np.arange(data_end_year, long_proj_end_year + 1, 1),
            y=Trafw.loc[data_end_year:, "CO2e"],
            fill="none",
            stackgroup="rafw",
            legendgroup="rafw",
        )
    )

fig.update_layout(
    title={"text": "Global Mean Temperature", "xanchor": "center", "x": 0.5, "y": 0.95},
    xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0, font=dict(size=10)),
    margin_b=80,
)

fig.add_annotation(
    text="Historical data is from NASA; projected data is from projected emissions input into the Hector climate model.",
    xref="paper",
    yref="paper",
    x=0,
    y=-0.27,
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
        file=("./charts/temp-" + "World" + "-" + str(altscen) + ".html").replace(
            " ", ""
        ),
        auto_open=False,
    )

# endregion

# endregion

#########################################
# //////////// NOT YET USED ////////////#
#########################################


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
        "V7 Adoption, " + region_list[i].replace(" ", "") + ", " + str(data_end_year)
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

##########################
# AFOLU PERCENT ADOPTION #
##########################

# region
scenario = scenario

for i in range(0, len(region_list)):
    plt.figure(i)
    plt.plot(
        afolu_per_adoption.loc[region_list[i], slice(None), slice(None), scenario].T
    )

# endregion