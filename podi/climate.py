#!/usr/bin/env python

# region

import numpy as np
import pandas as pd
import globalwarmingpotentials as gwp
import fair
from fair.forward import fair_scm
from fair.RCPs import rcp26, rcp45, rcp60, rcp85, rcp3pd
from fair.SSPs import ssp119
from fair.constants import radeff
from scipy.stats import gamma
import pyam

# endregion


def climate(
    scenario,
    emissions_output,
    emissions_output_co2e,
    cdr_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ############################################
    # PREPARE EMISSIONS DATA FOR CLIMATE MODEL #
    ############################################

    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output = emissions_output[
        ~(
            emissions_output.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    # Rename emissions_output gases to match required inputs for FAIR

    # SO2 to SOx
    emissions_output.rename(index={"SO2": "SOx"}, inplace=True)

    # Drop dashes
    for gas in [
        "HFC-23",
        "HFC-32",
        "HFC-125",
        "HFC-134a",
        "HFC-143a",
        "HFC-227ea",
        "HFC-245fa",
        "HCFC-141b",
        "HCFC-142b",
    ]:
        emissions_output.rename(index={gas: gas.replace("-", "")}, inplace=True)

    #'HFC-43-10-mee' to 'HFC43-10'
    emissions_output.rename(index={"HFC-43-10-mee": "HFC43-10"}, inplace=True)

    # Update emissions that don't list gas in flow_long (these are all CO2)
    emissions_output.reset_index(inplace=True)

    # Select CO2 emissions
    emissions_output_co2 = emissions_output[
        ~(
            emissions_output.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "SOx",
                    "CO",
                    "NMVOC",
                    "NOx",
                    "BC",
                    "OC",
                    "NH3",
                    "CF4",
                    "C2F6",
                    "C6F14",
                    "HFC23",
                    "HFC32",
                    "HFC43-10",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC227ea",
                    "HFC245fa",
                    "SF6",
                    "CFC11",
                    "CFC12",
                    "CFC113",
                    "CFC114",
                    "CFC115",
                    "CCl4",
                    "Methyl chloroform",
                    "HCFC22",
                    "HCFC141b",
                    "HCFC142b",
                    "Halon 1211",
                    "Halon 1202",
                    "Halon 1301",
                    "Halon 2401",
                    "CH3Br",
                    "CH3Cl",
                    "HFC-365mfc",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "c-C4F8",
                    "HFC-134",
                    "HFC-143",
                    "HFC-152a",
                    "HFC-236fa",
                    "HFC-41",
                    "C5F12",
                ]
            )
        ).values
    ]

    # Remove CO2 emissions from full emissions list
    emissions_output = emissions_output[
        (
            emissions_output.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "SOx",
                    "CO",
                    "NMVOC",
                    "NOx",
                    "BC",
                    "OC",
                    "NH3",
                    "CF4",
                    "C2F6",
                    "C6F14",
                    "HFC23",
                    "HFC32",
                    "HFC43-10",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC227ea",
                    "HFC245fa",
                    "SF6",
                    "CFC11",
                    "CFC12",
                    "CFC113",
                    "CFC114",
                    "CFC115",
                    "CCl4",
                    "Methyl chloroform",
                    "HCFC22",
                    "HCFC141b",
                    "HCFC142b",
                    "Halon 1211",
                    "Halon 1202",
                    "Halon 1301",
                    "Halon 2401",
                    "CH3Br",
                    "CH3Cl",
                    "HFC-365mfc",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "c-C4F8",
                    "HFC-134",
                    "HFC-143",
                    "HFC-152a",
                    "HFC-236fa",
                    "HFC-41",
                    "C5F12",
                ]
            )
        ).values
    ]

    # Replace 'flow_long' value with 'CO2'
    emissions_output_co2.drop(columns="flow_long", inplace=True)
    emissions_output_co2["flow_long"] = "CO2"

    # Replace 'CO2' with 'CO2-fossil' for subset
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

    emissions_output_fossil["flow_long"] = "CO2-fossil"

    # Replace 'CO2' with 'CO-landuse' for subset
    emissions_output_landuse = emissions_output_co2[
        (
            (emissions_output_co2.flow_long == "CO2")
            & (emissions_output_co2.sector.isin(["Agriculture", "Forests & Wetlands"]))
        ).values
    ].drop(columns="flow_long")

    emissions_output_landuse["flow_long"] = "CO2-landuse"

    # Recombine <ADD EMISSIONS_CDR_OUTPUT HERE>
    emissions_output_co2 = pd.concat(
        [emissions_output_fossil, emissions_output_landuse]
    )

    # Update units from 'MtCO2' to 'Mt'
    emissions_output_co2 = emissions_output_co2.replace("MtCO2", "Mt")

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

    # List gases that FAIR climate model takes as input, with associated units
    fair_input_gases = {
        "index": "Year",
        "CO2-fossil": "GtC/yr",
        "CO2-landuse": "GtC/yr",
        "CH4": "Mt/yr",
        "N2O": "MtN2/yr",
        "SOx": "MtS/yr",
        "CO": "Mt/yr",
        "NMVOC": "Mt/yr",
        "NOx": "MtN/yr",
        "BC": "Mt/yr",
        "OC": "Mt/yr",
        "NH3": "Mt/yr",
        "CF4": "kt/yr",
        "C2F6": "kt/yr",
        "C6F14": "kt/yr",
        "HFC23": "kt/yr",
        "HFC32": "kt/yr",
        "HFC43-10": "kt/yr",
        "HFC125": "kt/yr",
        "HFC134a": "kt/yr",
        "HFC143a": "kt/yr",
        "HFC227ea": "kt/yr",
        "HFC245fa": "kt/yr",
        "SF6": "kt/yr",
        "CFC11": "kt/yr",
        "CFC12": "kt/yr",
        "CFC113": "kt/yr",
        "CFC114": "kt/yr",
        "CFC115": "kt/yr",
        "CCl4": "kt/yr",
        "Methyl chloroform": "kt/yr",
        "HCFC22": "kt/yr",
        "HCFC141b": "kt/yr",
        "HCFC142b": "kt/yr",
        "Halon 1211": "kt/yr",
        "Halon 1202": "kt/yr",
        "Halon 1301": "kt/yr",
        "Halon 2401": "kt/yr",
        "CH3Br": "kt/yr",
        "CH3Cl": "kt/yr",
    }

    # Filter emissions_output to contain only inputs for fair_input_gases
    emissions_output = emissions_output[
        (emissions_output.reset_index().flow_long.isin(fair_input_gases.keys())).values
    ]

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output = emissions_output.apply(
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

    # Add in remaining gases needed for fair_input_gases and format for input into FAIR
    emissions_output = pd.concat(
        [
            emissions_output.groupby("flow_long").sum().T,
            pd.DataFrame(
                index=emissions_output.columns,
                columns=[
                    "CFC11",
                    "CFC12",
                    "CFC113",
                    "CFC114",
                    "CFC115",
                    "CCl4",
                    "Methyl chloroform",
                    "HCFC22",
                    "Halon 1211",
                    "Halon 1202",
                    "Halon 1301",
                    "Halon 2401",
                    "CH3Br",
                    "CH3Cl",
                ],
            ).fillna(0),
        ],
        axis=1,
    ).reset_index()

    emissions_output = np.array(emissions_output[list(fair_input_gases.keys())])

    # endregion

    ################################################
    # ESTIMATE CONCENTRATION, FORCING, TEMPERATURE #
    ################################################

    # region

    # Run the climate model. Note that natural emissions of CH4 and N2O is set to zero, and volcanic and solar forcing are provided externally and estimated here
    C, F, T = fair.forward.fair_scm(
        emissions=emissions_output,
        natural=np.zeros((len(emissions_output), 2)),
        F_solar=0.1 * np.sin(2 * np.pi * np.arange(len(emissions_output)) / 11.5),
        F_volcanic=-gamma.rvs(0.2, size=len(emissions_output), random_state=100),
    )

    # Gases that FAIR provides as output, with associated units
    fair_output_gases = {
        "CO2": "ppm",
        "CH4": "ppb",
        "N2O": "ppb",
        "CF4": "ppt",
        "C2F6": "ppt",
        "C6F14": "ppt",
        "HFC23": "ppt",
        "HFC32": "ppt",
        "HFC43-10": "ppt",
        "HFC125": "ppt",
        "HFC134a": "ppt",
        "HFC143a": "ppt",
        "HFC227ea": "ppt",
        "HFC245fa": "ppt",
        "SF6": "ppt",
        "CFC11": "ppt",
        "CFC12": "ppt",
        "CFC113": "ppt",
        "CFC114": "ppt",
        "CFC115": "ppt",
        "CCl4": "ppt",
        "Methyl chloroform": "ppt",
        "HCFC22": "ppt",
        "HCFC141b": "ppt",
        "HCFC142b": "ppt",
        "Halon 1211": "ppt",
        "Halon 1202": "ppt",
        "Halon 1301": "ppt",
        "Halon 2401": "ppt",
        "CH3Br": "ppt",
        "CH3Cl": "ppt",
    }

    # Forcing that FAIR provides as output
    fair_output_forcing = [
        "CO2",
        "CH4",
        "N2O",
        "All other well-mixed GHGs",
        "Tropospheric O3",
        "Stratospheric O3",
        "Stratospheric water vapour from CH4 oxidation",
        "Contrails",
        "Aerosols",
        "Black carbon on snow",
        "Land use change",
        "Volcanic",
        "Solar",
    ]

    climate_output_concentration = pd.DataFrame(
        data=C,
        index=np.arange(data_start_year, proj_end_year + 1, 1),
        columns=list(fair_output_gases.keys()),
    )
    climate_output_concentration.index.set_names("year", inplace=True)

    climate_output_forcing = pd.DataFrame(
        data=F,
        index=np.arange(data_start_year, proj_end_year + 1, 1),
        columns=fair_output_forcing,
    )
    climate_output_forcing.index.set_names("year", inplace=True)

    climate_output_temperature = pd.DataFrame(
        data=T,
        index=np.arange(data_start_year, proj_end_year + 1, 1),
        columns=["Temperature change"],
    )
    climate_output_temperature.index.set_names("year", inplace=True)

    # Create version of climate_output_concentration with units CO2e

    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output_co2e = emissions_output_co2e[
        ~(
            emissions_output_co2e.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output_co2e = emissions_output_co2e.groupby("flow_long").sum()

    emissions_output_co2e = emissions_output_co2e.apply(
        lambda x: x.multiply(
            pd.read_csv(
                "podi/data/climate_unit_conversions.csv", usecols=["value", "gas"]
            )
            .set_index("gas")
            .loc[x.name]
            .values[0]
        ),
        axis=1,
    )

    C_co2e, F_co2e, T_co2e = fair.forward.fair_scm(
        emissions=emissions_output_co2e.values[0],
        natural=np.zeros((len(emissions_output_co2e), 2)),
        F_solar=0.1 * np.sin(2 * np.pi * np.arange(len(emissions_output_co2e)) / 11.5),
        F_volcanic=-gamma.rvs(0.2, size=len(emissions_output_co2e), random_state=100),
        useMultigas=False,
    )

    climate_output_concentration_co2e = pd.DataFrame(
        data=C_co2e,
        index=np.arange(data_start_year, proj_end_year + 1, 1),
        columns=list(["CO2e"]),
    )
    climate_output_concentration_co2e.index.set_names("year", inplace=True)

    # endregion

    # endregion

    ######################################################
    #  LOAD HISTORICAL DATA & COMPARE TO MODELED RESULTS #
    ######################################################

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

    # Calculate error between modeled and observed
    climate_error_concentration = (
        abs(
            (
                climate_historical_concentration
                - climate_output_concentration[climate_historical_concentration.columns]
            ).dropna()
            / climate_historical_concentration
        )
        * 100
    )

    climate_error_forcing = (
        abs(
            (
                climate_historical_forcing
                - pd.DataFrame(
                    climate_output_forcing.sum(axis=1)[climate_historical_forcing.index]
                )
            ).dropna()
            / climate_historical_forcing
        )
        * 100
    )

    climate_error_temperature = (
        abs(
            (
                climate_historical_temperature
                - pd.DataFrame(
                    climate_output_temperature.sum(axis=1)[
                        climate_historical_temperature.index
                    ]
                )
            ).dropna()
            / climate_historical_temperature
        )
        * 100
    )

    # Plot
    climate_error_concentration.plot(
        legend=False, title="Error between PD22 and NOAA GHG Concentrations", ylabel="%"
    )

    climate_error_forcing.plot(
        legend=False, title="Error between PD22 and NOAA Radiative Forcing", ylabel="%"
    )

    climate_error_temperature.plot(
        legend=False, title="Error between PD22 and NOAA Temperature Change", ylabel="%"
    )

    # endregion

    ##############
    #  REFORMAT  #
    ##############

    # region

    climate_historical_concentration = climate_historical_concentration.T
    climate_historical_concentration["model"] = "PD22"
    climate_historical_concentration["scenario"] = "historical"
    climate_historical_concentration["region"] = "world"
    climate_historical_concentration["variable"] = (
        "Concentration|" + climate_historical_concentration.index
    )
    climate_historical_concentration["unit"] = "PPM"
    climate_historical_concentration.set_index(pyam.IAMC_IDX, inplace=True)

    climate_historical_forcing = climate_historical_forcing.T
    climate_historical_forcing["model"] = "PD22"
    climate_historical_forcing["scenario"] = "historical"
    climate_historical_forcing["region"] = "world"
    climate_historical_forcing["variable"] = "Radiative forcing"
    climate_historical_forcing["unit"] = "W/m2"
    climate_historical_forcing.set_index(pyam.IAMC_IDX, inplace=True)

    climate_historical_temperature = climate_historical_temperature.T
    climate_historical_temperature["model"] = "PD22"
    climate_historical_temperature["scenario"] = "historical"
    climate_historical_temperature["region"] = "world"
    climate_historical_temperature["variable"] = "Temperature change"
    climate_historical_temperature["unit"] = "F"
    climate_historical_temperature.set_index(pyam.IAMC_IDX, inplace=True)

    climate_output_concentration = climate_output_concentration.T
    climate_output_concentration["model"] = "PD22"
    climate_output_concentration["scenario"] = scenario
    climate_output_concentration["region"] = "world"
    climate_output_concentration["variable"] = (
        "Concentration|" + climate_output_concentration.index
    )
    climate_output_concentration["unit"] = "PPM"
    climate_output_concentration.set_index(pyam.IAMC_IDX, inplace=True)

    climate_output_forcing = climate_output_forcing.T
    climate_output_forcing["model"] = "PD22"
    climate_output_forcing["scenario"] = scenario
    climate_output_forcing["region"] = "world"
    climate_output_forcing["variable"] = (
        "Radiative forcing|" + climate_output_forcing.index
    )
    climate_output_forcing["unit"] = "W/m2"
    climate_output_forcing.set_index(pyam.IAMC_IDX, inplace=True)

    climate_output_temperature = climate_output_temperature.T
    climate_output_temperature["model"] = "PD22"
    climate_output_temperature["scenario"] = scenario
    climate_output_temperature["region"] = "world"
    climate_output_temperature["variable"] = climate_output_temperature.index
    climate_output_temperature["unit"] = "F"
    climate_output_temperature.set_index(pyam.IAMC_IDX, inplace=True)

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
    ).to_csv("podi/data/output/climate_output.csv")

    # endregion

    return
