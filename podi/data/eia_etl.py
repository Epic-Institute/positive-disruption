#!/usr/bin/env python

import pandas as pd


def eia_etl(data_source):
    electricity_generation = pd.read_csv(data_source).fillna(0)
    electricity_generation["API"] = electricity_generation["API"].astype("str")
    electricity_generation["World"] = electricity_generation["World"].astype("str")

    electricity_generation_total = (
        electricity_generation[
            electricity_generation["World"].str.contains("Generation")
        ]
        .set_index(["API", "World"])
        .replace("--", "0")
        .astype(float)
    )

    return electricity_generation, electricity_generation_total
