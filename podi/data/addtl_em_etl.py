#!/usr/bin/env python

# region

import pandas as pd
from numpy import NaN

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
    "1A3ai_International-aviation",
    "1A3aii_Domestic-aviation",
    "1A3b_Road",
    "1A3c_Rail",
    "1A3di_International-shipping",
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
]

other = ["other"]

# endregion


def rgroup(data, gas, sector, rgroup):
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=[rgroup, "IEA Region"]
    )

    # make new row for world level data
    data_world = pd.DataFrame(data.sum()).T.rename(index={0: "World "})

    data = data.merge(region_categories, right_on=[rgroup], left_on=["Country"])

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
    data.index.name = "IEA Region"

    data = pd.concat([data], names=["Sector"], keys=[sector])
    data = pd.concat([data], names=["Metric"], keys=[gas])
    data = pd.concat([data], names=["Gas"], keys=[gas])
    data2 = pd.concat([data], names=["Scenario"], keys=["baseline"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
    )
    data3 = pd.concat([data], names=["Scenario"], keys=["pathway"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
    )
    data = data2.append(data3)

    return data


def proj(data, sector, metric, gas):
    # project gas emissions using percent change in sector

    data_per_change = (
        energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
        .merge(
            data,
            right_on=["IEA Region", "Scenario"],
            left_on=["IEA Region", "Scenario"],
        )
        .reindex(sorted(energy_demand.columns), axis=1)
    )

    data = data_per_change.loc[:, :2019].merge(
        data_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )

    data4 = []

    data4 = pd.DataFrame(data4).append(
        pd.concat([data], keys=[metric], names=["Metric"])
    )

    data4 = pd.concat([data4], keys=[gas], names=["Gas"]).reorder_levels(
        ["IEA Region", "Metric", "Gas", "Scenario"]
    )

    data4 = pd.concat([data4], keys=[sector], names=["Sector"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
    )

    data4.index.set_names(
        ["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
    )

    return data4


##############
# CEMENT CO2 #
##############

# region

cement = pd.read_csv("podi/data/emissions_cement.csv").T.replace(-9999, 0)

cement.columns = cement.loc["Year", :].astype(int)
cement.drop(index="Year", inplace=True)

cement = pd.DataFrame(cement) / 1000
cement.index.name = "Region"

region_categories = pd.read_csv(
    "podi/data/region_categories.csv", usecols=["Region", "IEA Region"]
)

cement = cement.merge(region_categories, right_on=["Region"], left_on=["Region"])

cement = cement.groupby("IEA Region").sum()

# split into various levels of IEA regional grouping
cement["IEA Region 1"] = cement.apply(lambda x: x.name.split()[2] + " ", axis=1)
cement["IEA Region 2"] = cement.apply(lambda x: x.name.split()[4] + " ", axis=1)
cement["IEA Region 3"] = cement.apply(lambda x: x.name.split()[-1] + " ", axis=1)

cement.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

# make new row for world level data
cement_world = pd.DataFrame(cement.sum()).T.rename(index={0: "World "})

# make new rows for OECD/NonOECD regions
cement_oecd = pd.DataFrame(cement.groupby("IEA Region 1").sum()).rename(
    index={"OECD ": " OECD "}
)

# make new rows for IEA regions
cement_regions = pd.DataFrame(cement.groupby("IEA Region 2").sum())
cement_regions2 = pd.DataFrame(cement.groupby("IEA Region 3").sum())

# combine all
cement = cement_world.append(
    [cement_oecd, cement_regions.combine_first(cement_regions2)]
)
cement.index.name = "IEA Region"

cement = pd.concat([cement], keys=["cement"], names=["Metric"]).reorder_levels(
    ["IEA Region", "Metric"]
)
cement2 = pd.concat([cement], keys=["baseline"], names=["Scenario"]).reorder_levels(
    ["IEA Region", "Metric", "Scenario"]
)
cement = cement2.append(
    pd.concat([cement], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Metric", "Scenario"]
    )
)

# project cement emissions using percent change in industry energy demand
cement_per_change = (
    energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
    .loc[:, 2018:]
    .pct_change(axis=1)
    .dropna(axis=1)
    .apply(lambda x: x + 1, axis=1)
    .merge(
        cement,
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )
    .reindex(sorted(energy_demand.columns), axis=1)
)

cement = cement_per_change.loc[:, :2018].merge(
    cement_per_change.loc[:, 2018:].cumprod(axis=1).loc[:, 2019:],
    right_on=["IEA Region", "Scenario"],
    left_on=["IEA Region", "Scenario"],
)
cement = pd.concat([cement], keys=["cement"], names=["Metric"]).reorder_levels(
    ["IEA Region", "Metric", "Scenario"]
)
cement = pd.concat([cement], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Metric", "Gas", "Scenario"]
)
cement = pd.concat([cement], keys=["Industry"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
)

cement.index.set_names(["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True)

# endregion

#############
# STEEL CO2 #
#############

# region

steel = pd.read_csv(
    "podi/data/CO2_CEDS_emissions_by_sector_country_2021_02_05.csv"
).drop(columns=["Em", "Units"])

steel = pd.DataFrame(steel).set_index(["Country", "Sector"]) / 1000

steel.columns = steel.columns.astype(int)

steel = steel.loc[slice(None), "1A2a_Ind-Comb-Iron-steel", :]

region_categories = pd.read_csv(
    "podi/data/region_categories.csv", usecols=["ISO", "IEA Region"]
)

steel = steel.merge(region_categories, right_on=["ISO"], left_on=["Country"])

steel = steel.groupby("IEA Region").sum()

# split into various levels of IEA regional grouping
steel["IEA Region 1"] = steel.apply(lambda x: x.name.split()[2] + " ", axis=1)
steel["IEA Region 2"] = steel.apply(lambda x: x.name.split()[4] + " ", axis=1)
steel["IEA Region 3"] = steel.apply(lambda x: x.name.split()[-1] + " ", axis=1)

steel.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

# make new row for world level data
steel_world = pd.DataFrame(steel.sum()).T.rename(index={0: "World "})

# make new rows for OECD/NonOECD regions
steel_oecd = pd.DataFrame(steel.groupby("IEA Region 1").sum()).rename(
    index={"OECD ": " OECD "}
)

# make new rows for IEA regions
steel_regions = pd.DataFrame(steel.groupby("IEA Region 2").sum())
steel_regions2 = pd.DataFrame(steel.groupby("IEA Region 3").sum())

# combine all
steel = steel_world.append([steel_oecd, steel_regions.combine_first(steel_regions2)])
steel.index.name = "IEA Region"

steel = pd.concat([steel], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Gas"]
)
steel3 = pd.concat([steel], keys=["baseline"], names=["Scenario"]).reorder_levels(
    ["IEA Region", "Gas", "Scenario"]
)
steel = steel3.append(
    pd.concat([steel], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Gas", "Scenario"]
    )
)

# project gas emissions using percent change in industry energy demand

steel_per_change = (
    energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
    .loc[:, 2019:]
    .pct_change(axis=1)
    .dropna(axis=1)
    .apply(lambda x: x + 1, axis=1)
    .merge(
        steel,
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )
    .reindex(sorted(energy_demand.columns), axis=1)
)

steel = steel_per_change.loc[:, :2019].merge(
    steel_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
    right_on=["IEA Region", "Scenario"],
    left_on=["IEA Region", "Scenario"],
)

steel = pd.concat([steel], keys=["steel"], names=["Metric"]).reorder_levels(
    ["IEA Region", "Metric", "Scenario"]
)
steel = pd.concat([steel], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Metric", "Gas", "Scenario"]
)
steel = pd.concat([steel], keys=["Industry"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
)

steel.index.set_names(["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True)

# endregion

##########################
# FORESTS & WETLANDS CO2 #
##########################

# region

gas_fw = (
    pd.read_csv("podi/data/emissions_fw_historical.csv")
    .set_index(["Country", "Sector", "Gas", "Unit"])
    .droplevel("Unit")
    .groupby(["Country", "Sector", "Gas"])
    .sum()
)
gas_fw.columns = gas_fw.columns[::-1].astype(int)

co2_fw = gas_fw.loc[slice(None), slice(None), "CO2"]

co2_fw = rgroup(co2_fw, "CO2", "Forests & Wetlands", "CAIT Region")

co2_fw = proj(co2_fw, "Forests & Wetlands", "CO2", "CO2")

# endregion

#######
# CH4 #
#######

# region

ch4 = (
    pd.DataFrame(
        pd.read_csv(
            "podi/data/CH4_CEDS_emissions_by_sector_country_2021_02_05.csv"
        ).drop(columns=["Em", "Units"])
    ).set_index(["Country", "Sector"])
    / 1000
    * 25
)
ch4.columns = ch4.columns.astype(int)

# Electricity

ch4_elec = ch4.loc[slice(None), elec, :]

ch4_elec = rgroup(ch4_elec, "CH4", "Electricity", "ISO")

ch4_elec = proj(ch4_elec, "Electricity", "CH4", "CH4")

# Industry

ch4_ind = ch4.loc[slice(None), ind, :]

ch4_ind = rgroup(ch4_ind, "CH4", "Industry", "ISO")

ch4_ind = proj(ch4_ind, "Industry", "CH4", "CH4")

# Transport

ch4_trans = ch4.loc[slice(None), trans, :]

ch4_trans = rgroup(ch4_trans, "CH4", "Transport", "ISO")

ch4_trans = proj(ch4_trans, "Transport", "CH4", "CH4")

# Buildings

ch4_b = ch4.loc[slice(None), build, :]

ch4_b = rgroup(ch4_b, "CH4", "Buildings", "ISO")

ch4_b = proj(ch4_b, "Buildings", "CH4", "CH4")

# Agriculture

ch4_ag = ch4.loc[slice(None), ag, :]

ch4_ag = rgroup(ch4_ag, "CH4", "Regenerative Agriculture", "ISO")

ch4_ag = proj(ch4_ag, "Regenerative Agriculture", "CH4", "CH4")

# Forests & Wetlands

ch4_fw = gas_fw.loc[slice(None), slice(None), "CH4"]

ch4_fw = rgroup(ch4_fw, "CH4", "Forests & Wetlands", "CAIT Region")

ch4_fw = proj(ch4_fw, "Forests & Wetlands", "CH4", "CH4")

# Other
"""
ch4_o = ch4.loc[slice(None), other, :]

ch4_o = rgroup(ch4_o, "CH4", "Other", "ISO")

ch4_o = proj(ch4_o, "Other", "CH4", "CH4")
"""
# endregion

#######
# N2O #
#######

# region

n2o = (
    pd.read_csv("podi/data/N2O_CEDS_emissions_by_sector_country_2021_02_05.csv")
    .drop(columns=["Em", "Units"])
    .set_index(["Country", "Sector"])
    / 1000
    * 298
)
n2o.columns = n2o.columns.astype(int)

# Electricity

n2o_elec = n2o.loc[slice(None), elec, :]

n2o_elec = rgroup(n2o_elec, "N2O", "Electricity", "ISO")

n2o_elec = proj(n2o_elec, "Electricity", "N2O", "N2O")

# Industry

n2o_ind = n2o.loc[slice(None), ind, :]

n2o_ind = rgroup(n2o_ind, "N2O", "Industry", "ISO")

n2o_ind = proj(n2o_ind, "Industry", "N2O", "N2O")

# Transport

n2o_trans = n2o.loc[slice(None), trans, :]

n2o_trans = rgroup(n2o_trans, "N2O", "Transport", "ISO")

n2o_trans = proj(n2o_trans, "Transport", "N2O", "N2O")

# Buildings

n2o_b = n2o.loc[slice(None), build, :]

n2o_b = rgroup(n2o_b, "N2O", "Buildings", "ISO")

n2o_b = proj(n2o_b, "Buildings", "N2O", "N2O")

# Agriculture

n2o_ag = n2o.loc[slice(None), ag, :]

n2o_ag = rgroup(n2o_ag, "N2O", "Regenerative Agriculture", "ISO")

n2o_ag = proj(n2o_ag, "Regenerative Agriculture", "N2O", "N2O")

# Forests & Wetlands

n2o_fw = gas_fw.loc[slice(None), slice(None), "N2O"]

n2o_fw = rgroup(n2o_fw, "N2O", "Forests & Wetlands", "CAIT Region")

n2o_fw = proj(n2o_fw, "Forests & Wetlands", "N2O", "N2O")

# Other
"""
n2o_o = n2o.loc[slice(None), other, :]

n2o_o = rgroup(n2o_o, "N2O", "Other", "ISO")

n2o_o = proj(n2o_o, "Other", "N2O", "N2O")
"""
# endregion

###########
# F-gases #
###########

# region

fgas = (
    pd.read_csv("podi/data/emissions_historical_fgas.csv")
    .drop(columns=["Gas", "Unit"])
    .set_index("Country")
)

fgas = fgas[fgas.columns[::-1]]

fgas.columns = fgas.columns.astype(int)

fgas_ind = rgroup(fgas * 0.5, "F-gases", "Industry", "CAIT Region")

fgas_ind = proj(fgas_ind, "Industry", "F-gases", "F-gases")

fgas_build = rgroup(fgas * 0.5, "F-gases", "Buildings", "CAIT Region")

fgas_build = proj(fgas_build, "Buildings", "F-gases", "F-gases")

# endregion

# combine

addtl_em = pd.concat(
    [
        cement,
        steel,
        co2_fw,
        ch4_elec,
        ch4_ind,
        ch4_trans,
        ch4_b,
        ch4_ag,
        ch4_fw,
        n2o_elec,
        n2o_ind,
        n2o_trans,
        n2o_b,
        n2o_ag,
        n2o_fw,
        fgas_ind,
        fgas_build,
    ]
).fillna(method="ffill", axis=1)

addtl_em.to_csv("podi/data/emissions_additional.csv", index=True)
