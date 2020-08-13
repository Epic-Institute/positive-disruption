#!/usr/bin/env python

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply

# from podi.afolu import afolu
# from podi.emissions import emissions
# from podi.cdr import cdr
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

energy_supply_baseline = energy_supply("Baseline", energy_demand_baseline)
energy_supply_pathway = energy_supply("Pathway", energy_demand_pathway)

#########
# AFOLU #
#########

afolu_baseline = afolu("podi/data/afolu.csv")
afolu_pathway = afolu("podi/data/afolu.csv")

#############
# EMISSIONS #
#############

emissions_baseline = emissions(
    energy_supply_baseline, afolu_baseline, "additional_emissions_baseline.csv"
)
emissions_pathway = emissions(
    energy_supply_pathway, afolu_pathway, "additional_emissions_pathway.csv"
)

#######
# CDR #
#######

cdr_baseline = cdr(emissions_baseline)
cdr_pathway = cdr(emissions_pathway)

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
