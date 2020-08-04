#!/usr/bin/env python

import pandas as pd


def eia_etl(data_source):
    electricity_generation = pd.read_csv(data_source).fillna(0)
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["Region", "IEA Region"]
    ).set_index("Region")

    electricity_generation = electricity_generation.merge(
        region_categories, right_on=["Region"], left_on=["Region"]
    )

    return electricity_generation
