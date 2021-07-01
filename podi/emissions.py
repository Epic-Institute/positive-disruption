# region

import pandas as pd
from podi.energy_demand import data_start_year, data_end_year
from podi.energy_supply import long_proj_end_year
from numpy import NaN
import numpy as np

# endregion

region_list = pd.read_csv("podi/data/region_list.csv", header=None, squeeze=True)


def rgroup3(data, gas, sector, r, scenario):
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=[r, "IEA Region"]
    )

    # make new row for world level data
    data_world = pd.DataFrame(data.sum()).T.rename(index={0: "World "})

    data = data.merge(region_categories, right_on=[r], left_on=["Region"])

    data = data.groupby("IEA Region").sum()

    # split into various levels of IEA regional grouping
    data["IEA Region 1"] = data.apply(lambda x: x.name.split()[2] + " ", axis=1)
    data["IEA Region 2"] = data.apply(lambda x: x.name.split()[4] + " ", axis=1)
    data["IEA Region 3"] = data.apply(lambda x: x.name.split()[-1] + " ", axis=1)

    data.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new rows for OECD/NonOECD regions
    data_oecd = pd.DataFrame(data.groupby("IEA Region 1").sum()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    data_regions = pd.DataFrame(data.groupby("IEA Region 2").sum())
    data_regions2 = pd.DataFrame(data.groupby("IEA Region 3").sum())

    """
    # remove countries from higher level regions
    data_oecd.loc[" OECD "] = (
        data_oecd.loc[" OECD "] - data_regions2.loc["US "] - data_regions2.loc["SAFR "]
    )
    data_oecd.loc["NonOECD "] = data_oecd.loc["NonOECD "] - data_regions2.loc["BRAZIL "]

    data_regions.loc["CSAM "] = data_regions.loc["CSAM "] - data_regions2.loc["BRAZIL "]
    data_regions.loc["NAM "] = data_regions.loc["NAM "] - data_regions2.loc["US "]
    data_regions.loc["AFRICA "] = (
        data_regions.loc["AFRICA "] - data_regions2.loc["SAFR "]
    )
    """

    # combine all
    data = data_world.append(
        [data_oecd, data_regions, data_regions2.loc[["BRAZIL ", "US ", "SAFR "], :]]
    )
    data.index.name = "Region"

    data = pd.concat([data], names=["Sector"], keys=[sector])
    data = pd.concat([data], names=["Metric"], keys=[sector])
    data = pd.concat([data], names=["Gas"], keys=[gas])
    data = pd.concat([data], names=["Scenario"], keys=[scenario]).reorder_levels(
        ["Region", "Sector", "Metric", "Gas", "Scenario"]
    )
    data = data.loc[np.array(region_list), slice(None), slice(None), slice(None)]

    return data


def emissions(
    scenario,
    energy_demand,
    elec_consump,
    heat_consump,
    heat_per_adoption,
    transport_consump,
    afolu_em,
    addtl_em,
    targets_em,
):

    # region

    em_factors = (
        pd.read_csv("podi/data/emissions_factors.csv")
        .drop(columns=["Unit"])
        .set_index(["Region", "Sector", "Metric", "Gas", "Scenario"])
    ).loc[slice(None), slice(None), slice(None), slice(None), scenario]

    em_factors.columns = em_factors.columns.astype(int)
    em_factors = em_factors.loc[:, data_start_year:long_proj_end_year]

    # endregion

    #################
    #  ELECTRICITY  #
    #################

    # region

    elec_consump = (
        pd.concat(
            [elec_consump], keys=["Electricity"], names=["Sector"]
        ).reorder_levels(["Region", "Sector", "Metric", "Scenario"])
    ).loc[slice(None), slice(None), slice(None), scenario]

    elec_consump2 = []

    for i in ["CO2"]:
        elec_consump2 = pd.DataFrame(elec_consump2).append(
            pd.concat([elec_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    elec_em = (
        elec_consump2 * em_factors[em_factors.index.isin(elec_consump2.index.values)]
    )

    # endregion

    ###############
    #  BUILDINGS  #
    ###############

    # region

    # add 'Electricity' to energy_demand here to toggle emissions from Electricity to Buildings
    buildings_consump = (
        energy_demand.loc[slice(None), "Buildings", ["Heat"], scenario]
        .groupby("IEA Region")
        .sum()
    )
    buildings_consump.index.name = "Region"

    buildings_consump = (
        buildings_consump
        * heat_per_adoption.loc[slice(None), ["Fossil fuels"], scenario]
        .groupby("Region")
        .sum()
    )

    buildings_consump = pd.concat(
        [buildings_consump], keys=["Buildings"], names=["Sector"]
    )
    buildings_consump = pd.concat(
        [buildings_consump], keys=["Fossil fuels"], names=["Metric"]
    ).reorder_levels(["Region", "Sector", "Metric"])

    buildings_consump2 = []

    for i in ["CO2"]:
        buildings_consump2 = pd.DataFrame(buildings_consump2).append(
            pd.concat([buildings_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    buildings_em = (
        buildings_consump2
        * em_factors[em_factors.index.isin(buildings_consump2.index.values)]
    ).loc[:, data_start_year:long_proj_end_year]

    # endregion

    ###############
    #  INDUSTRY  #
    ###############

    # region

    # add 'Electricity' to energy_demand here to toggle emissions from Electricity to Industry
    industry_consump = (
        energy_demand.loc[slice(None), "Industry", ["Heat"], scenario]
        .groupby("IEA Region")
        .sum()
    )
    industry_consump.index.name = "Region"

    industry_consump = (
        industry_consump
        * heat_per_adoption.loc[slice(None), ["Fossil fuels"], scenario]
        .groupby("Region")
        .sum()
    )

    industry_consump = pd.concat(
        [industry_consump], keys=["Industry"], names=["Sector"]
    )
    industry_consump = pd.concat(
        [industry_consump], keys=["Fossil fuels"], names=["Metric"]
    ).reorder_levels(["Region", "Sector", "Metric"])

    industry_consump2 = []

    for i in ["CO2"]:
        industry_consump2 = pd.DataFrame(industry_consump2).append(
            pd.concat([industry_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    industry_em = (
        industry_consump2
        * em_factors[em_factors.index.isin(industry_consump2.index.values)]
    ).loc[:, data_start_year:long_proj_end_year]

    # endregion

    ###########################
    #  NONELECTRIC TRANSPORT  #
    ###########################

    # region

    transport_consump = (
        pd.concat([transport_consump], keys=["Transport"], names=["Sector"])
        .reorder_levels(["Region", "Sector", "Metric", "Scenario"])
        .loc[slice(None), slice(None), slice(None), scenario]
    )

    transport_consump2 = []

    for i in ["CO2"]:
        transport_consump2 = pd.DataFrame(transport_consump2).append(
            pd.concat([transport_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    transport_em = (
        transport_consump2
        * em_factors[em_factors.index.isin(transport_consump2.index.values)]
    ).drop(index=["Bioenergy", "Oil", "Other fuels"], level=2)

    # endregion

    ###########
    #  AFOLU  #
    ###########

    # region

    afolu_em = afolu_em.loc[
        slice(None), slice(None), slice(None), slice(None), scenario
    ]

    # endregion

    ##################################
    #  ADDITIONAL EMISSIONS SOURCES  #
    ##################################

    # region

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
    addtl_em = addtl_em.loc[:, data_start_year:long_proj_end_year]

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

    #################
    #  COMBINE ALL  #
    #################

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

    # endregion

    ##########################
    #  HISTORICAL EMISSIONS  #
    ##########################

    # region

    em_hist_old = (
        pd.read_csv("podi/data/emissions_historical_old.csv")
        .set_index(["Region", "Unit"])
        .droplevel("Unit")
    )

    em_hist_old = rgroup3(em_hist_old, "CO2", "CO2", "CAIT Region", scenario)
    em_hist_old.columns = em_hist_old.columns.astype(int)

    # estimate time between data and projections
    em_hist_old["2019"] = em_hist_old[2018] * (
        1 + (em_hist_old[2018] - em_hist_old[2017]) / em_hist_old[2017]
    )
    em_hist_old.columns = em_hist_old.columns.astype(int)

    # find emissions percent breakdown of historical estimates
    em.columns = em.columns.astype(int)

    per_em = em.loc[:, data_start_year:data_end_year].apply(
        lambda x: x.divide(
            em.loc[x.name[0]].loc[:, data_start_year:data_end_year].sum(axis=0)
        ),
        axis=1,
    )

    em2 = per_em.apply(
        lambda x: x.multiply(em_hist_old.loc[x.name[0]].squeeze()), axis=1
    )

    # harmonize emissions projections with current year emissions

    hf = (
        em2.loc[:, data_end_year]
        .divide(em.loc[:, data_end_year])
        .replace(NaN, 0)
        .replace(0, 1)
    )

    em = em.apply(
        lambda x: x.multiply(hf[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]),
        axis=1,
    )

    em = em2.join(em.loc[:, 2020:])

    # endregion

    ########################
    #  RELABEL SUBVECTORS  #
    ########################

    # region

    em = (
        em.rename(
            index={
                "Fossil fuels": "Fossil Fuel Heat",
                "1A1a_Electricity-autoproducer": "Fossil fuels",
                "1A1a_Electricity-public": "Fossil fuels",
                "1A1a_Heat-production": "Fossil Fuel Heat",
                "1A1bc_Other-transformation": "Other Fossil Transformation",
                "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
                "1B2_Fugitive-petr": "Fugitive Petroleum",
                "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
                "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
                "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
                "7A_Fossil-fuel-fires": "Fossil fuel Fires",
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
                "1A1a_Electricity-autoproducer": "Fossil fuels",
                "1A1a_Electricity-public": "Fossil fuels",
                "1A1a_Heat-production": "Fossil fuel Heat",
                "1A1bc_Other-transformation": "Other Fossil Transformation",
                "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
                "1B2_Fugitive-petr": "Fugitive Petroleum",
                "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
                "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
                "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
                "7A_Fossil-fuel-fires": "Fossil fuel Fires",
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

    #######################
    #  EMISSIONS TARGETS  #
    #######################

    # region

    em_targets = pd.read_csv(targets_em).set_index(
        ["Model", "Region", "Scenario", "Variable", "Unit"]
    )
    em_targets.columns = em_targets.columns.astype(int)
    em_targets = em_targets.loc[
        "MESSAGE-GLOBIOM 1.0",
        "World ",
        ["SSP2-Baseline", "SSP2-19", "SSP2-26"],
        "Emissions|Kyoto Gases",
    ].droplevel("Unit")

    # harmonize targets with historical emissions

    hf = pd.DataFrame(
        em_hist_old.loc["World "].loc[:, data_end_year].sum()
        / (em_targets.loc[:, data_end_year]).replace(NaN, 0)
    )

    em_targets = em_targets * (hf.values)

    # endregion

    return em, em_targets, em_hist_old
