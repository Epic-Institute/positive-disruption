#!/usr/bin/env python

import pandas as pd
from numpy import NaN


def wws_etl(data_source):
    elec_gen = pd.read_csv("podi/data/wws.csv")
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["WWS Region", "WEB Region"]
    )

    elec_gen = (
        elec_gen.merge(region_categories, right_on=["WWS Region"], left_on=["Region"])
        .dropna()
        .drop(columns=["Region", "WWS Region"])
        .rename(columns={"WEB Region": "Region"})
    )
    elec_gen["Region"] = elec_gen["Region"].str.lower()
    elec_gen.set_index("Region", inplace=True)

    # Reformat for insertion in tech_parameters.csv
    elec_gen = pd.melt(
        elec_gen, var_name="Product", value_name="Value", ignore_index=False
    )
    elec_gen["Metric"] = "saturation point"
    elec_gen["Sector"] = "Electric Power"
    elec_gen["Scenario"] = "pathway"
    elec_gen["Source"] = "wws"
    elec_gen.set_index(
        ["Product", "Scenario", "Sector", "Metric"], append=True, inplace=True
    )

    # Add to tech_parameters
    tech_parameters = pd.read_csv("podi/data/tech_parameters.csv")
    tech_parameters = tech_parameters.append(elec_gen.reset_index())
    tech_parameters.to_csv("podi/data/tech_parameters.csv", index=False)

    return
