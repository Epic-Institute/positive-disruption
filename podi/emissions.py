#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_demand import data_start_year, data_end_year
from podi.energy_supply import near_proj_start_year, long_proj_end_year
from numpy import NaN
import numpy as np
from podi.adoption_curve import adoption_curve

# endregion

region_list = pd.read_csv("podi/data/region_list.csv", header=None, squeeze=True)


def rgroup(data, gas, sector, rgroup, scenario):
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=[rgroup, "IEA Region"]
    )

    # make new row for world level data
    data_world = pd.DataFrame(data.sum()).T.rename(index={0: "World "})

    data = data.merge(region_categories, right_on=[rgroup], left_on=["Region"])

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
    )

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

    # afolu_em = afolu_em.loc[slice(None), slice(None), slice(None), scenario]
    afolu_em["Metric"] = afolu_em.index.get_level_values("Sector")
    # afolu_em = pd.concat([afolu_em], keys=["CO2"], names=["Gas"])
    afolu_em = afolu_em.reset_index()
    afolu_em = afolu_em.set_index(["Region", "Sector", "Metric", "Gas"])

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

    # remove steel to avoid double counting
    addtl_em = addtl_em.loc[
        slice(None),
        slice(None),
        slice(None),
        slice(None),
    ]

    # remove AFOLU to avoid double counting
    addtl_em = addtl_em.loc[
        slice(None),
        ["Electricity", "Industry", "Buildings", "Transport", "Other"],
        slice(None),
        slice(None),
    ]

    """
    # Set emissions change to follow elec ff emissions
    per_change = (
        industry_em.loc[slice(None), "Industry", "Fossil fuels", "CO2"]
        .loc[:, 2019:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .dropna(axis=1)
        .apply(lambda x: x + 1, axis=1)
    )
    """

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

    ##########################
    #  HISTORICAL EMISSIONS  #
    ##########################

    # region

    em_hist = (
        pd.read_csv("podi/data/emissions_historical.csv")
        .set_index(["Region", "Sector", "Gas", "Unit"])
        .droplevel("Unit")
    )
    em_hist.columns = em_hist.columns[::-1].astype(int)

    em_hist = (
        em_hist.loc[
            slice(None),
            [
                "Electricity",
                "Transport",
                "Buildings",
                "Industry",
                "Forests & Wetlands",
                "Regenerative Agriculture",
            ],
            slice(None),
            :,
        ]
        .groupby(["Region", "Sector", "Gas"])
        .sum()
    )

    em_hist2 = []

    for sector in em_hist.index.get_level_values(1).unique():
        for gas in (
            em_hist.loc[slice(None), sector, slice(None)]
            .index.get_level_values(1)
            .unique()
        ):
            em_hist2 = pd.DataFrame(em_hist2).append(
                rgroup(
                    em_hist.loc[slice(None), [sector], [gas], :],
                    gas,
                    sector,
                    "IAM Region",
                    scenario,
                )
            )

    em_hist = em_hist2.droplevel("Metric")

    em_hist.index.name = "IEA Region"

    # estimate time between data and projections
    em_hist["2019"] = em_hist[2018] * (
        1 + (em_hist[2018] - em_hist[2017]) / em_hist[2017]
    ).replace(NaN, 0)

    em_hist.columns = em_hist.columns.astype(int)

    # harmonize with historical emissions

    # add clip(lower=0) before .groupby to have em_hist not account for net negative F&W emissions
    hf = (
        em_hist.loc[:, data_end_year]
        .divide(em.loc[:, data_end_year].groupby(["Region", "Sector", "Gas"]).sum())
        .replace(NaN, 0)
    )

    em = em.apply(lambda x: x.multiply(hf[x.name[0], x.name[1], x.name[3]]), axis=1)

    em2 = []

    # add clip(lower=0) before .sum() to have em_hist not account for net negative F&W emissions
    for i in range(0, len(region_list)):
        em_per = (
            pd.DataFrame(
                em.loc[region_list[i]].apply(
                    lambda x: x.divide(x.sum()),
                    axis=0,
                )
            )
        ).loc[:, 1990:data_end_year]
        em_per = pd.concat([em_per], keys=[region_list[i]], names=["Region"])
        em_per = em_per.apply(
            lambda x: x.multiply(em_hist.loc[region_list[i]].loc[:, x.name].values[0]),
            axis=0,
        )
        em2 = pd.DataFrame(em2).append(em_per)

    em = em2.join(em.loc[:, 2020:])

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
        em_hist.loc["World ", data_end_year].sum()
        / (em_targets.loc[:, data_end_year]).replace(NaN, 0)
    )

    em_targets = em_targets * (hf.values)

    # endregion

    return em, em_targets, em_hist
