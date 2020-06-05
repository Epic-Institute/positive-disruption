#!/usr/bin/env python

import pandas as pd

from numpy import NaN

df = pd.read_excel(
    "/Volumes/GoogleDrive/My Drive/PD21/positive-disruption/data/iea_weo_data.xlsx"
)

df = df.drop(df.index[0:3])
df.columns = df.iloc[0]
df = df.drop(df.index[0])
df.drop(df.tail(1).index, inplace=True)
df.rename(columns={df.columns[0]: "Metric"}, inplace=True)

energy_demand_history = df.iloc[:, 0:4]
energy_demand_history.insert(
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
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Power Sector",
        "Other Energy Sector",
        "Other Energy Sector",
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

energy_demand_history.columns = ["Sector", "Metric", "2010", "2017", "2018"]
energy_demand_history["2010"] = pd.to_numeric(energy_demand_history["2010"]).astype(int)
energy_demand_history["2017"] = pd.to_numeric(energy_demand_history["2017"]).astype(int)
energy_demand_history["2018"] = pd.to_numeric(energy_demand_history["2018"]).astype(int)

energy_demand_history.insert(3, "2011", NaN)
energy_demand_history.insert(4, "2012", NaN)
energy_demand_history.insert(5, "2013", NaN)
energy_demand_history.insert(6, "2014", NaN)
energy_demand_history.insert(7, "2015", NaN)
energy_demand_history.insert(8, "2016", NaN)

energy_demand_history.iloc[:, 2:10] = (
    energy_demand_history.iloc[:, 2:10].interpolate(axis=1).astype(int)
)
energy_demand_history.head(10)

weo_demand_projection = energy_demand_history.iloc[:, 0:2].join(df.iloc[:, 3:8])

weo_demand_projection.columns = [
    "Sector",
    "Metric",
    "2018",
    "2025",
    "2030",
    "2035",
    "2040",
]

weo_demand_projection.insert(3, "2019", NaN)
weo_demand_projection.insert(4, "2020", NaN)
weo_demand_projection.insert(5, "2021", NaN)
weo_demand_projection.insert(6, "2022", NaN)
weo_demand_projection.insert(7, "2023", NaN)
weo_demand_projection.insert(8, "2024", NaN)

weo_demand_projection.insert(10, "2026", NaN)
weo_demand_projection.insert(11, "2027", NaN)
weo_demand_projection.insert(12, "2028", NaN)
weo_demand_projection.insert(13, "2029", NaN)

weo_demand_projection.insert(15, "2031", NaN)
weo_demand_projection.insert(16, "2032", NaN)
weo_demand_projection.insert(17, "2033", NaN)
weo_demand_projection.insert(18, "2034", NaN)

weo_demand_projection.insert(20, "2036", NaN)
weo_demand_projection.insert(21, "2037", NaN)
weo_demand_projection.insert(22, "2038", NaN)
weo_demand_projection.insert(23, "2039", NaN)

weo_demand_projection.iloc[:, 2:10] = (
    weo_demand_projection.iloc[:, 2:10].interpolate(axis=1).astype(int)
)
weo_demand_projection.iloc[:, 9:15] = (
    weo_demand_projection.iloc[:, 9:15].interpolate(axis=1).astype(int)
)
weo_demand_projection.iloc[:, 14:20] = (
    weo_demand_projection.iloc[:, 14:20].interpolate(axis=1).astype(int)
)
weo_demand_projection.iloc[:, 19:25] = (
    weo_demand_projection.iloc[:, 19:25].interpolate(axis=1).astype(int)
)
weo_demand_projection.head(10)

gcam_demand_projection = pd.read_excel(
    "/Volumes/GoogleDrive/My Drive/PD21/positive-disruption/data/gcam_data.xlsx"
)

gcam_demand_projection.insert(4, "2006", NaN)
gcam_demand_projection.insert(5, "2007", NaN)
gcam_demand_projection.insert(6, "2008", NaN)
gcam_demand_projection.insert(7, "2009", NaN)

gcam_demand_projection.insert(9, "2011", NaN)
gcam_demand_projection.insert(10, "2012", NaN)
gcam_demand_projection.insert(11, "2013", NaN)
gcam_demand_projection.insert(12, "2014", NaN)
gcam_demand_projection.insert(13, "2015", NaN)
gcam_demand_projection.insert(14, "2016", NaN)
gcam_demand_projection.insert(15, "2017", NaN)
gcam_demand_projection.insert(16, "2018", NaN)
gcam_demand_projection.insert(17, "2019", NaN)

gcam_demand_projection.insert(19, "2021", NaN)
gcam_demand_projection.insert(20, "2022", NaN)
gcam_demand_projection.insert(21, "2023", NaN)
gcam_demand_projection.insert(22, "2024", NaN)
gcam_demand_projection.insert(23, "2025", NaN)
gcam_demand_projection.insert(24, "2026", NaN)
gcam_demand_projection.insert(25, "2027", NaN)
gcam_demand_projection.insert(26, "2028", NaN)
gcam_demand_projection.insert(27, "2029", NaN)

gcam_demand_projection.insert(29, "2031", NaN)
gcam_demand_projection.insert(30, "2032", NaN)
gcam_demand_projection.insert(31, "2033", NaN)
gcam_demand_projection.insert(32, "2034", NaN)
gcam_demand_projection.insert(33, "2035", NaN)
gcam_demand_projection.insert(34, "2036", NaN)
gcam_demand_projection.insert(35, "2037", NaN)
gcam_demand_projection.insert(36, "2038", NaN)
gcam_demand_projection.insert(37, "2039", NaN)

gcam_demand_projection.insert(39, "2041", NaN)
gcam_demand_projection.insert(40, "2042", NaN)
gcam_demand_projection.insert(41, "2043", NaN)
gcam_demand_projection.insert(42, "2044", NaN)
gcam_demand_projection.insert(43, "2045", NaN)
gcam_demand_projection.insert(44, "2046", NaN)
gcam_demand_projection.insert(45, "2047", NaN)
gcam_demand_projection.insert(46, "2048", NaN)
gcam_demand_projection.insert(47, "2049", NaN)

gcam_demand_projection.insert(49, "2051", NaN)
gcam_demand_projection.insert(50, "2052", NaN)
gcam_demand_projection.insert(51, "2053", NaN)
gcam_demand_projection.insert(52, "2054", NaN)
gcam_demand_projection.insert(53, "2055", NaN)
gcam_demand_projection.insert(54, "2056", NaN)
gcam_demand_projection.insert(55, "2057", NaN)
gcam_demand_projection.insert(56, "2058", NaN)
gcam_demand_projection.insert(57, "2059", NaN)

gcam_demand_projection.insert(59, "2061", NaN)
gcam_demand_projection.insert(60, "2062", NaN)
gcam_demand_projection.insert(61, "2063", NaN)
gcam_demand_projection.insert(62, "2064", NaN)
gcam_demand_projection.insert(63, "2065", NaN)
gcam_demand_projection.insert(64, "2066", NaN)
gcam_demand_projection.insert(65, "2067", NaN)
gcam_demand_projection.insert(66, "2068", NaN)
gcam_demand_projection.insert(67, "2069", NaN)

gcam_demand_projection.insert(69, "2071", NaN)
gcam_demand_projection.insert(70, "2072", NaN)
gcam_demand_projection.insert(71, "2073", NaN)
gcam_demand_projection.insert(72, "2074", NaN)
gcam_demand_projection.insert(73, "2075", NaN)
gcam_demand_projection.insert(74, "2076", NaN)
gcam_demand_projection.insert(75, "2077", NaN)
gcam_demand_projection.insert(76, "2078", NaN)
gcam_demand_projection.insert(77, "2079", NaN)

gcam_demand_projection.insert(79, "2081", NaN)
gcam_demand_projection.insert(80, "2082", NaN)
gcam_demand_projection.insert(81, "2083", NaN)
gcam_demand_projection.insert(82, "2084", NaN)
gcam_demand_projection.insert(83, "2085", NaN)
gcam_demand_projection.insert(84, "2086", NaN)
gcam_demand_projection.insert(85, "2087", NaN)
gcam_demand_projection.insert(86, "2088", NaN)
gcam_demand_projection.insert(87, "2089", NaN)

gcam_demand_projection.insert(89, "2091", NaN)
gcam_demand_projection.insert(90, "2092", NaN)
gcam_demand_projection.insert(91, "2093", NaN)
gcam_demand_projection.insert(92, "2094", NaN)
gcam_demand_projection.insert(93, "2095", NaN)
gcam_demand_projection.insert(94, "2096", NaN)
gcam_demand_projection.insert(95, "2097", NaN)
gcam_demand_projection.insert(96, "2098", NaN)
gcam_demand_projection.insert(97, "2099", NaN)

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

iea_weo_dict = pd.read_excel(
    "/Volumes/GoogleDrive/My Drive/PD21/positive-disruption/data/weo_gcam_dict.xlsx"
)

gcam_demand_projection = gcam_demand_projection[
    (gcam_demand_projection.REGION == "World")
    & (gcam_demand_projection.VARIABLE.isin(iea_weo_dict.loc[:, "GCAM Value"]))
]

gcam_yoychange = gcam_demand_projection.iloc[:, 3:].pct_change(axis="columns")
gcam_yoychange = gcam_yoychange + 1
gcam_yoychange = gcam_demand_projection.iloc[:, 0:3].join(
    gcam_yoychange.loc[:, "2041":]
)

gcam_yoychange_merge = iea_weo_dict.merge(
    gcam_yoychange, right_on="VARIABLE", left_on="GCAM Value"
)

energy_demand_projection = weo_demand_projection.merge(
    gcam_yoychange_merge,
    right_on=["WEO Sector", "WEO Metric"],
    left_on=["Sector", "Metric"],
)

energy_demand_projection = energy_demand_projection.drop(
    columns=["WEO Sector", "WEO Metric", "GCAM Value", "REGION", "VARIABLE", "UNIT"]
)

energy_demand_projection = energy_demand_projection.loc[:, :"2039"].join(
    energy_demand_projection.loc[:, "2040":].cumprod(axis=1).fillna(0).astype(int)
)


energy_demand_projection = pd.melt(
    energy_demand_projection, ["Sector", "Metric"], var_name="Year", value_name="Value"
)


energy_demand_projection = energy_demand_projection.loc[:, :"Year"].join(
    energy_demand_projection.loc[:, "Value"].mul(11.63).astype(int)
)

energy_demand_projection.to_csv("baseline_energy_demand.csv")
