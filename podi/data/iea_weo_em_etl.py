#!/usr/bin/env python

import pandas as pd
from numpy import NaN
import numpy as np

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

input_data = pd.ExcelFile("podi/data/iea_weo.xlsx")


def iea_weo_em_etl(iea_region_list_i):
    if iea_region_list_i == "World ":
        df = pd.DataFrame(
            pd.read_excel(
                input_data, (iea_region_list_i + "_El_CO2_Ind").replace(" ", "")
            ).iloc[37:53, 0:7]
        ).fillna(0)
        df.set_index(df.iloc[:, 0].values, inplace=True)
        df.columns = df.iloc[0].values
        df.drop(columns=0, inplace=True)
        df.drop(index=0, inplace=True)
        df.columns = df.columns.astype(int)
        df.rename(index={"  Of which: bunkers": "International bunkers"}, inplace=True)
        df.index.name = "Metric"

        sector = pd.DataFrame(
            [
                [
                    "Total",
                    "Total",
                    "Total",
                    "Total",
                    "Power",
                    "Power",
                    "Power",
                    "Power",
                    "TFC",
                    "TFC",
                    "TFC",
                    "TFC",
                    "TFC",
                    "TFC",
                    "Other",
                ],
                df.index.values,
            ]
        ).T.set_index(1)

    else:
        df = pd.DataFrame(
            pd.read_excel(
                input_data, (iea_region_list_i + "_El_CO2_Ind").replace(" ", "")
            ).iloc[37:51, 0:7]
        ).fillna(0)
        df.set_index(df.iloc[:, 0].values, inplace=True)
        df.columns = df.iloc[0].values
        df.drop(columns=0, inplace=True)
        df.drop(index=0, inplace=True)
        df.columns = df.columns.astype(int)
        df.index.name = "Metric"

        sector = pd.DataFrame(
            [
                [
                    "Total",
                    "Total",
                    "Total",
                    "Total",
                    "Power",
                    "Power",
                    "Power",
                    "Power",
                    "TFC",
                    "TFC",
                    "TFC",
                    "TFC",
                    "TFC",
                ],
                df.index.values,
            ]
        ).T.set_index(1)

    df["Sector"] = sector
    df = pd.DataFrame(df.reset_index().set_index(["Sector", "Metric"]))

    df = pd.concat(
        [df],
        keys=[
            iea_region_list_i,
        ],
        names=["IEA Region"],
    ).reorder_levels(["IEA Region", "Sector", "Metric"])

    xnew = np.linspace(
        df.columns.values.astype(int).min(),
        df.columns.values.astype(int).max(),
        df.columns.values.astype(int).max() - df.columns.values.astype(int).min(),
    ).astype(int)

    df = (
        pd.DataFrame(columns=xnew, index=df.index)
        .combine_first(df)
        .astype(float)
        .interpolate(method="quadratic", axis=1)
    )

    # GCAM for 2040-2100

    gcam_demand_projection = (
        pd.read_csv("podi/data/gcam.csv")
        .replace(" -   ", 0)
        .set_index(["Region", "Variable", "Unit"])
        .astype(float)
    )
    gcam_demand_projection.index.rename(["Region", "Sector", "Unit"], inplace=True)

    for i in range(1, 5):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(6, 15):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(16, 25):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(26, 35):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(36, 45):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(46, 55):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(56, 65):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(66, 75):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(76, 85):
        gcam_demand_projection.insert(i, i + 2005, NaN)
    for i in range(86, 95):
        gcam_demand_projection.insert(i, i + 2005, NaN)

    gcam_demand_projection.columns = gcam_demand_projection.columns.astype(str)

    gcam_demand_projection.iloc[:, 0:6] = gcam_demand_projection.iloc[
        :, 0:6
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 5:16] = gcam_demand_projection.iloc[
        :, 5:16
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 15:26] = gcam_demand_projection.iloc[
        :, 15:26
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 25:36] = gcam_demand_projection.iloc[
        :, 25:36
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 35:46] = gcam_demand_projection.iloc[
        :, 35:46
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 45:56] = gcam_demand_projection.iloc[
        :, 45:56
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 55:66] = gcam_demand_projection.iloc[
        :, 55:66
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 65:76] = gcam_demand_projection.iloc[
        :, 65:76
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 75:86] = gcam_demand_projection.iloc[
        :, 75:86
    ].interpolate(axis=1)
    gcam_demand_projection.iloc[:, 85:96] = gcam_demand_projection.iloc[
        :, 85:96
    ].interpolate(axis=1)

    metrics = pd.read_csv("podi/data/metric_categories_em.csv")

    gcam_demand_projection = gcam_demand_projection.loc[
        (slice(None), metrics.loc[:, "GCAM Metric"].dropna(axis=0), slice(None)), :
    ]

    gcam_pct_change = (
        gcam_demand_projection.pct_change(axis="columns")
        .loc[:, "2041":]
        .fillna(0)
        .apply(lambda x: x + 1, axis=1)
    )
    gcam_pct_change.rename(
        index={
            "Emissions | CO2 | Fossil Fuels and Industry | Energy Demand | Industry": "Electricity",
            "Emissions | CO2 | Fossil Fuels and Industry | Energy Demand | Residential and Commercial": "Industry",
            "Emissions | CO2 | Fossil Fuels and Industry | Energy Demand | Transportation": "Transport",
            "Emissions | CO2 | Fossil Fuels and Industry | Energy Supply | Electricity": "Buildings",
        },
        inplace=True,
    )
    gcam_pct_change.droplevel(["Region", "Unit"])

    df = df.join(gcam_pct_change)
    df.columns = df.columns.astype(int)
    df = df.loc[:, :2039].join(df.loc[:, 2040:].cumprod(axis=1).fillna(0).astype(int))

    return df


em_baseline = dict()

for i in range(0, len(iea_region_list)):
    em_baseline[i] = iea_weo_em_etl(iea_region_list[i]).droplevel("Region")
    em_baseline[i].insert(0, "Region", iea_region_list[i])
    # em_baseline[i].insert(0, "GCAM Region", gcam_region_list[i])


em_baseline = pd.concat(
    [
        em_baseline[0],
        em_baseline[1],
        em_baseline[2],
        em_baseline[3],
        em_baseline[4],
        em_baseline[5],
        em_baseline[6],
        em_baseline[7],
        em_baseline[8],
        em_baseline[9],
        em_baseline[10],
        em_baseline[11],
        em_baseline[12],
        em_baseline[13],
        em_baseline[14],
        em_baseline[15],
        em_baseline[16],
        em_baseline[17],
        em_baseline[18],
        em_baseline[19],
        em_baseline[20],
    ]
)

em_baseline.to_csv("podi/data/emissions_baseline.csv")
