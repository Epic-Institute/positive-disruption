#!/usr/bin/env python

# region

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.afolu import afolu
import podi.data.iea_weo_etl
import podi.data.gcam_etl
import pandas as pd
from cdr.cdr_util import CDR_NEEDED_DEF
from podi.charts import charts

# from podi.afolu import afolu
from podi.emissions import emissions
from cdr.cdr_main import cdr_mix

# from podi.climate import climate
# from podi.results_analysis import results_analysis


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
    "podi/data/transport_efficiency.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/biofuels.csv",
    "podi/data/cdr_energy.csv",
    "podi/data/bunker.csv",
)

energy_demand_pathway = energy_demand(
    "Pathway",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/energy_efficiency.csv",
    "podi/data/heat_pumps.csv",
    "podi/data/transport_efficiency.csv",
    "podi/data/solar_thermal.csv",
    "podi/data/biofuels.csv",
    "podi/data/cdr_energy.csv",
    "podi/data/bunker.csv",
)

# endregion

#################
# ENERGY SUPPLY #
#################

# region

(
    elec_consump_baseline,
    elec_per_consump_baseline,
    elec_consump_cdr_baseline,
) = energy_supply("Baseline", energy_demand_baseline)

(
    elec_consump_pathway,
    elec_per_consump_pathway,
    elec_consump_cdr_pathway,
) = energy_supply("Pathway", energy_demand_pathway)

# endregion

#########
# AFOLU #
#########

# region

afolu_baseline = afolu("Baseline")
afolu_pathway = afolu("Pathway")

afolu_em_mitigated = afolu_pathway - afolu_baseline

# endregion

#############
# EMISSIONS #
#############

# region

em_baseline, ef_baseline = emissions(
    "Baseline", energy_supply_baseline, afolu_baseline, "emissions.csv"
)

em_pathway, ef_pathway = emissions(
    "Pathway", energy_supply_pathway, afolu_pathway, "emissions.csv"
)

em_mitigated = em_baseline - em_pathway

# endregion

#######
# CDR #
#######

# region

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

# endregion

###########
# CLIMATE #
###########

# region

climate_baseline = climate(emissions_baseline, cdr_baseline)
climate_pathway = climate(emissions_pathway, cdr_pathway)

# endregion

####################
# RESULTS ANALYSIS #
####################

# region

results_analysis = results_analysis(
    [
        energy_demand_baseline,
        energy_supply_baseline,
        afolu_baseline,
        emissions_baseline,
        cdr_baseline,
        climate_baseline,
    ],
    [
        energy_demand_pathway,
        energy_supply_pathway,
        afolu_pathway,
        emissions_pathway,
        cdr_pathway,
        climate_pathway,
    ],
)

# endregion

##########
# CHARTS #
##########

# region

charts(energy_demand_baseline, energy_demand_pathway)

# endregion