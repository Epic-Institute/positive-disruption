#!/usr/bin/env python

# region

import numpy as np
from numpy.random import random_integers
import pandas as pd
from matplotlib.lines import Line2D
from scipy import interpolate
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import chain, zip_longest
from math import ceil, pi, nan
from podi.curve_smooth import curve_smooth
from numpy import NaN, product, triu_indices_from
import fair
from fair.forward import fair_scm
from fair.RCPs import rcp26, rcp45, rcp60, rcp85, rcp3pd
from fair.constants import radeff
from podi.energy import energy

pd.options.display.float_format = "{:,.0f}".format

unit_name = ["TJ", "TWh", "GW"]
unit_val = [1, 0.0002777, 0.2777/8760]
unit = [unit_name[0], unit_val[0]]

save_figs = True
show_figs = True
show_annotations = True
start_year = 1990
scenario = "pathway"


#######################
# COLORS & LINESTYLES #
#######################

cl = {
    "Baseline": ["red", "dot"],
    "DAU21": ["#990099", "dashdot"],
    "DAU21+CDR": ["#3366CC", "dashdot"],
    "SSP2-RCP1.9": ["green", "dash"],
    "DAU-PL": ["orange", "dashdot"],
    "DAU-WE": ["#16ff32", "dashdot"],
    "DAU-RA": ["#eeca3b", "dashdot"],
    "DAU-FW": ["#66aa00", "dashdot"],
    "DAU-NCS": ["#eb663b", "dashdot"],
    "DAU-FFI": ["#862a16", "dashdot"],
    "DAU-NCS+FFI": ["#17becf", "dashdot"],
    "DAU-NCS+FFI+E+T": ["rgb(0,134,149)", "dashdot"],
    "V1: Electricity": ["rgba(154, 106, 144, 1)", "rgba(154, 106, 144, 0.5)"],
    "V2: Transport": ["rgba(110, 193, 228, 1)", "rgba(110, 193, 228, 0.5)"],
    "V3: Buildings": ["rgba(228, 148, 118, 1)", "rgba(228, 148, 118, 0.5)"],
    "V4: Industry": ["rgba(181, 170, 181, 1)", "rgba(181, 170, 181, 0.5)"],
    "V5: Agriculture": ["rgba(234, 214, 84, 1)", "rgba(234, 214, 84, 0.5)"],
    "V6: Forests & Wetlands": ["rgba(87, 141, 60, 1)", "rgba(87, 141, 60, 0.5)"],
    "V7: CDR": ["rgba(202, 132, 140, 1)", "rgba(202, 132, 140, 0.5)"],
}

cl_old = {
    "V1: Electricity": "#B279A2",
    "V2: Transport": "#7AA8B8",
    "V3: Buildings": "#F58518",
    "V4: Industry": "#60738C",
    "V5: Agriculture": "#EECA3B",
    "V6: Forests & Wetlands": "#54A24B",
    "V7: CDR": "#FF9DA6",
}

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

# endregion

###################
# ENERGY BALANCES #
###################

# region

scenario = scenario
region = "usa"
year = 2019

# Filter for region and year
energy_balance = (
    energy_pathway.loc[scenario, region, :]
    .loc[:, [year]]
    .groupby(
        ["Sector", "Product_category", "Product_long", "Flow_category", "Flow_long"]
    )
    .sum()
)

# Create energy balance table structure
energy_balance = (
    energy_balance.groupby(
        ["Product_category", "Product_long", "Flow_category", "Flow_long"]
    )
    .sum()
    .reset_index()
    .pivot(
        index=["Flow_category", "Flow_long"],
        columns=["Product_category", "Product_long"],
        values=2019,
    )
    .fillna(0)
    .reindex(
        axis="index",
        level=0,
        labels=[
            "Supply",
            "Transformation processes",
            "Energy industry own use and Losses",
            "Final consumption",
        ],
    )
    .reindex(
        axis="columns",
        level=0,
        labels=[
            "Coal",
            "Crude, NGL, refinery feedstocks",
            "Oil products",
            "Natural gas",
            "Biofuels and Waste",
            "Electricity and Heat",
        ],
    )
    .astype(int)
)

# Create Product categories (columns)
energy_balance = pd.concat(
    [
        energy_balance.groupby("Product_category", axis="columns")
        .sum()[
            [
                "Coal",
                "Crude, NGL, refinery feedstocks",
                "Oil products",
                "Natural gas",
                "Biofuels and Waste",
            ]
        ]
        .rename(columns={"Crude, NGL, refinery feedstocks": "Crude oil"}),
        energy_balance.loc[:, "Electricity and Heat"].loc[
            :, ["Nuclear", "Hydro", "Electricity", "Heat"]
        ],
        energy_balance.loc[:, "Electricity and Heat"]
        .drop(["Electricity", "Heat", "Nuclear","Hydro"], 1)
        .sum(axis=1)
        .to_frame()
        .rename(columns={0: "Wind, solar, etc."}),
    ],
    axis=1,
).reindex(
    axis="columns",
    labels=[
        "Coal",
        "Crude oil",
        "Oil products",
        "Natural gas",
        "Nuclear",
        "Hydro",
        "Wind, solar, etc.",
        "Biofuels and Waste",
        "Electricity",
        "Heat",
    ],
)

energy_balance = pd.concat(
    [
        energy_balance,
        pd.DataFrame(energy_balance.sum(axis=1)).rename(columns={0: "Total"}),
    ],
    axis=1,
)

# Create Flow categories (rows)
bunkers = energy_balance.loc["Supply", :].loc[
        energy_balance.loc["Supply", :]
        .index.get_level_values(0)
        .isin(
            ["International marine bunkers",
                "International aviation bunkers",
            ]
        ),
        :,
    ].iloc[::-1]

electricity_plants = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(
            [
                "Autoproducer electricity plants",
                "Main activity producer electricity plants",
                "Chemical heat for electricity production",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Electricity plants"})
)

chp_plants = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(["Autoproducer CHP", "Main activity producer CHP plants"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "CHP plants"})
)

heat_plants = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(
            [
                "Autoproducer heat plants",
                "Main activity producer heat plants",
                "Electric boilers",
                "Heat pumps",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Heat plants"})
)

gas_works = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(["Gas works", "For blended natural gas"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Gas works"})
)
gas_works["Natural gas"] = gas_works["Natural gas"] * 0.5
gas_works["Total"] = gas_works.loc[:, ["Coal", "Natural gas"]].sum(1)

oil_refineries = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(["Oil refineries"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Oil refineries"})
)

coal_transformation = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(
            [
                "Blast furnaces",
                "Coke ovens",
                "Patent fuel plants",
                "BKB/peat briquette plants",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Coal transformation"})
)

liquifaction_plants = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(["Gas-to-liquids (GTL) plants", "Coal liquefaction plants"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Liquifaction plants"})
)

other_transformation = (
    energy_balance.loc["Transformation processes", :]
    .loc[
        energy_balance.loc["Transformation processes", :]
        .index.get_level_values(0)
        .isin(
            [
                "Non-specified (transformation)",
                "Charcoal production plants",
                "Petrochemical plants",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Other transformation"})
)

own_use = (
    energy_balance.loc["Energy industry own use and Losses", :]
    .loc[
        energy_balance.loc["Energy industry own use and Losses", :]
        .index.get_level_values(0)
        .isin(
            [
                "Energy industry own use",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Energy industry own use"})
)

losses = (
    energy_balance.loc["Energy industry own use and Losses", :]
    .loc[
        energy_balance.loc["Energy industry own use and Losses", :]
        .index.get_level_values(0)
        .isin(["Losses"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Losses"})
)

industry = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(
            [
                "Chemical and petrochemical",
                "Construction",
                "Food and tobacco",
                "Industry not elsewhere specified",
                "Iron and steel",
                "Machinery",
                "Mining and quarrying",
                "Non-ferrous metals",
                "Non-metallic minerals",
                "Paper, pulp, and print",
                "Textile and leather",
                "Transport equipment",
                "Wood and wood products",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Industry"})
)

transport = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(
            [
                "Domestic aviation",
                "Domestic navigation",
                "Pipeline transport",
                "Rail",
                "Road",
                "Transport not elsewhere specified",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Transport"})
)

residential = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(["Residential"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Residential"})
)

commercial = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(["Commercial and public services"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Commercial and public services"})
)

agriculture = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(["Agriculture/forestry"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Agriculture / forestry"})
)

fishing = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(["Fishing"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Fishing"})
)

nonspecified = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(["Final consumption not elsewhere specified"]),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Non-specified"})
)

nonenergyuse = (
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
        .index.get_level_values(0)
        .isin(
            [
                "Non-energy use in other",
                "Non-energy use in transport",
                "Non-energy use industry/transformation/energy",
            ]
        ),
        :,
    ]
    .sum()
    .to_frame()
    .T.rename(index={0: "Non-energy use"})
)

energy_balance = pd.concat(
    [
        bunkers,electricity_plants,
        chp_plants,
        heat_plants,
        gas_works,
        oil_refineries,
        coal_transformation,
        liquifaction_plants,
        other_transformation,
        own_use,
        losses,
        industry,
        transport,
        residential,
        commercial,
        agriculture,
        fishing,
        nonspecified,
        nonenergyuse,
    ]
)

energy_balance

# endregion

#################################################
# TOTAL FINAL CONSUMPTION BY SOURCE (GW) WEDGES #
#################################################

# region

start_year = 1990
end_year = 2050
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
flow_category = ['Final consumption', 'Supply']
groupby = "Product_category"
nonenergyuse = ['Y','N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[2]
).T

fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[2])

bwedges = ((
        energy_electrified.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[2]
).T

bwedges.index.name = "Year"
bwedges.reset_index(inplace=True)
bwedges2 = pd.melt(
    bwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[2])

addtleffwedges = ((
        (energy_post_upstream - energy_post_addtl_eff).loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[2]
).T

addtleffwedges.index.name = "Year"
addtleffwedges.reset_index(inplace=True)
addtleffwedges2 = pd.melt(
    addtleffwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[2])

upstreamwedges = ((
        (energy_post_upstream - energy_baseline).loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[2]
).T

upstreamwedges.index.name = "Year"
upstreamwedges.reset_index(inplace=True)
upstreamwedges2 = pd.melt(
    upstreamwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[2])


fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[2]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in bwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Avoided use of " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(bwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+7],
            ),
            x=bwedges2["Year"],
            y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[2]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in addtleffwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Efficiency reduction of " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(addtleffwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+14],
            ),
            x=addtleffwedges2["Year"],
            y=addtleffwedges2[addtleffwedges2[groupby] == sub]["TFC, " + unit_name[2]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in upstreamwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Avoided use of upstream " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(upstreamwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+21],
            ),
            x=upstreamwedges2["Year"],
            y=upstreamwedges2[upstreamwedges2[groupby] == sub]["TFC, " + unit_name[2]],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": "Total Final Consumption, "
        + str(sector).replace("slice(None, None, None)", "All Sectors")
        + ", "
        + str(region).replace("slice(None, None, None)", "World")+ ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit_name[2]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()

# endregion

#####################################
# TOTAL FINAL CONSUMPTION BY SOURCE #
#####################################

# region

start_year = 1990
end_year = 2050
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
flow_category = ['Final consumption', 'Supply']
groupby = "Product_long"
nonenergyuse = ['Y', 'N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit[1]
).T

fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit[0])

fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": "Total Final Consumption, "
        + str(sector).replace("slice(None, None, None)", "All Sectors")
        + ", "
        + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit[0]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()

# endregion

#####################################
# TOTAL FINAL CONSUMPTION BY SECTOR #
#####################################

# region

start_year = 1990
end_year = 2050
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
flow_category = ['Final consumption', 'Supply']
groupby = "Sector"
nonenergyuse = ['Y','N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit[1]
).T

fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit[0])

fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": "Total Final Consumption, "
        + str(product_category).replace("slice(None, None, None)", "All Sources")
        + ", "
        + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit[0]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()

# endregion

#####################################
# ELECTRICITY CONSUMPTION BY SECTOR #
#####################################

# region

start_year = 1990
end_year = 2050
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
product = 'Electricity'
flow_category = ['Final consumption', 'Supply']
groupby = "Flow_long" # 'Sector' for sectors, 'Flow_long' for subsectors
nonenergyuse = ['N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            product,
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
).T

fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])

fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": "Electricity Consumption, "
        + str(sector).replace("slice(None, None, None)", "All Sectors")
        + ", "
        + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit_name[1]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()
# endregion

############################################
# ELECTRICITY CONSUMPTION BY SECTOR WEDGES #
############################################

# region

start_year = 1990
end_year = 2050
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
product = 'Electricity'
flow_category = ['Final consumption', 'Supply']
groupby = "Flow_long" # 'Sector' for sectors, 'Flow_long' for subsectors
nonenergyuse = ['N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            product,
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
).T

fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])

bwedges = ((
        energy_electrified.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            product,
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
).T

bwedges.index.name = "Year"
bwedges.reset_index(inplace=True)
bwedges2 = pd.melt(
    bwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])

addtleffwedges = ((
        (energy_post_upstream - energy_post_addtl_eff).loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            product,
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
).T

addtleffwedges.index.name = "Year"
addtleffwedges.reset_index(inplace=True)
addtleffwedges2 = pd.melt(
    addtleffwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])

upstreamwedges = ((
        (energy_post_upstream - energy_baseline).loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            product,
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
).T

upstreamwedges.index.name = "Year"
upstreamwedges.reset_index(inplace=True)
upstreamwedges2 = pd.melt(
    upstreamwedges, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])


fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in bwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Avoided use of " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(bwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+7],
            ),
            x=bwedges2["Year"],
            y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in addtleffwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Efficiency reduction of " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(addtleffwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+14],
            ),
            x=addtleffwedges2["Year"],
            y=addtleffwedges2[addtleffwedges2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )

for sub in upstreamwedges2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name="Avoided use of upstream " + sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(upstreamwedges2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)+21],
            ),
            x=upstreamwedges2["Year"],
            y=upstreamwedges2[upstreamwedges2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )



fig.update_layout(
    title={
        "text": "Electricity Consumption, "
        + str(sector).replace("slice(None, None, None)", "All Sectors")
        + ", "
        + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit_name[1]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()
# endregion

####################################
# ELECTRICITY GENERATION BY SOURCE #
####################################

# region

start_year = 1990
end_year = proj_end_year
df = pd.concat([energy_pathway, energy_baseline])
scenario = 'pathway'
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
flow_category = ['Electricity output']
groupby = "Product_long"
nonenergyuse = ['N']

fig = ((
        df.loc[
            scenario,
            region,
            sector,
            subsector,
            product_category,
            slice(None),
            slice(None),
            flow_category, 
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            nonenergyuse
        ].groupby([groupby]).sum()
    ).loc[:, start_year:end_year]
    * unit_val[1]
)

fig = fig[fig.sum(axis=1)!=0]
fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(
    fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit_name[1])

fig = go.Figure()

for sub in fig2[groupby].unique():
    fig.add_trace(
        go.Scatter(
            name=sub,
            line=dict(
                width=0.5,
                color=colors[
                    pd.DataFrame(fig2[groupby].unique())
                    .set_index(0)
                    .index.get_loc(sub)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
            fill="tonexty",
            stackgroup="1",
        )
    )

fig.update_layout(
    title={
        "text": "Electricity Generation, "
        + str(sector).replace("slice(None, None, None)", "All Sectors")
        + ", "
        + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    yaxis={"title": "TFC, " + unit_name[1]},
    margin_b=0,
    margin_t=20,
    margin_l=10,
    margin_r=10,
)

if show_figs is True:
    fig.show()

# endregion

###########################
# SOLUTION ADOPTION RATES #
###########################

# region

start_year = data_start_year
end_year = proj_end_year
scenario = scenario
region = slice(None)
sector = slice(None)
subsector = slice(None)
product_category = slice(None)
flow_category = slice(None)
nonenergyuse = ['N']

# Percent of electric power that is renewables
electricity = energy_pathway.loc[scenario, region, ['Electric Power'], subsector, product_category, slice(None), ["GEOTHERM", "HYDRO", "ROOFTOP", "SOLARPV", "SOLARTH", "OFFSHORE", "ONSHORE", "TIDE"], ['Electricity output'], slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().divide(energy_pathway.loc[scenario, region, ['Electric Power'], subsector, product_category, slice(None), slice(None), ['Electricity output'], slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().sum(0)) * 100

# Percent of transport energy that is electric or nonelectric renewables
transport = energy_pathway.loc[scenario, region, ['Transportation'], subsector, product_category, slice(None), ['BIODIESEL', 'BIOGASOL','BIOGASES','OBIOLIQ', 'ELECTR', 'RELECTR', 'HYDROGEN'], flow_category, slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().divide(energy_pathway.loc[scenario, region, ['Transportation'], subsector, product_category, slice(None), slice(None), slice(None), slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().sum(0)) * 100

# Percent of buildings energy that is electric or nonelectric renewables
buildings =  energy_pathway.loc[scenario, region, ['Commercial','Residential'], subsector, product_category, slice(None), ['ELECTR', 'SOLARTH', 'MUNWASTER','GEOTHERM'], flow_category, slice(None),['RESIDENT','COMMPUB'], slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].rename(index={'Residential':'Buildings','Commercial':'Buildings'}).groupby(['Sector','Product_long']).sum().divide(energy_pathway.loc[scenario, region, ['Commercial','Residential'], subsector, product_category, slice(None), slice(None), slice(None), slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].rename(index={'Residential':'Buildings','Commercial':'Buildings'}).groupby(['Sector','Product_long']).sum().sum(0)) * 100

# Percent of industry energy that is electric or nonelectric renewables
industry =  energy_pathway.loc[scenario, region, ['Industrial'], subsector, product_category, slice(None), ['ELECTR', 'SOLARTH', 'HYDROGEN', 'MUNWASTER', 'GEOTHERM'], 'Final consumption', slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().divide(energy_pathway.loc[scenario, region, ['Industrial'], subsector, product_category, slice(None), slice(None), 'Final consumption', slice(None), slice(None), slice(None), slice(None), nonenergyuse].loc[:, start_year:end_year].groupby(['Sector','Product_long']).sum().sum(0)) * 100


fig = pd.concat([electricity, transport, buildings, industry]).T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name=["Sector", "Product_long"], value_name="% Adoption")

for vertical in fig2['Sector'].unique():

    fig = go.Figure()

    for subvertical in fig2["Product_long"].unique(): 
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=subvertical,
                line=dict(width=1, color=colors[
                    pd.DataFrame(fig2['Product_long'].unique()).set_index(0).index.get_loc(subvertical)
                ]),
                x=fig2[(fig2["Sector"] == vertical) & (fig2["Product_long"] == subvertical)]["Year"],
                y=fig2[(fig2["Sector"] == vertical) & (fig2["Product_long"] == subvertical)]["% Adoption"],
                fill="tonexty",
                stackgroup="two",
                legendgroup=subvertical,
                showlegend=True,
            )
        )

        # Make historical trace
        fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=1, color="#1c352d"),
            x=fig2[(fig2["Year"] <= data_end_year) & (fig2["Sector"] == vertical) & (fig2["Product_long"] == subvertical)]["Year"],
            y=fig2[(fig2["Year"] <= data_end_year) & (fig2["Sector"] == vertical) & (fig2["Product_long"] == subvertical)]["% Adoption"],
            stackgroup="one",
            legendgroup=subvertical,
            showlegend=False
        )
    )

    fig.update_layout(
        title={
            "text": "Percent of Total Adoption, " + vertical + ", "
            + str(region).replace("slice(None, None, None)", "World").capitalize() + ", "
        + str(scenario).capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "% Adoption"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
    )

    if show_figs is True:
        fig.show()
    


# endregion

#####################################
# SOLUTION ADOPTION RATES DASHBOARD #
#####################################

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
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Transport")]["Year"],
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
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Buildings")]["Year"],
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
            x=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Industrial")]["Year"],
            y=fig2[(fig2["Year"] <= 2020) & (fig2["Sector"] == "Industrial")][
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

    '''
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
    '''
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
                y=fig2[
                    (fig2["Year"] <= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
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
                y=fig2[
                    (fig2["Year"] >= 2020)
                    & (fig2["Sector"] == "Carbon Dioxide Removal")
                ]["% Adoption"],
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

#####################################
# SUBVECTOR SOLUTION ADOPTION RATES #
#####################################

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
        "Carbon Dioxide Removal",
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
                    fillcolor=colors[
                        pd.DataFrame(fig2["Metric"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
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
                + "DAU21"
                + ", "
                + sector
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            # xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"},
            legend={"traceorder": "reversed"},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, x=0.05, font=dict(size=10)
            ),
            margin_t=100,
            margin_b=0,
            margin_l=15,
            margin_r=15,
        )
        """
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
        """
        """
        fig.add_vrect(
            x0=start_year, x1=2020, fillcolor="grey", opacity=0.6, line_width=0
        )
        """
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

#####################################
# SOLUTION ADOPTION RATES BY REGION #
#####################################

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

#######################################################
# SOLUTION ADOPTION RATES BY REGION SNAPSHOT BARCHART #
#######################################################

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

###############################################
# SUBVECTOR SOLUTION ADOPTION RATES UNSTACKED #
###############################################

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
                    x=fig2[fig2["Year"] <= 2020]["Year"],
                    y=fig2[(fig2["Year"] <= 2020) & (fig2["Metric"] == x)][
                        "% Adoption"
                    ],
                    fill="none",
                    stackgroup=x,
                    legendgroup=x,
                )
            )

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
                        dash="dot",
                    ),
                    x=fig2[fig2["Year"] >= 2020]["Year"],
                    y=fig2[(fig2["Year"] >= 2020) & (fig2["Metric"] == x)][
                        "% Adoption"
                    ],
                    fill="none",
                    legendgroup=x,
                    showlegend=False,
                )
            )
        """
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
        """
        fig.update_layout(
            title={
                "text": "Percent of Total PD Adoption, "
                + "DAU21"
                + ", "
                + sector
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            # xaxis={"title": "Year"},
            yaxis={"title": "% Adoption"},
            legend={"traceorder": "reversed"},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, x=0.1, font=dict(size=10)
            ),
            margin_b=0,
            margin_t=100,
            margin_l=15,
            margin_r=15,
        )
        """
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
        """
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

#########################################################
# AFOLU SUBVECTOR SOLUTION ADOPTION RATES AS MAX EXTENT #
#########################################################

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

################################################
# ACTUAL VS. PROJECTED SOLUTION ADOPTION RATES #
################################################

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

######################################
# SOLUTION ADOPTION RATES STAR CHART #
######################################

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

######################################
# SOLUTION ADOPTION RATES KNEE/ELBOW #
######################################

# region
"""
for i in range(0, len(region_list)):
    fig = adoption_curves.loc[region_list[i], slice(None), scenario] * 100
    kneedle = KneeLocator(
        fig.columns.values,
        fig.loc["Electricity"].values,
        S=1.0,
        curve="concave",
        direction="increasing",
    )
"""
# endregion

#################
# GHG EMISSIONS #
#################

# region

scenario = scenario
start_year = 2000
i = 0

ndcs = [
    [(2030, 2050), (24, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2025, 2050, 2030, 2050),
        (4.86, 2.84, 2.84, 0),
        ("NDC", "NDC 2050 est.", "50% by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.4, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.17),
    (3, 3),
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("50% by 2030", "NDC", "Net-zero by 2050"),
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
            line=dict(width=0.5, color=cl["V6: Forests & Wetlands"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="fw",
            fillcolor=cl["V6: Forests & Wetlands"][0],
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
            line=dict(width=0.5, color=cl["V5: Agriculture"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Regenerative Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
            fillcolor=cl["V5: Agriculture"][0],
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color=cl["V4: Industry"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V4: Industry"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color=cl["V3: Buildings"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V3: Buildings"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color=cl["V2: Transport"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V2: Transport"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color=cl["V1: Electricity"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V1: Electricity"][0],
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

    # Targets/NDCS

    # region

    if region_list[i] in ["World "]:

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][0]],
                y=[21.65],
                marker_color="#f71be9",
                name=ndcs[i][2][0],
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#f71be9",
                name=ndcs[i][2][0],
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=True,
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% by 2030",
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
        title={
            "text": "Emissions, " + "DAU21" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10)),
        margin_b=0,
        margin_t=90,
        margin_l=15,
        margin_r=15,
    )
    """
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
    """
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

######################################
# GHG EMISSIONS MITIGATION POTENTIAL #
######################################

# region

scenario = scenario
start_year = 2000
i = 0

ndcs = [
    [(2030, 2050), (24, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2025, 2050, 2030, 2050),
        (4.86, 2.84, 2.84, 0),
        ("NDC", "NDC 2050 est.", "50% by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.4, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.17),
    (3, 3),
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("50% by 2030", "NDC", "Net-zero by 2050"),
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
            line=dict(width=0.5, color=cl["V6: Forests & Wetlands"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tozeroy",
            stackgroup="fw",
            fillcolor=cl["V6: Forests & Wetlands"][0],
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
            line=dict(width=0.5, color=cl["V5: Agriculture"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Regenerative Agriculture"]["Emissions, GtCO2e"],
            fill=fill,
            stackgroup=stackgroup,
            fillcolor=cl["V5: Agriculture"][0],
        )
    )

    fill = "tonexty"
    stackgroup2 = stackgroup

    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color=cl["V4: Industry"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V4: Industry"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color=cl["V3: Buildings"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V3: Buildings"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color=cl["V2: Transport"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V2: Transport"][0],
        )
    )

    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color=cl["V1: Electricity"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup=stackgroup2,
            fillcolor=cl["V1: Electricity"][0],
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

    # Targets/NDCS

    # region

    if region_list[i] in ["World "]:

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][0]],
                y=[21.65],
                marker_color="#f71be9",
                name=ndcs[i][2][0],
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#f71be9",
                name=ndcs[i][2][0],
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=True,
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=pd.Series(2030),
                y=pd.Series(em_hist.loc[region_list[i], 2019].values[0] / 2000),
                marker_color="#f71be9",
                name="50% by 2030",
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
        title={
            "text": "Emissions, " + "DAU21" + ", " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1, x=0, font=dict(size=10)),
        margin_b=0,
        margin_t=90,
        margin_l=15,
        margin_r=15,
    )
    """
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
    """
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

###############################
# GHG EMISSIONS BY SUBVECTORS #
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

for i in range(0, len(region_list)):

    em_electricity = em.loc[
        region_list[i], ["Electricity"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_electricity = (
        em_electricity.loc[~(em_electricity == 0).all(axis=1)]
        .rename(index={"Fossil Fuel Heat": "Fossil Fuels"})
        .groupby(["Region", "Sector", "Metric", "Gas", "Scenario"])
        .sum()
    )

    em_transport = em.loc[
        region_list[i], ["Transport"], slice(None), slice(None), scenario
    ].loc[:, start_year:long_proj_end_year]
    em_transport = em_transport.loc[~(em_transport == 0).all(axis=1)].rename(
        index={"Fossil Fuel Heat": "Fossil Fuels"}
    )

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

        if sector == "Electricity":
            fig3 = fig2[fig2["Metric"] == "Fossil Fuels"]
            fig2 = fig3.append(fig2[fig2["Metric"] != "Fossil Fuels"])

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
                    fillcolor=colors[
                        pd.DataFrame(fig2["Metric"].unique())
                        .set_index(0)
                        .index.get_loc(sub)
                    ],
                )
            )

        fig.update_layout(
            title={
                "text": " Emissions in "
                + str(sector)
                + ", "
                + "V6"
                + ", "
                + region_list[i],
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            # xaxis={"title": "Year"},
            yaxis={"title": "GtCO2e/yr"},
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.03, x=0.06, font=dict(size=10)
            ),
            margin_t=120,
            margin_b=0,
            margin_l=15,
            margin_r=15,
        )
        """
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
        """
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

#####################################################
# GHG EMISSIONS ONE CHART PER SECTOR, GAS BREAKDOWN #
#####################################################

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

#####################################################
# GHG EMISSIONS ONE CHART PER GAS, SECTOR BREAKDOWN #
#####################################################

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

###############################################
# GHG EMISSIONS INDUSTRY FF HEAT REGION STACK #
###############################################

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

###############################
# GHG EMISSIONS AS RELATIVE % #
###############################

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

###################################
# GHG EMISSIONS MITIGATION WEDGES #
###################################

# region

scenario = "pathway"
start_year = start_year
altscen = str()

ndcs = [
    [(2030, 2050), (24, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    [
        (2030, 2050),
        (2.84, 0),
        ("50% by 2030", "Net-zero by 2050"),
    ],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.4, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    (2030, 0.398),
    (3, 3),
    (2030, 2.17),
    (3, 3),
    [
        (2030, 2030, 2050),
        (12.96, 6.15, 0),
        ("50% by 2030", "NDC", "Net-zero by 2050"),
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

em_hist[2020] = em_hist.loc[:, 2019]

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

        cdr2 = (
            pd.read_csv("podi/data/cdr_curve.csv")
            .set_index(["Region", "Sector", "Scenario"])
            .fillna(0)
        )
        cdr2.columns = cdr2.columns.astype(int)

        em_mit_cdr = (
            cdr2.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .sum()
            .rename("CDR")
        )
        """
        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", slice(None), scenario, :]
            .sum()
            .squeeze()
            .rename("CDR")
        )
        
        em_mit_cdr[2019] = 0
        em_mit_cdr[2020] = 0
        """
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
        cdr2 = (
            pd.read_csv("podi/data/cdr_curve.csv")
            .set_index(["Region", "Sector", "Scenario"])
            .fillna(0)
        )
        cdr2.columns = cdr2.columns.astype(int)

        em_mit_cdr = (
            cdr2.loc[region_list[i], "Carbon Dioxide Removal", scenario, :]
            .sum()
            .rename("CDR")
        )

        """
        em_mit_cdr = (
            cdr.loc[region_list[i], "Carbon Dioxide Removal", slice(None), scenario, :]
            .sum()
            .squeeze()
            .rename("CDR")
        )

        em_mit_cdr[2019] = 0
        em_mit_cdr[2020] = 0
        """
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
                line=dict(width=0.5, color=cl["V7: CDR"][0]),
                x=fig2["Year"],
                y=fig2[fig2["Sector"] == "CDR"]["Emissions, GtCO2e"],
                fill="tonexty",
                stackgroup="one",
                fillcolor=cl["V7: CDR"][0],
            )
        )

        fig.add_annotation(
            text="Cumulative CDR 2020-2030: "
            + str(
                fig2[(fig2["Sector"] == "CDR") & (fig2["Year"] < 2031)][
                    "Emissions, GtCO2e"
                ]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.31,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2030-2040: "
            + str(
                fig2[
                    (fig2["Sector"] == "CDR")
                    & (fig2["Year"] > 2030)
                    & (fig2["Year"] < 2041)
                ]["Emissions, GtCO2e"]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.21,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2040-2050: "
            + str(
                fig2[
                    (fig2["Sector"] == "CDR")
                    & (fig2["Year"] > 2040)
                    & (fig2["Year"] < 2051)
                ]["Emissions, GtCO2e"]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.11,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=4,
            bgcolor="#ffffff",
            opacity=1,
        )

        fig.add_annotation(
            text="Cumulative CDR 2050-2060: "
            + str(
                fig2[
                    (fig2["Sector"] == "CDR")
                    & (fig2["Year"] > 2050)
                    & (fig2["Year"] < 2061)
                ]["Emissions, GtCO2e"]
                .values.sum()
                .round(1)
            )
            + " GtCO2e",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.01,
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
            line=dict(width=0.5, color=cl["V6: Forests & Wetlands"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Forests & Wetlands"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V6: Forests & Wetlands"][0],
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V5: Agriculture",
            line=dict(width=0.5, color=cl["V5: Agriculture"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Agriculture"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V5: Agriculture"][0],
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V4: Industry",
            line=dict(width=0.5, color=cl["V4: Industry"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Industry"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V4: Industry"][0],
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V3: Buildings",
            line=dict(width=0.5, color=cl["V3: Buildings"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Buildings"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V3: Buildings"][0],
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V2: Transport",
            line=dict(width=0.5, color=cl["V2: Transport"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Transport"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V2: Transport"][0],
        )
    )
    fig.add_trace(
        go.Scatter(
            name="V1: Electricity",
            line=dict(width=0.5, color=cl["V1: Electricity"][0]),
            x=fig2["Year"],
            y=fig2[fig2["Sector"] == "Electricity"]["Emissions, GtCO2e"],
            fill="tonexty",
            stackgroup="one",
            fillcolor=cl["V1: Electricity"][0],
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
                name="SSP2-RCP1.9",
                line=dict(
                    width=2, color=cl["SSP2-RCP1.9"][0], dash=cl["SSP2-RCP1.9"][1]
                ),
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
                name="NCSmax",
                line=dict(width=2, color=cl["DAU21"][0], dash=cl["DAU21"][1]),
                x=pd.Series(
                    em_targets.loc["SSP2-26", near_proj_start_year:].index.values
                ),
                y=pd.Series(
                    (
                        spacer.loc[near_proj_start_year:].values
                        + em_mit_cdr.loc[near_proj_start_year:].values
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
                name="SR1.5",
                line=dict(width=2, color=cl["DAU21+CDR"][0], dash=cl["DAU21+CDR"][1]),
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
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[ndcs[i][0][1]],
                y=[ndcs[i][1][1]],
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#f71be9",
                name=ndcs[i][2][0],
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker_color="#211df2",
                name=ndcs[i][2][1],
                showlegend=True,
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
                name="50% by 2030",
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
            line=dict(width=2, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
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
        """
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

    """
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
    """
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            x=0.05,
            font=dict(size=10),
            traceorder="reversed",
        )
    )

    fig.update_layout(
        margin_b=0,
        margin_t=110,
        margin_l=15,
        margin_r=15,
        title={
            "text": "Emissions Mitigated, NCSmax, " + region_list[i],
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "Year"},
        yaxis={"title": "GtCO2e/yr"},
    )

    if show_figs is True:
        fig.show()
        fig.write_image("podi/Figure A.svg")
        fig.write_image("podi/Figure 4.svg")
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

###############################################
# GHG EMISSIONS MITIGATION WEDGES, SUBVECTORS #
###############################################

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

#####################################
# GHG EMISSIONS MITIGATION BARCHART #
#####################################

# region

ndcs = [
    [(2030, 2050), (24, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
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
    [(2030, 2050), (2.4, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
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
    [(2030, 2050), (24, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (2.99, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (0.69, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (2.39, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (0.26, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (1.02, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    (0, 0),
    [(2030, 2050), (12, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (1.75, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
    [(2030, 2050), (0.55, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
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

#################
# NDC ESTIMATES #
#################

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
    [(2030, 2050), (25, 0), ("50% by 2030", "Net-zero by 2050")],
    (3, 3),
    [(2030, 2050), (2.84, 0), ("NDC", "Net-zero by 2050")],
    (3, 3),
    (2030, 1.2),
    [(2030, 2050), (2.3, 0), ("50% by 2030", "Net-zero by 2050")],
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

########################
# ENERGY DEMAND WEDGES #
########################

# region

start_year = 1990
end_year = proj_end_year
scenario = scenario
region = slice(None)
product_category = slice(None)
product = slice(None)
flow_category = "Final consumption"  # Choose 'Final consumption' (applicable to Industrial/Transportation/Commercial/Residential); 'Energy industry own use and Losses' (applicable to Electric Power/Industrial/Transportation); 'Supply'(applicable to Transportation); 'Transformation processes'(applicable to Electric Power/Industrial); 'Electricity output'(applicable to Electric Power/Industrial); 'Heat output'(applicable to Industrial)
flow = slice(None)
groupby = "Product_long"  # Choose 'Subsector', 'Product_category', 'Product', 'Flow', 'Hydrogen', 'Flexible', 'Non-Energy Use'

for sector in energy_pathway.index.get_level_values(2).unique():
    # Calculate wedge due to removal of upstream demand 
        index = [
        "Scenario",
        "Region",
        "Sector",
        "Subsector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Hydrogen",
        "Flexible",
        "Non-Energy Use",
    ]

    energy_demand_post_upstream = pd.DataFrame(
        pd.read_csv("podi/data/energy_demand_post_upstream.csv")
    ).set_index(index)
    energy_demand_post_upstream.columns = energy_demand_post_upstream.columns.astype(int)
    energy_demand_post_upstream.index.rename(level=6,'Reduced demand from fossil fuel industry upstream processes')

    # Calculate wedge due to additional efficiency measures
    energy_demand_post_addtl_eff = pd.DataFrame(
        pd.read_csv("podi/data/energy_demand_post_addtl_eff.csv")
    ).set_index(index)
    energy_demand_post_addtl_eff.columns = energy_demand_post_addtl_eff.columns.astype(int)
    energy_demand_post_addtl_eff.index.rename(level=6,'Reduced demand due to additional efficiency')

    # Calculate wedge due to reduced demand due to electrification
    energy_demand_electrified = pd.DataFrame(
        pd.read_csv("podi/data/energy_demand_post_ef.csv")
    ).set_index(index)
    energy_demand_electrified.columns = energy_demand_electrified.columns.astype(int)
    energy_demand_electrified.index.rename(level=6,'Reduced demand due to reduced work required for electricity vs combustion'))

    fig = ((pd.concat([energy_demand_baseline - energy_demand_post_upstream, energy_demand_post_upstream - energy_demand_post_addtl_eff, energy_demand_electrified , energy_pathway]).loc[
                scenario,
                region,
                sector,
                slice(None),
                product_category,
                slice(None),
                product,
                flow_category,
                slice(None),
                flow,
            ]
            .groupby([groupby])
            .sum()).loc[:, start_year:end_year] * unit[1]).T

    fig.index.name = "Year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="Year", var_name=[groupby], value_name="TFC, " + unit[0]
    )

    fig = go.Figure()

    for sub in fig2[groupby].unique():
        fig.add_trace(
            go.Scatter(
                name=sub,
                line=dict(
                    width=0.5,
                    color=colors[
                        pd.DataFrame(fig2[groupby].unique())
                        .set_index(0)
                        .index.get_loc(sub)
                    ],
                ),
                x=fig2["Year"],
                y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                fill="tonexty",
                stackgroup="1",
            )
        )

    fig.update_layout(
        title={
            "text": "Energy Consumption, "
            + str(sector)
            + ", "
            + str(region).replace("slice(None, None, None)", "World"),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "TFC, " + unit[0]},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
    )

    if show_figs is True:
        fig.show()


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

cdr2 = (
    pd.read_csv("podi/data/cdr_curve.csv")
    .set_index(["Region", "Sector", "Scenario"])
    .fillna(0)
)
cdr2.columns = cdr2.columns.astype(int)

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
    30,
)
"""
results19 = pd.DataFrame(
    results.loc[
        "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
    ].loc[2010:]
).T
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
).values - (cdr2.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


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
        line=dict(width=3, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
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
        line=dict(width=3, color=cl["DAU21"][0], dash=cl["DAU21"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-RCP1.9",
        line=dict(width=3, color=cl["SSP2-RCP1.9"][0], dash=cl["SSP2-RCP1.9"][1]),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="SR1.5",
        line=dict(width=3, color=cl["DAU21+CDR"][0], dash=cl["DAU21+CDR"][1]),
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
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)),
    margin_b=0,
    margin_t=60,
    margin_l=15,
    margin_r=15,
    yaxis=dict(tickmode="linear", tick0=325, dtick=25),
)
"""
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
"""

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
        ]
        .loc[:, 2010:]
        .multiply([1, 25e-3, 298e-3], axis=0)
        .sum()
    ).T,
    "quadratic",
    19,
)
"""
results19 = pd.DataFrame(
    results.loc[
        "GCAM4", "SSP2-19", "World", "Diagnostics|MAGICC6|Concentration|CO2"
    ].loc[2010:]
).T
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
).values - (cdr2.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


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
        line=dict(width=3, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
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
        line=dict(width=3, color=cl["DAU21"][0], dash=cl["DAU21"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Cpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-RCP1.9",
        line=dict(width=3, color=cl["SSP2-RCP1.9"][0], dash=cl["SSP2-RCP1.9"][1]),
        x=results19.loc[:, 2020:2100].columns,
        y=results19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="SR1.5",
        line=dict(width=3, color=cl["DAU21+CDR"][0], dash=cl["DAU21+CDR"][1]),
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
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "ppm CO2e"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)),
    margin_b=0,
    margin_t=60,
    margin_l=15,
    margin_r=15,
    yaxis=dict(tickmode="linear", tick0=350, dtick=25),
)
"""
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
"""
if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/ghgconc-" + "World " + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

#########################
# GHG RADIATIVE FORCING #
#########################

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
"""
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
    ].loc[:, 2010:]
)


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
).values - (cdr2.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


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
        line=dict(width=3, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
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
        line=dict(width=3, color=cl["DAU21"][0], dash=cl["DAU21"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-RCP1.9",
        line=dict(width=3, color=cl["SSP2-RCP1.9"][0], dash=cl["SSP2-RCP1.9"][1]),
        x=F19.loc[:, 2020:2100].columns,
        y=F19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="SR1.5",
        line=dict(width=3, color=cl["DAU21+CDR"][0], dash=cl["DAU21+CDR"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Fcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

fig.update_layout(
    title={"text": "Radiative Forcing", "xanchor": "center", "x": 0.5, "y": 0.99},
    # xaxis={"title": "Year"},
    yaxis={"title": "W/m2"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)),
    margin_b=0,
    margin_t=60,
    margin_l=15,
    margin_r=15,
    yaxis=dict(tickmode="linear", tick0=0, dtick=0.5),
)

"""
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
"""

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
"""
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

cdr2 = (
    pd.read_csv("podi/data/cdr_curve.csv")
    .set_index(["Region", "Sector", "Scenario"])
    .fillna(0)
)
cdr2.columns = cdr2.columns.astype(int)

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
).values - (cdr2.loc["World ", "Carbon Dioxide Removal", "pathway"] / 3670).values


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

fig = make_subplots(specs=[[{"secondary_y": True}]])

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
        name="Historical",
        line=dict(width=3, color="black"),
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=hist.loc[:, data_start_year:long_proj_end_year].squeeze(),
        fill="none",
        stackgroup="hist",
        legendgroup="hist",
        showlegend=False,
    ),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
    )
)

fig.add_trace(
    go.Scatter(
        name="Baseline",
        line=dict(width=3, color=cl["Baseline"][0], dash=cl["Baseline"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tb.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="baseline",
        legendgroup="baseline",
        showlegend=False,
    ),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(
        name="DAU21",
        line=dict(width=3, color=cl["DAU21"][0], dash=cl["DAU21"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="pd21",
        legendgroup="pd21",
    )
)

fig.add_trace(
    go.Scatter(
        name="SSP2-RCP1.9",
        line=dict(width=3, color=cl["SSP2-RCP1.9"][0], dash=cl["SSP2-RCP1.9"][1]),
        x=T19.loc[:, 2020:2100].columns,
        y=T19.loc[:, 2020:2100].squeeze(),
        fill="none",
        stackgroup="19",
        legendgroup="19",
    )
)

fig.add_trace(
    go.Scatter(
        name="SR1.5",
        line=dict(width=3, color=cl["DAU21+CDR"][0], dash=cl["DAU21+CDR"][1]),
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, "CO2e"],
        fill="none",
        stackgroup="26",
        legendgroup="26",
    )
)

# temp range

# region

# Historical
# region

temp_range = pd.read_csv("podi/data/temp_range.csv").set_index("Range")
temp_range.columns = temp_range.columns.astype(int)

fig.add_trace(
    go.Scatter(
        name="Historical_upper",
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=temp_range.loc["83p", data_start_year:data_end_year].squeeze(),
        mode="lines",
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False,
    ),
)

fig.add_trace(
    go.Scatter(
        name="Historical_upper",
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=temp_range.loc["83p", data_start_year:data_end_year].squeeze(),
        mode="lines",
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False,
    ),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(
        name="Est. range",
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=temp_range.loc["17p", data_start_year:data_end_year].squeeze(),
        marker=dict(color="#444"),
        line=dict(width=0),
        mode="lines",
        fillcolor="rgba(255,155,5,0.15)",
        fill="tonexty",
        showlegend=False,
    ),
)

fig.add_trace(
    go.Scatter(
        name="Historical_lower",
        x=np.arange(data_start_year, data_end_year + 1, 1),
        y=temp_range.loc["17p", data_start_year:data_end_year].squeeze(),
        marker=dict(color="#444"),
        line=dict(width=0),
        mode="lines",
        fillcolor="rgba(255,155,5,0.15)",
        fill="tonexty",
        showlegend=False,
    ),
    secondary_y=True,
)
# endregion

# SR1.5
# region

fig.add_trace(
    go.Scatter(
        name="sr1.5_upper",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, "CO2e"] * 1.2,
        mode="lines",
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False,
    ),
)

fig.add_trace(
    go.Scatter(
        name="sr1.5_lower",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tcdr.loc[data_end_year:, "CO2e"] * 0.8,
        marker=dict(color="#444"),
        line=dict(width=0),
        mode="lines",
        fillcolor="rgba(51,102,204,0.15)",
        fill="tonexty",
        showlegend=False,
    ),
)

# endregion

"""
# DAU21
# region
fig.add_trace(
    go.Scatter(
        name="dau21_upper",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"] * 1.2,
        mode="lines",
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False,
    ),
)

fig.add_trace(
    go.Scatter(
        name="dau21_lower",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"] * 0.8,
        marker=dict(color="#444"),
        line=dict(width=0),
        mode="lines",
        fillcolor="rgba(153,0,153,0.15)",
        fill="tonexty",
        showlegend=False,
    ),
)

# endregion
"""

# DAU21 expanding
# region

tproj_err = pd.read_csv("podi/data/temp_range.csv").set_index("Range")
tproj_err.columns = temp_range.columns.astype(int)

fig.add_trace(
    go.Scatter(
        name="dau21_upper",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"] * 1.2
        + temp_range.loc["dau21_upper", data_end_year:long_proj_end_year].squeeze(),
        mode="lines",
        marker=dict(color="#444"),
        line=dict(width=0),
        showlegend=False,
    ),
)

fig.add_trace(
    go.Scatter(
        name="dau21_lower",
        x=np.arange(data_end_year, long_proj_end_year + 1, 1),
        y=Tpd.loc[data_end_year:, "CO2e"] * 0.8
        + temp_range.loc["dau21_lower", data_end_year:long_proj_end_year].squeeze(),
        marker=dict(color="#444"),
        line=dict(width=0),
        mode="lines",
        fillcolor="rgba(153,0,153,0.15)",
        fill="tonexty",
        showlegend=False,
    ),
)

# endregion

# endregion

fig.update_layout(
    title={"text": "Global Mean Temperature", "xanchor": "center", "x": 0.5, "y": 0.99},
    # xaxis={"title": "Year"},
    yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0.1, font=dict(size=10)),
    margin_b=0,
    margin_t=60,
    margin_l=15,
    margin_r=15,
    yaxis=dict(tickmode="linear", tick0=0.5, dtick=0.25),
    yaxis2=dict(tickmode="linear", tick0=0.5, dtick=0.25),
)

if show_annotations is True:
    """
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
    """
if show_figs is True:
    fig.show()
if save_figs is True:
    pio.write_html(
        fig,
        file=("./charts/temp-" + "World" + ".html").replace(" ", ""),
        auto_open=False,
    )

# endregion

#############
# CDR COSTS #
#############

# region

# eCDR

# region

cdr_pathway = pd.read_csv("podi/data/cdr_curve.csv").set_index(
    ["Region", "Sector", "Scenario"]
)
cdr_pathway.columns = cdr_pathway.columns.astype(int)

costs = []

for scen in ["pathway", "dauffi", "V5", "V6", "daupl", "NCSmax"]:
    cdr_i, cdr_cost_i, cdr_energy_i = cdr_mix(
        cdr_pathway.loc["World ", "Carbon Dioxide Removal", scen].loc[2020:].to_list(),
        grid_em_def,
        heat_em_def,
        transport_em_def,
        fuel_em_def,
        2020,
        long_proj_end_year,
    )

    costs = pd.DataFrame(costs).append(
        pd.DataFrame(cdr_cost_i).T.rename(index={0: scen})
    )

costs.columns = np.arange(2020, 2101, 1)
costs = (curve_smooth(-costs, "quadratic", 7)).clip(lower=0) / 1e6
costs.rename(index={"pathway": "DAU21", "dauffi": "V4", "daupl": "PL"}, inplace=True)
costs.index.name = "Scenario"

cdr_costs = costs

# endregion

# NCS

# region
costs_ra = pd.Series([0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55])
costs_fw = pd.Series([22, 24, 22, 55, 0, 30, 55, 36])
costs_fwra = pd.Series(
    [22, 24, 22, 55, 0, 30, 55, 36, 0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55]
)
costs_rafw = pd.Series(
    [0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55, 22, 24, 22, 55, 0, 30, 55, 36]
)


afolu_em_mit_dau21 = (
    (
        (
            afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture", "Forests & Wetlands"],
                slice(None),
                slice(None),
                "baseline",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture", "Forests & Wetlands"],
                slice(None),
                slice(None),
                "pathway",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        )
        .groupby(["Region", "Sector", "Metric"])
        .sum()
    )
    .multiply(costs_fwra.T.values, "index")
    .sum()
)

afolu_em_mit_v4 = (
    (
        (
            afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture", "Forests & Wetlands"],
                slice(None),
                slice(None),
                "baseline",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture", "Forests & Wetlands"],
                slice(None),
                slice(None),
                "pathway",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        )
        * 0
    )
    .groupby(["Region", "Sector", "Metric"])
    .sum()
    .sum()
)

afolu_em_mit_v5 = (
    (
        (
            afolu_em1.loc[
                "World ", ["Forests & Wetlands"], slice(None), slice(None), "baseline"
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em1.loc[
                "World ", ["Forests & Wetlands"], slice(None), slice(None), "pathway"
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        ).append(
            afolu_em.loc[
                "World ",
                ["Regenerative Agriculture"],
                slice(None),
                slice(None),
                "baseline",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em.loc[
                "World ",
                ["Regenerative Agriculture"],
                slice(None),
                slice(None),
                "pathway",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        )
    )
    .groupby(["Region", "Sector", "Metric"])
    .sum()
).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

afolu_em_mit_v6 = (
    (
        (
            afolu_em.loc[
                "World ", ["Forests & Wetlands"], slice(None), slice(None), "baseline"
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em.loc[
                "World ", ["Forests & Wetlands"], slice(None), slice(None), "pathway"
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        ).append(
            afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture"],
                slice(None),
                slice(None),
                "baseline",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
            - afolu_em1.loc[
                "World ",
                ["Regenerative Agriculture"],
                slice(None),
                slice(None),
                "pathway",
            ]
            .loc[:, 2020:]
            .droplevel("Scenario")
        )
    )
    .groupby(["Region", "Sector", "Metric"])
    .sum()
).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

afolu_em_mit_v5v6 = (
    (
        afolu_em.loc[
            "World ",
            ["Forests & Wetlands", "Regenerative Agriculture"],
            slice(None),
            slice(None),
            "baseline",
        ]
        .loc[:, 2020:]
        .droplevel("Scenario")
        - afolu_em.loc[
            "World ",
            ["Forests & Wetlands", "Regenerative Agriculture"],
            slice(None),
            slice(None),
            "pathway",
        ]
        .loc[:, 2020:]
        .droplevel("Scenario")
    )
    .groupby(["Region", "Sector", "Metric"])
    .sum()
).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

"""
em_pathway = afolu_em1.loc[slice(None), slice(None),slice(None), slice(None),'pathway',:]
em_baseline = afolu_em1.loc[slice(None), slice(None),slice(None), slice(None),'baseline',:]
"""
# run section to get em_mitigated_alt for PL

afolu_em_mit_pl = (em_mitigated_alt.loc[["World "]].loc[:, 2020:]).multiply(
    costs_fwra.T.values, "index"
).sum() - afolu_em_mit_dau21

afolu_costs = (
    pd.DataFrame(
        [
            afolu_em_mit_dau21 * 0,
            afolu_em_mit_v4 * 0,
            afolu_em_mit_v5,
            afolu_em_mit_v6,
            afolu_em_mit_pl,
            afolu_em_mit_v5v6,
        ]
    ).rename(index={0: "DAU21", 1: "V4", 2: "V5", 3: "V6", 4: "PL", 5: "NCSmax"})
    / 1e6
)

afolu_costs.index.name = "Scenario"

# endregion

costs = cdr_costs.append(afolu_costs).groupby("Scenario").sum()

cdr_costs = pd.DataFrame(pd.read_csv("cdr costs line28228.csv")).set_index("Scenario")

afolu_costs = pd.DataFrame(pd.read_csv("afolu costs line28228.csv")).set_index(
    "Scenario"
)

costs = pd.DataFrame(pd.read_csv("costs line28228.csv")).set_index("Scenario")

costs.columns = costs.columns.astype(int)
show_figs = True

# Plot NCS annual

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = afolu_costs.clip(lower=0)

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "NCS Cost, World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# Plot eCDR annual

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = cdr_costs.clip(lower=0)

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "eCDR Cost, World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# Plot Total annual

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = costs.clip(lower=0)

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "Total Cost, World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# Plot NCS cumulative

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = (afolu_costs.clip(lower=0)).cumsum(axis=1).loc[:, :2060]

fig.loc["DAU21"] = fig.loc["DAU21"] + 0.06

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "NCS Cumulative Cost, World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cumulative Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# Plot eCDR cumulative

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = cdr_costs.clip(lower=0).cumsum(axis=1).loc[:, :2060]

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "eCDR Cumulative Cost, World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cumulative Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# Plot Total cumulative

# region

scenario = scenario
start_year = 2020
i = 0

colors = px.colors.qualitative.Vivid

fig = costs.clip(lower=0).cumsum(axis=1).loc[:, :2060]

fig = fig.T
fig.index.name = "Year"
fig.reset_index(inplace=True)
fig2 = pd.melt(fig, id_vars="Year", var_name="Scenario", value_name="Cost")

fig = go.Figure()

for x in fig2["Scenario"].unique():
    fig.add_trace(
        go.Scatter(
            name=x,
            line=dict(
                width=3,
                color=colors[
                    pd.DataFrame(fig2["Scenario"].unique())
                    .set_index(0)
                    .index.get_loc(x)
                ],
            ),
            x=fig2["Year"],
            y=fig2[fig2["Scenario"] == x]["Cost"],
            fill="none",
            stackgroup=x,
            legendgroup=x,
        )
    )

fig.update_layout(
    title={
        "text": "Total Cumulative Cost (NCS + eCDR), World ",
        "xanchor": "center",
        "x": 0.5,
        "y": 0.99,
    },
    # xaxis={"title": "Year"},
    yaxis={"title": "Cumulative Cost [$T]"},
)

fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.3, font=dict(size=10)),
    margin_b=0,
    margin_t=70,
    margin_l=15,
    margin_r=15,
)

if show_figs is True:
    fig.show()

# endregion

# endregion
