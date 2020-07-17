#!/usr/bin/env python

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply
from podi.afolu import afolu
from podi.emissions import emissions
from podi.cdr import cdr
from podi.climate import climate
from podi.results_analysis import results_analysis
from podi.charts import charts

socioeconomic_baseline = socioeconomic("podi/data/socioeconomic_baseline.csv")
socioeconomic_pathway = socioeconomic("podi/data/socioeconomic_pathway.csv")

energy_demand_baseline = energy_demand(
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection_baseline.csv",
    "podi/data/energy_efficiency_baseline.csv",
    "podi/data/heat_pumps_baseline.csv",
    "podi/data/transport_efficiency_baseline.csv",
    "podi/data/solar_thermal_baseline.csv",
    "podi/data/biofuels_baseline.csv",
)

energy_demand_pathway = energy_demand(
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection_pathway.csv",
    "podi/data/energy_efficiency_pathway.csv",
    "podi/data/heat_pumps_pathway.csv",
    "podi/data/transport_efficiency_pathway.csv",
    "podi/data/solar_thermal_ pathway.csv",
    "podi/data/biofuels_pathway.csv",
)

energy_supply_baseline = energy_supply(energy_demand_baseline)
energy_supply_pathway = energy_supply(energy_demand_pathway)

afolu_baseline = afolu("podi/data/afolu_baseline.csv")
afolu_pathway = afolu("podi/data/afolu_pathway.csv")

emissions_baseline = emissions(
    energy_supply_baseline, afolu_baseline, "additional_emissions_baseline.csv"
)
emissions_pathway = emissions(
    energy_supply_pathway, afolu_pathway, "additional_emissions_pathway.csv"
)

cdr_baseline = cdr(emissions_baseline)
cdr_pathway = cdr(emissions_pathway)

climate_baseline = climate(emissions_baseline, cdr_baseline)
climate_pathway = climate(emissions_pathway, cdr_pathway)

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

charts(energy_demand_baseline, energy_demand_pathway)
