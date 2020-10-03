#!/usr/bin/env python

import pandas as pd


def climate(scenario, data_source):
    climate = (
        pd.read_csv(data_source)
        .set_index(["Region", "Sector", "Metric", "Scenario"])
        .drop(columns=["Unit"])
        .loc[slice(None), slice(None), slice(None), scenario]
    )

    conc = climate.loc[
        slice(None), slice(None), ["Atmospheric concentration", "Equivalent CO2"]
    ]

    temp = climate.loc[
        slice(None), slice(None), ["Temperature change from preindustrial"]
    ]

    sea_lvl = climate.loc[slice(None), slice(None), ["Sea level rise from 2000"]]

    return conc, temp, sea_lvl
