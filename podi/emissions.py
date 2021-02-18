#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_demand import data_start_year
from podi.energy_supply import long_proj_end_year
from podi.energy_demand import iea_region_list

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
        .set_index(["Region", "Sector", "Metric", "Scenario"])
    ).loc[slice(None), slice(None), slice(None), scenario]

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
    elec_em = (
        elec_consump * em_factors[em_factors.index.isin(elec_consump.index.values)]
    )

    # endregion

    ###############
    #  BUILDINGS  #
    ###############

    # region

    buildings_consump = (
        energy_demand.loc[slice(None), "Buildings", slice(None), scenario]
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

    buildings_em = (
        buildings_consump
        * em_factors[em_factors.index.isin(buildings_consump.index.values)]
    )

    # endregion

    ###############
    #  INDUSTRY  #
    ###############

    # region
    industry_consump = (
        energy_demand.loc[slice(None), "Industry", slice(None), scenario]
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

    industry_em = (
        industry_consump
        * em_factors[em_factors.index.isin(industry_consump.index.values)]
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

    transport_em = (
        transport_consump
        * em_factors[em_factors.index.isin(transport_consump.index.values)]
    ).drop(index=["Bioenergy", "Oil", "Other fuels"], level=2)

    # endregion

    ###########
    #  AFOLU  #
    ###########

    # region

    # afolu_em = afolu_em.droplevel(["Unit"])
    # afolu_em.columns = afolu_em.columns.astype(int)
    afolu_em = afolu_em.loc[:, data_start_year:long_proj_end_year]

    # endregion

    ##################################
    #  ADDITIONAL EMISSIONS SOURCES  #
    ##################################

    # region

    addtl_em = (
        (
            pd.read_csv(addtl_em)
            .set_index(["Region", "Sector", "Metric", "Scenario"])
            .drop(columns=["Unit"])
        )
        .loc[slice(None), slice(None), slice(None), scenario]
        .reorder_levels(["Region", "Sector", "Metric"])
    )
    addtl_em.columns = addtl_em.columns.astype(int)
    addtl_em = addtl_em.loc[:, data_start_year:long_proj_end_year]

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

    # endregion
    """
    if scenario == "baseline":

        em = pd.read_csv("podi/data/emissions_baseline.csv").set_index(
            ["Region", "Sector", "Metric"]
        )
        em.columns = em.columns.astype(int)

        em.rename(index={"Power sector": "Electricity"})

        em = (
            (em.loc[slice(None), ["Electricity"], slice(None)])
            .append(
                em.loc[slice(None), ["Industry", "Transport", "Buildings"], slice(None)]
            )
            .append(afolu_em)
            .append(addtl_em)
        )
    else:
    """
    em = (
        elec_em.append(transport_em)
        .append(buildings_em)
        .append(industry_em)
        .append(afolu_em)
        .append(addtl_em)
    )

    """
    em = pd.concat([em], keys=["Emissions"], names=["Metric"]).reorder_levels(
        ["Region", "Sector", "Metric"]
    )
    """

    # Add emissions targets
    em_targets = pd.read_csv(targets_em).set_index("Scenario")
    em_targets.columns = em_targets.columns.astype(int)

    return em.round(decimals=0), em_targets.round(decimals=0)
