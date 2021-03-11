#!/usr/bin/env python

import pandas as pd
from numpy import NaN
from podi.curve_smooth import curve_smooth

##########
# CEMENT #
##########

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
cement = pd.concat([cement], keys=["Other"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
)

cement.index.set_names(["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True)

# endregion

#########
# STEEL #
#########

# region

gas = pd.read_csv("podi/data/CO2_CEDS_emissions_by_sector_country_2021_02_05.csv").drop(
    columns=["Em", "Units"]
)

gas = pd.DataFrame(gas).set_index(["Country", "Sector"]) / 1000

gas.columns = gas.columns.astype(int)

gas = gas.loc[slice(None), "1A2a_Ind-Comb-Iron-steel", :]

region_categories = pd.read_csv(
    "podi/data/region_categories.csv", usecols=["ISO", "IEA Region"]
)

gas = gas.merge(region_categories, right_on=["ISO"], left_on=["Country"])

gas = gas.groupby("IEA Region").sum()

# split into various levels of IEA regional grouping
gas["IEA Region 1"] = gas.apply(lambda x: x.name.split()[2] + " ", axis=1)
gas["IEA Region 2"] = gas.apply(lambda x: x.name.split()[4] + " ", axis=1)
gas["IEA Region 3"] = gas.apply(lambda x: x.name.split()[-1] + " ", axis=1)

gas.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

# make new row for world level data
gas_world = pd.DataFrame(gas.sum()).T.rename(index={0: "World "})

# make new rows for OECD/NonOECD regions
gas_oecd = pd.DataFrame(gas.groupby("IEA Region 1").sum()).rename(
    index={"OECD ": " OECD "}
)

# make new rows for IEA regions
gas_regions = pd.DataFrame(gas.groupby("IEA Region 2").sum())
gas_regions2 = pd.DataFrame(gas.groupby("IEA Region 3").sum())

# combine all
gas = gas_world.append([gas_oecd, gas_regions.combine_first(gas_regions2)])
gas.index.name = "IEA Region"

gas = pd.concat([gas], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Gas"]
)
gas3 = pd.concat([gas], keys=["baseline"], names=["Scenario"]).reorder_levels(
    ["IEA Region", "Gas", "Scenario"]
)
gas = gas3.append(
    pd.concat([gas], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Gas", "Scenario"]
    )
)

# project gas emissions using percent change in industry energy demand

gas_per_change = (
    energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
    .loc[:, 2019:]
    .pct_change(axis=1)
    .dropna(axis=1)
    .apply(lambda x: x + 1, axis=1)
    .merge(
        gas,
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )
    .reindex(sorted(energy_demand.columns), axis=1)
)

"""
gas_per_change = (
    (
        pd.concat(
            [
                em_baseline.loc[slice(None), slice(None), slice(None), "CO2"]
                .groupby("Region")
                .sum()
                .loc[:, 2019:]
                .pct_change(axis=1)
                .loc[:, 2020:]
                .dropna(axis=0)
                .apply(lambda x: x + 1, axis=1)
            ],
            keys=["baseline"],
            names=["Scenario"],
        ).append(
            pd.concat(
                [
                    em_pathway.loc[slice(None), slice(None), slice(None), "CO2"]
                    .groupby("Region")
                    .sum()
                    .loc[:, 2019:]
                    .pct_change(axis=1)
                    .loc[:, 2020:]
                    .dropna(axis=0)
                    .apply(lambda x: x + 1, axis=1)
                ],
                keys=["pathway"],
                names=["Scenario"],
            )
        )
    )
    .reset_index()
    .merge(
        gas.droplevel("Gas"),
        right_on=["IEA Region", "Scenario"],
        left_on=["Region", "Scenario"],
    )
    .set_index(["Region", "Scenario"])
    .reindex(sorted(em_baseline.columns), axis=1)
)

gas_per_change.index.set_names(["IEA Region", "Scenario"], inplace=True)
"""
gas = gas_per_change.loc[:, :2019].merge(
    gas_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
    right_on=["IEA Region", "Scenario"],
    left_on=["IEA Region", "Scenario"],
)

steel = []

steel = pd.DataFrame(steel).append(pd.concat([gas], keys=["steel"], names=["Metric"]))

steel = pd.concat([steel], keys=["CO2"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Metric", "Gas", "Scenario"]
)

steel = pd.concat([steel], keys=["Other"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
)

steel.index.set_names(["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True)

# endregion

############
# CH4, N2O #
############

# region

data = {
    "CH4": "podi/data/CH4_CEDS_emissions_by_sector_country_2021_02_05.csv",
    "N2O": "podi/data/N2O_CEDS_emissions_by_sector_country_2021_02_05.
}

gas4 = []

for gas2 in ["CH4"]:
    gas = pd.read_csv(data[gas2]).drop(columns=["Em", "Units"])

    gas = pd.DataFrame(gas).set_index(["Country", "Sector"]) / 1000 * 25

    gas.columns = gas.columns.astype(int)

    gas_elec = gas.loc[slice(None), '1A1a_Electricity-autoproducer', '1A1a_Electricity-public', '1A1a_Heat-production', '1A1bc_Other-transformation', '1B1_Fugitive-solid-fuels', '1B2_Fugitive-petr', '1B2b_Fugitive-NG-distr', '1B2b_Fugitive-NG-prod', '1B2d_Fugitive-other-energy'], :]

    gas_ind = gas.loc[slice(None), ['1A2a_Ind-Comb-Iron-steel', '1A2b_Ind-Comb-Non-ferrous-metals', '1A2c_Ind-Comb-Chemicals', '1A2d_Ind-Comb-Pulp-paper', '1A2e_Ind-Comb-Food-tobacco', '1A2f_Ind-Comb-Non-metalic-minerals', '1A2g_Ind-Comb-Construction', '1A2g_Ind-Comb-machinery', '1A2g_Ind-Comb-mining-quarying', '1A2g_Ind-Comb-other', '1A2g_Ind-Comb-textile-leather', '1A2g_Ind-Comb-transpequip', '1A2g_Ind-Comb-wood-products', '1A5_Other-unspecified', '2A1_Cement-production', '2A2_Lime-production', '2Ax_Other-minerals', '2B_Chemical-industry', '2B2_Chemicals-Nitric-acid', '2B3_Chemicals-Adipic-acid', '2C_Metal-production', '2D_Chemical-products-manufacture-processing', '2D_Degreasing-Cleaning', '2D_Other-product-use', '2D_Paint-application', '2H_Pulp-and-paper-food-beverage-wood', '2L_Other-process-emissions', '5A_Solid-waste-disposal', '5C_Waste-combustion', '5D_Wastewater-handling', '5E_Other-waste-handling', '6A_Other-in-total', '6B_Other-not-in-total', '7A_Fossil-fuel-fires', '7BC_Indirect-N2O-non-agricultural-N', :]

    gas_trans = gas.loc[slice(None), ['1A3b_Road', '1A3c_Rail', '1A3di_Oil_Tanker_Loading', '1A3dii_Domestic-navigation', '1A3eii_Other-transp'], :]

    gas_b = gas.loc[slice(None), ['1A4a_Commercial-institutional','1A4b_Residential'], :]

    gas_ag = gas.loc[slice(None),['3B_Manure-management', '3D_Rice-Cultivation', '3D_Soil-emissions', '3E_Enteric-fermentation', '3I_Agriculture-other'], :]

    gas_fw = pd.read_csv('podi/data/emissions_fw_historical.csv').set_index(['Region', 'Sector', 'Gas', 'Unit']).droplevel('Unit').groupby(['Region','Sector']).sum()

    gas_en = gas_elec.append(gas_ind).append(gas_trans).append(gas_b)

    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["ISO", "IEA Region"]
    )

    gas = gas.merge(region_categories, right_on=["ISO"], left_on=["Country"])

    gas = gas.groupby("IEA Region").sum()

    def ieagroup(gas):

        # split into various levels of IEA regional grouping
        gas["IEA Region 1"] = gas.apply(lambda x: x.name.split()[2] + " ", axis=1)
        gas["IEA Region 2"] = gas.apply(lambda x: x.name.split()[4] + " ", axis=1)
        gas["IEA Region 3"] = gas.apply(lambda x: x.name.split()[-1] + " ", axis=1)

        gas.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

        # make new row for world level data
        gas_world = pd.DataFrame(gas.sum()).T.rename(index={0: "World "})

        # make new rows for OECD/NonOECD regions
        gas_oecd = pd.DataFrame(gas.groupby("IEA Region 1").sum()).rename(
            index={"OECD ": " OECD "}
        )

        # make new rows for IEA regions
        gas_regions = pd.DataFrame(gas.groupby("IEA Region 2").sum())
        gas_regions2 = pd.DataFrame(gas.groupby("IEA Region 3").sum())

        # combine all
        gas = gas_world.append([gas_oecd, gas_regions.combine_first(gas_regions2)])
        gas.index.name = "IEA Region"

        gas = pd.concat([gas], keys=[str(gas2)], names=["Gas"]).reorder_levels(
            ["IEA Region", "Gas"]
        )
        gas3 = pd.concat([gas], keys=["baseline"], names=["Scenario"]).reorder_levels(
            ["IEA Region", "Gas", "Scenario"]
        )
        gas = gas3.append(
            pd.concat([gas], keys=["pathway"], names=["Scenario"]).reorder_levels(
                ["IEA Region", "Gas", "Scenario"]
            )
        )
        
        return gas

    # project gas emissions using percent change in industry energy demand

    gas_per_change = (
        energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
        .merge(
            gas,
            right_on=["IEA Region", "Scenario"],
            left_on=["IEA Region", "Scenario"],
        )
        .reindex(sorted(energy_demand.columns), axis=1)
    )

    """
    gas_per_change = (
        (
            pd.concat(
                [
                    em_baseline.loc[slice(None), slice(None), slice(None), "CO2"]
                    .groupby("Region")
                    .sum()
                    .loc[:, 2019:]
                    .pct_change(axis=1)
                    .loc[:, 2020:]
                    .dropna(axis=0)
                    .apply(lambda x: x + 1, axis=1)
                ],
                keys=["baseline"],
                names=["Scenario"],
            ).append(
                pd.concat(
                    [
                        em_pathway.loc[slice(None), slice(None), slice(None), "CO2"]
                        .groupby("Region")
                        .sum()
                        .loc[:, 2019:]
                        .pct_change(axis=1)
                        .loc[:, 2020:]
                        .dropna(axis=0)
                        .apply(lambda x: x + 1, axis=1)
                    ],
                    keys=["pathway"],
                    names=["Scenario"],
                )
            )
        )
        .reset_index()
        .merge(
            gas.droplevel("Gas"),
            right_on=["IEA Region", "Scenario"],
            left_on=["Region", "Scenario"],
        )
        .set_index(["Region", "Scenario"])
        .reindex(sorted(em_baseline.columns), axis=1)
    )

    gas_per_change.index.set_names(["IEA Region", "Scenario"], inplace=True)
    """
    gas = gas_per_change.loc[:, :2019].merge(
        gas_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )

    gas4 = pd.DataFrame(gas4).append(
        pd.concat([gas], keys=[str(gas2)], names=["Metric"])
    )

    gas4 = pd.concat([gas4], keys=[str(gas2)], names=["Gas"]).reorder_levels(
        ["IEA Region", "Metric", "Gas", "Scenario"]
    )

    gas4 = pd.concat([gas4], keys=["Other"], names=["Sector"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
    )

    gas4.index.set_names(
        ["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
    )

gas5 = []

for gas2 in ["N2O"]:
    gas = pd.read_csv(data[gas2]).drop(columns=["Em", "Units"])

    gas = pd.DataFrame(gas).set_index(["Country", "Sector"]) / 1000 * 298
    gas.columns = gas.columns.astype(int)

    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["ISO", "IEA Region"]
    )

    gas = gas.merge(region_categories, right_on=["ISO"], left_on=["Country"])

    gas = gas.groupby("IEA Region").sum()

    # split into various levels of IEA regional grouping
    gas["IEA Region 1"] = gas.apply(lambda x: x.name.split()[2] + " ", axis=1)
    gas["IEA Region 2"] = gas.apply(lambda x: x.name.split()[4] + " ", axis=1)
    gas["IEA Region 3"] = gas.apply(lambda x: x.name.split()[-1] + " ", axis=1)

    gas.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new row for world level data
    gas_world = pd.DataFrame(gas.sum()).T.rename(index={0: "World "})

    # make new rows for OECD/NonOECD regions
    gas_oecd = pd.DataFrame(gas.groupby("IEA Region 1").sum()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    gas_regions = pd.DataFrame(gas.groupby("IEA Region 2").sum())
    gas_regions2 = pd.DataFrame(gas.groupby("IEA Region 3").sum())

    # combine all
    gas = gas_world.append([gas_oecd, gas_regions.combine_first(gas_regions2)])
    gas.index.name = "IEA Region"

    gas = pd.concat([gas], keys=[str(gas2)], names=["Gas"]).reorder_levels(
        ["IEA Region", "Gas"]
    )
    gas3 = pd.concat([gas], keys=["baseline"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Gas", "Scenario"]
    )
    gas = gas3.append(
        pd.concat([gas], keys=["pathway"], names=["Scenario"]).reorder_levels(
            ["IEA Region", "Gas", "Scenario"]
        )
    )

    # project gas emissions using percent change in industry CO2 emissions

    gas_per_change = (
        energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
        .merge(
            gas,
            right_on=["IEA Region", "Scenario"],
            left_on=["IEA Region", "Scenario"],
        )
        .reindex(sorted(energy_demand.columns), axis=1)
    )

    """
    gas_per_change = (
        (
            pd.concat(
                [
                    em_baseline.loc[slice(None), slice(None), slice(None), "CO2"]
                    .groupby("Region")
                    .sum()
                    .loc[:, 2019:]
                    .pct_change(axis=1)
                    .loc[:, 2020:]
                    .dropna(axis=0)
                    .apply(lambda x: x + 1, axis=1)
                ],
                keys=["baseline"],
                names=["Scenario"],
            )
            .append(
                pd.concat(
                    [
                        em_pathway.loc[slice(None), slice(None), slice(None), "CO2"]
                        .groupby("Region")
                        .sum()
                        .loc[:, 2019:]
                        .pct_change(axis=1)
                        .loc[:, 2020:]
                        .dropna(axis=0)
                        .apply(lambda x: x + 1, axis=1)
                    ],
                    keys=["pathway"],
                    names=["Scenario"],
                )
            )
            .reset_index()
        )
        .merge(
            gas.droplevel("Gas"),
            right_on=["IEA Region", "Scenario"],
            left_on=["Region", "Scenario"],
        )
        .set_index(["Region", "Scenario"])
        .reindex(sorted(em_baseline.columns), axis=1)
    )

    gas_per_change.index.set_names(["IEA Region", "Scenario"], inplace=True)
    """
    gas = gas_per_change.loc[:, :2019].merge(
        gas_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )

    gas5 = pd.DataFrame(gas5).append(
        pd.concat([gas], keys=[str(gas2)], names=["Metric"])
    )

    gas5 = pd.concat([gas5], keys=[str(gas2)], names=["Gas"]).reorder_levels(
        ["IEA Region", "Metric", "Gas", "Scenario"]
    )

    gas5 = pd.concat([gas5], keys=["Other"], names=["Sector"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
    )

    gas5.index.set_names(
        ["Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
    )


# endregion

###########
# F-gases #
###########

# region

gas = (
    pd.read_csv("podi/data/emissions_historical_fgas.csv")
    .drop(columns=["Gas", "Unit"])
    .set_index("Region")
)

gas = gas[gas.columns[::-1]]

gas.columns = gas.columns.astype(int)

region_categories = pd.read_csv(
    "podi/data/region_categories.csv", usecols=["CAIT Region", "IEA Region"]
)

gas = gas.merge(region_categories, right_on=["CAIT Region"], left_on=["Region"])

gas = gas.groupby("IEA Region").sum()

# split into various levels of IEA regional grouping
gas["IEA Region 1"] = gas.apply(lambda x: x.name.split()[2] + " ", axis=1)
gas["IEA Region 2"] = gas.apply(lambda x: x.name.split()[4] + " ", axis=1)
gas["IEA Region 3"] = gas.apply(lambda x: x.name.split()[-1] + " ", axis=1)

gas.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

# make new row for world level data
gas_world = pd.DataFrame(gas.sum()).T.rename(index={0: "World "})

# make new rows for OECD/NonOECD regions
gas_oecd = pd.DataFrame(gas.groupby("IEA Region 1").sum()).rename(
    index={"OECD ": " OECD "}
)

# make new rows for IEA regions
gas_regions = pd.DataFrame(gas.groupby("IEA Region 2").sum())
gas_regions2 = pd.DataFrame(gas.groupby("IEA Region 3").sum())

# combine all
gas = gas_world.append([gas_oecd, gas_regions.combine_first(gas_regions2)])
gas.index.name = "IEA Region"

gas = pd.concat([gas], keys=["F-gases"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Gas"]
)
gas3 = pd.concat([gas], keys=["baseline"], names=["Scenario"]).reorder_levels(
    ["IEA Region", "Gas", "Scenario"]
)
gas7 = gas3.append(
    pd.concat([gas], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Gas", "Scenario"]
    )
)

# project gas emissions using percent change in industry energy demand

gas_per_change = (
    energy_demand.loc[slice(None), "Industry", "Industry", slice(None)]
    .loc[:, 2017:]
    .pct_change(axis=1)
    .dropna(axis=1)
    .apply(lambda x: x + 1, axis=1)
    .merge(
        gas7,
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )
    .reindex(sorted(energy_demand.columns), axis=1)
)

"""
gas_per_change = (
    (
        pd.concat(
            [
                em_baseline.loc[slice(None), slice(None), slice(None), "CO2"]
                .groupby("Region")
                .sum()
                .loc[:, 2017:]
                .pct_change(axis=1)
                .loc[:, 2018:]
                .dropna(axis=0)
                .apply(lambda x: x + 1, axis=1)
            ],
            keys=["baseline"],
            names=["Scenario"],
        ).append(
            pd.concat(
                [
                    em_pathway.loc[slice(None), slice(None), slice(None), "CO2"]
                    .groupby("Region")
                    .sum()
                    .loc[:, 2017:]
                    .pct_change(axis=1)
                    .loc[:, 2018:]
                    .dropna(axis=0)
                    .apply(lambda x: x + 1, axis=1)
                ],
                keys=["pathway"],
                names=["Scenario"],
            )
        )
    )
    .reset_index()
    .merge(
        gas7.droplevel("Gas"),
        right_on=["IEA Region", "Scenario"],
        left_on=["Region", "Scenario"],
    )
    .set_index(["Region", "Scenario"])
    .reindex(sorted(em_baseline.columns), axis=1)
)

gas_per_change.index.set_names(["IEA Region", "Scenario"], inplace=True)
"""
gas = gas_per_change.loc[:, :2017].merge(
    gas_per_change.loc[:, 2017:].cumprod(axis=1).loc[:, 2018:],
    right_on=["IEA Region", "Scenario"],
    left_on=["IEA Region", "Scenario"],
)

gas8 = []

gas8 = pd.DataFrame(gas8).append(pd.concat([gas], keys=["F-gases"], names=["Metric"]))

gas8 = pd.concat([gas8], keys=["F-gases"], names=["Gas"]).reorder_levels(
    ["IEA Region", "Metric", "Gas", "Scenario"]
)

gas8 = pd.concat([gas8], keys=["Other"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"]
)

gas8.index.set_names(
    ["IEA Region", "Sector", "Metric", "Gas", "Scenario"], inplace=True
)

# endregion

# combine
addtl_em = cement.append(gas4).append(gas5).append(gas8).append(steel)

addtl_em.to_csv("podi/data/emissions_additional.csv", index=True)
