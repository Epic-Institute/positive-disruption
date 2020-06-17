#!/usr/bin/env python

import pandas as pd
from numpy import NaN

# from podi import conf

df = pd.read_excel("iea_weo_data.xlsx")

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

energy_demand_history = df.iloc[:, 0:5]
energy_demand_history.columns = ["Sector", "Metric", "2010", "2017", "2018"]
energy_demand_history["2010"] = pd.to_numeric(energy_demand_history["2010"]).astype(int)
energy_demand_history["2017"] = pd.to_numeric(energy_demand_history["2017"]).astype(int)
energy_demand_history["2018"] = pd.to_numeric(energy_demand_history["2018"]).astype(int)

for i in range(3, 9):
    energy_demand_history.insert(i, 2008 + i, NaN)

energy_demand_history.iloc[:, 2:10] = (
    energy_demand_history.iloc[:, 2:10].interpolate(axis=1).astype(int)
)

weo_demand_projection_cps = (
    energy_demand_history.iloc[:, 0:2].join(df.iloc[:, 3]).join(df.iloc[:, 14:18])
)

weo_demand_projection_cps.columns = [
    "Sector",
    "Metric",
    "2018",
    "2025",
    "2030",
    "2035",
    "2040",
]

for i in range(3, 24):
    weo_demand_projection_cps.insert(i, i + 2016, NaN)

weo_demand_projection_cps["2025"] = pd.to_numeric(weo_demand_projection_cps["2025"]).astype(float)

weo_demand_projection_cps.iloc[:, 2:10] = (
    weo_demand_projection_cps.iloc[:, 2:10].interpolate(axis=1).astype(int)
)
weo_demand_projection_cps.iloc[:, 9:15] = (
    weo_demand_projection_cps.iloc[:, 9:15].interpolate(axis=1).astype(int)
)
weo_demand_projection_cps.iloc[:, 14:20] = (
    weo_demand_projection_cps.iloc[:, 14:20].interpolate(axis=1).astype(int)
)
weo_demand_projection_cps.iloc[:, 19:25] = (
    weo_demand_projection_cps.iloc[:, 19:25].interpolate(axis=1).astype(int)
)

energy_demand_cps_baseline = energy_demand_history.join(weo_demand_projection_cps.loc[:, "2019":])

gcam_demand_projection = pd.read_excel("gcam_data.xlsx")

for i in range(4, 97):
    gcam_demand_projection.insert(i, i + 2002, NaN)

gcam_demand_projection.iloc[:, 3:9] = gcam_demand_projection.iloc[:, 3:9].interpolate(axis=1)
gcam_demand_projection.iloc[:, 8:19] = gcam_demand_projection.iloc[:, 8:19].interpolate(axis=1)
gcam_demand_projection.iloc[:, 18:29] = gcam_demand_projection.iloc[:, 18:29].interpolate(axis=1)
gcam_demand_projection.iloc[:, 28:39] = gcam_demand_projection.iloc[:, 28:39].interpolate(axis=1)
gcam_demand_projection.iloc[:, 38:49] = gcam_demand_projection.iloc[:, 38:49].interpolate(axis=1)
gcam_demand_projection.iloc[:, 48:59] = gcam_demand_projection.iloc[:, 48:59].interpolate(axis=1)
gcam_demand_projection.iloc[:, 58:69] = gcam_demand_projection.iloc[:, 58:69].interpolate(axis=1)
gcam_demand_projection.iloc[:, 68:79] = gcam_demand_projection.iloc[:, 68:79].interpolate(axis=1)
gcam_demand_projection.iloc[:, 78:89] = gcam_demand_projection.iloc[:, 78:89].interpolate(axis=1)
gcam_demand_projection.iloc[:, 88:99] = gcam_demand_projection.iloc[:, 88:99].interpolate(axis=1)

iea_weo_dict = pd.read_excel("weo_gcam_dict.xlsx")

gcam_demand_projection = gcam_demand_projection[
    (gcam_demand_projection.REGION == "World")
    & (gcam_demand_projection.VARIABLE.isin(iea_weo_dict.loc[:, "GCAM Value"]))
]

gcam_yoychange = gcam_demand_projection.iloc[:, 3:].pct_change(axis="columns")
gcam_yoychange = gcam_demand_projection.iloc[:, 0:3].join(
    gcam_yoychange.loc[:, "2041":].fillna(0).apply(lambda x: x + 1, axis=1)
)

gcam_yoychange_merge = iea_weo_dict.merge(
    gcam_yoychange, right_on="VARIABLE", left_on="GCAM Value"
)
energy_demand_cps_projection = energy_demand_cps_baseline.merge(
    gcam_yoychange_merge, right_on=["WEO Sector", "WEO Metric"], left_on=["Sector", "Metric"],
)

energy_demand_cps_projection = energy_demand_cps_projection.drop(
    columns=["WEO Sector", "WEO Metric", "GCAM Value", "REGION", "VARIABLE", "UNIT"]
)

energy_demand_cps_projection = energy_demand_cps_projection.loc[:, :"2039"].join(
    energy_demand_cps_projection.loc[:, "2040":].cumprod(axis=1).fillna(0).astype(int)
)

energy_demand_cps_projection = pd.melt(
    energy_demand_cps_projection, ["Sector", "Metric"], var_name="Year", value_name="Value",
)

energy_demand_cps_projection = energy_demand_cps_projection.loc[:, :"Year"].join(
    energy_demand_cps_projection.loc[:, "Value"].mul(11.63).astype(int)
)

energy_demand_cps_projection["Year"] = energy_demand_cps_projection["Year"].astype(int)

energy_demand_cps_projection.to_csv("refactored_1_energy_demand_cps_baseline.csv")
