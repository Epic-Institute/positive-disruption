#!/usr/bin/env python

# region
import warnings
import numpy as np
import pandas as pd
import pyam
from podi.energy import energy
from podi.afolu import afolu
from podi.emissions import emissions
from podi.results_analysis import results_analysis
from podi.cdr.cdr_main import cdr_mix
from podi.climate import climate
from podi.cdr.cdr_util import (
    grid_em_def,
    heat_em_def,
    transport_em_def,
    fuel_em_def,
)

warnings.simplefilter(action="ignore", category=FutureWarning)

# endregion

# Select model and choose a scenario name
model = "PD22"
scenario = "pathway"
data_start_year = 1990
data_end_year = 2020
proj_end_year = 2100

##########
# ENERGY #
##########

recalc_energy = False
# region

if recalc_energy is True:
    energy(model, scenario, data_start_year, data_end_year, proj_end_year)
index = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "product_short",
    "flow_category",
    "flow_long",
    "flow_short",
    "unit",
]

energy_post_upstream = pd.DataFrame(
    pd.read_csv("podi/data/energy_post_upstream.csv")
).set_index(index)
energy_post_upstream.columns = energy_post_upstream.columns.astype(int)

energy_post_addtl_eff = pd.DataFrame(
    pd.read_csv("podi/data/energy_post_addtl_eff.csv")
).set_index(index)
energy_post_addtl_eff.columns = energy_post_addtl_eff.columns.astype(int)

energy_electrified = pd.DataFrame(
    pd.read_csv("podi/data/energy_electrified.csv")
).set_index(index)
energy_electrified.columns = energy_electrified.columns.astype(int)

energy_reduced_electrified = pd.DataFrame(
    pd.read_csv("podi/data/energy_reduced_electrified.csv")
).set_index(index)
energy_reduced_electrified.columns = energy_reduced_electrified.columns.astype(int)

energy_output = pd.DataFrame(pd.read_csv("podi/data/energy_output.csv")).set_index(
    index
)
energy_output.columns = energy_output.columns.astype(int)

energy_percent = pd.DataFrame(pd.read_csv("podi/data/energy_percent.csv")).set_index(
    index
)
energy_percent.columns = energy_percent.columns.astype(int)

# endregion

#########
# AFOLU #
#########

recalc_afolu = False
# region

if recalc_afolu is True:
    afolu(scenario, data_start_year, data_end_year, proj_end_year)

index = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "product_short",
    "flow_category",
    "flow_long",
    "flow_short",
    "unit",
]
afolu_output = pd.DataFrame(pd.read_csv("podi/data/afolu_output.csv")).set_index(index)
afolu_output.columns = afolu_output.columns.astype(int)

# endregion

#############
# EMISSIONS #
#############

recalc_emissions = False
# region

if recalc_emissions is True:
    emissions(
        scenario,
        energy_output,
        afolu_output,
        data_start_year,
        data_end_year,
        proj_end_year,
    )

index = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "product_short",
    "flow_category",
    "flow_long",
    "flow_short",
    "unit",
]
emissions_output = pd.DataFrame(
    pd.read_csv("podi/data/emissions_output.csv")
).set_index(index)
emissions_output.columns = emissions_output.columns.astype(int)

emissions_output_co2e = pd.DataFrame(
    pd.read_csv("podi/data/emissions_output_co2e.csv")
).set_index(index)
emissions_output_co2e.columns = emissions_output_co2e.columns.astype(int)

# endregion

#######
# CDR #
#######

recalc_cdr = False
# region
if recalc_cdr is True:
    cdr_pathway = pd.read_csv("podi/data/cdr_curve.csv").set_index(
        ["region", "sector", "scenario"]
    )
    cdr_pathway.columns = cdr_pathway.columns.astype(int)

    cdr_subvs = []

    for scenario in ["pathway"]:

        cdr_pathway2, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
            cdr_pathway.loc["World ", "Carbon Dioxide Removal", scenario]
            .loc[2010:]
            .to_list(),
            grid_em_def,
            heat_em_def,
            transport_em_def,
            fuel_em_def,
            2010,
            2100,
        )

        cdr_pathway2 = (
            pd.DataFrame(cdr_pathway2, index=emissions.loc[:, 2010:].columns)
            .T.fillna(0)
            .drop(
                index=pd.DataFrame(cdr_pathway2, index=emissions.loc[:, 2010:].columns)
                .T.fillna(0)
                .iloc[
                    pd.DataFrame(cdr_pathway2, index=emissions.loc[:, 2010:].columns)
                    .T.fillna(0)
                    .index.str.contains("Deficit", na=False)
                ]
                .index
            )
        )

        cdr_subvs = pd.DataFrame(cdr_subvs).append(
            pd.concat([cdr_pathway2], keys=["World "], names=["region"])
        )

        cdr_subvs = (
            cdr_subvs.droplevel(1)
            .assign(Metric=["Enhanced Weathering", "Other", "LTSSDAC", "HTLSDAC"])
            .set_index("Metric", append=True)
        )

        cdr_subvs = pd.concat(
            [cdr_subvs], names=["sector"], keys=["Carbon Dioxide Removal"]
        )
        cdr_subvs["scenario"] = "pathway"
        cdr_subvs = cdr_subvs.reset_index().set_index(
            ["region", "sector", "Metric", "scenario"]
        )
        cdr_subvs_baseline = (cdr_subvs * 0).droplevel("scenario")
        cdr_subvs_baseline["scenario"] = "baseline"
        cdr_subvs_baseline = cdr_subvs_baseline.reset_index().set_index(
            ["region", "sector", "Metric", "scenario"]
        )
        cdr_subvs = cdr_subvs.append(cdr_subvs_baseline)

    cdr_fill = cdr_subvs.loc[:, 2011:2030] * 0
    cdr_fill.columns = np.arange(1990, 2010, 1)
    cdr_output = cdr_fill.join(cdr_subvs)

index = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "product_short",
    "flow_category",
    "flow_long",
    "flow_short",
    "unit",
]
cdr_output = pd.DataFrame(
    0, index=emissions_output.index, columns=emissions_output.columns
)
cdr_output.columns = cdr_output.columns.astype(int)

# endregion

###########
# CLIMATE #
###########

recalc_climate = False
# region

if recalc_climate is True:
    climate_output = climate(
        scenario,
        emissions_output,
        emissions_output_co2e,
        cdr_output,
        data_start_year,
        data_end_year,
        proj_end_year,
    )

climate_output = pd.DataFrame(
    pd.read_csv("podi/data/output/climate/climate_output.csv")
).set_index(pyam.IAMC_IDX)
climate_output.columns = climate_output.columns.astype(int)

# endregion

####################
# RESULTS ANALYSIS #
####################

recalc_analysis = False
# region

if recalc_analysis is True:
    results_analysis(
        scenario,
        energy_output,
        afolu_output,
        emissions_output,
        emissions_output_co2e,
        cdr_output,
        climate_output,
        data_start_year,
        data_end_year,
        proj_end_year,
    )

index = [
    "model",
    "scenario",
    "region",
    "sector",
    "product_category",
    "product_long",
    "product_short",
    "flow_category",
    "flow_long",
    "flow_short",
    "unit",
]
pdindex_output = pd.DataFrame(pd.read_csv("podi/data/pdindex_output.csv")).set_index(
    index
)
pdindex_output.columns = pdindex_output.columns.astype(int)

adoption_output = pd.DataFrame(pd.read_csv("podi/data/adoption_output.csv")).set_index(
    index
)
adoption_output.columns = adoption_output.columns.astype(int)

emissions_wedges = pd.DataFrame(
    pd.read_csv("podi/data/emissions_wedges.csv")
).set_index(index)
emissions_wedges.columns = emissions_wedges.columns.astype(int)

# endregion

#######################################
# SAVE OUTPUT FILES FOR DATA EXPLORER #
#######################################

# region

# Select output_start_date and output_end_date
output_start_date = 2010
output_end_date = 2070
energy_output = energy_output.loc[:, output_start_date:]

# For energy_output, groupby product_category, except for products in the Electricity and Heat product_category
energy_output_temp = energy_output[
    (energy_output.reset_index().product_category != "Electricity and Heat").values
].reset_index()

energy_output_temp["product_long"] = energy_output_temp["product_category"]
energy_output_temp["product_short"] = energy_output_temp["product_category"]
energy_output_temp.set_index(energy_output.index.names, inplace=True)
energy_output = pd.concat(
    [
        energy_output[
            (
                energy_output.reset_index().product_category == "Electricity and Heat"
            ).values
        ],
        energy_output_temp,
    ]
)

# Combine 'Residential' and 'Commercial' sectors into 'Buildings' sector
energy_output[
    energy_output.reset_index().sector.isin(["Residential", "Commercial"]).values
] = (
    energy_output[
        energy_output.reset_index().sector.isin(["Residential", "Commercial"]).values
    ]
    .rename(index={"Commercial": "Buildings", "Residential": "Buildings"})
    .groupby(
        level=[
            "model",
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "product_short",
            "flow_category",
            "flow_long",
            "flow_short",
            "unit",
        ]
    )
    .sum()
)

"""
# Change region codes to full names
energy_output.reset_index(inplace=True)
energy_output["region"] = energy_output["region"].replace(
    pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv", usecols=["WEB Region Lower", "ISO Name"]
        )
    )
    .set_index("WEB Region Lower")
    .to_dict()["ISO Name"]
)
energy_output.set_index(
    [
        "model",
        "scenario",
        "region",
        "sector",
        "product_category",
        "product_long",
        "product_short",
        "flow_category",
        "flow_long",
        "flow_short",
        "unit",
    ],
    inplace=True,
)
"""

# Drop flow_categories 'Transformation processes', 'Energy industry own use and Losses'
energy_output = energy_output[
    ~(
        energy_output.reset_index().flow_short.isin(
            ["Transformation Processes", "Energy industry own use and Losses"]
        )
    ).values
]

# Save as regional-level files and a global-level file
for output in [
    (energy_output, "energy"),
    (afolu_output, "afolu"),
    (emissions_output, "emissions"),
    (emissions_wedges, "emissions_wedges"),
]:
    for region in output[0].reset_index().region.unique():
        output[0][(output[0].reset_index().region == region).values].loc[
            :, output_start_date:output_end_date
        ].to_csv("podi/data/output/" + output[1] + "/" + region + ".csv")
    output_global = (
        output[0]
        .groupby(
            [
                "model",
                "scenario",
                "sector",
                "product_category",
                "product_long",
                "product_short",
                "flow_category",
                "flow_long",
                "flow_short",
                "unit",
            ]
        )
        .sum()
    )
    output_global.reset_index(inplace=True)
    output_global["region"] = "world"
    output_global.set_index(
        [
            "model",
            "scenario",
            "region",
            "sector",
            "product_category",
            "product_long",
            "product_short",
            "flow_category",
            "flow_long",
            "flow_short",
            "unit",
        ],
        inplace=True,
    )
    output_global.to_csv("podi/data/output/" + output[1] + "/" + "world" + ".csv")

# Save as regional-level files and a global-level file
for output in [
    (pdindex_output, "pdindex_output"),
]:
    for region in output[0].reset_index().region.unique():
        output[0][(output[0].reset_index().region == region).values].loc[
            :, output_start_date:output_end_date
        ].to_csv("podi/data/output/" + output[1] + "/" + region + ".csv")
    output_global = output[0].groupby(["sector", "subvertical", "unit"]).sum()
    output_global.reset_index(inplace=True)
    output_global["region"] = "world"
    output_global.set_index(
        ["region", "sector", "subvertical", "unit"],
        inplace=True,
    )
    output_global.to_csv("podi/data/output/" + output[1] + "/" + "world" + ".csv")

# endregion

####################
# REFORMAT TO IAMC #
####################

# region

# Create copy of results in IAMC format
"""
energy_output_pyam = pyam.IamDataFrame(
    energy_output.reset_index().drop(
        columns=[
            "product_category",
            "product_long",
            "flow_category",
            "flow_long",
            "nonenergy",
        ]
    ),
    variable=["sector", "product_short", "flow_short"],
)
"""
# endregion
