#!/usr/bin/env python

import pandas as pd

metric_list = [
    "Generation",
    "Nuclear",
    "Fossil fuels",
    "Hydroelectricity",
    "Geothermal",
    "Tide and wave",
    "Solar",
    "Wind",
    "Biomass and waste",
]


def eia_etl(data_source):
    elec_gen = (
        pd.read_csv(data_source).fillna(method="ffill", axis=1).drop(columns=["Sector"])
    )
    """
    elec_gen.loc[:, "1980":] = elec_gen.loc[:, "1980":].replace(
        {"baseline": 0.00001, "pathway": 0.00001}
    )
    """
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["Region", "IEA Region"]
    ).set_index("Region")

    elec_gen = elec_gen.merge(
        region_categories, right_on=["Region"], left_on=["Region"]
    ).set_index(["Region", "IEA Region", "Metric", "Scenario", "Unit"])

    elec_gen = elec_gen[elec_gen.index.isin(metric_list, level=2)]

    return elec_gen
