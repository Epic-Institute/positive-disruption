#!/usr/bin/env python

from podi.socioeconomic import socioeconomic
from podi.energy_demand import energy_demand
from podi.energy_supply import energy_supply
import podi.data.iea_weo_etl
import podi.data.gcam_etl
import pandas as pd
from cdr.cdr_util import CDR_NEEDED_DEF

# from podi.afolu import afolu
from podi.emissions import emissions
from cdr.cdr_main import cdr_mix

# from podi.climate import climate
# from podi.results_analysis import results_analysis
from podi.charts import charts

pd.set_option("mode.use_inf_as_na", True)
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

#########
# AFOLU #
#########

afolu_baseline = afolu("Baseline")
afolu_pathway = afolu("PD21")

afolu_em_mitigated = afolu_pathway - afolu_baseline

#############
# EMISSIONS #
#############

em_baseline, ef_baseline = emissions(
    "Baseline", energy_supply_baseline, afolu_baseline, "emissions.csv"
)
em_pathway, ef_pathway = emissions(
    "Pathway", energy_supply_pathway, afolu_pathway, "emissions.csv"
)

em_mitigated = em_baseline - em_pathway

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

# Adoption Curves
acurve_start = 2020
acurve_end = 2100

# Grid Decarb
decarb = [
    "Biomass and waste",
    "Geothermal",
    "Hydroelectricity",
    "Solar",
    "Wind",
    "Nuclear",
]
grid_decarb = (
    elec_consump.loc[elec_consump.index.isin(decarb, level=1)]
    .sum()
    .div(elec_consump.groupby("Region", axis=0, level=1).sum())
)
grid_decarb.columns = grid_decarb.columns.astype(int)
grid_decarb = grid_decarb.loc[:, acurve_start:acurve_end]
grid_decarb.rename(index={"World ": "Grid"}, inplace=True)

# Transportation Decarb
transport_decarb = transport_efficiency.loc[
    "World ", "Transport", ["Oil", "International bunkers", "Electricity"], slice(None)
]
transport_decarb = transport_decarb.loc[
    transport_decarb.index.isin(["Electricity"], level=2)
]
transport_decarb.columns = transport_decarb.columns.astype(int)
transport_decarb = (
    (transport_decarb / transport_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)
transport_decarb.rename(index={"World ": "Transport"}, inplace=True)

# Buildings Decarb
building_decarb = energy_efficiency.loc["World ", "Buildings", ["Electricity"]].apply(
    lambda x: 1 - x, axis=1
)
building_decarb.columns = building_decarb.columns.astype(int)
building_decarb = (
    (building_decarb / building_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)

heatpump_decarb = heat_pumps.loc["World ", "Buildings", ["Heat"]].apply(
    lambda x: 1 - x, axis=1
)
heatpump_decarb.columns = heatpump_decarb.columns.astype(int)
heatpump_decarb = (
    (heatpump_decarb / heatpump_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)

solart_decarb = solar_thermal.loc["World ", "Buildings", ["Heat"]].apply(
    lambda x: 1 - x, axis=1
)
solart_decarb.columns = solart_decarb.columns.astype(int)
solart_decarb = (
    (solart_decarb / solart_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)
building_decarb = pd.DataFrame((building_decarb.append(solart_decarb)).sum()).T
building_decarb.rename(index={0: "Buildings"}, inplace=True)

# Industry Decarb
industry_decarb = energy_efficiency.loc["World ", "Industry", ["Electricity"]].apply(
    lambda x: 1 - x, axis=1
)
industry_decarb.columns = industry_decarb.columns.astype(int)
industry_decarb = (
    (industry_decarb / industry_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)

solart_decarb = solar_thermal.loc["World ", "Industry", ["Heat"]].apply(
    lambda x: 1 - x, axis=1
)
solart_decarb.columns = solart_decarb.columns.astype(int)
solart_decarb = (
    (solart_decarb / solart_decarb.max(axis=1).values[0])
    .droplevel(["Sector", "Metric", "Scenario"])
    .loc[:, acurve_start:acurve_end]
)
industry_decarb = pd.DataFrame((industry_decarb.append(solart_decarb)).sum()).T

industry_decarb.rename(index={0: "Industry"}, inplace=True)

# Regenerative Agriculture Decarb
ra_decarb = afolu_per_adoption.loc[
    "World ",
    slice(None),
    [
        " Biochar ",
        " Cropland Soil Health ",
        " Improved Rice ",
        " Nitrogen Fertilizer Management ",
        " Trees in Croplands ",
        " Animal Mgmt ",
        " Legumes ",
        " Optimal intensity ",
        " Silvopasture ",
    ],
    slice(None),
]
ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb.sum().max()).T.rename(
    index={0: "Regenerative Agriculture"}
)
ra_decarb.columns = ra_decarb.columns.astype(int)
ra_decarb = ra_decarb.loc[:, acurve_start:acurve_end]

# Forests & Wetlands Decarb
fw_decarb = afolu_per_adoption.loc[
    "World ",
    slice(None),
    [
        " Avoided Coastal Impacts ",
        " Avoided Forest Conversion ",
        " Avoided Peat Impacts ",
        " Coastal Restoration ",
        " Improved Forest Mgmt ",
        " Natural Regeneration ",
    ],
    slice(None),
]
fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb.sum().max()).T.rename(
    index={0: "Forests & Wetlands"}
)
fw_decarb.columns = fw_decarb.columns.astype(int)
fw_decarb = fw_decarb.loc[:, acurve_start:acurve_end]

# CDR Decarb
cdr_decarb = pd.DataFrame(
    pd.DataFrame(CDR_NEEDED_DEF) / pd.DataFrame(CDR_NEEDED_DEF).max()
).T
cdr_decarb.columns = np.arange(acurve_start, acurve_end + 1)
cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)

adoption_curves = grid_decarb.append(transport_decarb)
adoption_curves = adoption_curves.append(building_decarb)
adoption_curves = adoption_curves.append(industry_decarb)
adoption_curves = adoption_curves.append(ra_decarb)
adoption_curves = adoption_curves.append(fw_decarb)
adoption_curves = adoption_curves.append(cdr_decarb)


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
