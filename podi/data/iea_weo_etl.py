#!/usr/bin/env python

import pandas as pd
from numpy import NaN

df = pd.ExcelFile("iea_weo_data.xlsx")

region_list = ("World", "NAM", "US", "CSAM", "BRAZIL", "EUR", "EU", "AFRICA", "SAFR", )

#for each sheet, run the code below
def iea_weo_etl(*regions):
    for i in regions
    df = pd.read_excel(df, regions)
    df = df.drop(df.index[0:3])
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])
    df.drop(df.tail(1).index, inplace=True)
    df.rename(columns={df.columns[0]: "Metric"}, inplace=True)
    df.insert(
        0,
        "Sector",
        [
            "TPED",
            "TPED",
            "TPED",
            "TPED",
            "TPED",
            "TPED",
            "TPED",
            "TPED",
            "Power sector",
            "Power sector",
            "Power sector",
            "Power sector",
            "Power sector",
            "Power sector",
            "Power sector",
            "Power sector",
            "Other energy sector",
            "Other energy sector",
            "TFC",
            "TFC",
            "TFC",
            "TFC",
            "TFC",
            "TFC",
            "TFC",
            "TFC",
            "Industry",
            "Industry",
            "Industry",
            "Industry",
            "Industry",
            "Industry",
            "Industry",
            "Industry",
            "Transport",
            "Transport",
            "Transport",
            "Transport",
            "Transport",
            "Transport",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Buildings",
            "Other",
            "Other",
        ],
        True,
    )

    energy_demand_historical = df.iloc[:, 0:5]
    energy_demand_historical.columns = ["Sector", "Metric", "2010", "2017", "2018"]
    energy_demand_historical["2010"] = pd.to_numeric(
        energy_demand_historical["2010"]
    ).astype(int)
    energy_demand_historical["2017"] = pd.to_numeric(
        energy_demand_historical["2017"]
    ).astype(int)
    energy_demand_historical["2018"] = pd.to_numeric(
        energy_demand_historical["2018"]
    ).astype(int)

    for i in range(3, 9):
        energy_demand_historical.insert(i, 2008 + i, NaN)

    energy_demand_historical.iloc[:, 2:10] = (
        energy_demand_historical.iloc[:, 2:10].interpolate(axis=1).astype(int)
    )

    energy_demand_projection = (
        energy_demand_historical.iloc[:, 0:2].join(df.iloc[:, 4]).join(df.iloc[:, 14:18])
    )

    energy_demand_projection.columns = [
        "Sector",
        "Metric",
        "2018",
        "2025",
        "2030",
        "2035",
        "2040",
    ]

    for i in range(3, 9):
        energy_demand_projection.insert(i, i + 2016, NaN)
    for i in range(10, 14):
        energy_demand_projection.insert(i, i + 2016, NaN)
    for i in range(15, 19):
        energy_demand_projection.insert(i, i + 2016, NaN)
    for i in range(20, 24):
        energy_demand_projection.insert(i, i + 2016, NaN)

    energy_demand_projection.columns = energy_demand_projection.columns.astype(str)

    energy_demand_projection["2025"] = pd.to_numeric(
        energy_demand_projection["2025"]
    ).astype(float)

    energy_demand_projection.iloc[:, 2:10] = (
        energy_demand_projection.iloc[:, 2:10].interpolate(axis=1).astype(int)
    )
    energy_demand_projection.iloc[:, 9:15] = (
        energy_demand_projection.iloc[:, 9:15].interpolate(axis=1).astype(int)
    )
    energy_demand_projection.iloc[:, 14:20] = (
        energy_demand_projection.iloc[:, 14:20].interpolate(axis=1).astype(int)
    )
    energy_demand_projection.iloc[:, 19:25] = (
        energy_demand_projection.iloc[:, 19:25].interpolate(axis=1).astype(int)
    )

    energy_demand_historical = energy_demand_historical.join(
        energy_demand_projection.loc[:, "2019":]
    )

    energy_demand_historical.loc[:, "2010":] = (
        energy_demand_historical.loc[:, "2010":].mul(11.63).astype(int)
    )

    #prevent overwrite on each region
    energy_demand_historical.to_csv("energy_demand_historical.csv", index=False)
    return