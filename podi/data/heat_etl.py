#!/usr/bin/env python

import pandas as pd


def heat_etl(data_source):
    heat_generation = (
        pd.read_csv(data_source)
        .fillna(0)
        .set_index(["Region", "Sector", "Metric", "Unit"])
    )

    return heat_generation
