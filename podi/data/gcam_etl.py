#!/usr/bin/env python

import pandas as pd
from numpy import NaN

gcam_demand_projection = pd.read_excel("gcam_data.xlsx")

for i in range(4, 8):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(9, 18):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(19, 28):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(29, 38):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(39, 48):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(49, 58):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(59, 68):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(69, 78):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(79, 88):
    gcam_demand_projection.insert(i, i + 2002, NaN)
for i in range(89, 98):
    gcam_demand_projection.insert(i, i + 2002, NaN)

gcam_demand_projection.columns = gcam_demand_projection.columns.astype(str)

gcam_demand_projection.iloc[:, 3:9] = gcam_demand_projection.iloc[:, 3:9].interpolate(
    axis=1
)
gcam_demand_projection.iloc[:, 8:19] = gcam_demand_projection.iloc[:, 8:19].interpolate(
    axis=1
)
gcam_demand_projection.iloc[:, 18:29] = gcam_demand_projection.iloc[
    :, 18:29
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 28:39] = gcam_demand_projection.iloc[
    :, 28:39
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 38:49] = gcam_demand_projection.iloc[
    :, 38:49
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 48:59] = gcam_demand_projection.iloc[
    :, 48:59
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 58:69] = gcam_demand_projection.iloc[
    :, 58:69
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 68:79] = gcam_demand_projection.iloc[
    :, 68:79
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 78:89] = gcam_demand_projection.iloc[
    :, 78:89
].interpolate(axis=1)
gcam_demand_projection.iloc[:, 88:99] = gcam_demand_projection.iloc[
    :, 88:99
].interpolate(axis=1)

iea_weo_dict = pd.read_excel("weo_gcam_dict.xlsx")

gcam_demand_projection = gcam_demand_projection[
    (gcam_demand_projection.REGION == "World")
    & (gcam_demand_projection.VARIABLE.isin(iea_weo_dict.loc[:, "GCAM Value"]))
]

gcam_pct_change = gcam_demand_projection.iloc[:, 3:].pct_change(axis="columns")
gcam_pct_change = gcam_demand_projection.iloc[:, 0:3].join(
    gcam_pct_change.loc[:, "2041":].fillna(0).apply(lambda x: x + 1, axis=1)
)

gcam_pct_change = iea_weo_dict.merge(
    gcam_pct_change, right_on="VARIABLE", left_on="GCAM Value"
)

gcam_pct_change.to_csv("energy_demand_projection_baseline.csv", index=False)
