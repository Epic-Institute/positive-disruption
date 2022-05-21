# region

import pandas as pd
from numpy import NaN, concatenate
import numpy as np
import pyam
import os.path
import traceback
import matplotlib.pyplot as plt
import silicone.database_crunchers
from silicone.utils import download_or_load_sr15
import aneris
from pandarallel import pandarallel
import globalwarmingpotentials as gwp

from podi.afolu import afolu

pandarallel.initialize(nb_workers=4)

# endregion


def emissions(
    scenario,
    energy_adoption,
    emissions_afolu_mitigated,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    #########################################
    #  CALCULATE CO2 EMISSIONS FROM ENERGY  #
    #########################################

    recalc_emissions_energy = False
    # region
    if recalc_emissions_energy == True:
        # Load emissions factors (currently a manually produced file, with duplicates in products/flows that were split to form more detailed streams for ROAD,RAIL,DOMESAIR,NONCRUDE,etc., so duplicates are dropped, but this can be removed once emission_factors is improved)
        emission_factors = pd.read_csv("podi/data/emission_factors.csv").set_index(
            pyam.IAMC_IDX
        )
        emission_factors = emission_factors[~emission_factors.index.duplicated()]
        emission_factors.columns = emission_factors.columns.astype(int)
        emission_factors = emission_factors.loc[:, data_start_year:proj_end_year]

        # Multiply energy by emission factors to get emissions estimates
        emissions_energy = energy_adoption.parallel_apply(
            lambda x: x
            * (
                (
                    emission_factors.loc[
                        x.name[0],
                        x.name[1],
                        x.name[2],
                        "|".join([x.name[6], x.name[9]]),
                    ]
                ).squeeze()
            ),
            axis=1,
        )

        emissions_energy.index = emissions_energy.index.set_levels(
            emissions_energy.index.levels[10].str.replace("TJ", "MtCO2"), level=10
        )

        # Save to CSV file
        emissions_energy.to_csv("podi/data/emissions_energy.csv")

    index = [
        "Model",
        "Scenario",
        "Region",
        "Sector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Unit",
        "Hydrogen",
        "Flexible",
        "Nonenergy",
    ]

    emissions_energy = pd.DataFrame(
        pd.read_csv("podi/data/emissions_energy.csv")
    ).set_index(index)
    emissions_energy.columns = emissions_energy.columns.astype(int)

    # endregion

    ########################################
    #  CALCULATE GHG EMISSIONS FROM AFOLU  #
    ########################################

    # region

    # Load historical AFOLU emissions and baseline estimates (retrieved from FAOSTAT)
    emissions_afolu = (
        pd.read_csv("podi/data/FAO/Emissions_Totals_E_All_Data_NOFLAG.csv")
        .drop(
            columns=[
                "Area Code",
                "Item Code",
                "Element Code",
                "Source Code",
                "Source",
            ]
        )
        .rename(
            columns={
                "Area": "Region",
                "Item": "Product_long",
                "Element": "Flow_category",
            }
        )
        .set_index("Region")
    )
    emissions_afolu.columns = emissions_afolu.columns.str.replace("Y", "")

    # Change FAO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "FAO Region"],
            ).dropna(axis=0)
        )
        .set_index(["FAO Region"])
        .rename_axis(index={"FAO Region": "Region"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add Model and Scenario indices
    emissions_afolu["model"] = "PD22"
    emissions_afolu["scenario"] = "baseline"

    # Add Sector index
    def addsector(x):
        if x["Product_long"] in [
            "Enteric Fermentation",
            "Manure Management",
            "Rice Cultivation",
            "Synthetic Fertilizers",
            "Manure applied to Soils",
            "Manure left on Pasture",
            "Crop Residues",
            "Burning - Crop residues",
        ]:
            return "Agriculture"
        elif x["Product_long"] in [
            "Net Forest conversion",
            "Forestland",
            "Savanna fires",
            "Fires in humid tropical forests",
            "Forest fires",
            "Fires in organic soils",
            "Drained organic soils (CO2)",
            "Drained organic soils (N2O)",
        ]:
            return "Forests & Wetlands"

    emissions_afolu["sector"] = emissions_afolu.apply(lambda x: addsector(x), axis=1)

    # Split Emissions and Gas into separate columns
    def splitgas(x):
        if x["Flow_category"] in ["Emissions (CO2)"]:
            return "CO2"
        elif x["Flow_category"] in ["Emissions (CH4)"]:
            return "CH4"
        elif x["Flow_category"] in ["Emissions (N2O)"]:
            return "N2O"

    emissions_afolu["Flow_long"] = emissions_afolu.apply(lambda x: splitgas(x), axis=1)

    emissions_afolu["Flow_category"] = "Emissions"

    emissions_afolu = (
        (
            emissions_afolu.reset_index()
            .set_index(["Region"])
            .merge(regions, on=["Region"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "sector",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "Unit",
            ]
        )
        .rename_axis(index={"WEB Region": "region", "Unit": "unit"})
    ).drop(columns="Region")

    # Select data between data_start_year and proj_end_year
    emissions_afolu.columns = emissions_afolu.columns.astype(int)
    emissions_afolu = emissions_afolu.loc[:, data_start_year:proj_end_year]

    # Change unit to Mt
    emissions_afolu.update(emissions_afolu / 1e6)
    emissions_afolu = emissions_afolu.rename(index={"kilotonnes": "Mt"})

    # Drop rows with NaN in index and/or all year columns, representing duplicate regions and/or emissions
    emissions_afolu = emissions_afolu[
        ~(
            (emissions_afolu.index.get_level_values(3).isna())
            | (emissions_afolu.index.get_level_values(6).isna())
            | (emissions_afolu.isna().all(axis=1))
        )
    ]

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_afolu[np.arange(2021, 2030, 1)] = NaN
    emissions_afolu[np.arange(2031, proj_end_year, 1)] = NaN
    emissions_afolu = emissions_afolu.sort_index(axis=1)
    emissions_afolu.interpolate(method="linear", axis=1, inplace=True)
    emissions_afolu.fillna(method="bfill", inplace=True)

    # Combine historical and baseline emissions with NCS estimates
    emissions_afolu = pd.concat(
        [
            emissions_afolu,
            emissions_afolu.rename(index={"baseline": scenario}),
            -emissions_afolu_mitigated,
        ]
    )

    # endregion

    #########################################
    #  ADD IN ADDITIONAL EMISSIONS SOURCES  #
    #########################################

    # region

    # Load historical addtional emissions datasets
    gas_ceds = ["BC", "CO", "OC", "CH4", "CO2", "N2O", "NH3", "NOx", "SO2", "NMVOC"]

    emissions_additional = pd.DataFrame([])
    for gas in gas_ceds:
        emissions_additional = pd.concat(
            [
                emissions_additional,
                pd.read_csv(
                    "podi/data/CEDS/"
                    + gas
                    + "_CEDS_emissions_by_sector_country_2021_04_21.csv"
                ),
            ]
        )
    emissions_additional.columns = emissions_additional.columns.str.replace("X", "")

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "country"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()
    regions.index = (regions.index).str.lower()

    # Add Model, Scenario, and Flow_category indices
    emissions_additional["model"] = "PD22"
    emissions_additional["scenario"] = "baseline"
    emissions_additional["Flow_category"] = "Emissions"

    # Change sector index to Product_long and 'em' to 'Flow_long'
    emissions_additional.rename(
        columns={"sector": "Product_long", "em": "Flow_long"}, inplace=True
    )

    # Add Sector index
    def addsector(x):
        if x["Product_long"] in [
            "1A1a_Electricity-autoproducer",
            "1A1a_Electricity-public",
            "1A1a_Heat-production",
            "1A1bc_Other-transformation",
            "1B1_Fugitive-solid-fuels",
            "1B2_Fugitive-petr",
            "1B2b_Fugitive-NG-distr",
            "1B2b_Fugitive-NG-prod",
            "1B2d_Fugitive-other-energy",
            "7A_Fossil-fuel-fires",
        ]:
            return "Electric Power"
        elif x["Product_long"] in [
            "1A3b_Road",
            "1A3c_Rail",
            "1A3di_Oil_Tanker_Loading",
            "1A3dii_Domestic-navigation",
            "1A3eii_Other-transp",
            "1A3ai_International-aviation",
            "1A3aii_Domestic-aviation",
            "1A3di_International-shipping",
        ]:
            return "Transport"
        elif x["Product_long"] in ["1A4b_Residential"]:
            return "Residential"
        elif x["Product_long"] in ["1A4a_Commercial-institutional"]:
            return "Commercial"
        elif x["Product_long"] in [
            "1A2a_Ind-Comb-Iron-steel",
            "1A2b_Ind-Comb-Non-ferrous-metals",
            "1A2c_Ind-Comb-Chemicals",
            "1A2d_Ind-Comb-Pulp-paper",
            "1A2e_Ind-Comb-Food-tobacco",
            "1A2f_Ind-Comb-Non-metalic-minerals",
            "1A2g_Ind-Comb-Construction",
            "1A2g_Ind-Comb-machinery",
            "1A2g_Ind-Comb-mining-quarying",
            "1A2g_Ind-Comb-other",
            "1A2g_Ind-Comb-textile-leather",
            "1A2g_Ind-Comb-transpequip",
            "1A2g_Ind-Comb-wood-products",
            "1A4c_Agriculture-forestry-fishing",
            "1A5_Other-unspecified",
            "2A1_Cement-production",
            "2A2_Lime-production",
            "2Ax_Other-minerals",
            "2B_Chemical-industry",
            "2B2_Chemicals-Nitric-acid",
            "2B3_Chemicals-Adipic-acid",
            "2C_Metal-production",
            "2D_Chemical-products-manufacture-processing",
            "2D_Degreasing-Cleaning",
            "2D_Other-product-use",
            "2D_Paint-application",
            "2H_Pulp-and-paper-food-beverage-wood",
            "2L_Other-process-emissions",
            "5A_Solid-waste-disposal",
            "5C_Waste-combustion",
            "5D_Wastewater-handling",
            "5E_Other-waste-handling",
            "6A_Other-in-total",
            "7BC_Indirect-N2O-non-agricultural-N",
        ]:
            return "Industrial"
        elif x["Product_long"] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ]:
            return "Agriculture"

    emissions_additional["sector"] = emissions_additional.apply(
        lambda x: addsector(x), axis=1
    )

    emissions_additional = (
        (
            emissions_additional.reset_index()
            .set_index(["country"])
            .merge(regions, on=["country"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "sector",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "units",
            ]
        )
        .rename_axis(index={"WEB Region": "region", "units": "unit"})
    ).drop(columns=["country", "index"])

    # Select data between data_start_year and proj_end_year
    emissions_additional.columns = emissions_additional.columns.astype(int)
    emissions_additional = emissions_additional.loc[:, data_start_year:proj_end_year]

    # Change unit from kt to Mt
    emissions_additional.update(emissions_additional / 1e6)
    emissions_additional = emissions_additional.rename(
        index={
            "ktC": "Mt",
            "ktCO": "Mt",
            "ktCH4": "Mt",
            "ktCO2": "Mt",
            "ktN2O": "Mt",
            "ktNH3": "Mt",
            "ktNO2": "Mt",
            "ktSO2": "Mt",
            "ktNMVOC": "Mt",
        }
    )

    # Drop rows with NaN in index and/or all year columns, representing duplicate regions and/or emissions
    emissions_additional = emissions_additional[
        ~(
            (emissions_additional.index.get_level_values(1).isna())
            | (emissions_additional.index.get_level_values(4).isna())
            | (emissions_additional.isna().all(axis=1))
        )
    ]

    # Create projections by applying most durrent data value to all future years
    emissions_additional[np.arange(data_end_year, proj_end_year + 1, 1)] = NaN
    emissions_additional = emissions_additional.sort_index(axis=1)
    emissions_additional.fillna(method="ffill", axis=1, inplace=True)

    # Drop double counted emissions
    def remove_doublcount(x):
        # Drop CO2 that was already estimated in energy module
        if x.name[4] in [
            "1A1a_Electricity-autoproducer",
            "1A1a_Electricity-public",
            "1A1a_Heat-production",
            "1A1bc_Other-transformation",
            "1A2a_Ind-Comb-Iron-steel",
            "1A2b_Ind-Comb-Non-ferrous-metals",
            "1A2c_Ind-Comb-Chemicals",
            "1A2d_Ind-Comb-Pulp-paper",
            "1A2e_Ind-Comb-Food-tobacco",
            "1A2f_Ind-Comb-Non-metalic-minerals",
            "1A2g_Ind-Comb-Construction",
            "1A2g_Ind-Comb-machinery",
            "1A2g_Ind-Comb-mining-quarying",
            "1A2g_Ind-Comb-other",
            "1A2g_Ind-Comb-textile-leather",
            "1A2g_Ind-Comb-transpequip",
            "1A2g_Ind-Comb-wood-products",
            "1A3b_Road",
            "1A3c_Rail",
            "1A3aii_Domestic-aviation",
            "1A3dii_Domestic-navigation",
            "1A3eii_Other-transp",
            "1A3ai_International-aviation",
            "1A3di_International-shipping" "1A4a_Commercial-institutional",
            "1A4b_Residential",
            "1A4c_Agriculture-forestry-fishing",
            "1A5_Other-unspecified",
        ] and x.name[6] in ["CO2"]:
            x.rename(
                ("NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"), inplace=True
            )

        # Drop CO2, CH4, N2O that was already estimated in FAO historical data
        if x.name[4] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ] and x.name[6] in ["CO2", "CH4", "N2O"]:
            x.rename(
                ("NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"), inplace=True
            )

        return x

    emissions_additional = emissions_additional.apply(
        lambda x: remove_doublcount(x), axis=1
    )
    emissions_additional = emissions_additional.loc[
        emissions_additional.index.dropna(how="any"), :
    ]

    # Get F-Gas data
    gas_edgar = [
        "C2F6",
        "C3F8",
        "C4F10",
        "C5F12",
        "C6F14",
        "c-C4F8",
        "CF4",
        "HCFC-141b",
        "HCFC-142b",
        "HFC-23",
        "HFC-32",
        "HFC-41",
        "HFC-43-10-mee",
        "HFC-125",
        "HFC-134",
        "HFC-134a",
        "HFC-143",
        "HFC-143a",
        "HFC-152a",
        "HFC-227ea",
        "HFC-236fa",
        "HFC-245fa",
        "HFC-365mfc",
        "NF3",
        "SF6",
    ]

    emissions_additional_fgas = pd.DataFrame([])
    for gas in gas_edgar:
        emissions_additional_fgas = pd.concat(
            [
                emissions_additional_fgas,
                pd.read_excel(
                    io="podi/data/EDGAR/" + gas + "_1990_2018.xlsx",
                    sheet_name="v6.0_EM_" + gas + "_IPCC2006",
                    skiprows=9,
                ),
            ]
        ).drop(
            columns=[
                "IPCC_annex",
                "C_group_IM24_sh",
                "Name",
                "ipcc_code_2006_for_standard_report",
                "fossil_bio",
            ]
        )
    emissions_additional_fgas.columns = emissions_additional_fgas.columns.str.replace(
        "Y_", ""
    )
    emissions_additional_fgas.columns = emissions_additional_fgas.columns.str.replace(
        "ipcc_code_2006_for_standard_report_name", "Product_long"
    )

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "Country_code_A3"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add Model and Scenario indices
    emissions_additional_fgas["model"] = "PD22"
    emissions_additional_fgas["scenario"] = "baseline"

    # Add Sector index
    def addsector(x):
        if x["Product_long"] in [
            "Metal Industry",
            "Other Product Manufacture and Use",
            "Electronics Industry",
            "Chemical Industry",
            "Product Uses as Substitutes for Ozone Depleting Substances",
        ]:
            return "Industrial"

    emissions_additional_fgas["sector"] = emissions_additional_fgas.apply(
        lambda x: addsector(x), axis=1
    )

    emissions_additional_fgas["Flow_category"] = "Emissions"

    emissions_additional_fgas["Flow_long"] = gas

    emissions_additional_fgas = (
        (
            emissions_additional_fgas.reset_index()
            .set_index(["Country_code_A3"])
            .merge(regions, on=["Country_code_A3"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "sector",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "Unit",
            ]
        )
        .rename_axis(index={"Country_code_A3": "region", "units": "unit"})
    ).drop(columns="Region")

    # Select data between data_start_year and proj_end_year
    emissions_additional_fgas.columns = emissions_additional_fgas.columns.astype(int)
    emissions_additional_fgas = emissions_additional_fgas.loc[
        :, data_start_year:proj_end_year
    ]

    # Change unit from kt to Mt
    emissions_additional_fgas.update(emissions_additional_fgas / 1e6)
    emissions_additional_fgas = emissions_additional_fgas.rename(index={"kt": "Mt"})

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_additional_fgas[np.arange(2021, 2030, 1)] = NaN
    emissions_additional_fgas[np.arange(2031, proj_end_year, 1)] = NaN
    emissions_additional_fgas = emissions_additional_fgas.sort_index(axis=1)
    emissions_additional_fgas.interpolate(method="linear", axis=1, inplace=True)
    emissions_additional_fgas.fillna(method="bfill", inplace=True)

    # Combine all gases
    emissions_additional = pd.concat([emissions_additional, emissions_additional_fgas])

    # Create baseline and pathway scenarios
    emissions_additional = pd.concat(
        [
            emissions_additional,
            emissions_additional.rename(index={"baseline": scenario}),
        ]
    )

    # Project additional emissions using percent change in each sector
    def proj(data):

        data_per_change = (
            data.loc[slice(None), slice(None), "Industrial"]
            .groupby(["Scenario", "Region"])
            .mean()
            .loc[:, data_end_year - 1 :]
            .pct_change(axis=1)
            .dropna(axis=1)
            .apply(lambda x: x + 1, axis=1)
            .merge(
                data,
                right_on=["Scenario", "Region"],
                left_on=["Scenario", "Region"],
            )
            .reindex(sorted(data.columns), axis=1)
        )

        data = data_per_change.loc[:, : data_end_year - 1].merge(
            data_per_change.loc[:, data_end_year - 1 :]
            .cumprod(axis=1)
            .loc[:, data_end_year:],
            right_on=["Region", "Scenario"],
            left_on=["Region", "Scenario"],
        )

        return data

    emissions_additional = proj(emissions_additional)

    # Rename Product_long values
    simple_index = {
        "Fossil fuels": "Fossil Fuel Heat",
        "1A1a_Electricity-autoproducer": "Fossil Fuels",
        "1A1a_Electricity-public": "Fossil Fuels",
        "1A1a_Heat-production": "Fossil Fuel Heat",
        "1A1bc_Other-transformation": "Other Fossil Transformation",
        "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
        "1B2_Fugitive-petr": "Fugitive Petroleum",
        "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
        "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
        "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
        "7A_Fossil-fuel-fires": "Fossil Fuel Fires",
        "1A2a_Ind-Comb-Iron-steel": "Other Industrial",
        "1A2b_Ind-Comb-Non-ferrous-metals": "Other Industrial",
        "1A2c_Ind-Comb-Chemicals": "Chemical Production",
        "1A2d_Ind-Comb-Pulp-paper": "Other Industrial",
        "1A2e_Ind-Comb-Food-tobacco": "Other Industrial",
        "1A2f_Ind-Comb-Non-metalic-minerals": "Other Industrial",
        "1A2g_Ind-Comb-Construction": "Other Industrial",
        "1A2g_Ind-Comb-machinery": "Other Industrial",
        "1A2g_Ind-Comb-mining-quarying": "Other Industrial",
        "1A2g_Ind-Comb-other": "Other Industrial",
        "1A2g_Ind-Comb-textile-leather": "Other Industrial",
        "1A2g_Ind-Comb-transpequip": "Other Industrial",
        "1A2g_Ind-Comb-wood-products": "Other Industrial",
        "2A1_Cement-production": "Cement Production",
        "2A2_Lime-production": "Lime Production",
        "2Ax_Other-minerals": "Other Industrial",
        "2B_Chemical-industry": "Chemical Production",
        "2B2_Chemicals-Nitric-acid": "Other Industrial",
        "2B3_Chemicals-Adipic-acid": "Other Industrial",
        "2C_Metal-production": "Metal Production",
        "2D_Chemical-products-manufacture-processing": "Chemical Production",
        "2D_Degreasing-Cleaning": "Chemical Production",
        "2D_Other-product-use": "Chemical Production",
        "2D_Paint-application": "Chemical Production",
        "2H_Pulp-and-paper-food-beverage-wood": "Other Industrial",
        "2L_Other-process-emissions": "Other Industrial",
        "5A_Solid-waste-disposal": "Solid Waste Disposal",
        "5C_Waste-combustion": "Other Industrial",
        "5D_Wastewater-handling": "Wastewater Handling",
        "5E_Other-waste-handling": "Other Industrial",
        "7BC_Indirect-N2O-non-agricultural-N": "Other Industrial",
        "1A5_Other-unspecified": "Other Industrial",
        "6A_Other-in-total": "Other Industrial",
        "1A3b_Road": "Road Transport",
        "1A3c_Rail": "Rail Transport",
        "1A3di_Oil_Tanker_Loading": "Maritime Transport",
        "1A3dii_Domestic-navigation": "Maritime Transport",
        "1A3eii_Other-transp": "Other Transport",
        "1A4a_Commercial-institutional": "Commercial Buildings",
        "1A4b_Residential": "Residential Buildings",
        "3B_Manure-management": "Manure Management",
        "3D_Rice-Cultivation": "Rice Cultivation",
        "3D_Soil-emissions": "Fertilized Soils",
        "3E_Enteric-fermentation": "Enteric Fermentation",
        "3I_Agriculture-other": "Other Agricultural",
    }

    detailed_index = {
        "Fossil fuels": "Fossil fuel Heat",
        "1A1a_Electricity-autoproducer": "Fossil Fuels",
        "1A1a_Electricity-public": "Fossil Fuels",
        "1A1a_Heat-production": "Fossil fuel Heat",
        "1A1bc_Other-transformation": "Other Fossil Transformation",
        "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
        "1B2_Fugitive-petr": "Fugitive Petroleum",
        "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
        "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
        "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
        "7A_Fossil-fuel-fires": "Fossil Fuel Fires",
        "1A2a_Ind-Comb-Iron-steel": "Steel Production",
        "1A2b_Ind-Comb-Non-ferrous-metals": "Non-ferrous Metal Production",
        "1A2c_Ind-Comb-Chemicals": "Chemical Production",
        "1A2d_Ind-Comb-Pulp-paper": "Pulp-Paper Production",
        "1A2e_Ind-Comb-Food-tobacco": "Food Production",
        "1A2f_Ind-Comb-Non-metalic-minerals": "Non-metalic Mineral Production",
        "1A2g_Ind-Comb-Construction": "Construction",
        "1A2g_Ind-Comb-machinery": "Machinery",
        "1A2g_Ind-Comb-mining-quarying": "Mining, Quarying",
        "1A2g_Ind-Comb-other": "Other Industrial",
        "1A2g_Ind-Comb-textile-leather": "Textile, Leather Production",
        "1A2g_Ind-Comb-transpequip": "Transportation Equipment Production",
        "1A2g_Ind-Comb-wood-products": "Wood Production",
        "2A1_Cement-production": "Cement Production",
        "2A2_Lime-production": "Lime Production",
        "2Ax_Other-minerals": "Other Mineral Production",
        "2B_Chemical-industry": "Chemical Production",
        "2B2_Chemicals-Nitric-acid": "Nitric Acid Production",
        "2B3_Chemicals-Adipic-acid": "Adipic Acid Production",
        "2C_Metal-production": "Metal Production",
        "2D_Chemical-products-manufacture-processing": "Chemical Production",
        "2D_Degreasing-Cleaning": "Chemical Production",
        "2D_Other-product-use": "Chemical Production",
        "2D_Paint-application": "Chemical Production",
        "2H_Pulp-and-paper-food-beverage-wood": "Food Production",
        "2L_Other-process-emissions": "Other Industrial",
        "5A_Solid-waste-disposal": "Solid Waste Disposal",
        "5C_Waste-combustion": "Waste Combustion",
        "5D_Wastewater-handling": "Wastewater Handling",
        "5E_Other-waste-handling": "Waste Combustion",
        "7BC_Indirect-N2O-non-agricultural-N": "Indirect N2O from Non-Ag N",
        "1A5_Other-unspecified": "Other Industrial",
        "6A_Other-in-total": "Other Industrial",
        "1A3b_Road": "Road Transport",
        "1A3c_Rail": "Rail Transport",
        "1A3di_Oil_Tanker_Loading": "Maritime Transport",
        "1A3dii_Domestic-navigation": "Maritime Transport",
        "1A3eii_Other-transp": "Other Transport",
        "1A4a_Commercial-institutional": "Commercial Buildings",
        "1A4b_Residential": "Residential Buildings",
        "3B_Manure-management": "Manure Management",
        "3D_Rice-Cultivation": "Rice Cultivation",
        "3D_Soil-emissions": "Fertilized Soils",
        "3E_Enteric-fermentation": "Enteric Fermentation",
        "3I_Agriculture-other": "Other Agricultural",
    }

    emissions_additional = (
        emissions_additional.rename(index=detailed_index)
        .groupby(
            [
                "model",
                "scenario",
                "region",
                "sector",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "unit",
            ]
        )
        .sum()
    )

    # endregion

    ##################################################################
    #  MODEL EMISSIONS OF OTHER GHGS FROM CO2/CH4/N2O/F-GAS RESULTS  #
    ##################################################################

    # region

    # At this point its likely that we want to limit Flow_categories to 'Final consumption' that is not Electricity or Heat, 'Energy industry own use and Losses', 'Electricity output', and 'Heat output', to avoid double counting

    emissions_output = pd.concat(
        [emissions_energy, emissions_afolu, emissions_additional]
    )

    # Looking to estimate aerosols, PM, etc

    # https://github.com/GranthamImperial/silicone/tree/master/notebooks

    # endregion

    ##############################################################
    #  LOAD HISTORICAL EMISSIONS & COMPARE TO MODELED EMISSIONS  #
    ##############################################################

    # region

    # Load historical emissions data from external source
    emissions_historical = pd.read_csv("podi/data/emissions_historical.csv").set_index(
        pyam.IAMC_IDX
    )
    emissions_historical.columns = emissions_historical.columns.astype(int)

    # Harmonize modeled emissions projections with observed historical emissions

    # https://aneris.readthedocs.io/en/latest/index.html

    # endregion

    ################################################
    #  CREATE A VERSION OF OUTPUT THAT IS IN CO2e  #
    ################################################

    # region
    emissions_output_co2e = emissions_output.copy()

    # Define global warming potential of all GHGs
    version = "AR6GWP100"  # Choose from ['SARGWP100', 'AR4GWP100', 'AR5GWP100', 'AR5CCFGWP100', 'AR6GWP100', 'AR6GWP20', 'AR6GWP500', 'AR6GTP100']

    # TODO check gas names match with gwp dict

    emissions_output_co2e = emissions_output_co2e.apply(
        lambda x: x.mul(gwp.data[version][x.name(6)]), axis=1
    )

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region
    emissions_output.to_csv("podi/data/emissions_output.csv")

    emissions_output_co2e.to_csv("podi/data/emissions_output_co2e.csv")

    # endregion

    return
