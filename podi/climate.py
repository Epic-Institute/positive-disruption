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

# endregion


def climate(
    emissions_output, cdr_output, data_start_year, data_end_year, proj_end_year
):

    ############################################
    # PREPARE EMISSIONS DATA FOR CLIMATE MODEL #
    ############################################

    # region

    # Gases that FAIR climate model takes as input, with associated units
    fair_input_gases = {
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

    # Gases that FAIR climate model provides as output, with associated units
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

    # Align gas names that are different between FAIR and emissions_output

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
        "HCFC142b",
    ]:
        emissions_output.rename(index={gas: gas.replace("-", "")}, inplace=True)

    #'HFC-43-10-mee' to 'HFC43-10'
    emissions_output.rename(index={"HFC-43-10-mee": "HFC43-10"}, inplace=True)

    # Add 'CFC11', 'CFC12', 'CFC113', 'CFC114', 'CFC115', 'CCl4', 'Methyl chloroform', 'HCFC22', 'Halon 1211', 'Halon 1202', 'Halon 1301', 'Halon 2401', 'CH3Br', 'CH3Cl' to emissions_output

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output = emissions_output[
        ~(
            emissions_output.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    # Update emissions that don't list gas in flow_long
    emissions_output.reset_index(inplace=True)

    # Select emissions that don't list gas in flow_long (all list unit as 'MtCO2')
    emissions_output_co2 = emissions_output[(emissions_output.unit == "MtCO2").values]

    # Remove the subset above from full emissions list
    emissions_output = emissions_output[~(emissions_output.unit == "MtCO2").values]

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

    # endregion

    ################################################
    # ESTIMATE CONCENTRATION, FORCING, TEMPERATURE #
    ################################################

    # region

    # Load RCP emissions, then swap in emissions_output

    # Run the climate model
    C, F, T = fair.forward.fair_scm(emissions=emissions_output)

    climate_output_concentration = (
        pd.DataFrame(C)
        .loc[225:335]
        .set_index(np.arange(data_start_year, proj_end_year + 1, 1))
    )

    climate_output_forcing = (
        pd.DataFrame(F)
        .loc[225:335]
        .set_index(np.arange(data_start_year, proj_end_year + 1, 1))
    )

    climate_output_temperature = (
        pd.DataFrame(T)
        .loc[225:335]
        .set_index(np.arange(data_start_year, proj_end_year + 1, 1))
    )

    # Create version of climate_output_concentration with units CO2e
    # Add missing GWP values to gwp
    gwp.data[version].update(
        {
            "CO2": 1,
            "BC": 2240,
            "CO": 0,
            "NH3": 0,
            "NMVOC": 0,
            "NOx": 0,
            "OC": 0,
            "SO2": 0,
        }
    )

    # Choose version of GWP values
    version = "AR6GWP100"  # Choose from ['SARGWP100', 'AR4GWP100', 'AR5GWP100', 'AR5CCFGWP100', 'AR6GWP100', 'AR6GWP20', 'AR6GWP500', 'AR6GTP100']

    climate_output_concentration_co2e = climate_output_concentration.apply(
        lambda x: x.mul(gwp.data[version[x.name[8]]]), axis=1
    )

    # endregion

    ######################################################
    #  LOAD HISTORICAL DATA & COMPARE TO MODELED RESULTS #
    ######################################################

    # region

    # Load GHG concentration data from external source
    climate_concentration_historical = pd.DataFrame(
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
    climate_concentration_historical = climate_concentration_historical[
        (climate_concentration_historical["Entity"] == "World").values
    ].drop(columns="Entity")

    # Update column names
    climate_concentration_historical = climate_concentration_historical.rename(
        {
            "CO2 concentrations": "CO2",
            "CH4 concentrations": "CH4",
            "N2O concentrations": "N2O",
        },
        axis="columns",
    )

    climate_concentration_historical = (
        climate_concentration_historical[
            (climate_concentration_historical["Year"] >= data_start_year).values
        ]
        .rename(columns={"Year": "year"})
        .set_index("year")
    )

    # Load radiative forcing data from external source
    climate_forcing_historical = pd.DataFrame(
        pd.read_csv("podi/data/external/radiative_forcing_historical.csv")
    )
    climate_forcing_historical.columns = climate_forcing_historical.columns.astype(int)
    climate_forcing_historical = climate_forcing_historical.loc[
        :, data_start_year:data_end_year
    ]

    # Load temperature change data from external source
    climate_temperature_historical = pd.DataFrame(
        pd.read_csv("podi/data/external/temperature_change_historical.csv")
    )
    climate_temperature_historical.columns = (
        climate_temperature_historical.columns.astype(int)
    )
    climate_temperature_historical = climate_temperature_historical.loc[
        :, data_start_year:data_end_year
    ]

    # Create annual timeseries df and merge with decadal climate_historical df
    climate_historical = pd.DataFrame(
        index=climate_historical2.index,
        columns=np.arange(data_start_year, data_end_year + 1, 1),
    )

    climate_historical.update(climate_historical2.loc[:, :data_end_year])
    climate_historical = climate_historical.astype(float)
    climate_historical.interpolate(axis=1, limit_area="inside", inplace=True)

    # Calculate error between modeled and observed
    climate_error = abs((climate_historical - climate_historical) / climate_historical)

    # Plot
    climate_error.T.plot(
        legend=False, title="Error between PD22 and NOAA GHG Concentrations", ylabel="%"
    )

    climate_error.T.plot(
        legend=False, title="Error between PD22 and NOAA Radiative Forcing", ylabel="%"
    )

    climate_error.T.plot(
        legend=False, title="Error between PD22 and NOAA Temperature Change", ylabel="%"
    )

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    pd.concat(
        [
            climate_output_concentration,
            climate_output_forcing,
            climate_output_temperature,
        ]
    ).to_csv("podi/data/climate_output.csv")

    # endregion

    return
