# region

import pandas as pd
from numpy import NaN
import numpy as np
import pyam
import os.path
import traceback
import matplotlib.pyplot as plt
import silicone.database_crunchers
from silicone.utils import download_or_load_sr15
import aneris

# endregion


def emissions(
    scenario,
    energy_adoption,
    afolu_adoption,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    #####################################
    #  CALCULATE EMISSIONS FROM ENERGY  #
    #####################################

    # region

    # Load emissions factors
    emission_factors = pd.read_csv("podi/data/emission_factors.csv").set_index(
        pyam.IAMC_IDX
    )
    emission_factors.columns = emission_factors.columns.astype(int)
    emission_factors = emission_factors.loc[:, data_start_year:proj_end_year]

    emissions_output = energy_adoption.timeseries().multiply(emission_factors)
    emissions_output.index = emissions_output.index.set_levels(
        emissions_output.index.levels[4].str.replace("MtCO2/TJ", "MtCO2"), level=4
    )

    # endregion

    ####################################
    #  CALCULATE EMISSIONS FROM AFOLU  #
    ####################################

    # region

    # Load historical AFOLU emissions
    afolu_em_hist = (
        pd.read_csv("podi/data/emissions_additional.csv")
        .set_index(["Region", "Sector", "Metric", "Gas", "Scenario"])
        .loc[
            slice(None),
            ["Forests & Wetlands", "Regenerative Agriculture"],
            slice(None),
            slice(None),
            scenario,
        ]
        .groupby(["Region", "Sector", "Metric", "Gas"])
        .sum()
    )

    afolu_em_hist.columns = afolu_em_hist.columns.astype(int)
    afolu_em_hist = afolu_em_hist.loc[:, data_start_year:]

    # CO2 F&W (F&W only has CO2 at this point)

    co2_fw = []

    for subv in [
        "Avoided Coastal Impacts",
        "Avoided Peat Impacts",
        "Avoided Forest Conversion",
        "Coastal Restoration",
        "Improved Forest Mgmt",
        "Natural Regeneration",
        "Peat Restoration",
    ]:
        co2_fw = pd.concat(
            [pd.DataFrame(co2_fw), pd.DataFrame(adoption.loc[slice(None), [subv], :])]
        )

    co2_fw = pd.concat([co2_fw], names=["Sector"], keys=["Forests & Wetlands"])
    co2_fw = pd.concat([co2_fw], names=["Scenario"], keys=[scenario])
    co2_fw = pd.concat([co2_fw], names=["Gas"], keys=["CO2"])
    co2_fw = co2_fw.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # CO2 Agriculture

    co2_ag = []

    for subv in [
        "Biochar",
        "Cropland Soil Health",
        "Optimal Intensity",
        "Silvopasture",
        "Trees in Croplands",
    ]:
        co2_ag = pd.concat(
            [pd.DataFrame(co2_ag), pd.DataFrame(adoption.loc[slice(None), [subv], :])]
        )

    co2_ag = pd.concat([co2_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    co2_ag = pd.concat([co2_ag], names=["Scenario"], keys=[scenario])
    co2_ag = pd.concat([co2_ag], names=["Gas"], keys=["CO2"])
    co2_ag = co2_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # CH4 Agriculture

    ch4_ag = []

    for subv in ["Improved Rice", "Animal Mgmt"]:
        ch4_ag = pd.concat(
            [pd.DataFrame(ch4_ag), pd.DataFrame(adoption.loc[slice(None), [subv], :])]
        )

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
    ch4_ag.loc[slice(None), ["Improved Rice"], :].update(
        ch4_ag.loc[slice(None), ["Improved Rice"], :] * 0.58
    )

    ch4_ag = pd.concat([ch4_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    ch4_ag = pd.concat([ch4_ag], names=["Scenario"], keys=[scenario])
    ch4_ag = pd.concat([ch4_ag], names=["Gas"], keys=["CH4"])
    ch4_ag = ch4_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # N2O Agriculture

    n2o_ag = []

    for subv in [
        "Improved Rice",
        "Nitrogen Fertilizer Management",
    ]:
        n2o_ag = pd.concat(
            [pd.DataFrame(n2o_ag), pd.DataFrame(adoption.loc[slice(None), [subv], :])]
        )

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
    n2o_ag.loc[slice(None), ["Improved Rice"], :].update(
        n2o_ag.loc[slice(None), ["Improved Rice"], :] * 0.42
    )

    n2o_ag = pd.concat([n2o_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    n2o_ag = pd.concat([n2o_ag], names=["Scenario"], keys=[scenario])
    n2o_ag = pd.concat([n2o_ag], names=["Gas"], keys=["N2O"])
    n2o_ag = n2o_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # Add mitigation estimates to historical and projected emissions to get net emissions

    # region

    # estimated mitigation
    afolu_em_mit = -(pd.concat([co2_fw, co2_ag, ch4_ag, n2o_ag]))
    afolu_em_mit.columns = afolu_em_mit.columns.astype(int)
    afolu_em_mit.loc[:, :data_end_year] = 0

    # shift mitigation values by data_end_year+1 value
    afolu_em_mit = afolu_em_mit.parallel_apply(
        lambda x: x.subtract(
            (
                afolu_em_mit.loc[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]
                .loc[:, data_end_year + 1]
                .values[0]
            )
        ),
        axis=1,
    ).clip(upper=0)

    # combine emissions and mitigation

    afolu_em = (
        pd.concat(
            [
                afolu_em_mit.groupby(["Region", "Sector", "Subvector", "Gas"]).sum(),
                afolu_em_hist,
            ]
        )
        .groupby(["Region", "Sector", "Subvector", "Gas"])
        .sum()
    )

    # Add scenario label
    afolu_em = pd.concat(
        [afolu_em], names=["Scenario"], keys=[scenario]
    ).reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    afolu_em.loc[
        slice(None),
        slice(None),
        [
            "Deforestation",
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ],
        slice(None),
        "baseline",
    ] = afolu_em.loc[
        slice(None),
        slice(None),
        [
            "Deforestation",
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ],
        slice(None),
        "pathway",
    ].values

    # endregion

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

        # Adds Sector, Metric, Gas, and Scenario labels to data, and duplicates data to allow for 'Baseline' and 'Pathway' scenarios to be made.
        data = pd.concat([data], names=["Metric"], keys=[gas])
        data = pd.concat([data], names=["Gas"], keys=[gas])
        data = pd.concat([data], names=["Scenario"], keys=["baseline"]).reorder_levels(
            ["Region", "Sector", "Metric", "Gas", "Scenario"]
        )
        data2 = data.droplevel("Scenario")
        data2 = pd.concat([data2], names=["Scenario"], keys=["pathway"]).reorder_levels(
            ["Region", "Sector", "Metric", "Gas", "Scenario"]
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

        data = pd.concat([data], keys=[metric], names=["Metric"])
        data = pd.concat([data], keys=[gas], names=["Gas"])
        data = pd.concat([data], keys=[sector], names=["Sector"]).reorder_levels(
            ["Region", "Sector", "Metric", "Gas", "Scenario"]
        )

        data.index.set_names(
            ["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
        )

        return data

    def proj_afolu(data, sector, metric, gas):

        # Makes projections for gas emissions using the percent change in sector

        ra_em = pd.read_csv("podi/data/emissions_agriculture.csv").set_index("Region")
        ra_em.columns = ra_em.columns.astype(int)
        ra_em = ra_em.interpolate(axis=1, method="quadratic")

        ra_em = rgroup(ra_em, "CO2")
        ra_em = ra_em.droplevel(["Metric", "Gas"])

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

        data = pd.concat([data], keys=[metric], names=["Metric"])
        data = pd.concat([data], keys=[gas], names=["Gas"])
        data = pd.concat([data], keys=[sector], names=["Sector"]).reorder_levels(
            ["Region", "Sector", "Metric", "Gas", "Scenario"]
        )
        data.index.set_names(
            ["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
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
                co2_ind2.loc[slice(None), [sub], :], "Industry", sub, "CO2"
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
                co2_build2.loc[slice(None), [sub], :], "Buildings", sub, "CO2"
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
                "Regenerative Agriculture",
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
                ch4_ind2.loc[slice(None), [sub], :], "Industry", sub, "CH4"
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
                ch4_build2.loc[slice(None), [sub], :], "Buildings", sub, "CH4"
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
                "Regenerative Agriculture",
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
                n2o_ind2.loc[slice(None), [sub], :], "Industry", sub, "N2O"
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
                n2o_build2.loc[slice(None), [sub], :], "Buildings", sub, "N2O"
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
                "Regenerative Agriculture",
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

    fgas_ind = rgroup(fgas * 1, "F-gases", "Industry")

    fgas_ind = proj(fgas_ind, "Industry", "F-gases", "F-gases")

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
                ["Region", "Sector", "Metric", "Gas", "Scenario"]
            )
        )
        .loc[slice(None), slice(None), slice(None), slice(None), scenario]
        .reorder_levels(
            [
                "Region",
                "Sector",
                "Metric",
                "Gas",
            ]
        )
    )
    addtl_em.columns = addtl_em.columns.astype(int)
    addtl_em = addtl_em.loc[:, data_start_year:proj_end_year]

    # remove AFOLU to avoid double counting
    addtl_em = addtl_em.loc[
        slice(None),
        ["Electricity", "Industry", "Buildings", "Transport", "Other"],
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
            right_on=["Region", "Sector", "Metric", "Gas"],
            left_on=["Region", "Sector", "Metric", "Gas"],
        )
    )

    per_change_ind = (
        industry_em.loc[slice(None), "Industry", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_ind = (
        addtl_em.loc[slice(None), ["Industry"], slice(None), slice(None), :]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None), ["Industry"], slice(None), slice(None), :
                    ].loc[:, 2019]
                )
                .combine_first(per_change_ind.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Metric", "Gas"],
            left_on=["Region", "Sector", "Metric", "Gas"],
        )
    )

    per_change_build = (
        buildings_em.loc[slice(None), "Buildings", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )

    addtl_em_build = (
        addtl_em.loc[slice(None), ["Buildings"], slice(None), slice(None), :]
        .loc[:, :2019]
        .merge(
            (
                pd.DataFrame(
                    addtl_em.loc[
                        slice(None), ["Buildings"], slice(None), slice(None), :
                    ].loc[:, 2019]
                )
                .combine_first(per_change_build.loc[:, 2020:])
                .cumprod(axis=1)
                .loc[:, 2020:]
            ),
            right_on=["Region", "Sector", "Metric", "Gas"],
            left_on=["Region", "Sector", "Metric", "Gas"],
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
            right_on=["Region", "Sector", "Metric", "Gas"],
            left_on=["Region", "Sector", "Metric", "Gas"],
        )
    )

    # endregion

    ############################################################
    #  MODEL EMISSIONS OF OTHER GHGS FROM CO2/CH4/N2O RESULTS  #
    ############################################################

    # region

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
        ["Region", "Sector", "Metric", "Gas", "Scenario"]
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
        .groupby(["Region", "Sector", "Metric", "Gas", "Scenario"])
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
        .groupby(["Region", "Sector", "Metric", "Gas", "Scenario"])
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
