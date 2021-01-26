#!/usr/bin/env python

import pandas as pd
import numpy as np
from podi.curve_smooth import curve_smooth
from podi.energy_demand import data_end_year, iea_region_list, gcam_region_list

input_data = pd.ExcelFile("podi/data/iea_weo2020.xlsx")


def iea_weo_em_etl(iea_region_list_i, gcam_region_list_i):
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
                    "TPED",
                    "TPED",
                    "TPED",
                    "TPED",
                    "Power sector",
                    "Power sector",
                    "Power sector",
                    "Power sector",
                    "TFC",
                    "TFC",
                    "TFC",
                    "Transport",
                    "Transport",
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
                    "TPED",
                    "TPED",
                    "TPED",
                    "TPED",
                    "Power sector",
                    "Power sector",
                    "Power sector",
                    "Power sector",
                    "TFC",
                    "TFC",
                    "Transport",
                    "TFC",
                    "TFC",
                ],
                df.index.values,
            ]
        ).T.set_index(1)

    df["Sector"] = sector
    df = pd.DataFrame(df.reset_index().set_index(["Sector", "Metric"]))

    xnew = np.linspace(
        df.columns.values.astype(int).min(),
        df.columns.values.astype(int).max(),
        df.columns.values.astype(int).max() - df.columns.values.astype(int).min() + 1,
    ).astype(int)

    df = (
        pd.DataFrame(columns=xnew, index=df.index)
        .combine_first(df)
        .astype(float)
        .interpolate(method="quadratic", axis=1)
    )

    df.rename(
        index={
            "Total CO2": "Total primary demand",
            "Final consumption": "Total final consumption",
            "Process emissions": "Other",
            "  Transport": "Transport",
        },
        inplace=True,
    )

    # GCAM for 2040-2100

    gcam_demand_projection = (
        pd.read_csv("podi/data/gcam.csv")
        .replace(" -   ", 0)
        .set_index(["Region", "Variable", "Unit"])
        .astype(float)
    )
    gcam_demand_projection.index.rename(["Region", "Sector", "Unit"], inplace=True)
    gcam_demand_projection.columns = gcam_demand_projection.columns.astype(int)

    xnew = np.linspace(
        gcam_demand_projection.columns.values.astype(int).min(),
        gcam_demand_projection.columns.values.astype(int).max(),
        gcam_demand_projection.columns.values.astype(int).max()
        - gcam_demand_projection.columns.values.astype(int).min(),
    ).astype(int)

    gcam_demand_projection = (
        pd.DataFrame(columns=xnew, index=gcam_demand_projection.index)
        .combine_first(gcam_demand_projection)
        .astype(float)
        .interpolate(method="quadratic", axis=1)
    )

    metrics = pd.read_csv("podi/data/metric_categories_em.csv")

    gcam_demand_projection = gcam_demand_projection.loc[
        "World ", metrics.loc[:, "GCAM Metric"].dropna(), slice(None)
    ]

    gcam_pct_change = (
        gcam_demand_projection.pct_change(axis="columns")
        .loc[:, df.columns.values.max() :]
        .fillna(0)
        .apply(lambda x: x + 1, axis=1)
    )

    gcam_pct_change = gcam_pct_change.droplevel(["Region", "Unit"])
    gcam_pct_change = (
        gcam_pct_change.reset_index()
        .merge(
            pd.DataFrame(
                metrics.loc[:, ["IEA Sector", "IEA Metric", "GCAM Metric"]].dropna()
            ).set_index("GCAM Metric"),
            right_on="GCAM Metric",
            left_on="Sector",
        )
        .set_index(["IEA Sector", "IEA Metric"])
        .drop(columns="Sector")
    )
    gcam_pct_change.columns = gcam_pct_change.columns.astype(int)

    df = df.join(gcam_pct_change.loc[:, 2041:], on=["Sector", "Metric"]).dropna()

    df = pd.concat(
        [df],
        keys=[
            iea_region_list_i,
        ],
        names=["Region"],
    ).reorder_levels(["Region", "Sector", "Metric"])

    df = df.loc[:, :2039].join(df.loc[:, 2040:].cumprod(axis=1).fillna(0).astype(int))

    return df


em = []

for i in range(0, len(iea_region_list)):
    em = pd.DataFrame(em).append(
        iea_weo_em_etl(iea_region_list[i], gcam_region_list[i])
    )

em_hist = em.loc[:, :data_end_year]

em_proj = curve_smooth(em.loc[:, (data_end_year + 1) :], "quadratic", 3)

em = em_hist.join(em_proj)

em.to_csv("podi/data/emissions_baseline.csv")
