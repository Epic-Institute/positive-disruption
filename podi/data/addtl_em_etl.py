# region

import pandas as pd

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
    "1A3b_Road",
    "1A3c_Rail",
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
    # "1A3b_Road",
    # "1A3c_Rail",
    # "1A3di_Oil_Tanker_Loading",
    # "1A3dii_Domestic-navigation",
    # "1A3eii_Other-transp",
    # "1A3di_International-shipping"
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


def proj2(data, sector, metric, gas):
    # project gas emissions using percent change in sector

    # MANUALLY EXTEND 2018 VALUES THROUGH 2100 FOR FW RA

    data_per_change = (
        (
            energy_demand.loc[slice(None), "Industry", "Heat", slice(None)].loc[
                :, 2019:
            ]
            * 0.001
        )
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


#######
# CO2 #
#######

# region

co2 = (
    pd.DataFrame(
        pd.read_csv(
            "podi/data/CO2_CEDS_emissions_by_sector_country_2021_02_05.csv"
        ).drop(columns=["Em", "Units"])
    ).set_index(["Country", "Sector"])
    / 1000
)
co2.columns = co2.columns.astype(int)

# Electricity

# region

co2_elec = co2.loc[slice(None), elec_co2, :]
co2_elec2 = []
co2_elec3 = []

for sub in elec_co2:
    co2_elec2 = pd.DataFrame(co2_elec2).append(
        rgroup(co2_elec.loc[slice(None), [sub], :], "CO2", sub, "ISO")
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
        rgroup(co2_ind.loc[slice(None), [sub], :], "CO2", sub, "ISO")
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
        rgroup(co2_trans.loc[slice(None), [sub], :], "CO2", sub, "ISO")
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
        rgroup(co2_build.loc[slice(None), [sub], :], "CO2", sub, "ISO")
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

co2_ag = co2.loc[slice(None), ag, :]
co2_ag2 = []
co2_ag3 = []

for sub in ag:
    co2_ag2 = pd.DataFrame(co2_ag2).append(
        rgroup(co2_ag.loc[slice(None), [sub], :], "CO2", sub, "ISO")
    )
for sub in ag:
    co2_ag3 = pd.DataFrame(co2_ag3).append(
        proj2(
            co2_ag2.loc[slice(None), [sub], :], "Regenerative Agriculture", sub, "CO2"
        )
    )

co2_ag = co2_ag3

# endregion

# Forests & Wetlands

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

co2_fw = proj2(co2_fw, "Forests & Wetlands", "Natural Regeneration", "CO2")

# endregion

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

# region

ch4_elec = ch4.loc[slice(None), elec, :]
ch4_elec2 = []
ch4_elec3 = []

for sub in elec:
    ch4_elec2 = pd.DataFrame(ch4_elec2).append(
        rgroup(ch4_elec.loc[slice(None), [sub], :], "CH4", sub, "ISO")
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
        rgroup(ch4_ind.loc[slice(None), [sub], :], "CH4", sub, "ISO")
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

for sub in trans:
    ch4_trans2 = pd.DataFrame(ch4_trans2).append(
        rgroup(ch4_trans.loc[slice(None), [sub], :], "CH4", sub, "ISO")
    )
for sub in trans:
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
        rgroup(ch4_build.loc[slice(None), [sub], :], "CH4", sub, "ISO")
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
        rgroup(ch4_ag.loc[slice(None), [sub], :], "CH4", sub, "ISO")
    )
for sub in ag:
    ch4_ag3 = pd.DataFrame(ch4_ag3).append(
        proj2(
            ch4_ag2.loc[slice(None), [sub], :], "Regenerative Agriculture", sub, "CH4"
        ).drop_duplicates()
    )

ch4_ag = ch4_ag3

# endregion

# Forests & Wetlands

# region

ch4_fw = gas_fw.loc[slice(None), slice(None), "CH4"]
"""
ch4_fw2 = []
ch4_fw3 = []

for sub in fw:
    ch4_fw2 = pd.DataFrame(ch4_fw2).append(rgroup(ch4_fw, "CH4", sub, "ISO"))
for sub in fw:
    ch4_fw3 = pd.DataFrame(ch4_fw3).append(
        proj(ch4_fw2, sub, "CH4", "CH4").drop_duplicates()
    )

ch4_fw = ch4_fw3
"""

ch4_fw = rgroup(ch4_fw, "CH4", "Forests & Wetlands", "CAIT Region")

ch4_fw = proj2(ch4_fw, "Forests & Wetlands", "Natural Regeneration", "CH4")

# endregion

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
n2o_elec2 = []
n2o_elec3 = []

for sub in elec:
    n2o_elec2 = pd.DataFrame(n2o_elec2).append(
        rgroup(n2o_elec.loc[slice(None), [sub], :], "N2O", sub, "ISO")
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

for sub in trans:
    n2o_trans2 = pd.DataFrame(n2o_trans2).append(
        rgroup(n2o_trans.loc[slice(None), [sub], :], "N2O", sub, "ISO")
    )
for sub in trans:
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
        rgroup(n2o_build.loc[slice(None), [sub], :], "N2O", sub, "ISO")
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
        rgroup(n2o_ag.loc[slice(None), [sub], :], "N2O", sub, "ISO")
    )
for sub in ag:
    n2o_ag3 = pd.DataFrame(n2o_ag3).append(
        proj2(
            n2o_ag2.loc[slice(None), [sub], :], "Regenerative Agriculture", sub, "N2O"
        ).drop_duplicates()
    )

n2o_ag = n2o_ag3

# Forests & Wetlands

n2o_fw = gas_fw.loc[slice(None), slice(None), "N2O"]
"""
n2o_fw2 = []
n2o_fw3 = []

for sub in fw:
    n2o_fw2 = pd.DataFrame(n2o_fw2).append(rgroup(n2o_fw, "N2O", sub, "ISO"))
for sub in fw:
    n2o_fw3 = pd.DataFrame(n2o_fw3).append(
        proj(n2o_fw2, sub, "N2O", "N2O").drop_duplicates()
    )

n2o_fw = n2o_fw3
"""

n2o_fw = rgroup(n2o_fw, "N2O", "Forests & Wetlands", "CAIT Region")

n2o_fw = proj2(n2o_fw, "Forests & Wetlands", "Natural Regeneration", "N2O")

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

fgas_ind = rgroup(fgas * 1, "F-gases", "Industry", "CAIT Region")

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
