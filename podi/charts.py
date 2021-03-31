#!/usr/bin/env python

# region

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
import pyhector
from pyhector import rcp19, rcp26, rcp45, rcp60, rcp85
from podi.energy_demand import iea_region_list, data_end_year, data_start_year
from podi.energy_supply import (
    near_proj_start_year,
    near_proj_end_year,
    long_proj_start_year,
    long_proj_end_year,
)
from pandas_datapackage_reader import read_datapackage
from shortcountrynames import to_name
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from itertools import chain, zip_longest
from math import ceil, pi, nan
from kneed import DataGenerator, KneeLocator
from podi.curve_smooth import curve_smooth
from numpy import NaN

unit_name = ["TWh", "EJ", "TJ", "Mtoe", "Ktoe"]
unit_val = [1, 0.00360, 3600, 0.086, 86]
unit = [unit_name[0], unit_val[0]]

save_figs = True
show_figs = True
start_year = 2000

annotation_source = [
    "Historical data is from IEA WEO 2020, projections are based on PD21 growth rate assumptions applied to IEA WEO projections for 2020-2040 and GCAM scenario x for 2040-2100"
]

iea_region_list = iea_region_list

# endregion

#######################################
# ENERGY DEMAND BY SECTOR AND END-USE #
#######################################

# region

scenario = "baseline"
start_year = 2000

for i in range(0, len(iea_region_list)):
    energy_demand_i = (
        energy_demand.loc[iea_region_list[i], slice(None), slice(None), scenario]
        * unit[1]
    ).loc[:, start_year:]

    if iea_region_list[i] == "World ":
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
            "text": "Energy Demand, " + iea_region_list[i] + ", " + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(
        x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0
    )

    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=(-0.1, 0.1),
        y=-0.3,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
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
                "./charts/demand-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

#####################################
# ENERGY SUPPLY BY SOURCE & END-USE #
#####################################

# region

scenario = "pathway"
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

for i in range(0, len(iea_region_list)):
    elec_consump_i = (
        elec_consump.loc[iea_region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    elec_consump_i = pd.concat([elec_consump_i], keys=["Electricity"], names=["Sector"])
    heat_consump_i = (
        heat_consump.loc[iea_region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    heat_consump_i = pd.concat([heat_consump_i], keys=["Heat"], names=["Sector"])
    transport_consump_i = (
        transport_consump.loc[iea_region_list[i], slice(None), scenario]
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
            "text": "Energy Supply, " + iea_region_list[i] + ", " + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(
        x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=[-0.1, 0.1],
        y=-0.3,
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
                + iea_region_list[i].replace(" ", "")
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

start_year = start_year
scenario = "pathway"

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


for i in range(0, len(iea_region_list)):
    elec_consump_i = (
        elec_consump.loc[iea_region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    elec_consump_i = pd.concat(
        [elec_consump_i], keys=["Electricity"], names=["Sector"]
    )
    heat_consump_i = (
        heat_consump.loc[iea_region_list[i], slice(None), scenario]
        .groupby("Metric")
        .sum()
    )
    heat_consump_i = pd.concat([heat_consump_i], keys=["Heat"], names=["Sector"])
    transport_consump_i = (
        transport_consump.loc[iea_region_list[i], slice(None), scenario]
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
            + iea_region_list[i].replace(" ", "")
            + ", "
            + scenario.title(),
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "TFC, " + unit[0]},
    )

    fig.add_vrect(x0=start_year, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (shaded gray) is from IEA World Energy Balance 2020; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100",
        xref="paper",
        yref="paper",
        x=[-0.1, 0.1],
        y=-0.3,
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
                + iea_region_list[i]
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

##############################
# ELECTRICITY PERCENT ADOPTION
##############################

# region
scenario = "pathway"

for i in range(0, len(iea_region_list)):
    fig = elec_per_adoption.loc[iea_region_list[i], slice(None), scenario]
    plt.figure(i)
    plt.plot(fig.T)
    plt.legend(fig.T)
    plt.title(iea_region_list[i])
    elec_per_adoption.loc[iea_region_list[i], slice(None), scenario].loc[:, 2019]

# endregion

#######################
# HEAT PERCENT ADOPTION
#######################

# region
scenario = "pathway"

for i in range(0, len(iea_region_list)):
    plt.figure(i)
    plt.plot(heat_per_adoption.loc[iea_region_list[i], slice(None), scenario].T)
    plt.legend(heat_per_adoption.loc[iea_region_list[i], slice(None), scenario].T)
    plt.title(iea_region_list[i])

# endregion

####################################
# NONELEC TRANSPORT PERCENT ADOPTION
####################################

# region
scenario = "pathway"

for i in range(0, len(iea_region_list)):
    plt.figure(i)
    plt.plot(transport_per_adoption.loc[iea_region_list[i], slice(None), scenario].T)
    plt.legend(transport_per_adoption.loc[iea_region_list[i], slice(None), scenario].T)
    plt.title(iea_region_list[i])

# endregion

###################
# ADOPTION CURVES #
###################

# region

scenario = "baseline"
start_year = start_year

for i in range(0, len(iea_region_list)):
    fig = (
        adoption_curves.loc[iea_region_list[i], slice(None), scenario].loc[
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
            name="Transport",
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
            name="Buildings",
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
            name="Industry",
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
            name="Regenerative Agriculture",
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
            name="Forests & Wetlands",
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
            name="Other Gases",
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
            name="Electricity",
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
            name="Transport",
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
            name="Buildings",
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
            name="Industry",
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
            name="Regenerative Agriculture",
            line=dict(width=3, color="#72B7B2", dash="dot"),
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
            name="Forests & Wetlands",
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

    fig.add_trace(
        go.Scatter(
            name="Other Gases",
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

    if iea_region_list[i] == "World ":
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

    fig.update_layout(
        title={
            "text": "Percent of Total PD Adoption, " + scenario + ', ' + iea_region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% Adoption"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Adoption rates are represented as:"
        + "<br>"
        + "<b>Electricity, Transport, Buildings, and Industry</b>: percent of energy demand from renewable resources"
        + "<br>"
        + "<b>Regenerative Agriculture and Forests & Wetlands</b>: percent of maximum estimated extent of mitigation available"
        + "<br>"
        + "<b>CDR</b>: percent of maximum CDR estimated to meet emissions targets",
        xref="paper",
        yref="paper",
        x=0,
        y=-0.3,
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

    fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/scurves-" + iea_region_list[i] + "-" + scenario + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

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
        adoption_curves.loc[iea_region_list[i], slice(None), scenario].loc[:, 2015:2025]
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
            line=dict(width=3, color="#72B7B2", dash="dot"),
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
            line=dict(width=3, color="#72B7B2", dash="dashdot"),
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
            line=dict(width=3, color="#72B7B2", dash="dot"),
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
    if iea_region_list[i] == "World ":
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
            "text": "Percent of Total PD Adoption, " + iea_region_list[i],
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

fig_type == ""
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


for i in range(0, len(iea_region_list)):
    fig = adoption_curves.loc[iea_region_list[i], slice(None), scenario] * 100

    data = [
        ("Grid", fig.loc["Grid", year]),
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
        + iea_region_list[i].replace(" ", "")
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
                file=("./charts/star-" + iea_region_list[i] + ".html").replace(" ", ""),
                auto_open=False,
            )

# endregion

##############################
# ADOPTION CURVES KNEE/ELBOW #
##############################

# region

for i in range(0, len(iea_region_list)):
    fig = adoption_curves.loc[iea_region_list[i], slice(None), scenario] * 100
    kneedle = KneeLocator(
        fig.columns,
        fig.loc["Grid"].values,
        S=1.0,
        curve="concave",
        direction="increasing",
    )

# endregion

#############
# EMISSIONS #
#############

# region

scenario = "pathway"
start_year = 2000

for i in range(0, len(iea_region_list)):
    if scenario == "baseline":
        em = em_baseline
    else:
        em = em_pathway

    em_electricity = (
        em.loc[iea_region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[iea_region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[iea_region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            iea_region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        em.loc[
            iea_region_list[i],
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
            iea_region_list[i],
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
        em.loc[iea_region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[iea_region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[iea_region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[iea_region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    if iea_region_list[i] == "World ":
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
    if iea_region_list[i] == "World ":
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
            line=dict(width=0.5, color="#72B7B2"),
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
                em_hist.loc[iea_region_list[i]].loc[:, start_year:].values[0] / 1000
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
            "text": "Emissions, " + scenario.title() + ", " + iea_region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (shaded gray) is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100;"
        + "<br>"
        + " emissions factors are from IEA Emissions Factors 2020.",
        xref="paper",
        yref="paper",
        x=(-0.1, 0.1),
        y=-0.35,
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
                "./charts/em2-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

###########################
# EMISSIONS AS RELATIVE % #
###########################

# region

scenario = "pathway"
start_year = 2000

for i in range(0, len(iea_region_list)):
    if scenario == "baseline":
        em = em_baseline
    else:
        em = em_pathway

    em_electricity = (
        em.loc[iea_region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[iea_region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[iea_region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            iea_region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        em.loc[
            iea_region_list[i],
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
            iea_region_list[i],
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
        em.loc[iea_region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[iea_region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[iea_region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[iea_region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    if iea_region_list[i] == "World ":
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
    if iea_region_list[i] == "World ":
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
            name="Agriculture",
            line=dict(width=0.5, color="#72B7B2"),
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
            name="Other Gases",
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

    fig.update_layout(
        title={
            "text": "Emissions, " + scenario.title() + ", " + iea_region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "% of Total Emissions"},
    )

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100;"
        + "<br>"
        + " emissions factors are from IEA Emissions Factors 2020.",
        xref="paper",
        yref="paper",
        x=-0.1,
        y=-0.3,
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
                "./charts/em3-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

##############
# EPIC INDEX #
##############

# region

scenario = "pathway"
start_year = 1990

for i in range(0, len(iea_region_list)):
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
        em.loc[iea_region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[iea_region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[iea_region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            iea_region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        afolu_em.loc[
            iea_region_list[i],
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
            iea_region_list[i],
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
        em.loc[iea_region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[iea_region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[iea_region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[iea_region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )
    """
    em_total = em_total.loc[iea_region_list[i], "CO2", scenario]
    """

    em_total = em_total.loc[iea_region_list[i], slice(None), slice(None), scenario]

    if iea_region_list[i] == "World ":
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

    ei = em_total.loc[:, data_end_year:2020].values / (em.sum().loc[data_end_year:2020])

    fig2 = ei

    # fig2.index.name = "Year"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="EI",
            line=dict(width=4, color="#72B7B2"),
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
            "text": "Epic Index, " + scenario.title() + ", " + iea_region_list[i],
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
        y=-0.3,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        borderwidth=2,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_shapes(dict(xref="x", yref="y"))

    """
    fig.add_vrect(x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0)
    """

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/ei-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()


# endregion

##########################
# EPIC INDEX ALL REGIONS #
##########################

# region

scenario = "pathway"
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
        em.loc[iea_region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[iea_region_list[i], "Transport", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[iea_region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[
            iea_region_list[i],
            ["Industry"],
            slice(None),
        ]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ra = (
        afolu_em.loc[
            iea_region_list[i],
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
            iea_region_list[i],
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
        em.loc[iea_region_list[i], "Other", ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[iea_region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[iea_region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[iea_region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[start_year:long_proj_end_year]
    )
    """
    em_total = em_total.loc[iea_region_list[i], "CO2", scenario]
    """

    em_total = em_total.loc[iea_region_list[i], slice(None), slice(None), scenario]

    if iea_region_list[i] == "World ":
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

    # fig2.index.name = "Year"

    fig = go.Figure()

    fig.add_trace(
        go.bar(
            name="EI",
            line=dict(width=4, color="#72B7B2"),
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
            "text": "Epic Index, " + scenario.title() + ", " + iea_region_list[i],
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
        y=-0.3,
        showarrow=False,
        font=dict(size=10, color="#2E3F5C"),
        align="left",
        borderpad=4,
        borderwidth=2,
        bgcolor="#ffffff",
        opacity=1,
    )

    fig.update_shapes(dict(xref="x", yref="y"))

    """
    fig.add_vrect(x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0)
    """

    if show_figs is True:
        fig.show()
    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/ei-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()


# endregion

###########################
# MITIGATION WEDGES CURVE #
###########################

# region

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
    (3, 3),
    (3, 3),
    (2030, 0.13),
    (3, 3),
    (2030, 2.67),
    (3, 3),
    (2030, 12.96),
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

scenario = "pathway"

for i in range(0, len(iea_region_list)):
    em_mit_electricity = em_mitigated.loc[
        iea_region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[
        iea_region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated.loc[
        iea_region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated.loc[
        iea_region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated.loc[
        iea_region_list[i],
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
        iea_region_list[i],
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

    em_mit_othergas = em_mitigated.loc[iea_region_list[i], "Other", :].sum()

    em_mit_ch4 = em_mitigated.loc[iea_region_list[i], "Other", "CH4"].rename("CH4")

    em_mit_n2o = em_mitigated.loc[iea_region_list[i], "Other", "N2O"].rename("N2O")

    em_mit_fgas = em_mitigated.loc[iea_region_list[i], "Other", "F-gases"].rename(
        "F-gases"
    )

    if iea_region_list[i] == "World ":
        em_mit_cdr = cdr.loc[slice(None), scenario, :].squeeze().rename("CDR")
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
                    em_mit_othergas,
                    em_mit_fgas,
                ]
            )
            .clip(lower=0)
            .rename(
                index={
                    "Unnamed 0": "Electricity",
                    "Unnamed 1": "Transport",
                    "Unnamed 2": "Buildings",
                    "Unnamed 3": "Industry",
                    "Unnamed 4": "Forests & Wetlands",
                    "Unnamed 5": "Agriculture",
                    "Unnamed 6": "Other Gases",
                }
            )
        )

    spacer = (
        pd.Series(
            em_baseline.groupby("Region").sum().loc[iea_region_list[i]] - em_mit.sum()
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

    if iea_region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="CDR",
                line=dict(width=0.5, color="#FF9DA6"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
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
            name="Other Gases",
            line=dict(width=0.5, color="#E45756"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Other Gases"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Agriculture",
            line=dict(width=0.5, color="#72B7B2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Electricity",
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
            y=pd.Series(em_hist.loc[iea_region_list[i], :].values[0] / 1000),
            fill="none",
            stackgroup="two",
        )
    )

    # Targets/NDCS

    # region
    if iea_region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="SSP2-1.9",
                line=dict(width=2, color="light blue", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-19", near_proj_start_year:].index.values
                ),
                y=pd.Series(em_targets.loc["SSP2-19", near_proj_start_year:].values),
                fill="none",
                stackgroup="three",
            )
        )

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
                        + cdr.loc[slice(None), scenario, :]
                        .loc[:, near_proj_start_year:]
                        .values[0]
                    )
                    / 1000
                ),
                fill="none",
                stackgroup="five",
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
            name="Baseline",
            line=dict(width=2, color="red", dash="dot"),
            x=pd.Series(em_targets.loc["SSP2-26", near_proj_start_year:].index.values),
            y=pd.Series(
                em_baseline.loc[:, near_proj_start_year:]
                .groupby("Region")
                .sum()
                .loc[iea_region_list[i]]
                / 1000
            ),
            fill="none",
            stackgroup="six",
        )
    )

    if iea_region_list[i] in ["World ", "US "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][0]],
                y=[ndcs[i][1][0]],
                marker_color="#FF7F0E",
                name=ndcs[i][2][0],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#FC0080",
                name=ndcs[i][2][1],
            )
        )

    if iea_region_list[i] in ["US "]:
        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][2]],
                y=[ndcs[i][1][2]],
                marker_color="#750D86",
                name=ndcs[i][2][2],
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][3]],
                y=[ndcs[i][1][3]],
                marker_color="#16FF32",
                name=ndcs[i][2][3],
            )
        )

        fig.add_annotation(
            text="The NDC commitment is to " + ndc_commit[i][0],
            xref="paper",
            yref="paper",
            x=0,
            y=-0.3,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="center",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    if iea_region_list[i] in [
        "SAFR ",
        "RUS ",
        "JPN ",
        "CHINA ",
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
            text="The NDC commitment is to " + ndc_commit[i][0],
            xref="paper",
            yref="paper",
            x=0,
            y=-0.3,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="center",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

    # endregion

    fig.update_layout(
        title={
            "text": "Emissions Mitigated, " + iea_region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    """
    fig.add_vrect(x0=start_year, x1=data_end_year, fillcolor="grey", opacity=0.6, line_width=0)
    """

    fig.update_layout(margin=dict())
    fig.add_annotation(
        text="Historical data (black) is from Global Carbon Project; projections are based on PD21 technology adoption rate assumptions applied to"
        + "<br>"
        + " IEA World Energy Outlook 2020 projections for 2020-2040, and Global Change Assessment Model Baseline Limited Technology Scenario for 2040-2100;"
        + "<br>"
        + " emissions factors are from IEA Emissions Factors 2020.",
        xref="paper",
        yref="paper",
        x=-0.1,
        y=-0.3,
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
                "./charts/mwedges-" + "pathway" + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    plt.clf()

# endregion

#################################
# EMISSIONS MITIGATION BARCHART #
#################################

# region

for year in [2030, 2050]:
    for i in range(0, len(iea_region_list)):
        em_mit_electricity = em_mitigated.loc[
            iea_region_list[i], "Electricity", slice(None)
        ].sum()

        em_mit_transport = em_mitigated.loc[
            iea_region_list[i], "Transport", slice(None)
        ].sum()

        em_mit_buildings = em_mitigated.loc[
            iea_region_list[i], "Buildings", slice(None)
        ].sum()

        em_mit_industry = em_mitigated.loc[
            iea_region_list[i], "Industry", slice(None)
        ].sum()

        em_mit_ra = em_mitigated.loc[
            iea_region_list[i],
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
            iea_region_list[i],
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

        em_mit_othergas = em_mitigated.loc[iea_region_list[i], "Other", :].sum()

        em_mit_cdr = pd.Series(
            cdr_pathway.sum(), index=np.arange(data_start_year, long_proj_end_year + 1)
        )

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
                0: "Electricity",
                1: "Transport",
                2: "Buildings",
                3: "Industry",
                4: "Forests & Wetlands",
                5: "Agriculture",
                6: "CH4, N2O, F-gases",
                7: "CDR",
            }
        )

        em_mit.loc[:, :2020] = 0

        if iea_region_list[i] == "World ":
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "CDR",
                        "CH4, N2O, F-gases",
                        "Agriculture",
                        "Forests & Wetlands",
                        "Industry",
                        "Buildings",
                        "Transport",
                        "Electricity",
                    ]
                )
                .round(decimals=4)
                .clip(lower=0)
            )

            data = {
                "Electricity": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Electricity", year],
                    fig.loc["Electricity", year],
                ],
                "Transport": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Transport", year],
                    0,
                    fig.loc["Transport", year],
                ],
                "Buildings": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Buildings", year],
                    0,
                    0,
                    fig.loc["Buildings", year],
                ],
                "Industry": [
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Industry", year],
                    0,
                    0,
                    0,
                    fig.loc["Industry", year],
                ],
                "Forests & Wetlands": [
                    0,
                    0,
                    0,
                    fig.loc["Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Forests & Wetlands", year],
                ],
                "Agriculture": [
                    0,
                    0,
                    fig.loc["Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Agriculture", year],
                ],
                "CH4, N2O, F-gases": [
                    0,
                    fig.loc["CH4, N2O, F-gases", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["CH4, N2O, F-gases", year],
                ],
                "CDR": [
                    fig.loc["CDR", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["CDR", year],
                ],
                "Total": [
                    0,
                    fig.loc["Electricity", year],
                    fig.loc["Transport", year],
                    fig.loc["Buildings", year],
                    fig.loc["Industry", year],
                    fig.loc["Forests & Wetlands", year],
                    fig.loc["Agriculture", year],
                    0,
                    0,
                ],
                "labels": [
                    "CDR",
                    "CH4, N2O, F-gases",
                    "Agriculture",
                    "Forests & Wetlands",
                    "Industry",
                    "Buildings",
                    "Transport",
                    "Electricity",
                    "Total",
                ],
            }
        else:
            fig = (
                ((em_mit) / 1000)
                .reindex(
                    [
                        "CH4, N2O, F-gases",
                        "Agriculture",
                        "Forests & Wetlands",
                        "Industry",
                        "Buildings",
                        "Transport",
                        "Electricity",
                    ]
                )
                .round(decimals=4)
                .clip(lower=0)
            )

            data = {
                "Electricity": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Electricity", year],
                    fig.loc["Electricity", year],
                ],
                "Transport": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Transport", year],
                    0,
                    fig.loc["Transport", year],
                ],
                "Buildings": [
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Buildings", year],
                    0,
                    0,
                    fig.loc["Buildings", year],
                ],
                "Industry": [
                    0,
                    0,
                    0,
                    fig.loc["Industry", year],
                    0,
                    0,
                    0,
                    fig.loc["Industry", year],
                ],
                "Forests & Wetlands": [
                    0,
                    0,
                    fig.loc["Forests & Wetlands", year],
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Forests & Wetlands", year],
                ],
                "Agriculture": [
                    0,
                    fig.loc["Agriculture", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["Agriculture", year],
                ],
                "CH4, N2O, F-gases": [
                    fig.loc["CH4, N2O, F-gases", year],
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    fig.loc["CH4, N2O, F-gases", year],
                ],
                "Total": [
                    0,
                    fig.loc["Electricity", year],
                    fig.loc["Transport", year],
                    fig.loc["Buildings", year],
                    fig.loc["Industry", year],
                    fig.loc["Forests & Wetlands", year],
                    fig.loc["Agriculture", year],
                    0,
                ],
                "labels": [
                    "CH4, N2O, F-gases",
                    "Agriculture",
                    "Forests & Wetlands",
                    "Industry",
                    "Buildings",
                    "Transport",
                    "Electricity",
                    "Total",
                ],
            }

        opacity = 0.5

        if iea_region_list[i] == "World ":
            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["CDR"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#B82E2E",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["CH4, N2O, F-gases"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#E45756",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#72B7B2",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Industry"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#60738C",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Buildings"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#F58518",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Transport"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#7AA8B8",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Electricity"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#B279A2",
                        opacity=opacity,
                    ),
                ]
            )
        else:
            figure = go.Figure(
                data=[
                    go.Bar(
                        y=data["labels"],
                        x=data["CH4, N2O, F-gases"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#E45756",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Agriculture"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#72B7B2",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Forests & Wetlands"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#54A24B",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Industry"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#60738C",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Buildings"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#F58518",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Transport"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#7AA8B8",
                        opacity=opacity,
                    ),
                    go.Bar(
                        y=data["labels"],
                        x=data["Electricity"],
                        offsetgroup=0,
                        orientation="h",
                        marker_color="#B279A2",
                        opacity=opacity,
                    ),
                ]
            )

        if year == 2030:
            j = 0
        else:
            j = 1

        if iea_region_list[i] in [
            "US ",
            "SAFR ",
            "RUS ",
            "JPN ",
            "CHINA ",
            "BRAZIL ",
            "INDIA ",
        ]:
            figure.add_shape(
                type="line",
                x0=em_mit_ndc[
                    (em_mit_ndc["Region"] == iea_region_list[i])
                    & (em_mit_ndc.index == year)
                ]["em_mit"].values[0],
                y0=-0.5,
                x1=em_mit_ndc[
                    (em_mit_ndc["Region"] == iea_region_list[i])
                    & (em_mit_ndc.index == year)
                ]["em_mit"].values[0],
                y1=7.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="NDC",
            )

            figure.add_trace(
                go.Scatter(
                    x=[
                        em_mit_ndc[
                            (em_mit_ndc["Region"] == iea_region_list[i])
                            & (em_mit_ndc.index == year)
                        ]["em_mit"].values[0]
                        * 0.9
                    ],
                    y=["CH4, N2O, F-gases"],
                    text=["NDC " + str(year)],
                    mode="text",
                    showlegend=False,
                )
            )

        if iea_region_list[i] == "World ":
            figure.add_shape(
                type="line",
                x0=em_mit_ndc[
                    (em_mit_ndc["Region"] == iea_region_list[i])
                    & (em_mit_ndc.index == year)
                ]["em_mit"].values[0],
                y0=-0.5,
                x1=em_mit_ndc[
                    (em_mit_ndc["Region"] == iea_region_list[i])
                    & (em_mit_ndc.index == year)
                ]["em_mit"].values[0],
                y1=8.5,
                line=dict(color="LightSeaGreen", width=3, dash="dot"),
                name="Target",
            )

            figure.add_trace(
                go.Scatter(
                    x=[
                        em_mit_ndc[
                            (em_mit_ndc["Region"] == iea_region_list[i])
                            & (em_mit_ndc.index == year)
                        ]["em_mit"].values[0]
                        * 0.9
                    ],
                    y=["CDR"],
                    text=["NDC " + str(year)],
                    mode="text",
                    showlegend=False,
                )
            )

            figure.update_layout(margin=dict())
            figure.add_annotation(
                text="Emissions mitigation target values represent a 50% reduction in the year 2030, and net-zero emissions in the year 2050.",
                xref="paper",
                yref="paper",
                x=-0.1,
                y=-0.3,
                showarrow=False,
                font=dict(size=10, color="#2E3F5C"),
                align="left",
                borderpad=4,
                bgcolor="#ffffff",
                opacity=1,
            )

        figure.update_layout(
            title="Climate Mitigation Potential, "
            + str(year)
            + ", "
            + iea_region_list[i],
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

        figure.show()

        pio.write_html(
            figure,
            file=(
                "./charts/em1-"
                + "pathway"
                + "-"
                + str(year)
                + "-"
                + iea_region_list[i]
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

# endregion

#################################
# CO2 ATMOSPHERIC CONCENTRATION #
#################################

# region
# from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

CONCENTRATION_CO2 = "simpleNbox.Ca"

low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
default = pyhector.run(rcp19, {"temperature": {"S": 3}})
high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

hist = pd.DataFrame(pd.read_csv("podi/data/CO2_conc.csv")).set_index(
    ["Region", "Model", "Metric", "Scenario"]
)
hist.columns = hist.columns.astype(int)
hist = hist.loc["World ", "NOAA", "PPM CO2", "pathway"].T.dropna()

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
    4,
).T

results26 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

results60 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

pd20 = (
    pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv"))
    .set_index(["Region", "Metric", "Units", "Scenario"])
    .droplevel(["Units"])
)
pd20.columns = pd20.columns.astype(int)


pd20.loc["World ", "Atm conc CO2", "pathway"] = pd20.loc[
    "World ", "Atm conc CO2", "pathway"
] * (hist[2019] / pd20.loc["World ", "Atm conc CO2", "pathway"].loc[2019])
results19 = results19 * (hist[2021] / results19[results19.index == 2021].values[0][0])
results26 = results26 * (hist[2021] / results26[results26.index == 2021].values[0][0])
results60 = results60 * (hist[2021] / results60[results60.index == 2021].values[0][0])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[(hist.index >= 1950) & (hist.index <= 2021)].index,
        y=hist[(hist.index >= 1950) & (hist.index <= 2021)],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD20",
        line=dict(width=3, color="blue", dash="dot"),
        x=pd20.loc["World ", "Atm conc CO2", "pathway"].loc[2019:].index,
        y=pd20.loc["World ", "Atm conc CO2", "pathway"].loc[2019:],
        fill="none",
        stackgroup="three",
        legendgroup="PD20",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="four",
        legendgroup="PD21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-2.6",
        line=dict(width=3, color="yellow", dash="dot"),
        x=results26[(results19.index >= 2021) & (results26.index <= 2100)].index,
        y=results26[(results26.index >= 2021) & (results26.index <= 2100)][
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="five",
        legendgroup="SSP2-2.6",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="orange", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="six",
        legendgroup="SSP2-1.9",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=results60[(results60.index >= 2021) & (results60.index <= 2100)].index,
        y=results60[(results60.index >= 2021) & (results60.index <= 2100)][
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="seven",
        legendgroup="Baseline",
    )
)

fig.update_layout(
    title={
        "text": "Atmospheric CO2 Concentration",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppmv CO2"},
)

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

CONCENTRATION_CO2 = "simpleNbox.Ca"

low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
default = pyhector.run(rcp19, {"temperature": {"S": 3}})
high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

hist = pd.DataFrame(pd.read_csv("podi/data/CO2_conc.csv")).set_index(
    ["Region", "Model", "Metric", "Scenario"]
)
hist.columns = hist.columns.astype(int)
hist = hist.loc["World ", "NOAA", "PPM CO2", "pathway"].T.dropna()

results = (
    pd.DataFrame(pd.read_csv("podi/data/SSP_IAM_V2_201811.csv"))
    .set_index(["MODEL", "SCENARIO", "REGION", "VARIABLE", "UNIT"])
    .droplevel(["UNIT"])
)
results.columns = results.columns.astype(int)

results19 = (
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
)

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
        ].loc[:,2010:]
    ).T,
    "quadratic",
    4,
).T
"""
results26 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

results60 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

pd20 = (
    pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv"))
    .set_index(["Region", "Metric", "Units", "Scenario"])
    .droplevel(["Units", "Scenario"])
)
pd20.columns = pd20.columns.astype(int)


pd20.loc["World ", "Equivalent CO2"] = pd20.loc["World ", "Equivalent CO2"] * (
    hist[2019] / pd20.loc["World ", "Equivalent CO2"].loc[2019]
)
results19 = results19 * (hist[2021] / results19[results19.index == 2021].values[0][0])
results26 = results26 * (hist[2021] / results26[results26.index == 2021].values[0][0])
results60 = results60 * (hist[2021] / results60[results60.index == 2021].values[0][0])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[(hist.index >= 1950) & (hist.index <= 2021)].index,
        y=hist[(hist.index >= 1950) & (hist.index <= 2021)],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD20",
        line=dict(width=3, color="blue", dash="dot"),
        x=pd20.loc["World ", "Equivalent CO2"].loc[2019:].index,
        y=pd20.loc["World ", "Equivalent CO2"].loc[2019:],
        fill="none",
        stackgroup="three",
        legendgroup="PD20",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="four",
        legendgroup="PD21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-2.6",
        line=dict(width=3, color="yellow", dash="dot"),
        x=results26[(results19.index >= 2021) & (results26.index <= 2100)].index,
        y=results26[(results26.index >= 2021) & (results26.index <= 2100)][
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="five",
        legendgroup="SSP2-2.6",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="orange", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="six",
        legendgroup="SSP2-1.9",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=results60[(results60.index >= 2021) & (results60.index <= 2100)].index,
        y=results60[(results60.index >= 2021) & (results60.index <= 2100)][
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="seven",
        legendgroup="Baseline",
    )
)

fig.update_layout(
    title={
        "text": "Atmospheric GHG Concentration",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppmv CO2e"},
)

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
# from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

FORCING = "forcing.Ftot"

low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
default = pyhector.run(rcp19, {"temperature": {"S": 3}})
high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

results19 = pyhector.run(rcp19)
results26 = pyhector.run(rcp26)
results60 = pyhector.run(rcp60)
results85 = pyhector.run(rcp85)

hist = default[FORCING].loc[1950:]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[hist.index <= 2020].index,
        y=hist[hist.index <= 2020],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results26[(results26.index >= 2020) & (results26.index <= 2100)].index,
        y=results26[results26.index >= 2020][FORCING],
        fill="none",
        stackgroup="two",
        legendgroup="PD21",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-2.6",
        line=dict(width=3, color="yellow", dash="dot"),
        x=results26[(results26.index >= 2020) & (results26.index <= 2100)].index,
        y=results26[results26.index >= 2020][FORCING],
        fill="none",
        stackgroup="three",
        legendgroup="SSP2-2.6",
    )
)
"""
fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=results19[(results19.index >= 2020) & (results19.index <= 2100)].index,
        y=results19[results19.index >= 2020][FORCING],
        fill="none",
        stackgroup="four",
        legendgroup="SSP2-1.9",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=results60[(results60.index >= 2020) & (results60.index <= 2100)].index,
        y=results60[results60.index >= 2020][FORCING]
        - results60[results60.index >= 2020][FORCING][2020]
        + hist[2020],
        fill="none",
        stackgroup="five",
        legendgroup="Baseline",
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

fig.show()

if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/forcing-" + iea_region_list[i] + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

######################
# TEMPERATURE CHANGE #
######################

# region
# From openclimatedata/pyhector https://github.com/openclimatedata/pyhector

# TEMPERATURE

# region


TEMP = "temperature.Tgav"

results19 = pyhector.run(rcp19)
results26 = pyhector.run(rcp26)
results60 = pyhector.run(rcp60)

hist = default[TEMP].loc[1950:]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[hist.index <= 2020].index,
        y=hist[hist.index <= 2020],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results19[(results19.index >= 2020) & (results19.index <= 2100)].index,
        y=results19[results19.index >= 2020][TEMP],
        fill="none",
        stackgroup="two",
        legendgroup="PD21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-2.6",
        line=dict(width=3, color="yellow", dash="dot"),
        x=results26[(results26.index >= 2020) & (results26.index <= 2100)].index,
        y=results26[results26.index >= 2020][TEMP],
        fill="none",
        stackgroup="three",
        legendgroup="SSP2-2.6",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="light blue", dash="dot"),
        x=results19[(results19.index >= 2020) & (results19.index <= 2100)].index,
        y=results19[results19.index >= 2020][TEMP],
        fill="none",
        stackgroup="four",
        legendgroup="SSP2-1.9",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=results60[(results60.index >= 2020) & (results60.index <= 2100)].index,
        y=results60[results60.index >= 2020][TEMP],
        fill="none",
        stackgroup="five",
        legendgroup="Baseline",
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

fig.show()

if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/temp-" + iea_region_list[i] + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

# CLIMATE SENSITIVITY
"""
# region

low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
default = pyhector.run(rcp19, {"temperature": {"S": 3}})
high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

plt.figure()
sel = slice(1900, 2100)
plt.fill_between(
    low[TEMP].loc[sel].index,
    low[TEMP].loc[sel],
    high[TEMP].loc[sel],
    color="lightgray",
)

default[TEMP].loc[sel]

hist = default[TEMP].loc[1900:2016]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[hist.index <= 2020].index,
        y=hist[hist.index <= 2020],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results19[(results19.index >= 2020) & (results19.index <= 2100)].index,
        y=results19[results19.index >= 2020][TEMP],
        fill="none",
        stackgroup="two",
        legendgroup="PD21",
    )
)

fig.update_layout(
    title={
        "text": "PD21 Temperature with equilibrium climate sensitivity set to 1.5, 3, and 4.5",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.show()

if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/forcing2-" + iea_region_list[i] + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion
"""
# endregion

###################################
# ENERGY DEMAND MITIGATION WEDGES #
###################################

# region

# endregion

####################################
# ELECTRICITY GENERATION BY SOURCE #
####################################

# region

# region

tech_list = ["Solar", "Wind", "Nuclear", "Other renewables", "Fossil fuels"]

group_keys = {
    "Biomass and waste": "Other renewables",
    "Fossil fuels": "Fossil fuels",
    "Geothermal": "Other renewables",
    "Hydroelectricity": "Other renewables",
    "Nuclear": "Nuclear",
    "Solar": "Solar",
    "Wind": "Wind",
}

color = (
    (0.645, 0.342, 0.138),
    (0.285, 0.429, 0.621),
    (0.564, 0.114, 0.078),
    (0.603, 0.651, 0.717),
    (0.267, 0.267, 0.267),
)

# endregion

# STACKED AREA PLOT

# region

for i in range(0, len(iea_region_list)):
    fig = (
        elec_consump_pathway.loc[iea_region_list[i], slice(None)]
        .groupby("Metric")
        .sum()
    )
    fig = fig.groupby(group_keys).sum()
    fig = fig.reindex(tech_list)
    plt.figure(i)
    plt.stackplot(
        fig.columns.astype(int), fig * unit[1], labels=fig.index, colors=color
    )
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([data_start_year, long_proj_end_year])
    plt.title("Electricity Generation by Source, " + iea_region_list[i])
    plt.legend(loc=2, fontsize="small")
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.savefig(
        fname=("podi/data/figs/electricity_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

# LINE PLOT

# region

for i in range(0, len(iea_region_list)):
    fig = (
        elec_per_adoption_pathway.loc[iea_region_list[i], slice(None)]
        .groupby("Metric")
        .sum()
    )
    fig = fig[fig.index.isin(tech_list)]
    plt.figure(i)
    plt.plot(fig.columns.astype(int).values, fig.T * 100)
    plt.ylabel("(%)")
    plt.xlim([data_start_year, long_proj_end_year])
    plt.title("Percent of Total Electricity Generation, " + iea_region_list[i])
    plt.legend(
        fig.index,
        loc=2,
        fontsize="small",
        bbox_to_anchor=(1.05, 1),
        borderaxespad=0.0,
    )
    plt.show()
    plt.clf()

# endregion

# STACKED 100% PLOT

# region

for i in range(0, len(iea_region_list)):
    fig = (
        elec_per_adoption_pathway.loc[iea_region_list[i], slice(None)]
        .groupby("Metric")
        .sum()
    )
    fig = fig[fig.index.isin(tech_list)]
    plt.figure(i)
    plt.stackplot(fig.columns.astype(int).values, fig * 100, labels=fig.index)
    plt.ylabel("(%)")
    plt.xlim([data_start_year, long_proj_end_year])
    plt.title("Percent of Total Electricity Generation, " + iea_region_list[i])
    plt.legend(
        fig.index,
        loc=2,
        fontsize="small",
        bbox_to_anchor=(1.05, 1),
        borderaxespad=0.0,
    )
    plt.show()
    plt.clf()

# endregion

# endregion

######################################
# ELECTRICITY DEMAND BY SECTOR (TWH) #
######################################

# region

color = ((0.116, 0.220, 0.364), (0.380, 0.572, 0.828), (0.368, 0.304, 0.48))

# pathway

for i in range(0, len(iea_region_list)):
    energy_demand_pathway_i = energy_demand_pathway.loc[
        iea_region_list[i], slice(None), slice(None), "pathway"
    ]
    fig = (
        energy_demand_pathway_i.loc[(iea_region_list[i], slice(None), "Electricity"), :]
        .groupby(["Sector"])
        .sum()
        .drop("TFC")
        .rename(
            index={
                "Buildings": ("Buildings", "Electricity"),
                "Industry": ("Industry", "Electricity"),
                "Transport": ("Transport", "Electricity"),
            }
        )
    )
    fig.loc[[("Industry", "Electricity")]] = (
        fig.loc[[("Industry", "Electricity")]] * 0.9
    )
    fig.loc[[("Transport", "Electricity")]] = (
        fig.loc[[("Transport", "Electricity")]] * 1.2
    )
    plt.figure(i)
    plt.stackplot(fig.T.index, fig * unit[1], labels=fig.index, colors=color)
    plt.legend(loc=2, fontsize="small")
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([2020, energy_demand_pathway.columns.max()])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
    plt.title("Electricity Demand by Sector, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/elecbysector_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

###########################
# BUILDINGS ENERGY SUPPLY #
###########################

# region

tech_list = ["Electricity", "Solar thermal", "Bioenergy", "Fossil fuels"]

group_keys = {
    "Bioenergy": "Bioenergy",
    "Geothermal": "Electricity",
    "Hydroelectricity": "Electricity",
    "Nuclear": "Electricity",
    "Solar": "Electricity",
    "Wind": "Electricity",
    "Coal": "Fossil fuels",
    "Electricity": "Electricity",
    "Natural gas": "Fossil fuels",
    "Oil": "Fossil fuels",
    "Other renewables": "Solar thermal",
}

color = (
    (0.380, 0.572, 0.828),
    (0.996, 0.096, 0.320),
    (0.792, 0.616, 0.204),
    (0.296, 0.276, 0.180),
)

# pathway

for i in range(0, len(iea_region_list)):
    fig = energy_demand_pathway.loc[
        iea_region_list[i], "Buildings", ["Electricity", "Heat"], "pathway"
    ]

    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig * unit[1],
        labels=fig.index.get_level_values(2),
        colors=(
            "cornflowerblue",
            "lightcoral",
        ),
    )
    plt.legend(loc=2, fontsize="small")
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([2020, energy_demand_pathway.columns.max()])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
    plt.title("Buildings Energy Supply, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/buildings_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

#####################################
# INDUSTRY ENERGY DEMAND BY END-USE #
#####################################

# region

tech_list = ["Solar thermal", "Bioenergy", "Fossil fuels", "Electricity"]

group_keys = {
    "Bioenergy": "Bioenergy",
    "Geothermal": "Electricity",
    "Hydroelectricity": "Electricity",
    "Nuclear": "Electricity",
    "Solar": "Electricity",
    "Wind": "Electricity",
    "Coal": "Fossil fuels",
    "Electricity": "Electricity",
    "Natural gas": "Fossil fuels",
    "Oil": "Fossil fuels",
    "Other renewables": "Solar thermal",
}

color = (
    (0.556, 0.244, 0.228),
    (0.380, 0.572, 0.828),
)

# pathway

for i in range(0, len(iea_region_list)):
    fig = energy_demand_pathway.loc[
        iea_region_list[i], "Industry", ["Electricity", "Heat"], "pathway"
    ]

    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig * unit[1],
        labels=fig.index.get_level_values(2),
        colors=(color),
    )
    plt.legend(loc=2, fontsize="small")
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([2020, energy_demand_pathway.columns.max()])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
    plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/industry_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

########################
# INDUSTRY HEAT SUPPLY #
########################

# region

# Heat generation by source

heat_tech_list = [
    "Bioenergy",
    "Coal",
    "Geothermal",
    "Natural gas",
    "Nuclear",
    "Oil",
    "Other sources",
    "Solar thermal",
    "Waste",
]

color = (
    (0.296, 0.276, 0.180),
    (0.860, 0.456, 0.184),
    (0.792, 0.616, 0.204),
    (0.832, 0.612, 0.060),
    (0.996, 0.096, 0.320),
)

# pathway

for i in range(0, len(iea_region_list)):
    fig = energy_demand_pathway.loc[
        iea_region_list[i],
        "Industry",
        ["Coal", "Natural gas", "Oil", "Bioenergy", "Other renewables"],
        "pathway",
    ]
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig * unit[1],
        labels=fig.index.get_level_values(2),
        colors=(color),
    )
    plt.legend(loc=2, fontsize="small")
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([2020, energy_demand_pathway.columns.max()])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
    plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/industryheat_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

# endregion

################################
# TRANSPORTATION ENERGY DEMAND #
################################

# region

color = ((0.220, 0.500, 0.136), (0.356, 0.356, 0.356), (0.380, 0.572, 0.828))

for i in range(0, len(iea_region_list)):
    fig = energy_demand_pathway.loc[
        iea_region_list[i],
        "Transport",
        ["Electricity", "Oil", "Bioenergy"],
        "pathway",
    ]
    plt.figure(i)
    plt.stackplot(
        fig.T.index,
        fig * unit[1],
        labels=fig.index.get_level_values(2),
        colors=(color),
    )
    plt.legend(loc=2, fontsize="small")
    plt.ylabel("TFC, " + unit[0])
    plt.xlim([2020, energy_demand_pathway.columns.max()])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xticks(np.arange(2020, 2110, 10))
    plt.title("Transportation Energy Supply, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/transport_pathway-" + iea_region_list[i]).replace(
            " ", ""
        ),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

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

for i in range(0, len(iea_region_list)):
    em_mit = (
        (
            em_mitigated.loc[
                iea_region_list[i],
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
        "Regenerative Agriculture Subvector Mitigation Wedges, " + iea_region_list[i]
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

for i in range(0, len(iea_region_list)):
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
    plt.title("Forests & Wetlands Subvector Mitigation Wedges, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/fw_pathway-" + iea_region_list[i]).replace(" ", ""),
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

for i in range(0, len(iea_region_list)):
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
    plt.title("AFOLU Subvector Mitigation Wedges, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/afolu_pathway-" + iea_region_list[i]).replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
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

for i in range(0, len(iea_region_list)):
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
    plt.title("CO2 Removed via CDR, " + iea_region_list[i])
    plt.savefig(
        fname=("podi/data/figs/cdr_pathway-" + iea_region_list[i]).replace(" ", ""),
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

###################
# EMISSIONS (OLD) #
###################

# region
pd20 = (
    pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv"))
    .set_index(["Region", "Metric", "Units", "Scenario"])
    .droplevel(["Units"])
)
pd20.columns = pd20.columns.astype(int)
pd20 = pd20.loc["World ", "Global CO2 Equivalent Emissions", slice(None)].apply(
    lambda x: x
    / (x.loc[2018] / (pd.Series(em_hist.loc["World "].loc[2018] / 1000).values)),
    axis=1,
)

scenario = "baseline"
start_year = 2000

for i in range(0, len(iea_region_list)):
    if scenario == "baseline":
        em = em_baseline
        afolu_em = em_baseline
    else:
        em = em_pathway
        afolu_em = em_pathway

    em_electricity = (
        em.loc[iea_region_list[i], "Electricity", slice(None)]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_transport = (
        em.loc[iea_region_list[i], "Transport", slice(None)]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_buildings = (
        em.loc[iea_region_list[i], "Buildings", slice(None)]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_industry = (
        em.loc[iea_region_list[i], ["Industry", "Other"], ["Fossil fuels", "cement"]]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_ra = (
        afolu_em.loc[
            iea_region_list[i],
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
            ["CH4", "N2O", "F-gases"],
        ]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_fw = (
        afolu_em.loc[
            iea_region_list[i],
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
        .loc[data_start_year:long_proj_end_year]
    )

    em_othergas = (
        em.loc[iea_region_list[i], slice(None), ["CH4", "N2O", "F-gases"]]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_ch4 = (
        em.loc[iea_region_list[i], slice(None), ["CH4"]]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_n2o = (
        em.loc[iea_region_list[i], slice(None), ["N2O"]]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    em_fgas = (
        em.loc[iea_region_list[i], slice(None), ["F-gases"]]
        .sum()
        .loc[data_start_year:long_proj_end_year]
    )

    if iea_region_list[i] == "World ":
        em_cdr = -cdr.loc[slice(None), scenario, :].squeeze()

        em = pd.DataFrame(
            [
                em_electricity,
                em_transport,
                em_buildings,
                em_industry,
                em_ch4,
                em_n2o,
                em_fgas,
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
                "Unnamed 4": "CH4",
                "Unnamed 5": "N2O",
                "Unnamed 6": "F-gases",
                "Unnamed 7": "Agriculture",
                "Unnamed 8": "Forests & Wetlands",
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
                em_ch4,
                em_n2o,
                em_fgas,
                em_ra,
                em_fw,
            ]
        ).rename(
            index={
                0: "Electricity",
                1: "Transport",
                2: "Buildings",
                3: "Industry",
                4: "CH4",
                5: "N2O",
                6: "F-gases",
                7: "Agriculture",
                8: "Forests & Wetlands",
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

    if iea_region_list[i] == "World ":
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
    fig.add_trace(go.Scatter(name='CH4, N2O, F-gases', line=dict(width=0.5, color="#E45756"), x=fig2["Year"], y=fig2[fig2['Sector'] == 'CH4, N2O, F-gases']['Emissions, GtCO2e'], fill='tonexty', stackgroup='one'))
    """

    fig.add_trace(
        go.Scatter(
            name="Agriculture",
            line=dict(width=0.5, color="#72B7B2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Forests & Wetlands",
            line=dict(width=0.5, color="#54A24B"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
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

    fig.add_trace(
        go.Scatter(
            name="Industry",
            line=dict(width=0.5, color="#60738C"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Buildings",
            line=dict(width=0.5, color="#F58518"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Transport",
            line=dict(width=0.5, color="#7AA8B8"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Electricity",
            line=dict(width=0.5, color="#B279A2"),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="two",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=2, color="black"),
            x=pd.Series(em_hist.loc[:, start_year:].columns.values),
            y=pd.Series(
                em_hist.loc[:, start_year:].loc[iea_region_list[i]].values / 1000
            ),
            fill="tozeroy",
            stackgroup="three",
        )
    )

    """
    # PD20 Check
    if iea_region_list[i] == "World ":
        fig.add_trace(
            go.Scatter(
                name="PD20",
                line=dict(width=2, color="blue"),
                x=pd.Series(pd20.loc[:, 2018:2021].columns.values),
                y=pd.Series(pd20.loc[scenario].loc[2018:2021].values),
                fill="tozeroy",
                stackgroup="PD20",
            )
        )
    """
    fig.update_layout(
        title={
            "text": "Emissions, " + scenario.title() + ", " + iea_region_list[i],
            "xanchor": "center",
            "x": 0.5,
        },
        xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
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
                "./charts/em2-" + scenario + "-" + iea_region_list[i] + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )
    plt.clf()

# endregion

#################################
# MITIGATION WEDGES CURVE (OLD) #
#################################

# region

fig_type = "plotly"

ndcs = [
    (3, 3),
    (3, 3),
    (2025, 4.86),
    (3, 3),
    (2030, 1.2),
    (3, 3),
    (3, 3),
    (2030, 0.13),
    (3, 3),
    (2030, 2.67),
    (3, 3),
    (2030, 12.96),
    (2030, 9.14),
    (2030, 1),
    (3, 3),
    (3, 3),
]

for i in range(0, len(iea_region_list)):
    em_mit_electricity = em_mitigated.loc[
        iea_region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[
        iea_region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated.loc[
        iea_region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated.loc[
        iea_region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated.loc[
        iea_region_list[i],
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
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_fw = em_mitigated.loc[
        iea_region_list[i],
        [
            "Avoided Coastal Impacts",
            "Avoided Forest Conversion",
            "Avoided Peat Impacts",
            "Coastal Restoration",
            "Improved Forest Mgmt",
            "Peat Restoration",
            "Natural Regeneration",
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_othergas = em_mitigated.loc[iea_region_list[i], "Other", :].sum()

    if iea_region_list[i] == "World ":
        em_mit_cdr = cdr_pathway[0].rename("CDR")
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
                "Unnamed 6": "CH4, N2O, F-gases",
                "Unnamed 7": "CDR",
            }
        )
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
                0: "Electricity",
                1: "Transport",
                2: "Buildings",
                3: "Industry",
                4: "Forests & Wetlands",
                5: "Agriculture",
                6: "CH4, N2O, F-gases",
            }
        )

    spacer = (
        pd.Series(
            em_baseline.groupby("Region").sum().loc[iea_region_list[i]] - em_mit.sum()
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
                "CH4, N2O, F-gases",
                "CDR",
                spacer.name,
            ]
        )
        .loc[:, data_end_year:]
    )

    if fig_type == "plotly":
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

        if iea_region_list[i] == "World ":
            fig.add_trace(
                go.Scatter(
                    name="CDR",
                    line=dict(width=0.5, color="#FF9DA6"),
                    x=fig2["Year"],
                    y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                    fill="tonexty",
                    stackgroup="one",
                )
            )
        fig.add_trace(
            go.Scatter(
                name="CH4, N2O, F-gases",
                line=dict(width=0.5, color="#B82E2E"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CH4, N2O, F-gases"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Agriculture",
                line=dict(width=0.5, color="#72B7B2"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Forests & Wetlands",
                line=dict(width=0.5, color="#54A24B"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Industry",
                line=dict(width=0.5, color="#60738C"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Buildings",
                line=dict(width=0.5, color="#F58518"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Transport",
                line=dict(width=0.5, color="#7AA8B8"),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Electricity",
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
                y=pd.Series(em_hist.loc[iea_region_list[i]].values / 1000),
                fill="none",
                stackgroup="two",
            )
        )
        if iea_region_list[i] == "World ":
            fig.add_trace(
                go.Scatter(
                    name="SSP2-1.9",
                    line=dict(width=2, color="light blue", dash="dot"),
                    x=pd.Series(
                        em_targets.loc["SSP2-19", near_proj_start_year:].index.values
                    ),
                    y=pd.Series(
                        em_targets.loc["SSP2-19", near_proj_start_year:].values
                    ),
                    fill="none",
                    stackgroup="three",
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="SSP2-2.6",
                    line=dict(width=2, color="yellow", dash="dot"),
                    x=pd.Series(
                        em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                    ),
                    y=pd.Series(
                        em_targets.loc["SSP2-26", near_proj_start_year:].values
                    ),
                    fill="none",
                    stackgroup="four",
                )
            )

        fig.add_trace(
            go.Scatter(
                name="PD21",
                line=dict(width=2, color="green", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(spacer.loc[near_proj_start_year:].values / 1000),
                fill="none",
                stackgroup="five",
            )
        )

        fig.add_trace(
            go.Scatter(
                name="Baseline",
                line=dict(width=2, color="red", dash="dot"),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    em_baseline.loc[:, near_proj_start_year:]
                    .groupby("Region")
                    .sum()
                    .loc[iea_region_list[i]]
                    / 1000
                ),
                fill="none",
                stackgroup="six",
            )
        )

        if iea_region_list[i] in [
            "US ",
            "SAFR ",
            "RUS ",
            "JPN ",
            "CHINA ",
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

        fig.update_layout(
            title={
                "text": "Emissions Mitigated, " + iea_region_list[i],
                "xanchor": "center",
                "x": 0.5,
            },
            xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
        )
        """
        fig.add_vrect(x0=1990, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)
        """
        if show_figs is True:
            fig.show()
        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/mwedges-" + "pathway" + "-" + iea_region_list[i] + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    else:
        color = (
            (0.999, 0.999, 0.999),
            (0.928, 0.828, 0.824),
            (0.688, 0.472, 0.460),
            (0.572, 0.792, 0.744),
            (0.536, 0.576, 0.432),
            (0.384, 0.460, 0.560),
            (0.904, 0.620, 0.384),
            (0.488, 0.672, 0.736),
            (0.560, 0.516, 0.640),
            (0.284, 0.700, 0.936),
            (0.384, 0.664, 0.600),
            (0.999, 0.976, 0.332),
            (0.748, 0.232, 0.204),
        )

        custom_legend = [
            Line2D([0], [0], color=color[8], linewidth=4),
            Line2D([0], [0], color=color[7], linewidth=4),
            Line2D([0], [0], color=color[6], linewidth=4),
            Line2D([0], [0], color=color[5], linewidth=4),
            Line2D([0], [0], color=color[4], linewidth=4),
            Line2D([0], [0], color=color[3], linewidth=4),
            Line2D([0], [0], color=color[2], linewidth=4),
            Line2D([0], [0], color=color[1], linewidth=4),
            Line2D(
                [0],
                [0],
                color=color[12],
                linewidth=2,
                linestyle="--",
                dashes=(2, 1, 0, 0),
            ),
            Line2D(
                [0],
                [0],
                color=color[10],
                linewidth=2,
                linestyle=":",
                dashes=(2, 1, 0, 0),
            ),
            Line2D(
                [0],
                [0],
                color=color[9],
                linewidth=2,
                linestyle=":",
                dashes=(2, 1, 0, 0),
            ),
            Line2D(
                [0],
                [0],
                color=color[11],
                linewidth=2,
                linestyle=":",
                dashes=(2, 1, 0, 0),
            ),
        ]

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
                "Electricity",
                "Transport",
                "Buildings",
                "Industry",
                "Agriculture",
                "Forests & Wetlands",
                "CH4, N2O, F-gases",
                "CDR",
                "Baseline",
                "DAU",
                "SSP2-RCP1.9",
                "SSP2-RCP2.6",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-25, 105, 10))
        plt.title("Emissions Mitigated, " + iea_region_list[i])
        plt.show()

        if save_figs is True:
            plt.savefig(
                fname=("podi/data/figs/mitigationwedges-" + iea_region_list[i]).replace(
                    " ", ""
                ),
                format="png",
                bbox_inches="tight",
                pad_inches=0.1,
            )

    plt.clf()

# endregion

#######################################
# GHG ATMOSPHERIC CONCENTRATION (OLD) #
#######################################

# region
# from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

CONCENTRATION_CO2 = "simpleNbox.Ca"

low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
default = pyhector.run(rcp19, {"temperature": {"S": 3}})
high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

hist = pd.DataFrame(pd.read_csv("podi/data/CO2_conc.csv")).set_index(
    ["Region", "Model", "Metric", "Scenario"]
)
hist.columns = hist.columns.astype(int)
hist = hist.loc["World ", "NOAA", "PPM CO2", "pathway"].T.dropna()

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
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

results26 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

results60 = curve_smooth(
    pd.DataFrame(
        results.loc[
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ].loc[2010:]
    ).T,
    "quadratic",
    4,
).T

pd20 = (
    pd.DataFrame(pd.read_csv("podi/data/emissions_conc_PD20.csv"))
    .set_index(["Region", "Metric", "Units", "Scenario"])
    .droplevel(["Units", "Scenario"])
)
pd20.columns = pd20.columns.astype(int)


pd20.loc["World ", "Equivalent CO2"] = pd20.loc["World ", "Equivalent CO2"] * (
    hist[2019] / pd20.loc["World ", "Equivalent CO2"].loc[2019]
)
results19 = results19 * (hist[2021] / results19[results19.index == 2021].values[0][0])
results26 = results26 * (hist[2021] / results26[results26.index == 2021].values[0][0])
results60 = results60 * (hist[2021] / results60[results60.index == 2021].values[0][0])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        name="Historical",
        line=dict(width=3, color="black"),
        x=hist[(hist.index >= 1950) & (hist.index <= 2021)].index,
        y=hist[(hist.index >= 1950) & (hist.index <= 2021)],
        fill="none",
        stackgroup="one",
        legendgroup="Historical",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD20",
        line=dict(width=3, color="blue", dash="dot"),
        x=pd20.loc["World ", "Equivalent CO2"].loc[2019:].index,
        y=pd20.loc["World ", "Equivalent CO2"].loc[2019:],
        fill="none",
        stackgroup="three",
        legendgroup="PD20",
    )
)

fig.add_trace(
    go.Scatter(
        name="PD21",
        line=dict(width=3, color="green", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="four",
        legendgroup="PD21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-2.6",
        line=dict(width=3, color="yellow", dash="dot"),
        x=results26[(results19.index >= 2021) & (results26.index <= 2100)].index,
        y=results26[(results26.index >= 2021) & (results26.index <= 2100)][
            "GCAM4", "SSP2-26", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="five",
        legendgroup="SSP2-2.6",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-1.9",
        line=dict(width=3, color="orange", dash="dot"),
        x=results19[(results19.index >= 2021) & (results19.index <= 2100)].index,
        y=results19[(results19.index >= 2021) & (results19.index <= 2100)][
            "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="six",
        legendgroup="SSP2-1.9",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color="red", dash="dot"),
        x=results60[(results60.index >= 2021) & (results60.index <= 2100)].index,
        y=results60[(results60.index >= 2021) & (results60.index <= 2100)][
            "GCAM4", "SSP2-Baseline", "World", "Diagnostics|MAGICC6|Concentration|CO2"
        ],
        fill="none",
        stackgroup="seven",
        legendgroup="Baseline",
    )
)

fig.update_layout(
    title={
        "text": "Atmospheric GHG Concentration",
        "xanchor": "center",
        "x": 0.5,
    },
    xaxis={"title": "Year"},
    yaxis={"title": "ppmv CO2e"},
)

fig.show()

if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/ghgconc-" + "World " + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

######################################################
# EMISSIONS MITIGATION BARCHART W CH4/N2O/FGAS (OLD) #
######################################################

# region

year = 2030

for i in range(0, len(iea_region_list)):
    em_mit_electricity = em_mitigated.loc[
        iea_region_list[i], "Electricity", slice(None)
    ].sum()

    em_mit_transport = em_mitigated.loc[
        iea_region_list[i], "Transport", slice(None)
    ].sum()

    em_mit_buildings = em_mitigated.loc[
        iea_region_list[i], "Buildings", slice(None)
    ].sum()

    em_mit_industry = em_mitigated.loc[
        iea_region_list[i], "Industry", slice(None)
    ].sum()

    em_mit_ra = em_mitigated.loc[
        iea_region_list[i],
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
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_fw = em_mitigated.loc[
        iea_region_list[i],
        [
            "Avoided Coastal Impacts",
            "Avoided Forest Conversion",
            "Avoided Peat Impacts",
            "Coastal Restoration",
            "Improved Forest Mgmt",
            "Peat Restoration",
            "Natural Regeneration",
        ],
        slice(None),
        slice(None),
    ].sum()

    em_mit_othergas = em_mitigated.loc[iea_region_list[i], "Other", :].sum()

    em_mit_ch4 = em_mitigated.loc[iea_region_list[i], "Other", ["CH4"]].sum()

    em_mit_n2o = em_mitigated.loc[iea_region_list[i], "Other", ["N2O"]].sum()

    em_mit_fgas = em_mitigated.loc[iea_region_list[i], "Other", ["F-gases"]].sum()

    em_mit_cdr = pd.Series(
        cdr_pathway.sum(), index=np.arange(data_start_year, long_proj_end_year + 1)
    )

    em_mit = pd.DataFrame(
        [
            em_mit_electricity,
            em_mit_transport,
            em_mit_buildings,
            em_mit_industry,
            em_mit_ra,
            em_mit_fw,
            em_mit_ch4,
            em_mit_n2o,
            em_mit_fgas,
            em_mit_cdr,
        ]
    ).rename(
        index={
            0: "Electricity",
            1: "Transport",
            2: "Buildings",
            3: "Industry",
            4: "Forests & Wetlands",
            5: "Agriculture",
            6: "CH4",
            7: "N2O",
            8: "F-gases",
            9: "CDR",
        }
    )

    em_mit.loc[:, :2020] = 0

    if iea_region_list[i] == "World ":
        fig = (
            ((em_mit) / 1000)
            .reindex(
                [
                    "CDR",
                    "CH4",
                    "N2O",
                    "F-gases",
                    "Agriculture",
                    "Forests & Wetlands",
                    "Industry",
                    "Buildings",
                    "Transport",
                    "Electricity",
                ]
            )
            .round(decimals=4)
            .clip(lower=0)
        )

        data = {
            "Electricity": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Electricity", year],
                fig.loc["Electricity", year],
            ],
            "Transport": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Transport", year],
                0,
                fig.loc["Transport", year],
            ],
            "Buildings": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Buildings", year],
                0,
                0,
                fig.loc["Buildings", year],
            ],
            "Industry": [
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Industry", year],
                0,
                0,
                0,
                fig.loc["Industry", year],
            ],
            "Forests & Wetlands": [
                0,
                0,
                0,
                0,
                0,
                fig.loc["Forests & Wetlands", year],
                0,
                0,
                0,
                0,
                fig.loc["Forests & Wetlands", year],
            ],
            "Agriculture": [
                0,
                0,
                0,
                0,
                fig.loc["Agriculture", year],
                0,
                0,
                0,
                0,
                0,
                fig.loc["Agriculture", year],
            ],
            "CH4": [
                0,
                fig.loc["CH4", year],
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["CH4", year],
            ],
            "N2O": [
                0,
                0,
                fig.loc["N2O", year],
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["N2O", year],
            ],
            "F-gases": [
                0,
                0,
                0,
                fig.loc["F-gases", year],
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["F-gases", year],
            ],
            "CDR": [
                fig.loc["CDR", year],
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["CDR", year],
            ],
            "Total": [
                0,
                fig.loc["Electricity", year],
                fig.loc["Transport", year],
                fig.loc["Buildings", year],
                fig.loc["Industry", year],
                fig.loc["Forests & Wetlands", year],
                fig.loc["Agriculture", year],
                0,
                0,
            ],
            "labels": [
                "CDR",
                "CH4",
                "N2O",
                "F-gases",
                "Agriculture",
                "Forests & Wetlands",
                "Industry",
                "Buildings",
                "Transport",
                "Electricity",
                "Total",
            ],
        }
    else:
        fig = (
            ((em_mit) / 1000)
            .reindex(
                [
                    "CH4",
                    "N2O",
                    "F-gases",
                    "Agriculture",
                    "Forests & Wetlands",
                    "Industry",
                    "Buildings",
                    "Transport",
                    "Electricity",
                ]
            )
            .round(decimals=4)
            .clip(lower=0)
        )

        data = {
            "Electricity": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Electricity", year],
                fig.loc["Electricity", year],
            ],
            "Transport": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Transport", year],
                0,
                fig.loc["Transport", year],
            ],
            "Buildings": [
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["Buildings", year],
                0,
                0,
                fig.loc["Buildings", year],
            ],
            "Industry": [
                0,
                0,
                0,
                0,
                0,
                fig.loc["Industry", year],
                0,
                0,
                0,
                fig.loc["Industry", year],
            ],
            "Forests & Wetlands": [
                0,
                0,
                0,
                0,
                fig.loc["Forests & Wetlands", year],
                0,
                0,
                0,
                0,
                fig.loc["Forests & Wetlands", year],
            ],
            "Agriculture": [
                0,
                0,
                0,
                fig.loc["Agriculture", year],
                0,
                0,
                0,
                0,
                0,
                fig.loc["Agriculture", year],
            ],
            "CH4": [
                fig.loc["CH4", year],
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["CH4", year],
            ],
            "N2O": [
                0,
                fig.loc["N2O", year],
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["N2O", year],
            ],
            "F-gases": [
                0,
                0,
                fig.loc["F-gases", year],
                0,
                0,
                0,
                0,
                0,
                0,
                fig.loc["F-gases", year],
            ],
            "Total": [
                0,
                fig.loc["Electricity", year],
                fig.loc["Transport", year],
                fig.loc["Buildings", year],
                fig.loc["Industry", year],
                fig.loc["Forests & Wetlands", year],
                fig.loc["Agriculture", year],
                0,
            ],
            "labels": [
                "CH4",
                "N2O",
                "F-gases",
                "Agriculture",
                "Forests & Wetlands",
                "Industry",
                "Buildings",
                "Transport",
                "Electricity",
                "Total",
            ],
        }

    opacity = 0.5

    if iea_region_list[i] == "World ":
        figure = go.Figure(
            data=[
                go.Bar(
                    y=data["labels"],
                    x=data["CDR"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#FF9DA6",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["CH4"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#B82e2e",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["N2O"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#77453b",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["F-gases"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#bbe272",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Agriculture"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#72B7B2",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Forests & Wetlands"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#54A24B",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Industry"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#60738C",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Buildings"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#F58518",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Transport"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#7AA8B8",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Electricity"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#B279A2",
                    opacity=opacity,
                ),
            ]
        )
    else:
        figure = go.Figure(
            data=[
                go.Bar(
                    y=data["labels"],
                    x=data["CH4"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#b82e2e",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["N2O"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#77453b",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["F-gases"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#bbe272",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Agriculture"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#72B7B2",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Forests & Wetlands"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#54A24B",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Industry"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#60738C",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Buildings"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#F58518",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Transport"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#7AA8B8",
                    opacity=opacity,
                ),
                go.Bar(
                    y=data["labels"],
                    x=data["Electricity"],
                    offsetgroup=0,
                    orientation="h",
                    marker_color="#B279A2",
                    opacity=opacity,
                ),
            ]
        )

    if year == 2030:
        j = 0
    else:
        j = 1

    if iea_region_list[i] in [
        "US ",
        "SAFR ",
        "RUS ",
        "JPN ",
        "CHINA ",
        "BRAZIL ",
        "INDIA ",
    ]:
        figure.add_shape(
            type="line",
            x0=em_mit_ndc[
                (em_mit_ndc["Region"] == iea_region_list[i])
                & (em_mit_ndc.index == year)
            ]["em_mit"].values[0],
            y0=-0.5,
            x1=em_mit_ndc[
                (em_mit_ndc["Region"] == iea_region_list[i])
                & (em_mit_ndc.index == year)
            ]["em_mit"].values[0],
            y1=9.5,
            line=dict(color="LightSeaGreen", width=3, dash="dot"),
            name="NDC",
        )

        figure.add_trace(
            go.Scatter(
                x=[
                    em_mit_ndc[
                        (em_mit_ndc["Region"] == iea_region_list[i])
                        & (em_mit_ndc.index == year)
                    ]["em_mit"].values[0]
                    * 0.9
                ],
                y=["CH4"],
                text=["NDC " + str(year)],
                mode="text",
                showlegend=False,
            )
        )

    if iea_region_list[i] == "World ":
        figure.add_shape(
            type="line",
            x0=em_mit_ndc[
                (em_mit_ndc["Region"] == iea_region_list[i])
                & (em_mit_ndc.index == year)
            ]["em_mit"].values[0],
            y0=-0.5,
            x1=em_mit_ndc[
                (em_mit_ndc["Region"] == iea_region_list[i])
                & (em_mit_ndc.index == year)
            ]["em_mit"].values[0],
            y1=10.5,
            line=dict(color="LightSeaGreen", width=3, dash="dot"),
            name="NDC",
        )

        figure.add_trace(
            go.Scatter(
                x=[
                    em_mit_ndc[
                        (em_mit_ndc["Region"] == iea_region_list[i])
                        & (em_mit_ndc.index == year)
                    ]["em_mit"].values[0]
                    * 0.9
                ],
                y=["CDR"],
                text=["NDC " + str(year)],
                mode="text",
                showlegend=False,
            )
        )

    figure.update_layout(
        title="Climate Mitigation Potential, " + str(year) + ", " + iea_region_list[i],
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

    figure.show()

    pio.write_html(
        figure,
        file=(
            "./charts/em1-"
            + "pathway"
            + "-"
            + str(year)
            + "-"
            + iea_region_list[i]
            + ".html"
        ).replace(" ", ""),
        auto_open=False,
    )

# endregion
