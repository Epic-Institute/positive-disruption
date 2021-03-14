#!/usr/bin/env python

# region

import pandas as pd
from podi.curve_smooth import curve_smooth
import numpy as np
from numpy import NaN
from podi.energy_demand import data_start_year, data_end_year

iea_region_list = (
    "World ",
    "NAM ",
    "US ",
    "CSAM ",
    "BRAZIL ",
    "EUR ",
    "AFRICA ",
    "SAFR ",
    "ME ",
    "RUS ",
    "ASIAPAC ",
    "CHINA ",
    "INDIA ",
    "JPN ",
    " OECD ",
    "NonOECD ",
)

# endregion


def energy_demand_hist(energy_demand_baseline):

    ############################
    #  LOAD DEMAND INPUT DATA  #
    ############################

    # region

    # Load energy demand historical data (ktoe)
    demand = (
        pd.read_csv("podi/data/energy_demand_historical_IEA.csv")
        .set_index(["WEB Region", "Sector", "Metric"])
        .replace("..", 0)
    )

    demand = demand.loc[
        slice(None),
        ["Industry", "Transport", "Buildings", "Other", "TFC"],
        [
            "Coal",
            "Oil",
            "Natural gas",
            "Nuclear",
            "Other renewables",
            "Electricity",
            "Heat",
            "Total final consumption",
            "Industry",
            "Transport",
            "Buildings",
            "Other fuels",
            "Bioenergy",
        ],
        :,
    ]

    # endregion

    ##################################
    #  DEFINE AND REALLOCATE DEMAND  #
    ##################################

    # region

    # convert from ktoe to TWh
    demand = demand.astype(float) * 1 / 0.086

    """
    # combine residential and commercial

    demand_b = (
        demand.loc[
            slice(None),
            ["Residential (ktoe)", "Commercial and public services (ktoe)"],
            slice(None),
        ]
        .groupby(["WEB Region", "Metric"])
        .sum()
    )

    demand_b = pd.concat([demand_b], keys=["Buildings"], names=["Sector"])

    demand = demand.loc[
        slice(None),
        ["Industry (ktoe)", "Transport (ktoe)", "Other final consumption (ktoe)"],
        slice(None),
        :,
    ].append(demand_b.reorder_levels(["WEB Region", "Sector", "Metric"]))
    """
    # Reallocate 'Other' energy demand from ag/non-energy use to industry heat

    demand_i = (
        demand.loc[
            slice(None),
            ["Other", "Industry"],
            slice(None),
        ]
        .groupby(["WEB Region", "Metric"])
        .sum()
    )

    demand_i = pd.concat([demand_i], keys=["Industry"], names=["Sector"])

    demand = demand.loc[
        slice(None), ["Transport", "Buildings", "TFC"], slice(None), :
    ].append(demand_i.reorder_levels(["WEB Region", "Sector", "Metric"]))

    # Reallocate heat demand within industry

    demand_h = (
        demand.loc[
            slice(None),
            "Industry",
            [
                "Coal",
                "Oil",
                "Natural gas",
                "Heat",
                "Other renewables",
            ],
        ]
        .groupby(["WEB Region", "Metric"])
        .sum()
    )

    demand_h = pd.concat([demand_h], keys=["Industry"], names=["Sector"])

    demand = (
        demand.loc[slice(None), ["Transport", "Buildings", "TFC"], slice(None), :]
        .append(demand_h.reorder_levels(["WEB Region", "Sector", "Metric"]))
        .append(demand.loc[slice(None), ["Industry"], ["Electricity"], :])
    )

    # Reallocate heat demand within buildings

    demand_b = (
        demand.loc[
            slice(None),
            "Buildings",
            [
                "Coal",
                "Oil",
                "Natural gas",
                "Heat",
                "Other renewables",
            ],
        ]
        .groupby(["WEB Region", "Metric"])
        .sum()
    )

    demand_b = pd.concat([demand_b], keys=["Buildings"], names=["Sector"])

    demand = (
        demand.loc[slice(None), ["Transport", "Industry", "TFC"], slice(None), :]
        .append(demand_b.reorder_levels(["WEB Region", "Sector", "Metric"]))
        .append(demand.loc[slice(None), ["Buildings"], ["Electricity"], :])
    )

    # endregion

    #################################################
    #  COMBINE, RECALCULATE SECTOR & END-USE DEMAND #
    #################################################

    # region
    """
    demand.loc[slice(None), "Industry", "Industry"] = (
        (
            demand.loc[slice(None), "Industry", ["Electricity", "Heat"]].groupby(
                "WEB Region"
            )
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "Buildings", "Buildings"] = (
        (
            energy_demand.loc[
                slice(None), "Buildings", ["Electricity", "Heat"]
            ].groupby("WEB Region")
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "Transport", "Transport"] = (
        (
            energy_demand.loc[
                slice(None),
                "Transport",
                ["Electricity", "Oil", "Bioenergy", "Other fuels"],
            ].groupby("WEB Region")
        )
        .sum()
        .values
    )
    """
    demand.loc[slice(None), "TFC", "Electricity"] = (
        (
            demand.loc[
                slice(None), ["Industry", "Buildings", "Transport"], ["Electricity"]
            ].groupby("WEB Region")
        )
        .sum()
        .values
    )

    demand.loc[slice(None), "TFC", "Heat"] = (
        (
            demand.loc[
                slice(None), ["Industry", "Buildings", "Transport"], ["Heat"]
            ].groupby("WEB Region")
        )
        .sum()
        .values
    )

    demand.loc[slice(None), "TFC", "Total final consumption"] = (
        (
            demand.loc[
                slice(None),
                ["Industry", "Buildings", "Transport"],
                ["Industry", "Buildings", "Transport"],
            ].groupby("WEB Region")
        )
        .sum()
        .values
    )

    # endregion

    #############################
    #  REGROUP INTO IEA REGIONS #
    #############################

    # region

    region_categories = (
        pd.read_csv(
            "podi/data/region_categories.csv", usecols=["WEB Region", "IEA Region"]
        )
        .dropna()
        .set_index("WEB Region")
    )

    demand = demand.combine_first(region_categories)
    """
    demand = demand.droplevel('WEB Region').reset_index().set_index(['IEA Region'])

    demand.index = demand.index.astype(str)
    """
    # World

    demand_w = demand.loc["World"]
    demand_w = pd.concat([demand_w], keys=["World "], names=["IEA Region"])

    # OECD

    demand_o = demand.loc["OECD Total"]
    demand_o = pd.concat([demand_o], keys=[" OECD "], names=["IEA Region"])

    # NonOECD

    demand_n = demand.loc["Non-OECD Total"]
    demand_n = pd.concat([demand_n], keys=["NonOECD "], names=["IEA Region"])

    # NAM

    demand_na = (
        demand.loc[["United States", "Canada", "Mexico"]]
        .groupby(["Sector", "Metric"])
        .sum()
    )
    demand_na = pd.concat([demand_na], keys=["NAM "], names=["IEA Region"])

    # ASIAPAC

    demand_a = (
        demand.loc[
            ["Australia", "People's Republic of China", "India", "Japan", "Korea"]
        ]
        .groupby(["Sector", "Metric"])
        .sum()
    )
    demand_a = pd.concat([demand_a], keys=["ASIAPAC "], names=["IEA Region"])

    # CSAM

    demand_c = demand.loc[["Non-OECD Americas"]].groupby(["Sector", "Metric"]).sum()
    demand_c = pd.concat([demand_c], keys=["CSAM "], names=["IEA Region"])

    # EUR

    demand_e = (
        demand.loc[
            [
                "Austria",
                "Belgium",
                "Czech Republic",
                "Denmark",
                "Estonia",
                "Finland",
                "France",
                "Germany",
                "Greece",
                "Hungary",
                "Iceland",
                "Ireland",
                "Israel",
                "Italy",
                "Latvia",
                "Lithuania",
                "Luxembourg",
                "Netherlands",
                "Norway",
                "Poland",
                "Portugal",
                "Slovak Republic",
                "Slovenia",
                "Spain",
                "Sweden",
                "Switzerland",
                "Turkey",
                "United Kingdom",
            ]
        ]
        .groupby(["Sector", "Metric"])
        .sum()
    )
    demand_e = pd.concat([demand_e], keys=["EUR "], names=["IEA Region"])

    # AFRICA

    demand_aa = demand.loc["Africa"]
    demand_aa = pd.concat([demand_aa], keys=["AFRICA "], names=["IEA Region"])

    # ME

    demand_me = demand.loc["Middle East"]
    demand_me = pd.concat([demand_me], keys=["ME "], names=["IEA Region"])

    # US

    demand_us = demand.loc["United States"]
    demand_us = pd.concat([demand_us], keys=["US "], names=["IEA Region"])

    # SAFR

    demand_sa = demand.loc["South Africa"]
    demand_sa = pd.concat([demand_sa], keys=["SAFR "], names=["IEA Region"])

    # RUS

    demand_r = demand.loc["Estonia"]
    demand_r = pd.concat([demand_r], keys=["RUS "], names=["IEA Region"])

    # JPN

    demand_j = demand.loc["Japan"]
    demand_j = pd.concat([demand_j], keys=["JPN "], names=["IEA Region"])

    # CHINA

    demand_ch = demand.loc["People's Republic of China"]
    demand_ch = pd.concat([demand_ch], keys=["CHINA "], names=["IEA Region"])

    # BRAZIL

    demand_br = demand.loc["Brazil"]
    demand_br = pd.concat([demand_br], keys=["BRAZIL "], names=["IEA Region"])

    # INDIA

    demand_in = demand.loc["India"]
    demand_in = pd.concat([demand_in], keys=["INDIA "], names=["IEA Region"])

    demand = (
        demand_w.append(demand_o)
        .append(demand_n)
        .append(demand_na)
        .append(demand_a)
        .append(demand_c)
        .append(demand_e)
        .append(demand_aa)
        .append(demand_me)
        .append(demand_us)
        .append(demand_sa)
        .append(demand_r)
        .append(demand_j)
        .append(demand_ch)
        .append(demand_br)
        .append(demand_in)
    )

    # endregion

    # region

    # update Sector and Metric naming
    """
    demand = demand.rename(
        index={
            "Transport (ktoe)": "Transport",
            "Industry (ktoe)": "Industry",
            "Coal, peat and oil shale": "Coal",
            "Crude, NGL and feedstocks": "Oil",
            "Oil products": "Oil",
            "Renewables and waste": "Other renewables",
        }
    )
    """
    demand.drop(columns="IEA Region", inplace=True)
    demand.columns = demand.columns.astype(int)

    demand.loc["World ", "Buildings", "Heat"].loc[:, :1997] = NaN
    demand.loc["World ", "Buildings", "Heat"].loc[:, 1971] = demand.loc[
        "World ", "Buildings", "Heat"
    ].loc[:, 1998]
    demand.loc["World ", "Buildings", "Heat"] = demand.loc[
        "World ",
        "Buildings",
        "Heat",
    ].interpolate(limit_area="inside")

    demand.loc["RUS ", "Industry", "Heat"].loc[:, :2012] = NaN
    demand.loc["RUS ", "Industry", "Heat"].loc[:, 1971] = 0
    demand.loc["RUS ", "Industry", "Heat"] = demand.loc[
        "RUS ",
        "Industry",
        "Heat",
    ].interpolate(limit_area="inside")

    demand.loc["US ", "Industry", "Heat"].loc[:, 1999:2006] = NaN
    demand.loc["US ", "Industry", "Heat"] = demand.loc[
        "US ", "Industry", "Heat"
    ].interpolate(limit_area="inside")

    demand.loc["US ", "Buildings", "Heat"].loc[:, 1999:2006] = NaN
    demand.loc["US ", "Buildings", "Heat"] = demand.loc[
        "US ", "Buildings", "Heat"
    ].interpolate(limit_area="inside")

    demand.loc["NAM ", "Industry", "Heat"].loc[:, 1999:2006] = NaN
    demand.loc["NAM ", "Industry", "Heat"] = demand.loc[
        "NAM ", "Industry", "Heat"
    ].interpolate(limit_area="inside")

    demand.loc["NAM ", "Buildings", "Heat"].loc[:, 1999:2006] = NaN
    demand.loc["NAM ", "Buildings", "Heat"] = demand.loc[
        "NAM ", "Buildings", "Heat"
    ].interpolate(limit_area="inside")

    demand.loc["NonOECD ", "Buildings", "Heat"].loc[:, :1992] = NaN
    demand.loc["NonOECD ", "Buildings", "Heat"].loc[:, 1971] = demand.loc[
        "NonOECD ", "Buildings", "Heat"
    ].loc[:, :1993]
    demand.loc["NonOECD ", "Buildings", "Heat"] = demand.loc[
        "NAM ", "Buildings", "Heat"
    ].interpolate(limit_area="inside")

    demand = demand.groupby(["IEA Region", "Sector", "Metric"]).sum()

    # estimate time between data and projections

    demand.loc[:, 2019] = demand.loc[:, 2018] * (
        1 + (demand.loc[:, 2018] - demand.loc[:, 2017]) / demand.loc[:, 2017]
    ).replace(NaN, 0)

    demand = pd.concat([demand], keys=["baseline"], names=["Scenario"]).reorder_levels(
        ["IEA Region", "Sector", "Metric", "Scenario"]
    )

    # harmonize with current demand
    hf_year = 2018

    hf = (
        demand.loc[:, hf_year]
        .divide(
            energy_demand_baseline.loc[
                [
                    "World ",
                    "NAM ",
                    "US ",
                    "CSAM ",
                    "BRAZIL ",
                    "EUR ",
                    "AFRICA ",
                    "SAFR ",
                    "ME ",
                    "RUS ",
                    "ASIAPAC ",
                    "CHINA ",
                    "INDIA ",
                    "JPN ",
                    " OECD ",
                    "NonOECD ",
                ],
                ["Buildings", "Industry", "Transport", "TFC"],
                [
                    "Coal",
                    "Electricity",
                    "Heat",
                    "Natural gas",
                    "Oil",
                    "Other renewables",
                    "Industry",
                    "Transport",
                    "Buildings",
                    "Bioenergy",
                    "Other fuels",
                ],
                "baseline",
            ]
            .reindex_like(demand)
            .loc[:, hf_year]
        )
        .replace(NaN, 0)
    )

    demand = demand.apply(lambda x: x.divide(hf[x.name]), axis=1).replace(NaN, 0)

    # back-extrapolate hist data where not available

    def zero(data):
        if data[1971] < 0.00001:
            data = data.replace(0, NaN)
            data[1971] = 0
            # data[2010] = 0
        return data

    demand = demand.apply(lambda x: zero(x), axis=1)

    demand_proj = (
        energy_demand_baseline.loc[
            [
                "World ",
                "NAM ",
                "US ",
                "CSAM ",
                "BRAZIL ",
                "EUR ",
                "AFRICA ",
                "SAFR ",
                "ME ",
                "RUS ",
                "ASIAPAC ",
                "CHINA ",
                "INDIA ",
                "JPN ",
                " OECD ",
                "NonOECD ",
            ],
            ["Buildings", "Industry", "Transport", "TFC"],
            [
                "Coal",
                "Electricity",
                "Heat",
                "Natural gas",
                "Oil",
                "Other renewables",
                "Industry",
                "Transport",
                "Buildings",
                "Bioenergy",
                "Other fuels",
            ],
            "baseline",
        ]
    ).loc[:, 2018:]

    demand = demand.loc[:, :2017].combine_first(demand_proj)

    demand = demand.apply(lambda x: x.interpolate(limit_area="inside"), axis=1)

    # endregion

    demand2 = pd.concat(
        [demand.droplevel("Scenario")], keys=["pathway"], names=["Scenario"]
    ).reorder_levels(["IEA Region", "Sector", "Metric", "Scenario"])

    demand = demand.append(demand2).loc[:, :2018]

    return demand.replace(NaN, 0)
