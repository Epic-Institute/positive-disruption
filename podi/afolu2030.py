# region

from podi.afolu import afolu
import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
import numpy as np
from podi.energy_supply import long_proj_end_year, data_end_year
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


# endregion


def afolu2030(scenario):
    input_data_3 = pd.read_csv("podi/data/tnc_input_data_3_2030.csv")
    avoided_pathways_input = pd.read_csv(
        "podi/data/tnc_avoided_pathways_input_2030.csv"
    )
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
            | (max_extent["Duration 1 (Years)"] > 2300 - 2019)
        ),
        2300 - 2019,
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
        columns=np.arange(1990, 2300 + 1, 1),
        dtype=float,
    )
    max_extent2.loc[:, 1990] = max_extent["Value 1"].values
    max_extent2.loc[:, 2300] = max_extent["Value 1"].values
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

    # endregion

    # create avg mitigation potential flux df

    # region

    flux = input_data_3[input_data_3["Metric"] == "Avg mitigation potential flux"].drop(
        columns=["Metric", "Model", "Scenario", "Region", "iso", "Unit"]
    )

    flux["Duration 1 (Years)"] = np.where(
        (
            (flux["Duration 1 (Years)"].isna())
            | (flux["Duration 1 (Years)"] > 2300 - 2019)
        ),
        2300 - 2019,
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
        columns=np.arange(1990, 2300 + 1, 1),
        dtype=float,
    )
    flux2.loc[:, 1990] = flux["Value 1"].values

    flux2.interpolate(axis=1, limit_area="inside", inplace=True)

    flux2 = pd.read_csv("podi/data/tnc_flux_2030.csv").set_index(
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
                "Nitrogen Fertilizer Management",
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

    per2 = pd.DataFrame(columns=np.arange(2101, 2301, 1), index=per.index)
    per2.columns = per2.columns.astype(int)
    per2 = per2.astype(float)
    per2.loc[:, 2300] = per.loc[:, 2100]
    per2.loc[:, 2101] = per.loc[:, 2100]
    per2.interpolate(axis=1, limit_area="inside", inplace=True)
    per = per.join(per2)

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

    adoption2 = []

    for i in range(0, len(adoption)):
        adopt_row = []
        for j in range(0, len(adoption.iloc[i])):
            foo = pd.DataFrame(
                flux2.loc[adoption.index[i][0], adoption.index[i][1]]
            ).T * (adoption.iloc[i, j] - adoption.iloc[i, max(0, j - 1)])
            foo2 = foo.loc[:, : str(1990 + int(2300 - adoption.columns[j]))]
            foo2.columns = foo.loc[:, str(adoption.columns[j]) :].columns

            adopt_row = pd.DataFrame(adopt_row).append(foo2)

        adopt_row.iloc[0] = adopt_row.sum().values
        adoption2 = pd.DataFrame(adoption2).append(pd.DataFrame(adopt_row.iloc[0]).T)

    adoption = adoption2
    adoption.index.names = flux2.index.names
    adoption.columns = adoption.columns.astype(int)

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

    avoid.loc[:, "Avoided Forest Conversion", :] = (
        avoid.loc[:, "Avoided Forest Conversion", :] / 1e1
    ).values

    avoid.columns = avoid.columns.astype(int)

    avoid.loc[:, :2019] = 0

    avoid.loc[:, 2020:] = -avoid.loc[:, 2020:].apply(
        lambda x: x.subtract(
            avoid.loc[x.name[0], x.name[1], x.name[2], :][2020].values[0]
        ),
        axis=1,
    )

    avoid_per = -avoid.apply(lambda x: ((x[2019] - x) / x.max()).fillna(0), axis=1)

    avoid.loc[:, 2077:] = avoid.loc[:, 2077].values[:, None]

    # endregion

    # combine dfs and reformat index to regions

    # region

    # make placeholder for Animal Mgmt CH4
    adoption_am = pd.concat(
        [adoption.loc[slice(None), "Cropland Soil Health", :] * 0],
        keys=["Animal Mgmt"],
        names=["Subvector"],
    ).reorder_levels(["Country", "Subvector"])

    adoption = adoption.append(adoption_am).append(avoid)
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

    """
    co2_fw.loc[
        slice(None), "Forests & Wetlands", "Natural Regeneration"
    ] = curve_smooth(
        co2_fw.loc[slice(None), "Forests & Wetlands", "Natural Regeneration"],
        "quadratic",
        3,
    ).values
    """
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

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
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
        "Nitrogen Fertilizer Management",
    ]:
        n2o_ag = pd.DataFrame(n2o_ag).append(
            pd.DataFrame(
                rgroup(
                    adoption.loc[slice(None), subv, :], "N2O", subv, "Region", scenario
                )
            )
        )

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
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
        "Nitrogen Fertilizer Management",
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

    # add mitigation to hist/projected emissions to get net emissions

    # region

    # historical emissions
    afolu_em_hist = (
        pd.read_csv("podi/data/emissions_additional_2030.csv")
        .set_index(["Region", "Sector", "Metric", "Gas", "Scenario"])
        .loc[
            slice(None),
            ["Forests & Wetlands", "Regenerative Agriculture"],
            slice(None),
            slice(None),
            scenario,
        ]
        .groupby(["Region", "Sector", "Metric", "Gas"])
        .sum()
    )

    afolu_em_hist.columns = afolu_em_hist.columns.astype(int)
    afolu_em_hist = afolu_em_hist.loc[:, 1990:]

    # estimated mitigation
    afolu_em_mit = -(pd.concat([co2_fw, co2_ag, ch4_ag, n2o_ag]))
    afolu_em_mit.columns = afolu_em_mit.columns.astype(int)
    afolu_em_mit.loc[:, :2019] = 0

    # shift mitigation values by 2020 value
    afolu_em_mit = afolu_em_mit.apply(
        lambda x: x.subtract(
            (
                afolu_em_mit.loc[
                    x.name[0], x.name[1], x.name[2], x.name[3], x.name[4], :
                ]
                .loc[:, 2020]
                .values[0]
            )
        ),
        axis=1,
    ).clip(upper=0)

    # combine emissions and mitigation

    afolu_em = (
        pd.concat(
            [
                afolu_em_mit.groupby(["Region", "Sector", "Metric", "Gas"]).sum(),
                afolu_em_hist,
            ]
        )
        .groupby(["Region", "Sector", "Metric", "Gas"])
        .sum()
    )

    afolu_em = pd.concat(
        [afolu_em], names=["Scenario"], keys=[scenario]
    ).reorder_levels(["Region", "Sector", "Metric", "Gas", "Scenario"])

    per_adoption = pd.concat([per_fw, per_ag])

    # endregion

    if scenario == "baseline":
        afolu_em.loc[:, 2019:] = curve_smooth(afolu_em.loc[:, 2019:], "linear", 1)

    # create 16 region df for max extent

    # region

    max_extent3 = []

    for subv in [
        "Biochar",
        "Coastal Restoration",
        "Cropland Soil Health",
        "Improved Forest Mgmt",
        "Improved Rice",
        "Natural Regeneration",
        "Nitrogen Fertilizer Management",
        "Optimal Intensity",
        "Peat Restoration",
        "Silvopasture",
        "Trees in Croplands",
    ]:
        max_extent3 = pd.DataFrame(max_extent3).append(
            pd.DataFrame(
                rgroup(
                    max_extent2.loc[slice(None), subv, :],
                    "CO2",
                    subv,
                    "Region",
                    scenario,
                )
            )
        )

    max_extent3.index = max_extent3.index.droplevel("Sector")
    max_extent3 = pd.concat(
        [max_extent3], names=["Sector"], keys=["Regenerative Agriculture"]
    )
    max_extent3 = max_extent3.reorder_levels(["Region", "Sector", "Metric", "Scenario"])

    max_extent3 = pd.concat([max_extent3], names=["Gas"], keys=["CO2"])
    max_extent3 = max_extent3.reorder_levels(
        ["Region", "Sector", "Metric", "Gas", "Scenario"]
    )

    per_max = (
        per_adoption.loc[
            slice(None),
            slice(None),
            [
                "Biochar",
                "Coastal Restoration",
                "Cropland Soil Health",
                "Improved Forest Mgmt",
                "Improved Rice",
                "Natural Regeneration",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Peat Restoration",
                "Silvopasture",
                "Trees in Croplands",
            ],
            scenario,
            :,
        ]
        .apply(
            lambda x: x.multiply(
                max_extent3.loc[x.name[0], slice(None), x.name[2]].values[0]
            ),
            axis=1,
        )
        .fillna(0)
    )

    # endregion

    # accelerate so 2030 is max

    # region

    accel = 5

    # RA-mx2030
    ra_mx2030 = True

    # region

    if ra_mx2030 is True:
        afolu_em_alt = (
            afolu_em.loc[
                slice(None),
                slice(None),
                [
                    "Biochar",
                    "Cropland Soil Health",
                    "Improved Rice",
                    "Nitrogen Fertilizer Management",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Trees in Croplands",
                    "Animal Mgmt",
                ],
                slice(None),
            ]
            .loc[:, data_end_year + 1 :]
            .loc[:, ::accel]
        )
        afolu_em_alt.columns = np.arange(2020, 2077, 1)

        afolu_em_alt2 = afolu_em_alt.apply(
            lambda x: x[x.index <= x.idxmin(axis=1)], axis=1
        )

        afolu_em_alt3 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Silvopasture",
                "Trees in Croplands",
                "Animal Mgmt",
            ],
            slice(None),
        ].apply(lambda x: x[x.index > x.idxmin(axis=1)], axis=1)

        afolu_em_alt4 = afolu_em_alt2.apply(
            lambda x: np.concatenate(
                [
                    x.values,
                    afolu_em_alt3.loc[
                        x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]
                    ]
                    .dropna()
                    .values,
                ]
            ),
            axis=1,
        )

        afolu_em_alt5 = []

        for i in range(0, len(afolu_em_alt4)):
            this = pd.DataFrame(afolu_em_alt4[i]).T
            afolu_em_alt5 = pd.DataFrame(afolu_em_alt5).append(this)

        afolu_em_alt5 = afolu_em_alt5.loc[:, :80]
        afolu_em_alt5.columns = np.arange(2020, 2101, 1)
        afolu_em_alt5.interpolate(axis=1, inplace=True, limit_area="inside")

        afolu_em_alt6 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Silvopasture",
                "Trees in Croplands",
                "Animal Mgmt",
            ],
            slice(None),
        ].loc[:, :2100]

        afolu_em_alt6.loc[:, 2020:2100] = afolu_em_alt5.loc[:, 2020:2100].values
    else:
        afolu_em_alt6 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Optimal Intensity",
                "Silvopasture",
                "Trees in Croplands",
                "Animal Mgmt",
            ],
            slice(None),
        ].loc[:, :2100]

    # endregion

    # FW-mx2030
    fw_mx2030 = True

    # region

    if fw_mx2030 is True:
        afolu_em_alt = (
            afolu_em.loc[
                slice(None),
                slice(None),
                [
                    "Avoided Coastal Impacts",
                    "Avoided Forest Conversion",
                    "Avoided Peat Impacts",
                    "Coastal Restoration",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Peat Restoration",
                ],
                slice(None),
            ]
            .loc[:, data_end_year + 1 :]
            .loc[:, ::accel]
        )
        afolu_em_alt.columns = np.arange(2020, 2077, 1)

        afolu_em_alt2 = afolu_em_alt.apply(
            lambda x: x[x.index <= x.idxmin(axis=1)], axis=1
        )

        afolu_em_alt3 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Peat Restoration",
            ],
            slice(None),
        ].apply(lambda x: x[x.index > x.idxmin(axis=1)], axis=1)

        afolu_em_alt4 = afolu_em_alt2.apply(
            lambda x: np.concatenate(
                [
                    x.values,
                    afolu_em_alt3.loc[
                        x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]
                    ]
                    .dropna()
                    .values,
                ]
            ),
            axis=1,
        )

        afolu_em_alt5 = []

        for i in range(0, len(afolu_em_alt4)):
            this = pd.DataFrame(afolu_em_alt4[i]).T
            afolu_em_alt5 = pd.DataFrame(afolu_em_alt5).append(this)

        afolu_em_alt5 = afolu_em_alt5.loc[:, :80]
        afolu_em_alt5.columns = np.arange(2020, 2101, 1)
        afolu_em_alt5.interpolate(axis=1, inplace=True, limit_area="inside")

        afolu_em_alt7 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Peat Restoration",
            ],
            slice(None),
        ].loc[:, :2100]

        afolu_em_alt7.loc[:, 2020:2100] = afolu_em_alt5.loc[:, 2020:2100].values
    else:
        afolu_em_alt7 = afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Peat Restoration",
            ],
            slice(None),
        ].loc[:, :2100]

    # endregion

    afolu_em2 = (
        afolu_em.loc[
            slice(None),
            slice(None),
            [
                "Deforestation",
                "3B_Manure-management",
                "3D_Rice-Cultivation",
                "3D_Soil-emissions",
                "3E_Enteric-fermentation",
                "3I_Agriculture-other",
            ],
            slice(None),
        ]
        .loc[:, :2100]
        .append(afolu_em_alt6)
        .append(afolu_em_alt7)
    )

    # old method, assume same saturation
    """
    afolu_em_end = afolu_em.loc[:, 2077:2100] * 0
    afolu_em_end.loc[:, :] = afolu_em_alt.iloc[:, -1].values[:, None]
    afolu_em_alt = (
        pd.DataFrame(afolu_em.loc[:, :data_end_year])
        .join(afolu_em_alt)
        .join(afolu_em_end)
    )
    afolu_em2 = afolu_em_alt
    """

    per_adoption = per_adoption.loc[:, :2100]
    per_max = per_max.loc[:, 2100]

    # endregion

    return afolu_em2, per_adoption, per_max
