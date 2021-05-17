#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
import numpy as np
from podi.energy_supply import long_proj_end_year
from podi.curve_smooth import curve_smooth

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
            max_extent["Value 3"],
            max_extent["Duration 3 (Years)"],
        ],
        columns=np.arange(1990, long_proj_end_year + 1, 1),
        dtype=float,
    )
    max_extent2.loc[:, 1990] = max_extent["Value 1"].values
    max_extent2.loc[:, 2100] = max_extent["Value 1"].values
    max_extent2.interpolate(axis=1, limit_area="inside", inplace=True)
    max_extent2 = max_extent2.droplevel(
        [
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    )

    # update Improved Forest Mgmt max extent units for consistency (m^3 to Mha)
    max_extent2.loc[slice(None), "Improved Forest Mgmt", :] = (
        max_extent2.loc[slice(None), "Improved Forest Mgmt", :] / 1e3
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
            flux["Value 3"],
            flux["Duration 3 (Years)"],
        ],
        columns=np.arange(1990, long_proj_end_year + 1, 1),
        dtype=float,
    )
    flux2.loc[:, 1990] = flux["Value 1"].values

    flux2.interpolate(axis=1, limit_area="inside", inplace=True)

    flux2 = pd.read_csv("podi/data/tnc_flux.csv").set_index(
        [
            "Country",
            "Subvector",
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    )

    flux2 = flux2.droplevel(
        [
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    ).fillna(0)

    # flux2 = curve_smooth(flux2, "quadratic", 10)

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
    hist1 = hist1.replace(0, NaN).clip(upper=0.99)

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

    # region

    adoption = hist1.apply(
        lambda x: x.multiply(max_extent2.loc[x.name[0], x.name[1]]), axis=1
    ).fillna(0)

    # endregion

    # multiply by avg mitigation potential flux to get emissions mitigated

    # region

    adoption = adoption.apply(
        lambda x: x.multiply(flux2.loc[x.name[0], x.name[1]].values), axis=1
    )

    # endregion

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

    avoid.loc[:, :2019] = 0
    avoid.loc[:, 2020:] = avoid.loc[:, 2020:].apply(
        lambda x: x.subtract(
            avoid.loc[x.name[0], x.name[1], x.name[2], :][2020].values[0]
        ),
        axis=1,
    )

    avoid_per = avoid.apply(lambda x: ((x[2019] - x) / x[2019]).fillna(0), axis=1)

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

    # make placeholder for Animal Mgmt CH4, N Fertilizer Mgmt
    adoption_am = pd.concat(
        [adoption.loc[slice(None), "Cropland Soil Health", :] * 0],
        keys=["Animal Mgmt"],
        names=["Subvector"],
    ).reorder_levels(["Country", "Subvector"])

    adoption_n = pd.concat(
        [adoption.loc[slice(None), "Cropland Soil Health", :] * 0],
        keys=["N Fertilizer Mgmt"],
        names=["Subvector"],
    ).reorder_levels(["Country", "Subvector"])

    adoption = adoption.append(adoption_am).append(adoption_n).append(avoid)
    hist1.loc[:, 2100] = hist1.loc[:, 2099]
    per_adoption = pd.concat([hist1, avoid_per], axis=0).fillna(0)

    # CO2 F&W (F&W only has CO2 at this point)

    co2_fw = []

    for subv in [
        "Avoided Coastal Impacts",
        "Avoided Peat Impacts",
        "Avoided Forest Conversion",
        "Coastal Restoration",
        "Improved Forest Mgmt",
        "Natural Regeneration",
        "Peat Restoration",
    ]:
        co2_fw = pd.DataFrame(co2_fw).append(
            pd.DataFrame(
                rgroup(
                    adoption.loc[slice(None), subv, :], "CO2", subv, "Region", scenario
                )
            )
        )

    co2_fw.index = co2_fw.index.droplevel("Sector")
    co2_fw = pd.concat([co2_fw], names=["Sector"], keys=["Forests & Wetlands"])
    co2_fw = co2_fw.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    co2_fw = pd.concat([co2_fw], names=["Gas"], keys=["CO2"])
    co2_fw = co2_fw.reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

    # CO2 Agriculture

    co2_ag = []

    for subv in [
        "Biochar",
        "Cropland Soil Health",
        "Optimal Intensity",
        "Silvopasture",
        "Trees in Croplands",
    ]:
        co2_ag = pd.DataFrame(co2_ag).append(
            pd.DataFrame(
                rgroup(
                    adoption.loc[slice(None), subv, :], "CO2", subv, "Region", scenario
                )
            )
        )

    co2_ag.index = co2_ag.index.droplevel("Sector")
    co2_ag = pd.concat([co2_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    co2_ag = co2_ag.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    co2_ag = pd.concat([co2_ag], names=["Gas"], keys=["CO2"])
    co2_ag = co2_ag.reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

    # CH4 Agriculture

    ch4_ag = []

    for subv in ["Improved Rice", "Animal Mgmt"]:
        ch4_ag = pd.DataFrame(ch4_ag).append(
            pd.DataFrame(
                rgroup(
                    adoption.loc[slice(None), subv, :], "CH4", subv, "Region", scenario
                )
            )
        )

    # Improved rice is 58% CH4 and 42% N2O
    ch4_ag.loc[slice(None), slice(None), "Improved Rice", scenario] = (
        ch4_ag.loc[slice(None), slice(None), "Improved Rice", scenario] * 0.58
    ).values

    ch4_ag.index = ch4_ag.index.droplevel("Sector")
    ch4_ag = pd.concat([ch4_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    ch4_ag = ch4_ag.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    ch4_ag = pd.concat([ch4_ag], names=["Gas"], keys=["CH4"])
    ch4_ag = ch4_ag.reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

    # N2O Agriculture

    n2o_ag = []

    for subv in [
        "Improved Rice",
        # "Nitrogen Fertilizer Management",
    ]:
        n2o_ag = pd.DataFrame(n2o_ag).append(
            pd.DataFrame(
                rgroup(
                    adoption.loc[slice(None), subv, :], "N2O", subv, "Region", scenario
                )
            )
        )

    # Improved rice is 58% CH4 and 42% N2O
    n2o_ag.loc[slice(None), slice(None), "Improved Rice", scenario] = (
        n2o_ag.loc[slice(None), slice(None), "Improved Rice", scenario] * 0.42
    ).values

    n2o_ag.index = n2o_ag.index.droplevel("Sector")
    n2o_ag = pd.concat([n2o_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    n2o_ag = n2o_ag.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    n2o_ag = pd.concat([n2o_ag], names=["Gas"], keys=["N2O"])
    n2o_ag = n2o_ag.reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

    per_fw = []

    for subv in [
        "Avoided Coastal Impacts",
        "Avoided Peat Impacts",
        "Avoided Forest Conversion",
        "Coastal Restoration",
        "Improved Forest Mgmt",
        "Natural Regeneration",
        "Peat Restoration",
    ]:
        per_fw = pd.DataFrame(per_fw).append(
            pd.DataFrame(
                rgroup2(
                    per_adoption.loc[slice(None), subv, :],
                    "CO2",
                    subv,
                    "Region",
                    scenario,
                )
            )
        )

    per_fw.index = per_fw.index.droplevel("Sector")
    per_fw = pd.concat([per_fw], names=["Sector"], keys=["Forests & Wetlands"])
    per_fw = per_fw.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    per_ag = []

    for subv in [
        "Biochar",
        "Cropland Soil Health",
        "Improved Rice",
        # "Nitrogen Fertilizer Management",
        "Optimal Intensity",
        "Silvopasture",
        "Trees in Croplands",
    ]:
        per_ag = pd.DataFrame(per_ag).append(
            pd.DataFrame(
                rgroup2(
                    per_adoption.loc[slice(None), subv, :],
                    "CO2",
                    subv,
                    "Region",
                    scenario,
                )
            )
        )

    per_ag.index = per_ag.index.droplevel("Sector")
    per_ag = pd.concat([per_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    per_ag = per_ag.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

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
        .groupby(["Region", "Sector", "Gas"])
        .sum()
    )
    afolu_em_hist.columns = afolu_em_hist.columns.astype(int)

    afolu_em = (
        -pd.concat([co2_fw, co2_ag, ch4_ag, n2o_ag])
        .groupby(["Region", "Sector", "Gas"])
        .sum()
        .apply(
            lambda x: x.add(
                afolu_em_hist.loc[x.name[0], x.name[1], x.name[2], :][2020].values[0]
            ),
            axis=1,
        )
    )

    afolu_em = pd.concat(
        [afolu_em], names=["Scenario"], keys=[scenario]
    ).reorder_levels(["Region", "Sector", "Gas", "Scenario"])

    per_adoption = pd.concat([per_fw, per_ag])

    # endregion

    # smooth from jumps in avg mitigation flux
    """
    if scenario == 'baseline':
        afolu_em = curve_smooth(afolu_em, "quadratic", 3)
        per_adoption = curve_smooth(per_adoption, "quadratic", 3)
    """
    """
    # add in Mariculture estimate

    # region
   
    afolu_em = pd.concat(
        [
            afolu_em,
            pd.DataFrame(afolu_em.loc["World ", "Forests & Wetlands"]).T.rename(
                index={"Forests & Wetlands": "Mariculture"}
            ),
        ]
    )

    if scenario == "baseline":
        afolu_em.loc["World ", "Mariculture"] = (
            afolu_em.loc["World ", "Mariculture"] * 0
        )
    else:
        afolu_em.loc["World ", "Mariculture"] = (
            per_adoption.loc[
                "World ", "Forests & Wetlands", "Coastal Restoration", "pathway"
            ].values
            * -290
        )

    # endregion
    """
    return afolu_em, per_adoption
