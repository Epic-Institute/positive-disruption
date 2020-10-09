#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_supply import data_start_year, long_proj_end_year
from podi.data import iea_weo_em_etl

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
        .set_index(["Region", "Sector", "Metric"])
    )

    em_factors.columns = em_factors.columns.astype(int)
    em_factors = em_factors.loc[:, data_start_year:long_proj_end_year]

    # endregion

    #################
    #  ELECTRICITY  #
    #################

    # region
    elec_consump = pd.concat(
        [elec_consump], keys=["Electricity"], names=["Sector"]
    ).reorder_levels(["Region", "Sector", "Metric"])
    elec_em = (
        elec_consump * em_factors[em_factors.index.isin(elec_consump.index.values)]
    )

    # endregion

    ##########
    #  HEAT  #
    ##########

    # region
    heat_consump = pd.concat(
        [heat_consump], keys=["Heat"], names=["Sector"]
    ).reorder_levels(["Region", "Sector", "Metric"])

    heat_em = (
        heat_consump * em_factors[em_factors.index.isin(heat_consump.index.values)]
    ).drop(index=["Fossil fuels"], level=2)

    # endregion

    ###############
    #  BUILDINGS  #
    ###############

    # region
    buildings_consump = (
        energy_demand.loc[["OECD ", "NonOECD "], "Buildings", slice(None)]
        .groupby("IEA Region")
        .sum()
    )
    buildings_consump.index.name = "Region"

    buildings_consump = (
        buildings_consump
        * heat_per_adoption.loc[
            ["OECD ", "NonOECD "], ["Coal", "Natural gas", "Oil"], slice(None)
        ]
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
        energy_demand.loc[["OECD ", "NonOECD "], "Industry", slice(None)]
        .groupby("IEA Region")
        .sum()
    )
    industry_consump.index.name = "Region"

    industry_consump = (
        industry_consump
        * heat_per_adoption.loc[
            ["OECD ", "NonOECD "], ["Coal", "Natural gas", "Oil"], slice(None)
        ]
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
    transport_consump = pd.concat(
        [transport_consump], keys=["Transport"], names=["Sector"]
    ).reorder_levels(["Region", "Sector", "Metric"])

    transport_em = (
        transport_consump
        * em_factors[em_factors.index.isin(transport_consump.index.values)]
    ).drop(index=["Fossil fuels"], level=2)

    # endregion

    ###########
    #  AFOLU  #
    ###########

    # region

    afolu_em = afolu_em.droplevel(["Unit"])
    afolu_em.columns = afolu_em.columns.astype(int)
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

    # endregion

    if scenario == "Baseline":
        em = (
            pd.read_csv("podi/data/emissions_baseline.csv")
            .set_index(["Region", "Sector", "Unit"])
            .droplevel(["Unit"])
        )
    else:
        em = (
            elec_em.loc[slice(None), slice(None), "Fossil fuels"]
            .append(transport_em)
            .append(buildings_em)
            .append(industry_em)
            .append(afolu_em)
            .append(addtl_em)
        )

    # Add emissions targets
    em_targets = pd.read_csv(targets_em).set_index("Scenario")
    em_targets.columns = em_targets.columns.astype(int)

    return em, em_targets
