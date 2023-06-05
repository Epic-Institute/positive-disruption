# region
import pandas as pd

from podi.afolu import afolu
from podi.climate import climate
from podi.emissions import emissions
from podi.energy import energy
from podi.results_analysis.results_analysis import results_analysis

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

energy_post_upstream = pd.read_parquet(
    "podi/data/energy_post_upstream.parquet"
)
energy_post_upstream.columns = energy_post_upstream.columns.astype(int)

energy_post_addtl_eff = pd.read_parquet(
    "podi/data/energy_post_addtl_eff.parquet"
)
energy_post_addtl_eff.columns = energy_post_addtl_eff.columns.astype(int)

energy_electrified = pd.read_parquet("podi/data/energy_electrified.parquet")
energy_electrified.columns = energy_electrified.columns.astype(int)

energy_reduced_electrified = pd.read_parquet(
    "podi/data/energy_reduced_electrified.parquet"
)
energy_reduced_electrified.columns = energy_reduced_electrified.columns.astype(
    int
)

energy_output = pd.read_parquet("podi/data/energy_output.parquet")
energy_output.columns = energy_output.columns.astype(int)

energy_percent = pd.read_parquet("podi/data/energy_percent.parquet")
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
afolu_output = pd.read_parquet("podi/data/afolu_output.parquet")
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
emissions_output = pd.read_parquet("podi/data/emissions_output.parquet")
emissions_output.columns = emissions_output.columns.astype(int)

emissions_output_co2e = pd.read_parquet(
    "podi/data/emissions_output_co2e.parquet"
)
emissions_output_co2e.columns = emissions_output_co2e.columns.astype(int)

# endregion

###########
# CLIMATE #
###########

recalc_climate = False
# region

if recalc_climate is True:
    climate_output = climate(
        model,
        scenario,
        emissions_output,
        emissions_output_co2e,
        data_start_year,
        data_end_year,
        proj_end_year,
    )


# load climate_output_concentration, climate_output_temperature, climate_output_forcing from parquet
climate_output_concentration = pd.read_parquet(
    "podi/data/climate_output_concentration.parquet"
)
climate_output_concentration.columns = (
    climate_output_concentration.columns.astype(int)
)
climate_output_temperature = pd.read_parquet(
    "podi/data/climate_output_temperature.parquet"
)
climate_output_temperature.columns = climate_output_temperature.columns.astype(
    int
)
climate_output_forcing = pd.read_parquet(
    "podi/data/climate_output_forcing.parquet"
)
climate_output_forcing.columns = climate_output_forcing.columns.astype(int)


# endregion

####################
# RESULTS ANALYSIS #
####################

recalc_analysis = True
# region

if recalc_analysis is True:
    results_analysis(
        scenario,
        energy_output,
        afolu_output,
        emissions_output,
        emissions_output_co2e,
        climate_output_concentration,
        climate_output_temperature,
        climate_output_forcing,
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
technology_adoption_output = pd.read_parquet(
    "podi/data/technology_adoption_output.parquet"
)
technology_adoption_output.columns = technology_adoption_output.columns.astype(
    int
)

# endregion

#######################################
# SAVE OUTPUT FILES FOR DATA EXPLORER #
#######################################

# region

# Combine 'Residential' and 'Commercial' sectors into 'Buildings' sector
energy_output = pd.concat(
    [
        energy_output,
        energy_output[
            energy_output.reset_index()
            .sector.isin(["Residential", "Commercial"])
            .values
        ]
        .rename(index={"Commercial": "Buildings", "Residential": "Buildings"})
        .groupby(energy_output.index.names, observed=True)
        .sum(numeric_only=True),
    ]
)
energy_output = energy_output[
    ~(
        energy_output.reset_index().sector.isin(["Residential", "Commercial"])
    ).values
]

emissions_output = pd.concat(
    [
        emissions_output,
        emissions_output[
            emissions_output.reset_index()
            .sector.isin(["Residential", "Commercial"])
            .values
        ]
        .rename(index={"Commercial": "Buildings", "Residential": "Buildings"})
        .groupby(emissions_output.index.names, observed=True)
        .sum(numeric_only=True),
    ]
)
emissions_output = emissions_output[
    ~(
        emissions_output.reset_index().sector.isin(
            ["Residential", "Commercial"]
        )
    ).values
]

emissions_output_co2e = pd.concat(
    [
        emissions_output_co2e,
        emissions_output_co2e[
            emissions_output_co2e.reset_index()
            .sector.isin(["Residential", "Commercial"])
            .values
        ]
        .rename(index={"Commercial": "Buildings", "Residential": "Buildings"})
        .groupby(emissions_output_co2e.index.names, observed=True)
        .sum(numeric_only=True),
    ]
)
emissions_output_co2e = emissions_output_co2e[
    ~(
        emissions_output_co2e.reset_index().sector.isin(
            ["Residential", "Commercial"]
        )
    ).values
]

# Split energy_output into energy_output_supply and energy_output_demand
energy_output_supply = energy_output[
    (
        energy_output.reset_index().flow_category.isin(
            [
                "Electricity output",
                "Heat output",
            ]
        )
    ).values
]

energy_output_demand = energy_output[
    (
        energy_output.reset_index().flow_category.isin(
            [
                "Final consumption",
                "Transformation processes",
                "Energy industry own use and Losses",
            ]
        )
    ).values
]

# Save
for output in [
    (energy_output_supply, "energy_output_supply"),
    (energy_output_demand, "energy_output_demand"),
    (emissions_output, "emissions_output"),
    (emissions_output_co2e, "emissions_output_co2e"),
]:
    # change columns to str
    output[0].columns = output[0].columns.astype(str)
    # save as parquet
    output[0].to_parquet(f"podi/data/{output[1]}.parquet")

# endregion
