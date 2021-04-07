#!/usr/bin/env python

import pandas as pd
from numpy import NaN
from podi.curve_smooth import curve_smooth

gcam_demand_projection = (
    pd.read_csv("podi/data/gcam.csv")
    .replace(" -   ", 0)
    .set_index(["Region", "Variable", "Unit"])
    .astype(float)
)

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

gcam_demand_projection.iloc[:, 0:6] = gcam_demand_projection.iloc[:, 0:6].interpolate(
    axis=1
)
gcam_demand_projection.iloc[:, 5:16] = gcam_demand_projection.iloc[:, 5:16].interpolate(
    axis=1
)
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

metrics = pd.read_csv("podi/data/metric_categories.csv")

gcam_demand_projection = gcam_demand_projection.loc[
    (slice(None), metrics.loc[:, "GCAM Metric"], slice(None)), :
]

gcam_pct_change2 = (
    gcam_demand_projection.pct_change(axis="columns")
    .loc[:, "2041":]
    .fillna(0)
    .apply(lambda x: x + 1, axis=1)
    .reset_index()
    .merge(metrics, right_on="GCAM Metric", left_on="Variable")
    .set_index(
        ["Region", "Variable", "Unit", "IEA Sector", "IEA Metric", "GCAM Metric"]
    )
)
"""
gcam_pct_change2 = curve_smooth(
    gcam_pct_change.loc[:, "2041":"2100"], "quadratic", 3
).join(gcam_pct_change.loc[:, "EIA Metric":])
"""
gcam_pct_change2.to_csv("podi/data/energy_demand_projection.csv", index=True)
