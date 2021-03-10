#!/usr/bin/env python

# region

from podi.socioeconomics import socioeconomics
from podi.energy_demand import energy_demand, data_start_year, data_end_year
from podi.energy_supply import energy_supply, long_proj_end_year
from podi.afolu import afolu
from podi.results_analysis import results_analysis

# from podi.charts import charts
from podi.curve_smooth import curve_smooth

import podi.data.iea_weo_etl
import podi.data.iea_weo_em_etl
import podi.data.gcam_etl
import pandas as pd
from podi.cdr.cdr_util import (
    cdr_needed_def,
    grid_em_def,
    heat_em_def,
    transport_em_def,
    fuel_em_def,
)
from podi.energy_demand import iea_region_list
from podi.emissions import emissions
from podi.cdr.cdr_main import cdr_mix
from podi.climate import climate
import time
from datetime import timedelta
import numpy as np
from pandas_profiling import ProfileReport
import streamlit as st
from podi.adoption_curve import adoption_curve
from podi.energy_demand_hist import energy_demand_hist

pd.set_option("mode.use_inf_as_na", True)
start_time = time.monotonic()

# endregion

#################
# ENERGY DEMAND #
#################

# region

podi.data.gcam_etl
podi.data.iea_weo_etl

energy_demand_baseline = energy_demand(
    "baseline",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand_pathway = energy_demand(
    "pathway",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand = energy_demand_baseline.append(energy_demand_pathway)

energy_demand_hist = energy_demand_hist(energy_demand_baseline)

# endregion

#################
# ENERGY SUPPLY #
#################

# region
params = pd.read_csv("podi/data/params.csv")
params.drop(params.index, inplace=True)
params.to_csv("podi/data/params.csv", index=False)

(
    elec_consump_baseline,
    elec_per_adoption_baseline,
    elec_consump_cdr_baseline,
    heat_consump_baseline,
    heat_per_adoption_baseline,
    heat_consump_cdr_baseline,
    transport_consump_baseline,
    transport_per_adoption_baseline,
    transport_consump_cdr_baseline,
) = energy_supply("baseline", energy_demand_baseline)

(
    elec_consump_pathway,
    elec_per_adoption_pathway,
    elec_consump_cdr_pathway,
    heat_consump_pathway,
    heat_per_adoption_pathway,
    heat_consump_cdr_pathway,
    transport_consump_pathway,
    transport_per_adoption_pathway,
    transport_consump_cdr_pathway,
) = energy_supply("pathway", energy_demand_pathway)

elec_consump = elec_consump_baseline.append(elec_consump_pathway)
elec_per_adoption = elec_per_adoption_baseline.append(elec_per_adoption_pathway)
# elec_consump_cdr = elec_consump_cdr_baseline.append(elec_consump_cdr_pathway)
heat_consump = heat_consump_baseline.append(heat_consump_pathway)
heat_per_adoption = heat_per_adoption_baseline.append(heat_per_adoption_pathway)
# heat_consump_cdr = heat_consump_cdr_baseline.append(heat_consump_cdr_pathway)
transport_consump = transport_consump_baseline.append(transport_consump_pathway)
transport_per_adoption = transport_per_adoption_baseline.append(
    transport_per_adoption_pathway
)
# transport_consump_cdr = transport_consump_cdr_baseline.append(transport_consump_cdr_pathway)


(
    elec_consump_hist,
    elec_per_adoption_hist,
    elec_consump_cdr_hist,
    heat_consump_hist,
    heat_per_adoption_hist,
    heat_consump_cdr_hist,
    transport_consump_hist,
    transport_per_adoption_hist,
    transport_consump_cdr_hist,
) = energy_supply("baseline", energy_demand_hist)

# endregion

#########
# AFOLU #
#########

# region

afolu_em_baseline, afolu_per_adoption_baseline = afolu("baseline")
afolu_em_mitigated, afolu_per_adoption_pathway = afolu("pathway")

afolu_em_pathway = pd.concat(
    [
        afolu_em_baseline.droplevel(["Metric", "Unit"])
        - afolu_em_mitigated.droplevel(["Metric", "Unit"])
    ],
    keys=["Emissions"],
    names=["Metric"],
).reorder_levels(["Region", "Sector", "Metric"])
afolu_em_pathway = afolu_em_pathway.apply(lambda x: x.subtract(x.loc[2020]), axis=1)

afolu_em_baseline = afolu_em_baseline.droplevel(["Unit"])

afolu_em_mitigated = afolu_em_mitigated.apply(
    lambda x: x.subtract(afolu_em_mitigated.loc[:, 2020].values), axis=0
)

# endregion

#############
# EMISSIONS #
#############

# region

podi.data.iea_weo_em_etl

em_baseline, em_targets_baseline, em_hist = emissions(
    "baseline",
    energy_demand_baseline,
    elec_consump_baseline,
    heat_consump_baseline,
    heat_per_adoption_baseline,
    transport_consump_baseline,
    afolu_em_baseline,
    "podi/data/emissions_additional.csv",
    "podi/data/iamc_data.csv",
)

em_pathway, em_targets_pathway, em_hist = emissions(
    "pathway",
    energy_demand_pathway,
    elec_consump_pathway,
    heat_consump_pathway,
    heat_per_adoption_pathway,
    transport_consump_pathway,
    afolu_em_pathway,
    "podi/data/emissions_additional.csv",
    "podi/data/iamc_data.csv",
)

em_mitigated = (
    em_baseline.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway.groupby(["Region", "Sector", "Metric"]).sum()
)

# endregion

#######
# CDR #
#######

# region

cdr_needed = (
    pd.DataFrame(
        em_pathway.groupby("Region").sum().loc["World "]
        - em_targets_pathway.loc[
            "MESSAGE-GLOBIOM 1.0", "World ", "SSP2-19", "Emissions|Kyoto Gases"
        ].loc[data_start_year:long_proj_end_year]
    )
    .clip(lower=1)
    .T
)
cdr_needed.rename(index={0: "World "}, inplace=True)

cdr_pathway = []

for i in range(0, 1):
    cdr_pathway2, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
        cdr_needed.loc[iea_region_list[i]].to_list(),
        grid_em_def,
        heat_em_def,
        transport_em_def,
        fuel_em_def,
        data_start_year,
        long_proj_end_year,
    )

    cdr_pathway2 = (
        pd.DataFrame(cdr_pathway2, index=em_mitigated.columns)
        .T.fillna(0)
        .drop(
            index=pd.DataFrame(cdr_pathway2, index=em_mitigated.columns)
            .T.fillna(0)
            .iloc[
                pd.DataFrame(cdr_pathway2, index=em_mitigated.columns)
                .T.fillna(0)
                .index.str.contains("Deficit", na=False)
            ]
            .index
        )
    )

    cdr_pathway = pd.DataFrame(cdr_pathway).append(
        pd.concat([cdr_pathway2], keys=[iea_region_list[i]], names=["Region"])
    )
    """
    cdr_pathway = (
        cdr_pathway.droplevel(1)
        .assign(Technology=["Enhanced Weathering", "LTSSDAC", "HTLSDAC", "Other"])
        .set_index("Technology", append=True)
    )
    """
    cdr_pathway = cdr_pathway.droplevel(1).groupby("Region").sum()
    cdr_pathway = (
        em_pathway.groupby("Region").sum().divide(em_pathway.loc["World "].sum())
    ).apply(lambda x: x.multiply(cdr_pathway.values[0]), axis=1)

    # cdr_pathway = curve_smooth(cdr_pathway, "quadratic", 3)

    cdr_pathway = (
        1 - transport_per_adoption_pathway.loc["World ", "Fossil fuels"]
    ).rename(index={"pathway": "Carbon Dioxide Removal"}).apply(
        adoption_curve, axis=1, args=(["World ", "pathway"]), sector="All"
    )[
        0
    ] * cdr_pathway.loc[
        "World "
    ].max()

# check if energy oversupply is at least energy demand needed for CDR

if (
    sum(
        elec_consump_cdr_pathway,
        heat_consump_cdr_pathway,
    )
    > cdr_energy_pathway
):
    print("Electricity oversupply does not meet CDR energy demand for pathway Scenario")

# endregion

###########
# CLIMATE #
###########

# region

conc_baseline, temp_baseline, sea_lvl_baseline = climate(
    "baseline", "podi/data/climate.csv"
)
conc_pathway, temp_pathway, sea_lvl_pathway = climate(
    "pathway", "podi/data/climate.csv"
)

# endregion

####################
# RESULTS ANALYSIS #
####################

# region

adoption_curves = []

for i in range(0, len(iea_region_list)):
    adoption_curves = pd.DataFrame(adoption_curves).append(
        results_analysis(
            iea_region_list[i],
            "pathway",
            energy_demand_baseline,
            energy_demand_pathway,
            elec_consump_pathway,
            heat_consump_pathway,
            transport_consump_pathway,
            afolu_per_adoption_pathway,
            cdr_pathway,
        ).replace(np.nan, 1)
    )

# endregion

########
# NDCS #
########

# region

em_mit_ndc = []

for i in range(0, len(iea_region_list)):
    if iea_region_list[i] in [
        "World ",
        "US ",
        "SAFR ",
        "RUS ",
        "JPN ",
        "CHINA ",
        "BRAZIL ",
        "INDIA ",
    ]:
        em_ndc = (
            pd.read_csv("podi/data/emissions_ndcs.csv")
            .set_index(["Region"])
            .loc[iea_region_list[i]]
        )

        em_ndc = pd.DataFrame(
            (
                em_baseline.loc[iea_region_list[i]].sum().loc[[2025, 2030, 2050]] / 1000
            ).values
            - (em_ndc).values
        ).rename(index={0: 2025, 1: 2030, 2: 2050}, columns={0: "em_mit"})

        em_ndc["Region"] = iea_region_list[i]
    else:
        em_ndc = []

    em_mit_ndc = pd.DataFrame(em_mit_ndc).append(em_ndc)

# endregion

end_time = time.monotonic()
print(timedelta(seconds=end_time - start_time))
