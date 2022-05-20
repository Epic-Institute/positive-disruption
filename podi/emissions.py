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

from podi.afolu import afolu

pandarallel.initialize(nb_workers=4)

# endregion


def emissions(
    scenario,
    energy_adoption,
    afolu_adoption,
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
    emissions_afolu["Model"] = "PD22"
    emissions_afolu["Scenario"] = "baseline"

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

    emissions_afolu["Sector"] = emissions_afolu.apply(lambda x: addsector(x), axis=1)

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
                "Model",
                "Scenario",
                "WEB Region",
                "Sector",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "Unit",
            ]
        )
        .rename_axis(index={"WEB Region": "Region"})
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
            (emissions_afolu.index.get_level_values(1).isna())
            | (emissions_afolu.index.get_level_values(4).isna())
            | (emissions_afolu.isna().all(axis=1))
        )
    ]

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_afolu.interpolate(method="linear", axis=1, inplace=True)
    emissions_afolu.fillna(method="bfill", inplace=True)

    # Add Sector, Product_long, Flow_category, Flow_long indices to NCS

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

    elec = [
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
    ]

    ind = [
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
        "7BC_Indirect-N2O-non-agricultural-N",
        "1A5_Other-unspecified",
        "6A_Other-in-total",
    ]

    trans = [
        # "1A3ai_International-aviation",
        "1A3aii_Domestic-aviation",
        "1A3b_Road",
        "1A3c_Rail",
        # "1A3di_International-shipping",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
    ]

    build = ["1A4a_Commercial-institutional", "1A4b_Residential"]

    ag = [
        "3B_Manure-management",
        "3D_Rice-Cultivation",
        "3D_Soil-emissions",
        "3E_Enteric-fermentation",
        "3I_Agriculture-other",
        # "1A4c_Agriculture-forestry-fishing",
    ]

    # modified set of additional emissions for CO2, to avoid double counting with bottom-up combustion-based CO2 emissions estimates
    elec_co2 = [
        # "1A1a_Electricity-autoproducer",
        # "1A1a_Electricity-public",
        # "1A1a_Heat-production",
        "1A1bc_Other-transformation",
        "1B1_Fugitive-solid-fuels",
        "1B2_Fugitive-petr",
        "1B2b_Fugitive-NG-distr",
        "1B2b_Fugitive-NG-prod",
        "1B2d_Fugitive-other-energy",
        "7A_Fossil-fuel-fires",
    ]

    ind_co2 = [
        # "1A2a_Ind-Comb-Iron-steel",
        # "1A2b_Ind-Comb-Non-ferrous-metals",
        # "1A2c_Ind-Comb-Chemicals",
        # "1A2d_Ind-Comb-Pulp-paper",
        # "1A2e_Ind-Comb-Food-tobacco",
        # "1A2f_Ind-Comb-Non-metalic-minerals",
        # "1A2g_Ind-Comb-Construction",
        # "1A2g_Ind-Comb-machinery",
        # "1A2g_Ind-Comb-mining-quarying",
        # "1A2g_Ind-Comb-other",
        # "1A2g_Ind-Comb-textile-leather",
        # "1A2g_Ind-Comb-transpequip",
        # "1A2g_Ind-Comb-wood-products",
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
        "7BC_Indirect-N2O-non-agricultural-N",
        "1A5_Other-unspecified",
        "6A_Other-in-total",
    ]

    trans_co2 = [
        "1A3b_Road",
        "1A3c_Rail",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
        # "1A3di_International-shipping",
    ]

    build_co2 = []  # "1A4a_Commercial-institutional", "1A4b_Residential"

    ag_co2 = [
        "3B_Manure-management",
        "3D_Rice-Cultivation",
        "3D_Soil-emissions",
        "3E_Enteric-fermentation",
        "3I_Agriculture-other",
        # "1A4c_Agriculture-forestry-fishing",
    ]

    def rgroup(data, gas, sector):

        # Adds Sector, Variable, Gas, and Scenario labels to data, and duplicates data to allow for 'Baseline' and 'Pathway' scenarios to be made.
        data = pd.concat([data], names=["Variable"], keys=[gas])
        data = pd.concat([data], names=["Gas"], keys=[gas])
        data = pd.concat([data], names=["Scenario"], keys=["baseline"]).reorder_levels(
            ["Region", "Sector", "Variable", "Gas", "Scenario"]
        )
        data2 = data.droplevel("Scenario")
        data2 = pd.concat([data2], names=["Scenario"], keys=["pathway"]).reorder_levels(
            ["Region", "Sector", "Variable", "Gas", "Scenario"]
        )
        data = pd.concat([data, data2])

        return data

    def proj(data, sector, metric, gas):

        # Makes projections for gas emissions using the percent change in sector

        data_per_change = (
            energy_pathway.loc[slice(None), slice(None), "Industrial"]
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
            .reindex(sorted(energy_pathway.columns), axis=1)
        )

        data = data_per_change.loc[:, : data_end_year - 1].merge(
            data_per_change.loc[:, data_end_year - 1 :]
            .cumprod(axis=1)
            .loc[:, data_end_year:],
            right_on=["Region", "Scenario"],
            left_on=["Region", "Scenario"],
        )

        data = pd.concat([data], keys=[metric], names=["Variable"])
        data = pd.concat([data], keys=[gas], names=["Gas"])
        data = pd.concat([data], keys=[sector], names=["Sector"]).reorder_levels(
            ["Region", "Sector", "Variable", "Gas", "Scenario"]
        )

        data.index.set_names(
            ["Region", "Sector", "Variable", "Gas", "Scenario"], inplace=True
        )

        return data

    def proj_afolu(data, sector, metric, gas):

        # Makes projections for gas emissions using the percent change in sector

        ra_em = pd.read_csv("podi/data/emissions_agriculture.csv").set_index("Region")
        ra_em.columns = ra_em.columns.astype(int)
        ra_em = ra_em.interpolate(axis=1, method="quadratic")

        ra_em = rgroup(ra_em, "CO2")
        ra_em = ra_em.droplevel(["Variable", "Gas"])

        data_per_change = (
            ra_em.loc[:, data_end_year - 1 :]
            .pct_change(axis=1)
            .dropna(axis=1)
            .apply(lambda x: x + 1, axis=1)
            .merge(
                data,
                right_on=["Region", "Scenario"],
                left_on=["Region", "Scenario"],
            )
            .reindex(sorted(energy_pathway.columns), axis=1)
        )

        data = data_per_change.loc[:, : data_end_year - 1].merge(
            data_per_change.loc[:, data_end_year - 1 :]
            .cumprod(axis=1)
            .loc[:, data_end_year:],
            right_on=["Region", "Scenario"],
            left_on=["Region", "Scenario"],
        )

        data = pd.concat([data], keys=[metric], names=["Variable"])
        data = pd.concat([data], keys=[gas], names=["Gas"])
        data = pd.concat([data], keys=[sector], names=["Sector"]).reorder_levels(
            ["Region", "Sector", "Variable", "Gas", "Scenario"]
        )
        data.index.set_names(
            ["Region", "Sector", "Variable", "Gas", "Scenario"], inplace=True
        )

        return data

    #######
    # CO2 #
    #######

    # region

    co2 = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/emissions_CEDS_CO2_by_sector_country_2021_02_05.csv"
            ).drop(columns=["Em", "Units"])
        ).set_index(["Region", "Sector"])
        / 1000
    )
    co2.columns = co2.columns.astype(int)

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["WEB Region", "ISO"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "Region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["Region"] = regions["Region"].str.lower()

    co2 = (
        co2.reset_index()
        .set_index(["Region"])
        .merge(regions, left_on=["Region"], right_on=["ISO"])
    ).set_index(["Region", "Sector"])

    # Electricity

    # region

    co2_elec = co2.loc[slice(None), elec_co2, :]
    co2_elec2 = []
    co2_elec3 = []

    for sub in elec_co2:
        co2_elec2 = pd.DataFrame(co2_elec2).append(
            rgroup(co2_elec.loc[slice(None), [sub], :], "CO2", sub)
        )
    for sub in elec_co2:
        co2_elec3 = pd.DataFrame(co2_elec3).append(
            proj(
                co2_elec2.loc[slice(None), [sub], :], "Electricity", sub, "CO2"
            ).drop_duplicates()
        )

    co2_elec = co2_elec3

    # endregion

    # Industry

    # region

    co2_ind = co2.loc[slice(None), ind_co2, :]
    co2_ind2 = []
    co2_ind3 = []

    for sub in ind_co2:
        co2_ind2 = pd.DataFrame(co2_ind2).append(
            rgroup(co2_ind.loc[slice(None), [sub], :], "CO2", sub)
        )
    for sub in ind_co2:
        co2_ind3 = pd.DataFrame(co2_ind3).append(
            proj(
                co2_ind2.loc[slice(None), [sub], :], "Industrial", sub, "CO2"
            ).drop_duplicates()
        )

    co2_ind = co2_ind3

    # endregion

    # Transport

    # region

    co2_trans = co2.loc[slice(None), trans_co2, :]
    co2_trans2 = []
    co2_trans3 = []

    for sub in trans_co2:
        co2_trans2 = pd.DataFrame(co2_trans2).append(
            rgroup(co2_trans.loc[slice(None), [sub], :], "CO2", sub)
        )
    for sub in trans_co2:
        co2_trans3 = pd.DataFrame(co2_trans3).append(
            proj(
                co2_trans2.loc[slice(None), [sub], :], "Transport", sub, "CO2"
            ).drop_duplicates()
        )

    co2_trans = co2_trans3

    # endregion

    # Buildings

    # region

    co2_build = co2.loc[slice(None), build_co2, :]
    co2_build2 = []
    co2_build3 = []

    for sub in build_co2:
        co2_build2 = pd.DataFrame(co2_build2).append(
            rgroup(co2_build.loc[slice(None), [sub], :], "CO2", sub)
        )
    for sub in build_co2:
        co2_build3 = pd.DataFrame(co2_build3).append(
            proj(
                co2_build2.loc[slice(None), [sub], :],
                ["Residential", "Commercial"],
                sub,
                "CO2",
            ).drop_duplicates()
        )

    co2_build = co2_build3

    # endregion

    # Agriculture

    # region

    co2_ag = co2.loc[slice(None), ag_co2, :]
    co2_ag2 = []
    co2_ag3 = []

    for sub in ag_co2:
        co2_ag2 = pd.DataFrame(co2_ag2).append(
            rgroup(co2_ag.loc[slice(None), [sub], :], "CO2", sub)
        )
    for sub in ag_co2:
        co2_ag3 = pd.DataFrame(co2_ag3).append(
            proj_afolu(
                co2_ag2.loc[slice(None), [sub], :],
                "Agriculture",
                sub,
                "CO2",
            )
        )

    co2_ag = co2_ag3

    # endregion

    # Forests & Wetlands

    # region

    gas_fw = (
        pd.read_csv("podi/data/emissions_fw_historical.csv")
        .set_index(["Region", "Sector", "Gas", "Unit"])
        .droplevel("Unit")
        .groupby(["Region", "Sector", "Gas"])
        .sum()
    )
    gas_fw.columns = gas_fw.columns[::-1].astype(int)

    co2_fw = gas_fw.loc[slice(None), slice(None), "CO2"]

    co2_fw = rgroup(co2_fw, "CO2", "Forests & Wetlands")

    co2_fw = proj_afolu(co2_fw, "Forests & Wetlands", "Deforestation", "CO2")

    # endregion

    # endregion

    #######
    # CH4 #
    #######

    # region

    ch4 = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/emissions_CEDS_CH4_by_sector_country_2021_02_05.csv"
            ).drop(columns=["Em", "Units"])
        ).set_index(["Region", "Sector"])
        / 1000
        * 25
    )
    ch4.columns = ch4.columns.astype(int)

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["WEB Region", "ISO"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "Region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["Region"] = regions["Region"].str.lower()

    ch4 = (
        ch4.reset_index()
        .set_index(["Region"])
        .merge(regions, left_on=["Region"], right_on=["ISO"])
    ).set_index(["Region", "Sector"])

    # Electricity

    # region

    ch4_elec = ch4.loc[slice(None), elec, :]
    ch4_elec2 = []
    ch4_elec3 = []

    for sub in elec:
        ch4_elec2 = pd.DataFrame(ch4_elec2).append(
            rgroup(ch4_elec.loc[slice(None), [sub], :], "CH4", sub)
        )
    for sub in elec:
        ch4_elec3 = pd.DataFrame(ch4_elec3).append(
            proj(
                ch4_elec2.loc[slice(None), [sub], :], "Electricity", sub, "CH4"
            ).drop_duplicates()
        )

    ch4_elec = ch4_elec3

    # endregion

    # Industry

    # region

    ch4_ind = ch4.loc[slice(None), ind, :]
    ch4_ind2 = []
    ch4_ind3 = []

    for sub in ind:
        ch4_ind2 = pd.DataFrame(ch4_ind2).append(
            rgroup(ch4_ind.loc[slice(None), [sub], :], "CH4", sub)
        )
    for sub in ind:
        ch4_ind3 = pd.DataFrame(ch4_ind3).append(
            proj(
                ch4_ind2.loc[slice(None), [sub], :], "Industrial", sub, "CH4"
            ).drop_duplicates()
        )

    ch4_ind = ch4_ind3

    # endregion

    # Transport

    # region

    ch4_trans = ch4.loc[slice(None), trans, :]
    ch4_trans2 = []
    ch4_trans3 = []

    for sub in [
        "1A3b_Road",
        "1A3c_Rail",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
    ]:
        ch4_trans2 = pd.DataFrame(ch4_trans2).append(
            rgroup(ch4_trans.loc[slice(None), [sub], :], "CH4", sub)
        )
    for sub in [
        "1A3b_Road",
        "1A3c_Rail",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
    ]:
        ch4_trans3 = pd.DataFrame(ch4_trans3).append(
            proj(
                ch4_trans2.loc[slice(None), [sub], :], "Transport", sub, "CH4"
            ).drop_duplicates()
        )

    ch4_trans = ch4_trans3

    # endregion

    # Buildings

    # region

    ch4_build = ch4.loc[slice(None), build, :]
    ch4_build2 = []
    ch4_build3 = []

    for sub in build:
        ch4_build2 = pd.DataFrame(ch4_build2).append(
            rgroup(ch4_build.loc[slice(None), [sub], :], "CH4", sub)
        )
    for sub in build:
        ch4_build3 = pd.DataFrame(ch4_build3).append(
            proj(
                ch4_build2.loc[slice(None), [sub], :],
                ["Residential", "Commercial"],
                sub,
                "CH4",
            ).drop_duplicates()
        )

    ch4_build = ch4_build3

    # endregion

    # Agriculture

    # region

    ch4_ag = ch4.loc[slice(None), ag, :]
    ch4_ag2 = []
    ch4_ag3 = []

    for sub in ag:
        ch4_ag2 = pd.DataFrame(ch4_ag2).append(
            rgroup(ch4_ag.loc[slice(None), [sub], :], "CH4", sub)
        )
    for sub in ag:
        ch4_ag3 = pd.DataFrame(ch4_ag3).append(
            proj_afolu(
                ch4_ag2.loc[slice(None), [sub], :],
                "Agriculture",
                sub,
                "CH4",
            )
        )

    ch4_ag = ch4_ag3

    # endregion

    # Forests & Wetlands

    # region

    ch4_fw = gas_fw.loc[slice(None), slice(None), "CH4"]

    ch4_fw = rgroup(ch4_fw, "CH4", "Forests & Wetlands")

    ch4_fw = proj_afolu(ch4_fw, "Forests & Wetlands", "Deforestation", "CH4")

    # endregion

    # endregion

    #######
    # N2O #
    #######

    # region

    n2o = (
        pd.read_csv("podi/data/emissions_CEDS_N2O_by_sector_country_2021_02_05.csv")
        .drop(columns=["Em", "Units"])
        .set_index(["Region", "Sector"])
        / 1000
        * 298
    )
    n2o.columns = n2o.columns.astype(int)

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["WEB Region", "ISO"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "Region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["Region"] = regions["Region"].str.lower()

    n2o = (
        n2o.reset_index()
        .set_index(["Region"])
        .merge(regions, left_on=["Region"], right_on=["ISO"])
    ).set_index(["Region", "Sector"])

    # Electricity

    n2o_elec = n2o.loc[slice(None), elec, :]
    n2o_elec2 = []
    n2o_elec3 = []

    for sub in elec:
        n2o_elec2 = pd.DataFrame(n2o_elec2).append(
            rgroup(n2o_elec.loc[slice(None), [sub], :], "N2O", sub)
        )
    for sub in elec:
        n2o_elec3 = pd.DataFrame(n2o_elec3).append(
            proj(
                n2o_elec2.loc[slice(None), [sub], :], "Electricity", sub, "N2O"
            ).drop_duplicates()
        )

    n2o_elec = n2o_elec3

    # Industry

    n2o_ind = n2o.loc[slice(None), ind, :]
    n2o_ind2 = []
    n2o_ind3 = []

    for sub in ind:
        n2o_ind2 = pd.DataFrame(n2o_ind2).append(
            rgroup(n2o_ind.loc[slice(None), [sub], :], "N2O", sub, "ISO")
        )
    for sub in ind:
        n2o_ind3 = pd.DataFrame(n2o_ind3).append(
            proj(
                n2o_ind2.loc[slice(None), [sub], :], "Industrial", sub, "N2O"
            ).drop_duplicates()
        )

    n2o_ind = n2o_ind3

    # Transport

    n2o_trans = n2o.loc[slice(None), trans, :]
    n2o_trans2 = []
    n2o_trans3 = []

    for sub in [
        "1A3b_Road",
        "1A3c_Rail",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
    ]:
        n2o_trans2 = pd.DataFrame(n2o_trans2).append(
            rgroup(n2o_trans.loc[slice(None), [sub], :], "N2O", sub)
        )
    for sub in [
        "1A3b_Road",
        "1A3c_Rail",
        "1A3di_Oil_Tanker_Loading",
        "1A3dii_Domestic-navigation",
        "1A3eii_Other-transp",
    ]:
        n2o_trans3 = pd.DataFrame(n2o_trans3).append(
            proj(
                n2o_trans2.loc[slice(None), [sub], :], "Transport", sub, "N2O"
            ).drop_duplicates()
        )

    n2o_trans = n2o_trans3

    # Buildings

    n2o_build = n2o.loc[slice(None), build, :]
    n2o_build2 = []
    n2o_build3 = []

    for sub in build:
        n2o_build2 = pd.DataFrame(n2o_build2).append(
            rgroup(n2o_build.loc[slice(None), [sub], :], "N2O", sub)
        )
    for sub in build:
        n2o_build3 = pd.DataFrame(n2o_build3).append(
            proj(
                n2o_build2.loc[slice(None), [sub], :],
                ["Residential", "Commercial"],
                sub,
                "N2O",
            ).drop_duplicates()
        )

    n2o_build = n2o_build3

    # Agriculture

    n2o_ag = n2o.loc[slice(None), ag, :]
    n2o_ag2 = []
    n2o_ag3 = []

    for sub in ag:
        n2o_ag2 = pd.DataFrame(n2o_ag2).append(
            rgroup(n2o_ag.loc[slice(None), [sub], :], "N2O", sub)
        )
    for sub in ag:
        n2o_ag3 = pd.DataFrame(n2o_ag3).append(
            proj_afolu(
                n2o_ag2.loc[slice(None), [sub], :],
                "Agriculture",
                sub,
                "N2O",
            )
        )

    n2o_ag = n2o_ag3

    # Forests & Wetlands

    n2o_fw = gas_fw.loc[slice(None), slice(None), "N2O"]

    n2o_fw = rgroup(n2o_fw, "N2O", "Forests & Wetlands")

    n2o_fw = proj_afolu(n2o_fw, "Forests & Wetlands", "Deforestation", "N2O")

    # endregion

    ###########
    # F-gases #
    ###########

    # region

    fgas = (
        pd.read_csv("podi/data/emissions_historical_fgas.csv")
        .drop(columns=["Gas", "Unit"])
        .set_index("Region")
    )

    fgas = fgas[fgas.columns[::-1]]

    fgas.columns = fgas.columns.astype(int)

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["WEB Region", "ISO"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "Region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["Region"] = regions["Region"].str.lower()

    fgas = (
        fgas.reset_index()
        .set_index(["Region"])
        .merge(regions, left_on=["Region"], right_on=["ISO"])
    ).set_index(["Region", "Sector"])

    fgas_ind = rgroup(fgas * 1, "F-gases", "Industrial")

    fgas_ind = proj(fgas_ind, "Industrial", "F-gases", "F-gases")

    # endregion

    # combine

    addtl_em = pd.concat(
        [
            co2_elec,
            co2_ind,
            co2_ag,
            co2_fw,
            ch4_elec,
            ch4_ind,
            ch4_trans,
            ch4_build,
            ch4_ag,
            ch4_fw,
            n2o_elec,
            n2o_ind,
            n2o_trans,
            n2o_build,
            n2o_ag,
            n2o_fw,
            fgas_ind,
        ]
    )

    addtl_em.to_csv("podi/data/emissions_additional.csv", index=True)

    addtl_em = (
        (
            pd.read_csv("podi/data/emissions_additional.csv").set_index(
                ["Region", "Sector", "Variable", "Gas", "Scenario"]
            )
        )
        .loc[slice(None), slice(None), slice(None), slice(None), scenario]
        .reorder_levels(
            [
                "Region",
                "Sector",
                "Variable",
                "Gas",
            ]
        )
    )
    addtl_em.columns = addtl_em.columns.astype(int)
    addtl_em = addtl_em.loc[:, data_start_year:proj_end_year]

    # remove AFOLU to avoid double counting
    addtl_em = addtl_em.loc[
        slice(None),
        [
            "Electricity",
            "Industrial",
            "Residential",
            "Commercial",
            "Transport",
            "Other",
        ],
        slice(None),
        slice(None),
    ]

    # Set emissions change to follow sector emissions
    per_change_elec = (
        elec_em.loc[slice(None), "Electricity", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_elec = (
        addtl_em.loc[slice(None), ["Electricity"], slice(None), slice(None), :]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None), ["Electricity"], slice(None), slice(None), :
                    ].loc[:, 2019]
                )
                .combine_first(per_change_elec.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Variable", "Gas"],
            left_on=["Region", "Sector", "Variable", "Gas"],
        )
    )

    per_change_ind = (
        industry_em.loc[slice(None), "Industrial", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_ind = (
        addtl_em.loc[slice(None), ["Industrial"], slice(None), slice(None), :]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None), ["Industrial"], slice(None), slice(None), :
                    ].loc[:, 2019]
                )
                .combine_first(per_change_ind.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Variable", "Gas"],
            left_on=["Region", "Sector", "Variable", "Gas"],
        )
    )

    per_change_build = (
        buildings_em.loc[
            slice(None), ["Residential", "Commercial"], "Fossil fuels", "CO2"
        ]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_build = (
        addtl_em.loc[
            slice(None), ["Residential", "Commercial"], slice(None), slice(None), :
        ]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None),
                        ["Residential", "Commercial"],
                        slice(None),
                        slice(None),
                        :,
                    ].loc[:, 2019]
                )
                .combine_first(per_change_build.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Variable", "Gas"],
            left_on=["Region", "Sector", "Variable", "Gas"],
        )
    )

    per_change_trans = (
        transport_em.loc[slice(None), "Transport", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_trans = (
        addtl_em.loc[slice(None), ["Transport"], slice(None), slice(None), :]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None), ["Transport"], slice(None), slice(None), :
                    ].loc[:, 2019]
                )
                .combine_first(per_change_trans.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Variable", "Gas"],
            left_on=["Region", "Sector", "Variable", "Gas"],
        )
    )

    # endregion

    ############################################################
    #  MODEL EMISSIONS OF OTHER GHGS FROM CO2/CH4/N2O RESULTS  #
    ############################################################

    # region

    # At this point its likely that we want to limit Flow_categories to 'Final consumption' that is not Electricity or Heat, 'Energy industry own use and Losses', 'Electricity output', and 'Heat output', to avoid double counting

    # https://github.com/GranthamImperial/silicone/tree/master/notebooks

    # endregion

    ###########################
    #  COMBINE ALL & RELABEL  #
    ###########################

    # region

    em = pd.concat(
        [
            elec_em,
            transport_em,
            buildings_em,
            industry_em,
            afolu_em,
            addtl_em_elec,
            addtl_em_ind,
            addtl_em_build,
            addtl_em_trans,
        ]
    )

    em = pd.concat([em], keys=[scenario], names=["Scenario"]).reorder_levels(
        ["Region", "Sector", "Variable", "Gas", "Scenario"]
    )

    em = (
        em.rename(
            index={
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
        )
        .groupby(["Region", "Sector", "Variable", "Gas", "Scenario"])
        .sum()
    )
    """
    em = (
        em.rename(
            index={
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
        )
        .groupby(["Region", "Sector", "Variable", "Gas", "Scenario"])
        .sum()
    )
    """

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

    #################
    #  SAVE OUTPUT  #
    #################

    # region
    emissions.to_csv("podi/data/emissions_output.csv")

    # endregion

    return
