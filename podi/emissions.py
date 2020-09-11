#!/usr/bin/env python

import pandas as pd


def emissions(scenario, energy_supply, afolu_emissions, additional_emissions):
    em_factors = pd.read_csv("podi/data/emissions_factors.csv")

    # filter for Region
    em_factors = em_factors.loc[em_factors["Region"] == "World "]

    em_factors.set_index(["Region", "Metric", "Variable", "Unit"], inplace=True)

    em_factors.columns = em_factors.columns.astype(int)
    em_factors = em_factors[
        em_factors.index.get_level_values(1).isin(tech_list)
    ].droplevel(["Variable", "Unit"])

    elec_consump.drop(labels="Generation", level=1, inplace=True)
    elec_consump.columns = elec_consump.columns.astype(int)

    em = []

    # multiply emissions by emissions factors
    elec_em = elec_consump * em_factors
    em = pd.DataFrame(em).append(elec_em)

    # add heat emissions
    # heat_em =
    em = em.append(heat_em)

    # add transportation emissions
    # transport_em =
    em = em.append(transport_em)

    # add AFOLU emissions
    # afolu_em =
    em = em.append(afolu_em)

    # add additional emissions sources
    # addtl_em =
    em = em.append(addtl_em)

    return em
