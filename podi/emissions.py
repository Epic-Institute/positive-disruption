#!/usr/bin/env python

import pandas as pd


def emissions(energy_supply, afolu_emissions):
    energy_supply_emitters = 
    emissions_factors = pd.read_excel("podi/data/emissions_factors.xlsx").reindex(energy_supply_emitters.index)

    emissions = energy_supply.mul(
        emissions_factors[emissions_factors.Value].loc[:, 2018:]
    )

    return emissions
