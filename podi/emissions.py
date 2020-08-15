#!/usr/bin/env python

import pandas as pd


def emissions(scenario, energy_supply, afolu_emissions, additional_emissions):
    # energy_supply_emitters =

    emissions_factors = pd.read_excel("podi/data/emissions_factors.xlsx").set_index(
        ["Region", "Sector", "Metric", "Unit"]
    )

    # emissions = energy_supply.mul(
    #    emissions_factors[emissions_factors.Value].loc[:, 2018:]
    # )

    emissions = [
        1,
        10,
        50,
        100,
        200,
        348,
        386,
        428,
        475,
        527,
        584,
        647,
        717,
        794,
        879,
        973,
        1076,
        1189,
        1314,
        1450,
        1600,
        1763,
        1942,
        2136,
        2347,
        2576,
        2824,
        3092,
        3379,
        3688,
        4018,
        4370,
        4744,
        5138,
        5554,
        5990,
        6445,
        6917,
        7405,
        7907,
        8420,
        8941,
        9468,
        9999,
        10529,
        11057,
        11578,
        12091,
        12593,
        13081,
        13553,
        14008,
        14444,
        14860,
        15255,
        15628,
        15980,
        16310,
        16619,
        16907,
        17175,
        17423,
        17652,
        17863,
        18057,
        18236,
        18399,
        18399,
        18399,
        18399,
        18187,
        17974,
        17762,
        17550,
        17337,
        17125,
        16912,
        16700,
        16487,
        16275,
        16062,
    ]

    return emissions, emissions_factors
