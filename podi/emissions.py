#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_supply import data_start_year, long_proj_end_year

# endregion


def emissions(
    scenario,
    elec_consump,
    heat_consump,
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
    #  Heat  #
    ##########

    # region
    heat_consump = pd.concat(
        [heat_consump], keys=["Heat"], names=["Sector"]
    ).reorder_levels(["Region", "Sector", "Metric"])

    heat_em = (
        heat_consump * em_factors[em_factors.index.isin(heat_consump.index.values)]
    ).drop(index=["Fossil fuels"], level=2)

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
        elec_em = 
        heat_em = 
        transport_em = 

    em = elec_em.append(heat_em).append(transport_em).append(afolu_em).append(addtl_em)

    # Add emissions targets
    em_targets = pd.read_csv(targets_em).set_index("Scenario")
    em_targets.columns = em_targets.columns.astype(int)

    return em, em_targets
