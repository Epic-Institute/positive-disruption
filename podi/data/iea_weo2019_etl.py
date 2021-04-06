#!/usr/bin/env python

import pandas as pd
from numpy import NaN
from podi.curve_smooth import curve_smooth
from podi.data.energy_demand import data_end_year, gcam_region_list
from main import region_list

input_data = pd.ExcelFile("podi/data/iea_weo2020.xlsx")


def iea_weo_etl(region_list_i):
    df = pd.read_excel(input_data, (region_list_i + "_Balance").replace(" ", ""))
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
        energy_demand_historical.iloc[:, 0:2]
        .join(df.iloc[:, 4])
        .join(df.iloc[:, 14:18])
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

    return energy_demand_historical


energy_demand_historical = dict()

for i in range(0, len(region_list)):
    energy_demand_historical[i] = iea_weo_etl(region_list[i])

    energy_demand_historical[i].insert(0, "IEA Region", region_list[i])
    energy_demand_historical[i].insert(0, "GCAM Region", gcam_region_list[i])

energy_demand_historical = pd.concat(
    [
        energy_demand_historical[0],
        energy_demand_historical[1],
        energy_demand_historical[2],
        energy_demand_historical[3],
        energy_demand_historical[4],
        energy_demand_historical[5],
        energy_demand_historical[6],
        energy_demand_historical[7],
        energy_demand_historical[8],
        energy_demand_historical[9],
        energy_demand_historical[10],
        energy_demand_historical[11],
        energy_demand_historical[12],
        energy_demand_historical[13],
        energy_demand_historical[14],
        energy_demand_historical[15],
        energy_demand_historical[16],
        energy_demand_historical[17],
        energy_demand_historical[18],
        energy_demand_historical[19],
        energy_demand_historical[20],
    ]
)

energy_demand_historical = pd.DataFrame(
    energy_demand_historical.loc[:, :data_end_year].set_index(
        ["GCAM Region", "IEA Region", "Sector", "Metric"]
    )
)

energy_demand_proj = curve_smooth(
    pd.DataFrame(
        energy_demand_historical.loc[:, data_end_year:].set_index(
            ["GCAM Region", "IEA Region", "Sector", "Metric"]
        )
    ),
    "quadratic",
    4,
)

energy_demand_historical = energy_demand_historical.join(energy_demand_proj)


energy_demand_historical.to_csv("podi/data/energy_demand_historical.csv", index=True)
