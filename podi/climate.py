# region

import pandas as pd
import fair
from fair import FAIR
from fair.io import read_properties
from fair.interface import fill, initialise

# endregion


def climate(
    model,
    scenario,
    emissions_output,
    emissions_output_co2e,
    cdr_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ########################
    # LOAD HISTORICAL DATA #
    ########################

    # region

    # Load GHG concentration data from external source
    climate_historical_concentration = pd.DataFrame(
        pd.read_csv(
            "podi/data/external/climate-change.csv",
            usecols=[
                "Entity",
                "Year",
                "CO2 concentrations",
                "CH4 concentrations",
                "N2O concentrations",
            ],
        )
    )

    # Select World-level data
    climate_historical_concentration = climate_historical_concentration[
        (climate_historical_concentration["Entity"] == "World").values
    ].drop(columns="Entity")

    # Update column names
    climate_historical_concentration = climate_historical_concentration.rename(
        {
            "CO2 concentrations": "CO2",
            "CH4 concentrations": "CH4",
            "N2O concentrations": "N2O",
        },
        axis="columns",
    )

    climate_historical_concentration = (
        climate_historical_concentration[
            (climate_historical_concentration["Year"] >= data_start_year).values
        ]
        .rename(columns={"Year": "year"})
        .set_index("year")
    )

    # Load radiative forcing data from external source
    climate_historical_forcing = pd.DataFrame(
        pd.read_csv("podi/data/external/radiative_forcing_historical.csv")
    )
    climate_historical_forcing.columns = climate_historical_forcing.columns.astype(int)
    climate_historical_forcing = climate_historical_forcing.loc[
        :, data_start_year:data_end_year
    ].T

    # Load temperature change data from external source
    climate_historical_temperature = pd.DataFrame(
        pd.read_csv("podi/data/external/temperature_change_historical.csv")
    )
    climate_historical_temperature.columns = (
        climate_historical_temperature.columns.astype(int)
    )
    climate_historical_temperature = climate_historical_temperature.loc[
        :, data_start_year:data_end_year
    ].T

    # endregion

    ############################################
    # PREPARE EMISSIONS DATA FOR CLIMATE MODEL #
    ############################################

    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when
    # summing emissions
    emissions_output = emissions_output[
        ~(
            emissions_output.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    # Rename emissions_output gases to match required inputs for FAIR

    # SO2 to Sulfur
    emissions_output.rename(index={"SO2": "Sulfur"}, inplace=True)
    emissions_output_co2e.rename(index={"SO2": "Sulfur"}, inplace=True)

    # NMVOC to VOC
    emissions_output.rename(index={"NMVOC": "VOC"}, inplace=True)
    emissions_output_co2e.rename(index={"NMVOC": "VOC"}, inplace=True)

    # 'HFC-43-10-mee' to 'HFC-4310mee'
    emissions_output.rename(index={"HFC-43-10-mee": "HFC-4310mee"}, inplace=True)
    emissions_output_co2e.rename(index={"HFC-43-10-mee": "HFC-4310mee"}, inplace=True)

    # Update emissions that don't list gas in flow_long (these are all CO2)
    emissions_output.reset_index(inplace=True)

    # Select CO2 emissions
    emissions_output_co2 = emissions_output[
        ~(
            emissions_output.flow_long.isin(
                (
                    {
                        key: value
                        for key, value in fair.structure.units.desired_emissions_units.items()
                        if key not in ["CO2 FFI", "CO2 AFOLU", "CO2"]
                    }
                ).keys()
            )
        ).values
    ]

    # Remove CO2 emissions from full emissions list
    emissions_output = emissions_output[
        (
            emissions_output.flow_long.isin(
                (
                    {
                        key: value
                        for key, value in fair.structure.units.desired_emissions_units.items()
                        if key not in ["CO2 FFI", "CO2 AFOLU", "CO2"]
                    }
                ).keys()
            )
        ).values
    ]

    # Replace 'flow_long' value with 'CO2'
    emissions_output_co2.drop(columns="flow_long", inplace=True)
    emissions_output_co2["flow_long"] = "CO2"

    # Replace 'CO2' with 'CO2 FFI' for subset
    emissions_output_fossil = emissions_output_co2[
        (
            (emissions_output_co2.flow_long == "CO2")
            & (
                emissions_output_co2.sector.isin(
                    [
                        "Electric Power",
                        "Transportation",
                        "Residential",
                        "Commercial",
                        "Industrial",
                    ]
                )
            )
        ).values
    ].drop(columns="flow_long")

    emissions_output_fossil["flow_long"] = "CO2 FFI"

    # Replace 'CO2' with 'CO2 AFOLU' for subset
    emissions_output_landuse = emissions_output_co2[
        (
            (emissions_output_co2.flow_long == "CO2")
            & (emissions_output_co2.sector.isin(["Agriculture", "Forests & Wetlands"]))
        ).values
    ].drop(columns="flow_long")

    emissions_output_landuse["flow_long"] = "CO2 AFOLU"

    # Recombine
    emissions_output_co2 = pd.concat(
        [emissions_output_fossil, emissions_output_landuse]
    )

    # Add the updated subset back into the original df
    emissions_output = pd.concat([emissions_output, emissions_output_co2])

    emissions_output = emissions_output.set_index(
        [
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
    )

    # Filter emissions_output to contain only inputs for
    # fair.structure.units.desired_emissions_units
    emissions_output = emissions_output[
        (
            emissions_output.reset_index().flow_long.isin(
                fair.structure.units.desired_emissions_units.keys()
            )
        ).values
    ].sort_index()

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output = emissions_output.parallel_apply(
        lambda x: x.multiply(
            pd.read_csv(
                "podi/data/climate_unit_conversions.csv", usecols=["value", "gas"]
            )
            .set_index("gas")
            .loc[x.name[8]]
            .values[0]
        ),
        axis=1,
    )

    # endregion

    ################################################
    # ESTIMATE CONCENTRATION, FORCING, TEMPERATURE #
    ################################################

    # region

    # Run the climate model for each scenario. Note that natural emissions of
    # CH4 and N2O is set to zero, and volcanic and solar forcing are provided
    # externally and estimated here

    climate_output_concentration = pd.DataFrame()
    climate_output_forcing = pd.DataFrame()
    climate_output_temperature = pd.DataFrame()

    for scenario in emissions_output.reset_index().scenario.unique():

        # Format for input into FAIR
        emissions_output_fair = (
            emissions_output.loc[slice(None), scenario, :]
            .groupby(["flow_long"])
            .sum()
            .T.fillna(0)
            .rename_axis("year")
        )

        f = FAIR()
        f.define_time(data_end_year, proj_end_year, 1)
        f.define_scenarios([scenario])
        f.define_configs(["high", "central", "low"])
        species, properties = read_properties()
        species = list(
            set(species) & set(emissions_output_fair.columns.tolist())
        ) + list(["CO2"])
        properties = {k: v for k, v in properties.items() if k in species}
        f.define_species(species, properties)
        f.ghg_method = "leach2021"
        f.ch4_method = "leach2021"
        f.allocate()

        # Fill emissions with emissions from Emissions module
        for config in f.configs:
            for specie in list(
                (
                    pd.DataFrame(f.species)[
                        ~pd.DataFrame(f.species).isin(["CO2"])
                    ].dropna()
                )[0]
            ):
                fill(
                    f.emissions,
                    emissions_output_fair.loc[int(data_end_year + 1) :][specie].values,
                    scenario=scenario,
                    config=config,
                    specie=specie,
                )

        # Define first timestep
        initialise(f.forcing, 0)
        initialise(f.temperature, 0)
        initialise(f.cumulative_emissions, 0)
        initialise(f.airborne_emissions, 0)

        # Fill climate configs
        fill(f.climate_configs["ocean_heat_transfer"], [0.6, 1.3, 1.0], config="high")
        fill(f.climate_configs["ocean_heat_capacity"], [5, 15, 80], config="high")
        fill(f.climate_configs["deep_ocean_efficacy"], 1.29, config="high")

        fill(
            f.climate_configs["ocean_heat_transfer"], [1.1, 1.6, 0.9], config="central"
        )
        fill(f.climate_configs["ocean_heat_capacity"], [8, 14, 100], config="central")
        fill(f.climate_configs["deep_ocean_efficacy"], 1.1, config="central")

        fill(f.climate_configs["ocean_heat_transfer"], [1.7, 2.0, 1.1], config="low")
        fill(f.climate_configs["ocean_heat_capacity"], [6, 11, 75], config="low")
        fill(f.climate_configs["deep_ocean_efficacy"], 0.8, config="low")

        # Fill species configs with default values
        FAIR.fill_species_configs(f)

        # Run
        f.run()

        # Plot
        pl.plot(
            f.timebounds,
            f.temperature.loc[dict(scenario="pathway", layer=0)],
            label=f.configs,
        )
        pl.title("Ramp scenario: temperature")
        pl.xlabel("year")
        pl.ylabel("Temperature anomaly (K)")
        pl.legend()

        for specie in species:
            pl.figure()
            pl.plot(
                f.timebounds,
                f.concentration.loc[dict(scenario="pathway", specie=specie)],
                label=f.configs,
            )
            pl.title(str(specie) + " concentration")
            pl.xlabel("year")
            pl.ylabel("(ppm)")
            pl.legend()

        # Write to DataFrame
        climate_output_concentration_temp = (
            f.concentration.to_dataframe(name="Concentration")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_concentration_temp.columns = (
            climate_output_concentration_temp.columns.astype(int)
        )
        climate_output_concentration_temp.columns.name = None
        climate_output_concentration_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_forcing_temp = (
            f.forcing.to_dataframe(name="Forcing")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_forcing_temp.columns = (
            climate_output_forcing_temp.columns.astype(int)
        )
        climate_output_forcing_temp.columns.name = None
        climate_output_forcing_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_temperature_temp = (
            f.temperature.to_dataframe(name="Temperature")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_temperature_temp.columns = (
            climate_output_temperature_temp.columns.astype(int)
        )
        climate_output_temperature_temp.columns.name = None
        climate_output_temperature_temp = climate_output_temperature_temp[
            (climate_output_temperature_temp.reset_index().layer == 0).values
        ]
        climate_output_temperature_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_concentration = pd.concat(
            [climate_output_concentration_temp, climate_output_concentration]
        )
        climate_output_forcing = pd.concat(
            [climate_output_forcing_temp, climate_output_forcing]
        )
        climate_output_temperature = pd.concat(
            [climate_output_temperature_temp, climate_output_temperature]
        )

    # Create version of climate_output_concentration with units CO2e
    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output_co2e_fair = emissions_output_co2e[
        ~(
            emissions_output_co2e.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ].sort_index()

    emissions_output_co2e_fair.reset_index(inplace=True)
    emissions_output_co2e_fair["flow_long"] = "CO2"
    emissions_output_co2e_fair.set_index(emissions_output.index.names, inplace=True)

    # Convert units from emissions_output_co2e_fair to assumed units for FAIR model input
    emissions_output_co2e_fair = emissions_output_co2e_fair.parallel_apply(
        lambda x: x.multiply(
            pd.read_csv(
                "podi/data/climate_unit_conversions.csv", usecols=["value", "gas"]
            )
            .set_index("gas")
            .loc[x.name[8]]
            .values[0]
        ),
        axis=1,
    )

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output_co2e_fair = emissions_output_co2e_fair.groupby(
        ["model", "scenario", "flow_long"]
    ).sum()

    climate_output_concentration_co2e = pd.DataFrame()
    climate_output_forcing_co2e = pd.DataFrame()
    climate_output_temperature_co2e = pd.DataFrame()

    for scenario in emissions_output_co2e_fair.reset_index().scenario.unique():

        # Format for input into FAIR
        emissions_output_co2e_fair2 = (
            emissions_output_co2e_fair.loc[slice(None), scenario, :]
            .groupby(["flow_long"])
            .sum()
            .T.fillna(0)
            .rename_axis("year")
        )

        f = FAIR()
        f.define_time(data_end_year, proj_end_year, 1)
        f.define_scenarios([scenario])
        f.define_configs(["high", "central", "low"])
        species, properties = read_properties()
        species = list(set(species) & set(emissions_output_co2e_fair2.columns.tolist()))
        properties = {k: v for k, v in properties.items() if k in species}
        f.define_species(species, properties)
        f.ghg_method = "leach2021"
        f.ch4_method = "leach2021"
        f.allocate()

        # Fill emissions with emissions from Emissions module
        for config in f.configs:
            for specie in list(
                (
                    pd.DataFrame(f.species)[
                        ~pd.DataFrame(f.species).isin(["CO2"])
                    ].dropna()
                )[0]
            ):
                fill(
                    f.emissions,
                    emissions_output_co2e_fair2.loc[int(data_end_year + 1) :][
                        specie
                    ].values,
                    scenario=scenario,
                    config=config,
                    specie=specie,
                )

        # Define first timestep
        initialise(f.forcing, 0)
        initialise(f.temperature, 0)
        initialise(f.cumulative_emissions, 0)
        initialise(f.airborne_emissions, 0)

        # Fill climate configs
        fill(f.climate_configs["ocean_heat_transfer"], [0.6, 1.3, 1.0], config="high")
        fill(f.climate_configs["ocean_heat_capacity"], [5, 15, 80], config="high")
        fill(f.climate_configs["deep_ocean_efficacy"], 1.29, config="high")

        fill(
            f.climate_configs["ocean_heat_transfer"], [1.1, 1.6, 0.9], config="central"
        )
        fill(f.climate_configs["ocean_heat_capacity"], [8, 14, 100], config="central")
        fill(f.climate_configs["deep_ocean_efficacy"], 1.1, config="central")

        fill(f.climate_configs["ocean_heat_transfer"], [1.7, 2.0, 1.1], config="low")
        fill(f.climate_configs["ocean_heat_capacity"], [6, 11, 75], config="low")
        fill(f.climate_configs["deep_ocean_efficacy"], 0.8, config="low")

        # Fill species configs with default values
        FAIR.fill_species_configs(f)

        # Run
        f.run()

        # Plot
        pl.plot(
            f.timebounds,
            f.temperature.loc[dict(scenario="pathway", layer=0)],
            label=f.configs,
        )
        pl.title("Ramp scenario: temperature")
        pl.xlabel("year")
        pl.ylabel("Temperature anomaly (K)")
        pl.legend()

        for specie in species:
            pl.figure()
            pl.plot(
                f.timebounds,
                f.concentration.loc[dict(scenario="pathway", specie=specie)],
                label=f.configs,
            )
            pl.title(str(specie) + " concentration")
            pl.xlabel("year")
            pl.ylabel("(ppm)")
            pl.legend()

        # Write to DataFrame
        climate_output_concentration_co2e_temp = (
            f.concentration.to_dataframe(name="Concentration")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_concentration_co2e_temp.columns = (
            climate_output_concentration_co2e_temp.columns.astype(int)
        )
        climate_output_concentration_co2e_temp.columns.name = None
        climate_output_concentration_co2e_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_forcing_co2e_temp = (
            f.forcing.to_dataframe(name="Forcing")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_forcing_co2e_temp.columns = (
            climate_output_forcing_co2e_temp.columns.astype(int)
        )
        climate_output_forcing_co2e_temp.columns.name = None
        climate_output_forcing_co2e_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_temperature_co2e_temp = (
            f.temperature.to_dataframe(name="Temperature")
            .unstack(level=0)
            .droplevel(level=0, axis=1)
        )
        climate_output_temperature_co2e_temp.columns = (
            climate_output_temperature_co2e_temp.columns.astype(int)
        )
        climate_output_temperature_co2e_temp.columns.name = None
        climate_output_temperature_co2e_temp = climate_output_temperature_co2e_temp[
            (climate_output_temperature_co2e_temp.reset_index().layer == 0).values
        ]
        climate_output_temperature_co2e_temp.index.set_names(
            "product_long", level=2, inplace=True
        )

        climate_output_concentration = pd.concat(
            [climate_output_concentration_co2e_temp, climate_output_concentration_co2e]
        )
        climate_output_forcing = pd.concat(
            [climate_output_forcing_co2e_temp, climate_output_forcing_co2e]
        )
        climate_output_temperature = pd.concat(
            [climate_output_temperature_co2e_temp, climate_output_temperature_co2e]
        )

    # endregion

    # endregion

    ##############
    #  REFORMAT  #
    ##############

    # region

    climate_historical_concentration = climate_historical_concentration.T
    climate_historical_concentration["model"] = "PD22"
    climate_historical_concentration["scenario"] = "historical"
    climate_historical_concentration["region"] = "world"
    climate_historical_concentration["variable"] = "Concentration"
    climate_historical_concentration["gas"] = climate_historical_concentration.index
    climate_historical_concentration["unit"] = "PPM"
    climate_historical_concentration.set_index(
        ["model", "scenario", "region", "variable", "gas", "unit"], inplace=True
    )

    climate_historical_forcing = climate_historical_forcing.T
    climate_historical_forcing["model"] = "PD22"
    climate_historical_forcing["scenario"] = "historical"
    climate_historical_forcing["region"] = "world"
    climate_historical_forcing["variable"] = "Radiative forcing"
    climate_historical_forcing["gas"] = climate_historical_forcing.index
    climate_historical_forcing["unit"] = "W/m2"
    climate_historical_forcing.set_index(
        ["model", "scenario", "region", "variable", "gas", "unit"], inplace=True
    )

    climate_historical_temperature = climate_historical_temperature.T
    climate_historical_temperature["model"] = "PD22"
    climate_historical_temperature["scenario"] = "historical"
    climate_historical_temperature["region"] = "world"
    climate_historical_temperature["variable"] = "Temperature change"
    climate_historical_temperature["gas"] = climate_historical_temperature.index
    climate_historical_temperature["unit"] = "F"
    climate_historical_temperature.set_index(
        ["model", "scenario", "region", "variable", "gas", "unit"], inplace=True
    )

    climate_output_concentration["model"] = "PD22"
    climate_output_concentration["region"] = "world"
    climate_output_concentration["variable"] = "Concentration"
    climate_output_concentration[
        "gas"
    ] = climate_output_concentration.index.get_level_values(1)
    climate_output_concentration["unit"] = "PPM"
    climate_output_concentration = (
        climate_output_concentration.droplevel("product_long")
        .reset_index()
        .set_index(["model", "scenario", "region", "variable", "gas", "unit"])
    )

    climate_output_forcing["model"] = "PD22"
    climate_output_forcing["region"] = "world"
    climate_output_forcing["variable"] = "Radiative forcing"
    climate_output_forcing["gas"] = climate_output_forcing.index.get_level_values(1)
    climate_output_forcing["unit"] = "W/m2"
    climate_output_forcing = (
        climate_output_forcing.droplevel("product_long")
        .reset_index()
        .set_index(["model", "scenario", "region", "variable", "gas", "unit"])
    )

    climate_output_temperature["model"] = "PD22"
    climate_output_temperature["region"] = "world"
    climate_output_temperature["variable"] = "Temperature change"
    climate_output_temperature["gas"] = 0
    climate_output_temperature["unit"] = "F"
    climate_output_temperature = (
        climate_output_temperature.droplevel("product_long")
        .reset_index()
        .set_index(["model", "scenario", "region", "variable", "gas", "unit"])
    )

    climate_output_concentration_co2e.reset_index(inplace=True)
    climate_output_concentration_co2e["model"] = model
    climate_output_concentration_co2e["region"] = "world"
    climate_output_concentration_co2e.rename(
        columns={"product_long": "variable"}, inplace=True
    )
    climate_output_concentration_co2e["gas"] = 0
    climate_output_concentration_co2e.replace({"CO2e": "Concentration"}, inplace=True)
    climate_output_concentration_co2e["gas"] = "CO2e"
    climate_output_concentration_co2e["unit"] = "PPM"
    climate_output_concentration_co2e.set_index(
        ["model", "scenario", "region", "variable", "gas", "unit"], inplace=True
    )

    climate_output_forcing_co2e.reset_index(inplace=True)
    climate_output_forcing_co2e["model"] = model
    climate_output_forcing_co2e["region"] = "world"
    climate_output_forcing_co2e.rename(
        columns={"product_long": "variable"}, inplace=True
    )
    climate_output_forcing_co2e["gas"] = 0
    climate_output_forcing_co2e.replace({"CO2e": "Radiative forcing"}, inplace=True)
    climate_output_forcing_co2e["gas"] = "CO2e"
    climate_output_forcing_co2e["unit"] = "W/m2"
    climate_output_forcing_co2e.set_index(
        ["model", "scenario", "region", "variable", "gas", "unit"], inplace=True
    )

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    pd.concat(
        [
            climate_historical_concentration,
            climate_historical_forcing,
            climate_historical_temperature,
            climate_output_concentration,
            climate_output_forcing,
            climate_output_temperature,
        ]
    ).to_csv("podi/data/output/climate/climate_output.csv")

    pd.concat(
        [
            climate_output_concentration_co2e,
            climate_output_forcing_co2e,
            climate_output_temperature,
        ]
    ).to_csv("podi/data/output/climate/climate_output_co2e.csv")

    # endregion

    return
