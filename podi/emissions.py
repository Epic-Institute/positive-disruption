#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_demand import data_start_year, data_end_year
from podi.energy_supply import near_proj_start_year, long_proj_end_year
from podi.energy_demand import iea_region_list
from numpy import NaN

# endregion


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

    for i in ["CO2", "CH4", "N2O"]:
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

    for i in ["CO2", "CH4", "N2O"]:
        buildings_consump2 = pd.DataFrame(buildings_consump2).append(
            pd.concat([buildings_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    buildings_em = (
        buildings_consump2
        * em_factors[em_factors.index.isin(buildings_consump2.index.values)]
    )

    # endregion

    ###############
    #  INDUSTRY  #
    ###############

    # region

    # add 'Electricity' to energy_demand here to toggle emissions from Electricity to Buildings
    industry_consump = (
        energy_demand.loc[slice(None), "Industry", ["Heat"], scenario]
        .groupby("IEA Region")
        .sum()
    )
    industry_consump.index.name = "Region"

    industry_consump = (
        industry_consump
        * heat_per_adoption.loc[slice(None), ["Coal", "Natural gas", "Oil"], scenario]
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

    for i in ["CO2", "CH4", "N2O"]:
        industry_consump2 = pd.DataFrame(industry_consump2).append(
            pd.concat([industry_consump], keys=[i], names=["Gas"]).reorder_levels(
                ["Region", "Sector", "Metric", "Gas"]
            )
        )

    industry_em = (
        industry_consump2
        * em_factors[em_factors.index.isin(industry_consump2.index.values)]
    )
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

    for i in ["CO2", "CH4", "N2O"]:
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

    # afolu_em = afolu_em.droplevel(["Unit"])
    # afolu_em.columns = afolu_em.columns.astype(int)
    afolu_em = afolu_em.loc[:, data_start_year:long_proj_end_year]

    afolu_em = pd.concat([afolu_em], keys=["CO2"], names=["Gas"]).reorder_levels(
        ["Region", "Sector", "Metric", "Gas"]
    )

    # endregion

    ##################################
    #  ADDITIONAL EMISSIONS SOURCES  #
    ##################################

    # region

    addtl_em = (
        (
            pd.read_csv(addtl_em).set_index(
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

    per_change = (
        elec_em.loc[slice(None), "Electricity", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
        .combine_first(addtl_em)
        .reindex(sorted(elec_em.columns), axis=1)
    )

    addtl_em = addtl_em.loc[:, :2019].merge(
        pd.DataFrame(addtl_em.loc[:, 2019])
        .merge(
            per_change.loc[:, 2020:],
            right_on=["Region", "Metric", "Gas"],
            left_on=["Region", "Metric", "Gas"],
        )
        .cumprod(axis=1)
        .loc[:, 2020:],
        right_on=["Region", "Metric", "Gas"],
        left_on=["Region", "Metric", "Gas"],
    )

    addtl_em = pd.concat([addtl_em], keys=["Other"], names=["Sector"]).reorder_levels(
        ["Region", "Sector", "Metric", "Gas"]
    )

    """
    for i in range(0, len(iea_region_list)):
        addtl_em.loc[iea_region_list[i], slice(None), slice(None)] = (
            addtl_em.loc["World ", slice(None), slice(None)].apply(
                lambda x: x
                * energy_demand.loc[
                    iea_region_list[i], "Industry", "Industry", scenario
                ].div(energy_demand.loc["World ", "Industry", "Industry", scenario]),
                axis=1,
            )
        ).values
    """

    # endregion

    em = (
        elec_em.append(transport_em)
        .append(buildings_em)
        .append(industry_em)
        .append(afolu_em)
        .append(addtl_em)
    )

    ##########################
    #  HISTORICAL EMISSIONS  #
    ##########################

    # region

    # pyhector data
    """
    em_hist = (
        pd.read_csv(
            "podi/pyhector/pyhector/emissions/RCP19_emissions.csv",
            header=3,
            usecols=[
                "Date",
                "ffi_emissions",
                "luc_emissions",
                "CH4_emissions",
                "N2O_emissions",
            ],
        )
        .dropna(axis=1)
        .multiply([1, 3.67, 3.67, 0.025, 0.298])
        .set_index("Date")
    )

    em_hist.index = em_hist.index.astype(int)
    em_hist = em_hist[(em_hist.index >= 1900) & (em_hist.index <= data_start_year)]
    em_hist["total_emissions"] = em_hist.sum(axis=1)
    """

    # CAIT data
    em_hist = (
        pd.read_csv("podi/data/emissions_historical.csv")
        .set_index(["Region", "Unit"])
        .droplevel("Unit")
    )

    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["IAM Region", "IEA Region"]
    )

    em_hist = em_hist.merge(
        region_categories, right_on=["IAM Region"], left_on=["Region"]
    )

    em_hist = em_hist.groupby("IEA Region").sum()

    # split into various levels of IEA regional grouping
    em_hist["IEA Region 1"] = em_hist.apply(lambda x: x.name.split()[2] + " ", axis=1)
    em_hist["IEA Region 2"] = em_hist.apply(lambda x: x.name.split()[4] + " ", axis=1)
    em_hist["IEA Region 3"] = em_hist.apply(lambda x: x.name.split()[-1] + " ", axis=1)

    em_hist.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new row for world level data
    em_hist_world = pd.DataFrame(em_hist.sum()).T.rename(index={0: "World "})

    # make new rows for OECD/NonOECD regions
    em_hist_oecd = pd.DataFrame(em_hist.groupby("IEA Region 1").sum()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    em_hist_regions = pd.DataFrame(em_hist.groupby("IEA Region 2").sum())
    em_hist_regions2 = pd.DataFrame(em_hist.groupby("IEA Region 3").sum())

    # combine all
    em_hist = em_hist_world.append(
        [em_hist_oecd, em_hist_regions.combine_first(em_hist_regions2)]
    )
    em_hist.index.name = "IEA Region"

    # estimate time between data and projections
    em_hist["2018"] = em_hist["2017"] * (
        1 + (em_hist["2017"] - em_hist["2016"]) / em_hist["2016"]
    )
    em_hist["2019"] = em_hist["2018"] * (
        1 + (em_hist["2018"] - em_hist["2017"]) / em_hist["2017"]
    )

    em_hist.columns = em_hist.columns.astype(int)

    # harmonize with historical emissions
    hf = (
        em_hist.loc[:, data_end_year]
        .divide(em.loc[:, data_end_year].groupby("Region").sum())
        .replace(NaN, 0)
    )

    em = em.apply(lambda x: x.multiply(hf[x.name[0]]), axis=1)

    #######################
    #  EMISSIONS TARGETS  #
    #######################
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
        em_hist.loc["World ", data_end_year]
        / (em_targets.loc[:, data_end_year]).replace(NaN, 0)
    )

    em_targets = em_targets * (hf.values)

    # endregion

    return em.round(decimals=3), em_targets.round(decimals=3), em_hist
