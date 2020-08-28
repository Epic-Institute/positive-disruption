#!/usr/bin/env python

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply
import podi.data.iea_weo_etl
import podi.data.gcam_etl


# from podi.afolu import afolu
from podi.emissions import emissions
from cdr.cdr_main import cdr_mix

# from podi.climate import climate
# from podi.results_analysis import results_analysis
from podi.charts import charts


##################
# SOCIOECONOMICS #
##################

socioeconomic_baseline = socioeconomic("Baseline", "podi/data/socioeconomic.csv")
socioeconomic_pathway = socioeconomic("Pathway", "podi/data/socioeconomic.csv")

#################
# ENERGY DEMAND #
#################

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
)

#################
# ENERGY SUPPLY #
#################

elec_consump, elec_percent_consump, elec_consump_cdr = energy_supply(
    "Baseline", energy_demand_baseline
)
elec_consump, elec_percent_consump, elec_consump_cdr = energy_supply(
    "Pathway", energy_demand_pathway
)

#########
# AFOLU #
#########

afolu_baseline = afolu("podi/data/afolu.csv")
afolu_pathway = afolu("podi/data/afolu.csv")

#############
# EMISSIONS #
#############

em_baseline, ef_baseline = emissions(
    "Baseline", energy_supply_baseline, afolu_baseline, "emissions.csv"
)
em_pathway, ef_pathway = emissions(
    "Pathway", energy_supply_pathway, afolu_pathway, "emissions.csv"
)

#######
# CDR #
#######

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

###########
# CLIMATE #
###########

climate_baseline = climate(emissions_baseline, cdr_baseline)
climate_pathway = climate(emissions_pathway, cdr_pathway)

####################
# RESULTS ANALYSIS #
####################

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

##########
# CHARTS #
##########

charts(energy_demand_baseline, energy_demand_pathway)
