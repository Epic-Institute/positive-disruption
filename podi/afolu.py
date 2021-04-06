#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
import numpy as np
from podi.energy_supply import long_proj_end_year

region_list = pd.read_csv("podi/data/region_list.csv", header=None, squeeze=True)


def rgroup(data, gas, sector, rgroup, scenario):
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=[rgroup, "IEA Region"]
    )

    # make new row for world level data
    data_world = pd.DataFrame(data.sum()).T.rename(index={0: "World "})

    data = data.merge(region_categories, right_on=[rgroup], left_on=["Country"])

    data = data.groupby("IEA Region").sum()

    # split into various levels of IEA regional grouping
    data["IEA Region 1"] = data.apply(lambda x: x.name.split()[2] + " ", axis=1)
    data["IEA Region 2"] = data.apply(lambda x: x.name.split()[4] + " ", axis=1)
    data["IEA Region 3"] = data.apply(lambda x: x.name.split()[-1] + " ", axis=1)

    data.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new rows for OECD/NonOECD regions
    data_oecd = pd.DataFrame(data.groupby("IEA Region 1").sum()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    data_regions = pd.DataFrame(data.groupby("IEA Region 2").sum())
    data_regions2 = pd.DataFrame(data.groupby("IEA Region 3").sum())

    """
    # remove countries from higher level regions
    data_oecd.loc[" OECD "] = (
        data_oecd.loc[" OECD "] - data_regions2.loc["US "] - data_regions2.loc["SAFR "]
    )
    data_oecd.loc["NonOECD "] = data_oecd.loc["NonOECD "] - data_regions2.loc["BRAZIL "]

    data_regions.loc["CSAM "] = data_regions.loc["CSAM "] - data_regions2.loc["BRAZIL "]
    data_regions.loc["NAM "] = data_regions.loc["NAM "] - data_regions2.loc["US "]
    data_regions.loc["AFRICA "] = (
        data_regions.loc["AFRICA "] - data_regions2.loc["SAFR "]
    )
    """
    # combine all
    data = data_world.append(
        [data_oecd, data_regions, data_regions2.loc[["BRAZIL ", "US ", "SAFR "], :]]
    )
    data.index.name = "Region"

    data = pd.concat([data], names=["Sector"], keys=[sector])
    data = pd.concat([data], names=["Metric"], keys=[sector])
    data = pd.concat([data], names=["Scenario"], keys=[scenario]).reorder_levels(
        ["Region", "Sector", "Metric", "Scenario"]
    )
    data = data.loc[np.array(region_list), slice(None), slice(None), slice(None)]

    return data


def rgroup2(data, gas, sector, rgroup, scenario):
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=[rgroup, "IEA Region"]
    )

    # make new row for world level data
    data_world = pd.DataFrame(data.mean()).T.rename(index={0: "World "})

    data = data.merge(region_categories, right_on=[rgroup], left_on=["Country"])

    data = data.groupby("IEA Region").mean()

    # split into various levels of IEA regional grouping
    data["IEA Region 1"] = data.apply(lambda x: x.name.split()[2] + " ", axis=1)
    data["IEA Region 2"] = data.apply(lambda x: x.name.split()[4] + " ", axis=1)
    data["IEA Region 3"] = data.apply(lambda x: x.name.split()[-1] + " ", axis=1)

    data.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new rows for OECD/NonOECD regions
    data_oecd = pd.DataFrame(data.groupby("IEA Region 1").mean()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    data_regions = pd.DataFrame(data.groupby("IEA Region 2").mean())
    data_regions2 = pd.DataFrame(data.groupby("IEA Region 3").mean())

    """
    # remove countries from higher level regions
    data_oecd.loc[" OECD "] = (
        data_oecd.loc[" OECD "] - data_regions2.loc["US "] - data_regions2.loc["SAFR "]
    )
    data_oecd.loc["NonOECD "] = data_oecd.loc["NonOECD "] - data_regions2.loc["BRAZIL "]

    data_regions.loc["CSAM "] = data_regions.loc["CSAM "] - data_regions2.loc["BRAZIL "]
    data_regions.loc["NAM "] = data_regions.loc["NAM "] - data_regions2.loc["US "]
    data_regions.loc["AFRICA "] = (
        data_regions.loc["AFRICA "] - data_regions2.loc["SAFR "]
    )
    """
    # combine all
    data = data_world.append(
        [data_oecd, data_regions, data_regions2.loc[["BRAZIL ", "US ", "SAFR "], :]]
    )
    data.index.name = "Region"

    data = pd.concat([data], names=["Sector"], keys=[sector])
    data = pd.concat([data], names=["Metric"], keys=[sector])
    data = pd.concat([data], names=["Scenario"], keys=[scenario]).reorder_levels(
        ["Region", "Sector", "Metric", "Scenario"]
    )
    data = data.loc[np.array(region_list), slice(None), slice(None), slice(None)]

    return data


def afolu(scenario):
    """
    afolu = pd.read_excel(
        "podi/data/Positive Disruption NCS Vectors.xlsx",
        sheet_name=[
            "Input data 3",
            "Avoided pathways input",
            "Historical Observations",
            "Pathway - analog crosswalk",
            "Analogs",
        ],
    )
    """

    input_data_3 = pd.read_csv("podi/data/tnc_input_data_3.csv")
    avoided_pathways_input = pd.read_csv("podi/data/tnc_avoided_pathways_input.csv")
    hist_obs = pd.read_csv("podi/data/tnc_hist_obs.csv")
    crosswalk = pd.read_csv("podi/data/tnc_crosswalk.csv")
    analogs = pd.read_csv("podi/data/tnc_analogs.csv")

    # create max extent df

    # region
    max_extent = input_data_3[input_data_3["Metric"] == "Max extent"].drop(
        columns=["Metric", "Model", "Scenario", "Region", "iso", "Unit"]
    )

    """
    max_extent = afolu["Input data 3"][
        afolu["Input data 3"]["Metric"] == "Max extent"
    ].drop(columns=["Metric", "Model", "Scenario", "Region", "iso", "Unit"])
    """

    max_extent["Duration 1 (Years)"] = np.where(
        (
            (max_extent["Duration 1 (Years)"].isna())
            | (max_extent["Duration 1 (Years)"] > 2100 - 2019)
        ),
        2100 - 2019,
        max_extent["Duration 1 (Years)"],
    )

    max_extent["Value 2"] = np.where(
        max_extent["Value 2"].isna(), max_extent["Value 1"], max_extent["Value 2"]
    )

    max_extent["Duration 2 (Years)"] = np.where(
        (max_extent["Duration 2 (Years)"].isna()),
        max_extent["Duration 1 (Years)"],
        max_extent["Duration 2 (Years)"],
    )

    max_extent["Value 3"] = np.where(
        max_extent["Value 3"].isna(), max_extent["Value 2"], max_extent["Value 3"]
    )

    max_extent["Duration 3 (Years)"] = np.where(
        max_extent["Duration 3 (Years)"].isna(),
        max_extent["Duration 2 (Years)"],
        max_extent["Duration 3 (Years)"],
    )

    max_extent2 = pd.DataFrame(
        index=[
            max_extent["Country"],
            max_extent["Subvector"],
            max_extent["Duration 1 (Years)"],
            max_extent["Value 2"],
            max_extent["Duration 2 (Years)"],
        ],
        columns=np.arange(1990, long_proj_end_year + 1, 1),
        dtype=float,
    )
    max_extent2.loc[:, 1990] = max_extent["Value 1"].values
    max_extent2.loc[:, 2100] = max_extent["Value 1"].values
    max_extent2.interpolate(axis=1, limit_area="inside", inplace=True)
    max_extent2 = max_extent2.droplevel(
        ["Duration 1 (Years)", "Value 2", "Duration 2 (Years)"]
    )

    # update Improved Forest Mgmt max extent units for consistency
    max_extent2.loc[slice(None), "Improved Forest Mgmt", :] = (
        max_extent2.loc[slice(None), "Improved Forest Mgmt", :] / 1e6
    )

    # endregion

    # create avg mitigation potential flux df

    # region

    flux = input_data_3[input_data_3["Metric"] == "Avg mitigation potential flux"].drop(
        columns=["Metric", "Model", "Scenario", "Region", "iso", "Unit"]
    )

    flux["Duration 1 (Years)"] = np.where(
        (
            (flux["Duration 1 (Years)"].isna())
            | (flux["Duration 1 (Years)"] > 2100 - 2019)
        ),
        2100 - 2019,
        flux["Duration 1 (Years)"],
    )

    flux["Value 2"] = np.where(flux["Value 2"].isna(), flux["Value 1"], flux["Value 2"])

    flux["Duration 2 (Years)"] = np.where(
        (flux["Duration 2 (Years)"].isna()),
        flux["Duration 1 (Years)"],
        flux["Duration 2 (Years)"],
    )

    flux["Value 3"] = np.where(flux["Value 3"].isna(), flux["Value 2"], flux["Value 3"])

    flux["Duration 3 (Years)"] = np.where(
        flux["Duration 3 (Years)"].isna(),
        flux["Duration 2 (Years)"],
        flux["Duration 3 (Years)"],
    )

    flux2 = pd.DataFrame(
        index=[
            flux["Country"],
            flux["Subvector"],
            flux["Duration 1 (Years)"],
            flux["Value 2"],
            flux["Duration 2 (Years)"],
        ],
        columns=np.arange(1990, long_proj_end_year + 1, 1),
        dtype=float,
    )
    flux2.loc[:, 1990] = flux["Value 1"].values
    flux2.loc[:, 2100] = flux["Value 1"].values
    flux2.interpolate(axis=1, limit_area="inside", inplace=True)
    flux2 = flux2.droplevel(
        ["Duration 1 (Years)", "Value 2", "Duration 2 (Years)"]
    ).fillna(0)

    # endregion

    # create historical observations df (as % of max extent)

    # region

    hist = hist_obs.drop(
        columns=["iso", "Model", "Scenario", "Region", "Metric", "Unit"]
    )

    hist = pd.DataFrame(hist).set_index(["Country", "Subvector"])
    hist.columns = hist.columns.astype(int)
    hist = hist.loc[:, 1990:]
    hist.interpolate(axis=1, limit_area="inside", inplace=True)
    hist1 = (
        hist.loc[
            slice(None),
            [
                "Biochar",
                "Coastal Restoration",
                "Cropland Soil Health",
                "Improved Forest Mgmt",
                "Improved Rice",
                "Natural Regeneration",
                # "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Peat Restoration",
                "Silvopasture",
                "Trees in Croplands",
            ],
            :,
        ]
        .fillna(0)
        .apply(
            lambda x: x.divide(max_extent2.loc[x.name[0], x.name[1]].loc[:2020]), axis=1
        )
    )

    # correct units
    hist1.loc[
        slice(None),
        ["Improved Rice", "Trees in Croplands", "Peat Restoration", "Silvopasture"],
        :,
    ] = (
        hist1.loc[
            slice(None),
            ["Improved Rice", "Trees in Croplands", "Peat Restoration", "Silvopasture"],
            :,
        ]
        / 1e3
    )

    hist1 = hist1.replace(0, NaN)

    # endregion

    # compute adoption curves of historical analogs

    # region

    acurves = (
        pd.DataFrame(analogs)
        .drop(columns=["Note", "Units", "Actual start year"])
        .set_index(["Analog name", "Max (Mha)"])
    )
    acurves.columns = acurves.loc[NaN, NaN].astype(int)
    acurves.columns.rename("Year", inplace=True)
    acurves.drop(index=NaN, inplace=True)
    acurves.interpolate(axis=1, limit_area="inside", inplace=True)
    acurves = acurves.apply(lambda x: x / x.name[1], axis=1)
    acurves = acurves.apply(lambda x: x - x[1], axis=1)
    acurves.columns = np.arange(2021, 2065, 1)

    proj_per_adoption = acurves.apply(
        lambda x: adoption_curve(
            x.dropna().rename(x.name[0]),
            x.name[0],
            scenario,
            "AFOLU",
        ),
        axis=1,
    )

    per = []
    for i in range(0, len(proj_per_adoption.index)):
        per = pd.DataFrame(per).append(proj_per_adoption[proj_per_adoption.index[i]].T)

    per.set_index(proj_per_adoption.index, inplace=True)

    per = per.apply(lambda x: x - x[2021], axis=1)
    # per = per.apply(lambda x: x / x[2100], axis=1)

    per = per.droplevel("Max (Mha)")

    # endregion

    # match historical analogs to each subvector

    # region

    cw = crosswalk[["Sub-vector", "Analog Name"]]

    hist1.loc[:, 1990] = 0
    hist0 = hist1[hist1.loc[:, :2020].sum(axis=1) <= 0.0]
    hist1 = hist1[hist1.loc[:, :2020].sum(axis=1) > 0.0]
    hist0.loc[:, 2020] = 0.0
    hist1 = hist1.append(hist0)
    hist1.interpolate(axis=1, limit_area="inside", inplace=True)

    hist1 = hist1.apply(
        lambda x: pd.concat(
            [
                x.dropna(),
                pd.DataFrame(
                    [
                        per.loc[cw[cw["Sub-vector"] == x.name[1]]["Analog Name"], :]
                        .where(
                            per.loc[
                                cw[cw["Sub-vector"] == x.name[1]]["Analog Name"]
                            ].values
                            >= x.dropna().iloc[-1]
                        )
                        .dropna(axis=1)
                        .squeeze()
                        .values
                    ]
                )
                .T.set_index(
                    np.arange(
                        x.dropna().index[-1] + 1,
                        x.dropna().index[-1]
                        + 1
                        + len(
                            pd.DataFrame(
                                [
                                    per.loc[
                                        cw[cw["Sub-vector"] == x.name[1]][
                                            "Analog Name"
                                        ],
                                        :,
                                    ]
                                    .where(
                                        per.loc[
                                            cw[cw["Sub-vector"] == x.name[1]][
                                                "Analog Name"
                                            ]
                                        ].values
                                        >= x.dropna().iloc[-1]
                                    )
                                    .dropna(axis=1)
                                    .squeeze()
                                    .values
                                ]
                            ).columns
                        ),
                        1,
                    ).squeeze()
                )
                .squeeze(),
            ]
        ),
        axis=1,
    )

    hist1 = hist1.fillna(method="ffill", axis=1)

    # endregion

    # project adoption by applying s-curve growth to max extent

    adoption = hist1.multiply(max_extent2).fillna(0)

    # multiply by avg mitigation potential flux to get emissions mitigated

    adoption = adoption.multiply(flux2).fillna(0)

    # estimate emissions mitigated by avoided pathways

    # region

    avoid = (
        pd.DataFrame(
            avoided_pathways_input.drop(
                columns=[
                    "Model",
                    "Region",
                    "Initial Extent (Mha)",
                    "Mitigation (Mg CO2/ha)",
                ]
            )
        )
        .set_index(
            [
                "Scenario",
                "Country",
                "Subvector",
                "Initial Loss Rate (%)",
                "Rate of Improvement",
            ]
        )
        .loc[scenario, slice(None), slice(None), slice(None), :]
    )

    avoid = avoid / 1e6
    avoid.columns = avoid.columns.astype(int)

    """
    avoid_per = avoid.apply(lambda x: ((x[2019] - x) / x[2019]).fillna(0), axis=1)
    """

    avoid_per = (
        (
            avoid.apply(lambda x: x * 0, axis=1)
            .apply(lambda x: x + x.name[3], axis=1)
            .cumsum(axis=1)
            .apply(lambda x: -x - x.name[2], axis=1)
        )
        .clip(lower=0)
        .apply(
            lambda x: pd.Series(
                np.where(x.name[3] > 0, (-x + 1), (x * 0)), index=x.index
            ),
            axis=1,
        )
    ).clip(lower=0)

    # endregion

    # combine dfs and reformat index to regions

    # region

    adoption = adoption.append(avoid)
    hist1.loc[:, 2100] = hist1.loc[:, 2099]
    per_adoption = pd.concat([hist1, avoid_per], axis=0).fillna(0)

    co2_fw = rgroup(
        adoption.loc[
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Peat Impacts",
                "Avoided Forest Conversion",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Peat Restoration",
            ],
            :,
        ],
        "CO2",
        "Forests & Wetlands",
        "Region",
        scenario,
    )

    co2_ag = rgroup(
        adoption.loc[
            slice(None),
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Silvopasture",
                "Trees in Croplands",
            ],
            :,
        ],
        "CO2",
        "Regenerative Agriculture",
        "Region",
        scenario,
    )

    per_fw = rgroup2(
        per_adoption.loc[
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Peat Impacts",
                "Avoided Forest Conversion",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Peat Restoration",
            ],
            :,
        ],
        "CO2",
        "Forests & Wetlands",
        "Region",
        scenario,
    )

    per_ag = rgroup2(
        per_adoption.loc[
            slice(None),
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Silvopasture",
                "Trees in Croplands",
            ],
            :,
        ],
        "CO2",
        "Regenerative Agriculture",
        "Region",
        scenario,
    )

    # endregion

    # subtract from current year emissions to get emissions

    # region

    afolu_em_hist = (
        pd.read_csv("podi/data/emissions_additional.csv")
        .set_index(["Region", "Sector", "Metric", "Gas", "Scenario"])
        .loc[
            slice(None),
            ["Forests & Wetlands", "Regenerative Agriculture"],
            slice(None),
            slice(None),
            scenario,
        ]
        .groupby(["Region", "Sector"])
        .sum()
    )
    afolu_em_hist.columns = afolu_em_hist.columns.astype(int)

    afolu_em = -pd.concat([co2_fw, co2_ag]).apply(
        lambda x: x.subtract(
            afolu_em_hist.loc[x.name[0], x.name[1], :][2020].values[0]
        ),
        axis=1,
    )

    per_adoption = pd.concat([per_fw, per_ag])

    # endregion

    return afolu_em, per_adoption
