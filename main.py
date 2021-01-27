#!/usr/bin/env python

# region

from podi.socioeconomics import socioeconomics
from podi.energy_demand import energy_demand
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
from podi.energy_demand import data_start_year, data_end_year
from pandas_profiling import ProfileReport
import streamlit as st

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

# endregion

#################
# ENERGY SUPPLY #
#################

# region

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

# endregion

#########
# AFOLU #
#########

# region

afolu_em_baseline, afolu_per_adoption_baseline = afolu("baseline")
afolu_em_pathway, afolu_per_adoption_pathway = afolu("pathway")

afolu_em_mitigated = afolu_em_pathway
afolu_em_mitigated = afolu_em_mitigated.apply(lambda x: x.subtract(x.loc[2020]), axis=1)

# endregion

#############
# EMISSIONS #
#############

# region

podi.data.iea_weo_em_etl

em_baseline, em_targets_baseline = emissions(
    "baseline",
    energy_demand_baseline,
    elec_consump_baseline,
    heat_consump_baseline,
    heat_per_adoption_baseline,
    transport_consump_baseline,
    afolu_em_baseline,
    "podi/data/emissions_additional.csv",
    "podi/data/emissions_targets.csv",
)

em_pathway, em_targets_pathway = emissions(
    "pathway",
    energy_demand_pathway,
    elec_consump_pathway,
    heat_consump_pathway,
    heat_per_adoption_pathway,
    transport_consump_pathway,
    afolu_em_pathway,
    "podi/data/emissions_additional.csv",
    "podi/data/emissions_targets.csv",
)

em_mitigated = (
    em_baseline.groupby(["Region", "Sector"]).sum()
    - em_pathway.groupby(["Region", "Sector"]).sum()
)

# endregion

#######
# CDR #
#######

# region

cdr_needed = em_pathway.groupby("Region").sum()

cdr_pathway = []

for i in range(0, len(iea_region_list)):
    cdr_pathway2, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
        cdr_needed.loc[iea_region_list[i]].to_list(),
        grid_em_def,
        heat_em_def,
        transport_em_def,
        fuel_em_def,
        data_start_year,
        long_proj_end_year,
    )

    cdr_pathway2 = pd.DataFrame(cdr_pathway2, index=em_mitigated.columns).T.fillna(0)

    cdr_pathway = pd.DataFrame(cdr_pathway).append(
        pd.concat([cdr_pathway2], keys=[iea_region_list[i]], names=["Region"])
    )

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
    adoption_curves = (
        pd.DataFrame(adoption_curves)
        .append(
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
        .clip(upper=1)
    )

adoption_curves_hist = pd.DataFrame(adoption_curves.loc[:, :data_end_year])

adoption_curves_proj = curve_smooth(
    pd.DataFrame(adoption_curves.loc[:, data_end_year + 1 :]), "quadratic", 4
)

adoption_curves = (adoption_curves_hist.join(adoption_curves_proj)).clip(
    upper=1, lower=0
)

# endregion

##########
# CHARTS #
##########
"""
# region

charts(
    energy_demand_baseline,
    energy_demand_pathway,
    adoption_curves,
    em_targets_pathway,
    em_mitigated,
)

# endregion
"""
##################
# SOCIOECONOMICS #
##################

# region

# podi.socioeconomics

# endregion

end_time = time.monotonic()
print(timedelta(seconds=end_time - start_time))
