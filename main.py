#!/usr/bin/env python

# region

from podi.socioeconomics import socioeconomics
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply
from podi.afolu import afolu
from podi.results_analysis import results_analysis
from podi.charts import charts
from podi.curve_smooth import curve_smooth
import podi.data.iea_weo_etl
import podi.data.gcam_etl
import pandas as pd
from podi.cdr.cdr_util import (
    cdr_needed_def,
    grid_em_def,
    heat_em_def,
    transport_em_def,
    fuel_em_def,
)
from podi.data.iea_weo_etl import iea_region_list
from podi.emissions import emissions
from podi.cdr.cdr_main import cdr_mix
from podi.climate import climate
import time
from datetime import timedelta
import numpy as np

pd.set_option("mode.use_inf_as_na", True)
start_time = time.monotonic()

# endregion

##################
# SOCIOECONOMICS #
##################

# region

pop_baseline, gdp_baseline = socioeconomics("Baseline", "podi/data/socioeconomic.csv")
pop_pathway, gdp_pathway = socioeconomics("Pathway", "podi/data/socioeconomic.csv")

# endregion

#################
# ENERGY DEMAND #
#################

# region

podi.data.gcam_etl
podi.data.iea_weo2020_etl

energy_demand_baseline = energy_demand(
    "Baseline",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand_pathway = energy_demand(
    "Pathway",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

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
) = energy_supply("Baseline", energy_demand_baseline)

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
) = energy_supply("Pathway", energy_demand_pathway)

# endregion

#########
# AFOLU #
#########

# region

afolu_em_baseline, afolu_per_adoption_baseline = afolu("Baseline")
afolu_em_pathway, afolu_per_adoption_pathway = afolu("Pathway")

afolu_em_mitigated = afolu_em_pathway
afolu_em_mitigated = afolu_em_mitigated.apply(lambda x: x.subtract(x.loc[2020]), axis=1)

# endregion

#############
# EMISSIONS #
#############

# region

podi.data.iea_weo_em_etl

em_baseline, em_targets_baseline = emissions(
    "Baseline",
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
    "Pathway",
    energy_demand_pathway,
    elec_consump_pathway,
    heat_consump_pathway,
    heat_per_adoption_pathway,
    transport_consump_pathway,
    afolu_em_pathway,
    "podi/data/emissions_additional.csv",
    "podi/data/emissions_targets.csv",
)

"""
em_pathway2 = pd.read_csv(
    "/home/n/.local/share/virtualenvs/positive-disruption-XAvGHklr/lib/python3.8/site-packages/pyhector/emissions/RCP19_emissions.csv"
)

em_pathway2.iloc[248:339, 1] = (
    (
        em_pathway.loc[
            slice(None), ["Electricity", "Transport", "Buildings", "Industry"], :
        ].sum()
        / 3670
    )
    .values.round(4)
)

em_pathway2.to_csv(
    "/home/n/.local/share/virtualenvs/positive-disruption-XAvGHklr/lib/python3.8/site-packages/pyhector/emissions/RCP19_emissions.csv",
    index=False,
)
"""

em_mitigated = (
    em_baseline.groupby(["Region", "Sector"]).sum()
    - em_pathway.groupby(["Region", "Sector"]).sum()
)

# endregion

#######
# CDR #
#######

# region
"""
cdr_needed = (
    abs(
        em_targets_pathway.loc["Baseline PD20", 2010:]
        - em_targets_pathway.loc["Pathway PD20", 2010:]
    )    - em_targets_pathway.loc["Baseline PD20", 2010:] - em_pathway.sum())
"""

cdr_needed = cdr_needed_def
grid_em = grid_em_def
heat_em = heat_em_def
transport_em = transport_em_def
fuel_em = fuel_em_def

cdr_pathway, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
    cdr_needed, grid_em, heat_em, transport_em, fuel_em, 2010, 2100
)

cdr_pathway = (
    pd.DataFrame(cdr_pathway, index=em_mitigated.columns)
    .T.fillna(0)
    .iloc[[True, False, True, True], :]
)


# check if energy oversupply is at least energy demand needed for CDR

if (
    sum(
        elec_consump_cdr_pathway,
        heat_consump_cdr_pathway,
    )
    > cdr_energy_pathway
):
    print("Electricity oversupply does not meet CDR energy demand for Pathway Scenario")

# endregion

###########
# CLIMATE #
###########

# region

conc_baseline, temp_baseline, sea_lvl_baseline = climate(
    "Baseline", "podi/data/climate.csv"
)
conc_pathway, temp_pathway, sea_lvl_pathway = climate(
    "Pathway", "podi/data/climate.csv"
)

# endregion

####################
# RESULTS ANALYSIS #
####################

# region

adoption_curves = []

for i in range(0, len(iea_region_list)):
    adoption_curves = curve_smooth(
        pd.DataFrame(adoption_curves).append(
            results_analysis(
                iea_region_list[i],
                "Pathway",
                energy_demand_baseline,
                energy_demand_pathway,
                elec_consump_pathway,
                heat_consump_pathway,
                transport_consump_pathway,
                afolu_per_adoption_pathway,
                cdr_pathway,
            ).replace(np.nan, 1)
        ),
        11,
    ).clip(upper=1)

# endregion

##########
# CHARTS #
##########

# region

charts(
    energy_demand_baseline,
    energy_demand_pathway,
    adoption_curves,
    em_targets_pathway,
    em_mitigated,
)

# endregion


end_time = time.monotonic()
print(timedelta(seconds=end_time - start_time))
