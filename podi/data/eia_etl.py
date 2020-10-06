#!/usr/bin/env python

import pandas as pd

metric_list = [
    "Biomass and waste",
    "Fossil fuels",
    "Generation",
    "Geothermal",
    "Hydroelectricity",
    "Nuclear",
    "Solar",
    "Wind",
    "Tide and wave",
]


def eia_etl(data_source):
    elec_gen = pd.read_csv(data_source).fillna(0).drop(columns=["Sector"])
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["Region", "IEA Region"]
    ).set_index("Region")

    elec_gen = elec_gen.merge(
        region_categories, right_on=["Region"], left_on=["Region"]
    ).set_index(["Region", "IEA Region", "Metric", "Scenario", "Unit"])

    elec_gen = elec_gen[elec_gen.index.isin(metric_list, level=2)]

    return elec_gen
