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

cement = pd.concat([cement], keys=["cement"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector"]
)
cement2 = pd.concat([cement], keys=["baseline"], names=["Scenario"]).reorder_levels(
    ["IEA Region", "Sector", "Scenario"]
)
cement = cement2.append(
    pd.concat([cement], keys=["pathway"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Sector", "Scenario"]
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
cement = pd.concat([cement], keys=["cement"], names=["Sector"]).reorder_levels(
    ["IEA Region", "Sector", "Scenario"]
)

# endregion

############
# CH4, N2O #
############

# region

data = {
    "ch4": "podi/data/CH4_CEDS_emissions_by_sector_country_2021_02_05.csv",
    "n2o": "podi/data/N2O_CEDS_emissions_by_sector_country_2021_02_05.csv",
}

gas4 = []

for gas2 in ["ch4", "n2o"]:
    gas = pd.read_csv(data[gas2]).drop(columns=["Em", "Units"])

    gas = pd.DataFrame(gas).set_index(["Country", "Sector"]) / 1000
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

    gas = pd.concat([gas], keys=[str(gas2)], names=["Sector"]).reorder_levels(
        ["IEA Region", "Sector"]
    )
    gas3 = pd.concat([gas], keys=["baseline"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Sector", "Scenario"]
    )
    gas = gas3.append(
        pd.concat([gas], keys=["pathway"], names=["Scenario"]).reorder_levels(
            ["IEA Region", "Sector", "Scenario"]
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

    gas = gas_per_change.loc[:, :2019].merge(
        gas_per_change.loc[:, 2019:].cumprod(axis=1).loc[:, 2020:],
        right_on=["IEA Region", "Scenario"],
        left_on=["IEA Region", "Scenario"],
    )

    gas4 = pd.DataFrame(gas4).append(
        pd.concat([gas], keys=[str(gas2)], names=["Sector"]).reorder_levels(
            ["IEA Region", "Sector", "Scenario"]
        )
    )

# endregion

# combine
addtl_em = cement.append(gas4)

addtl_em.to_csv("podi/data/emissions_additional.csv", index=True)
