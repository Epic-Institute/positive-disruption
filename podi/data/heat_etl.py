#!/usr/bin/env python

import pandas as pd

metric_list = [
    "Coal",
    "Oil",
    "Natural gas",
    "Biofuels",
    "Waste",
    "Nuclear",
    "Geothermal",
    "Solar thermal",
    "Other sources",
]


def heat_etl(data_source, scenario):
    heat_gen = pd.read_csv(data_source).set_index(
        ["Region", "Sector", "Metric", "Scenario", "Unit"]
    )
    heat_gen = pd.DataFrame(heat_gen).interpolate(method="linear", axis=1)
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["Region", "IEA Region"]
    ).set_index("Region")

    # heat_gen = heat_gen.merge(
    #    region_categories, on='Region'
    # )

    # heat_gen.reset_index(inplace=True)
    # heat_gen.set_index(["Region", "IEA Region", "Metric", "Scenario", "Unit"], #inplace=True)

    heat_gen = heat_gen[heat_gen.index.isin(metric_list, level=2)]

    return heat_gen
