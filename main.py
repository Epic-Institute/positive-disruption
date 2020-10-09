#!/usr/bin/env python

# region

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply
from podi.afolu import afolu
from podi.results_analysis import results_analysis
import podi.data.iea_weo_etl
import podi.data.gcam_etl
import pandas as pd
from cdr.cdr_util import cdr_needed_def
from podi.charts import charts
from podi.data.iea_weo_etl import iea_region_list
from podi.adoption_curve import adoption_curve
from podi.emissions import emissions
from cdr.cdr_main import cdr_mix
from podi.climate import climate

pd.set_option("mode.use_inf_as_na", True)

# endregion

##################
# SOCIOECONOMICS #
##################

# region

socioeconomic_baseline = socioeconomic("Baseline", "podi/data/socioeconomic.csv")
socioeconomic_pathway = socioeconomic("Pathway", "podi/data/socioeconomic.csv")

# endregion

#################
# ENERGY DEMAND #
#################

# region

podi.data.gcam_etl
podi.data.iea_weo_etl

energy_demand_baseline = energy_demand(
    "Baseline",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand_pathway = energy_demand(
    "Pathway",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/solar_thermal.csv",
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


em_mitigated = em_baseline - em_pathway

# endregion

#######
# CDR #
#######

# region
"""
cdr_baseline, cdr_cost_baseline, cdr_energy_baseline = cdr_mix(
    em_baseline,
    ef_baseline.loc["Grid"],
    ef_baseline.loc["Heat"],
    ef_baseline.loc["Transport"],
    em_baseline.loc["Fuels"],
)

cdr_pathway, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
    em_pathway.loc["Grid"],
    ef_pathway.loc["Heat"],
    ef_pathway.loc["Transport"],
    em_pathway.loc["Fuels"],
)

# check if energy oversupply is at least energy demand needed for CDR

if consump_cdr_baseline > cdr_energy_baseline:
    print(
        "Electricity oversupply does not meet CDR energy demand for Baseline Scenario"
    )
if consump_cdr_pathway > cdr_energy_pathway:
    print("Electricity oversupply does not meet CDR energy demand for Pathway Scenario")
"""
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

for i in range(17, 19):
    adoption_curves = results_analysis(
        iea_region_list[i],
        energy_demand_baseline,
        energy_demand_pathway,
        elec_consump_pathway,
        heat_consump_pathway,
        transport_consump_pathway,
        afolu_per_adoption_pathway,
        cdr_needed_def,
    )

# endregion