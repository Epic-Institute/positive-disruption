#!/usr/bin/env python

import pandas as pd
from podi.energy_supply import data_start_year


def etl(data):
    data = (
        pd.read_csv(data)
        .set_index(["Region", "Sector", "Metric", "Unit", "Scenario"])
        .droplevel("Unit")
    )

    data.columns = data.columns.astype(int)

    data = data.loc[:, data_start_year:]

    return data
