#!/usr/bin/env python

import pandas as pd
import numpy as np
from podi.curve_smooth import curve_smooth

data_start_year = 2010
data_end_year = 2019

iea_regions = pd.read_csv("podi/data/region_categories.csv")["IEA Region"]

iea_region_list = (
    "World ",
    "NAM ",
    "US ",
    "CSAM ",
    "BRAZIL ",
    "EUR ",
    "EU ",
    "AFRICA ",
    "SAFR ",
    "ME ",
    "EURASIA ",
    "RUS ",
    "ASIAPAC ",
    "CHINA ",
    "INDIA ",
    "JPN ",
    "ASEAN ",
    " OECD ",
    "NonOECD ",
    "DevelopingECO ",
    "AdvancedECO ",
)

gcam_region_list = (
    "World ",
    "OECD90 ",
    "OECD90 ",
    "LAM ",
    "LAM ",
    "OECD90 ",
    "OECD90 ",
    "MAF ",
    "MAF ",
    "MAF ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "OECD90 ",
    "World ",
    "World ",
    "World ",
)

input_data = pd.ExcelFile("podi/data/iea_weo2020.xlsx")


def iea_weo_etl(iea_region_list_i, gcam_region_list_i):
    df = pd.read_excel(input_data, (iea_region_list_i + "_Balance").replace(" ", ""))
    df.columns = df.iloc[3]
    df = df.drop(df.index[0:4])
    df.drop(df.tail(1).index, inplace=True)
    df.rename(columns={df.columns[0]: "Metric"}, inplace=True)

    if iea_region_list_i == "World ":
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
    else:
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

    energy_demand = df.iloc[:, 0:8]

    energy_demand = pd.DataFrame(energy_demand.set_index(["Sector", "Metric"]))

    xnew = np.linspace(
        energy_demand.columns.values.astype(int).min(),
        energy_demand.columns.values.astype(int).max(),
        energy_demand.columns.values.astype(int).max()
        - energy_demand.columns.values.astype(int).min(),
    ).astype(int)

    energy_demand = (
        pd.DataFrame(columns=xnew, index=energy_demand.index)
        .combine_first(energy_demand)
        .astype(float)
        .interpolate(method="quadratic", axis=1)
    )

    energy_demand.columns = energy_demand.columns.astype(int)

    energy_demand = pd.concat(
        [energy_demand],
        keys=[
            iea_region_list_i,
        ],
        names=["IEA Region"],
    ).reorder_levels(["IEA Region", "Sector", "Metric"])

    energy_demand = pd.concat(
        [energy_demand],
        keys=[
            gcam_region_list_i,
        ],
        names=["GCAM Region"],
    ).reorder_levels(["IEA Region", "GCAM Region", "Sector", "Metric"])

    return energy_demand


energy_demand2 = []

for i in range(0, len(iea_region_list)):
    energy_demand2 = pd.DataFrame(energy_demand2).append(
        iea_weo_etl(iea_region_list[i], gcam_region_list[i])
    )

energy_demand_hist = energy_demand2.loc[:, :data_end_year]

energy_demand_proj = curve_smooth(energy_demand2.loc[:, (data_end_year + 1) :], 3)

energy_demand2 = energy_demand_hist.join(energy_demand_proj)

# unit conversion from Mtoe to TWh
energy_demand2 = energy_demand2.mul(11.63)

energy_demand2.to_csv("podi/data/energy_demand_historical.csv", index=True)
