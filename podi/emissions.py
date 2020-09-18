#!/usr/bin/env python

import pandas as pd

tech_list = [
    "Biomass and waste",
    "Fossil fuels",
    "Geothermal",
    "Hydroelectricity",
    "Nuclear",
    "Solar",
    "Wind",
]


def emissions(scenario, energy_supply, afolu_emissions, additional_emissions):
    em_factors = pd.read_csv("podi/data/emissions_factors.csv")

    # filter for Region
    em_factors = em_factors.loc[em_factors["Region"] == "World "]

    em_factors.set_index(["Region", "Metric", "Variable", "Unit"], inplace=True)

    em_factors.columns = em_factors.columns.astype(int)

    # filter for electricity technologies
    elec_em_factors = em_factors[
        em_factors.index.get_level_values(1).isin(tech_list)
    ].droplevel(["Variable", "Unit"])

    elec_consump.columns = elec_consump.columns.astype(int)

    em = []

    # multiply emissions by emissions factors
    elec_em = elec_consump * elec_em_factors
    em = pd.DataFrame(em).append(elec_em)

    # add heat emissions

    # filter for electricity technologies
    em_factors.columns = em_factors.columns.astype(int)
    heat_em_factors = em_factors[
        em_factors.index.get_level_values(1).isin(["Fossil fuels"])
    ].droplevel(["Variable", "Unit"])

    heat_em = (heat_consump2 * heat_em_factors).fillna(0)
    em = em.append(heat_em)

    # add transportation emissions

    # filter for transportation technologies
    transport_em_factors = em_factors[
        em_factors.index.get_level_values(1).isin(["Oil", "Other fuels"])
    ].droplevel(["Variable", "Unit"])

    transport_em = (transport_consump2 * transport_em_factors).fillna(0)
    em = em.append(transport_em)

    # add AFOLU emissions
    # afolu_em =
    em = em.append(afolu_em)

    # add additional emissions sources
    # addtl_em =
    em = em.append(addtl_em)

    return em
