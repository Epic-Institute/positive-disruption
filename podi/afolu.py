# region

import pandas as pd
from podi.adoption_curve_afolu import adoption_curve_afolu
from numpy import NaN
import numpy as np
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel

pandarallel.initialize(nb_workers=4)

# endregion


def afolu(scenario, data_start_year, data_end_year, proj_end_year):

    # create max extent df

    # region
    tnc_input_data = pd.read_csv("podi/data/tnc_input_data.csv")

    max_extent = tnc_input_data[tnc_input_data["Metric"] == "Max extent"].drop(
        columns=["Metric", "Model", "Scenario", "iso", "Unit"]
    )

    max_extent["Duration 1 (Years)"] = np.where(
        (
            (max_extent["Duration 1 (Years)"].isna())
            | (max_extent["Duration 1 (Years)"] > proj_end_year - data_end_year)
        ),
        proj_end_year - data_end_year,
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
            max_extent["Region"],
            max_extent["Subvector"],
            max_extent["Duration 1 (Years)"],
            max_extent["Value 2"],
            max_extent["Duration 2 (Years)"],
            max_extent["Value 3"],
            max_extent["Duration 3 (Years)"],
        ],
        columns=np.arange(data_start_year, proj_end_year + 1, 1),
        dtype=float,
    )
    max_extent2.loc[:, data_start_year] = max_extent["Value 1"].values
    max_extent2.loc[:, proj_end_year] = max_extent["Value 1"].values
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

    flux = tnc_input_data[
        tnc_input_data["Metric"] == "Avg mitigation potential flux"
    ].drop(columns=["Metric", "Model", "Scenario", "iso", "Unit"])

    flux["Duration 1 (Years)"] = np.where(
        (
            (flux["Duration 1 (Years)"].isna())
            | (flux["Duration 1 (Years)"] > proj_end_year - data_end_year)
        ),
        proj_end_year - data_end_year,
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
            flux["Region"],
            flux["Subvector"],
            flux["Duration 1 (Years)"],
            flux["Value 2"],
            flux["Duration 2 (Years)"],
            flux["Value 3"],
            flux["Duration 3 (Years)"],
        ],
        columns=np.arange(data_start_year, proj_end_year + 1, 1),
        dtype=float,
    )
    flux2.loc[:, data_start_year] = flux["Value 1"].values

    flux2.interpolate(axis=1, limit_area="inside", inplace=True)

    flux2 = pd.read_csv("podi/data/tnc_flux.csv").set_index(
        [
            "Region",
            "Subvector",
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    )
    flux2.columns = flux2.columns.astype(int)
    flux2 = flux2.loc[:, :proj_end_year]

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
    hist = pd.read_csv("podi/data/tnc_hist_obs.csv").drop(
        columns=["iso", "Model", "Scenario", "Metric", "Unit"]
    )

    hist = pd.DataFrame(hist).set_index(["Region", "Subvector"])
    hist.columns = hist.columns.astype(int)
    hist = hist.loc[:, data_start_year:]
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
        .parallel_apply(
            lambda x: x.divide(
                max_extent2.loc[x.name[0], x.name[1]].loc[:data_end_year]
            ),
            axis=1,
        )
    )
    hist1 = hist1.replace(0, NaN).clip(upper=0.99)

    # endregion

    # compute adoption curves of historical analogs

    # region
    tnc_analogs = pd.read_csv("podi/data/tnc_analogs.csv")

    acurves = (
        pd.DataFrame(tnc_analogs)
        .drop(columns=["Note", "Units", "Actual start year"])
        .set_index(["Analog name", "Max (Mha)"])
    )
    acurves.columns = acurves.loc[NaN, NaN].astype(int)
    acurves.columns.rename("Year", inplace=True)
    acurves.drop(index=NaN, inplace=True)
    acurves.interpolate(axis=1, limit_area="inside", inplace=True)
    acurves = acurves.parallel_apply(lambda x: x / x.name[1], axis=1)
    acurves = acurves.parallel_apply(lambda x: x - x[1], axis=1)
    acurves.columns = np.arange(
        data_end_year + 1, data_end_year + 1 + len(acurves.columns), 1
    )

    proj_per_adoption = acurves.parallel_apply(
        lambda x: adoption_curve_afolu(
            x.dropna().rename(x.name[0]),
            x.name[0],
            scenario,
            "AFOLU",
            data_start_year,
            data_end_year,
            2100,
        ),
        axis=1,
    )

    per = []
    for i in range(0, len(proj_per_adoption.index)):
        per = pd.DataFrame(per).append(proj_per_adoption[proj_per_adoption.index[i]].T)

    per.set_index(proj_per_adoption.index, inplace=True)
    per = per.parallel_apply(lambda x: x - x[data_end_year + 1], axis=1)
    per = per.droplevel("Max (Mha)")

    # endregion

    # match historical analogs to each subvector

    # region
    cw = pd.read_csv(
        "podi/data/tnc_crosswalk.csv", usecols=["Sub-vector", "Analog Name"]
    )

    hist1.loc[:, data_start_year] = 0
    hist0 = hist1[hist1.loc[:, :data_end_year].sum(axis=1) <= 0.0]
    hist1 = hist1[hist1.loc[:, :data_end_year].sum(axis=1) > 0.0]
    hist0.loc[:, data_end_year] = 0.0
    hist1 = pd.concat([hist1, hist0])
    hist1.interpolate(axis=1, limit_area="inside", inplace=True)

    # For each historical adoption row, concatenate the corresponding historical analog
    hist1 = hist1.parallel_apply(
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
            ],
        ),
        axis=1,
    )

    hist1 = hist1.fillna(method="ffill", axis=1)

    # endregion

    # project adoption by applying s-curve growth to max extent

    # region

    adoption = hist1.parallel_apply(
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
            foo2 = foo.loc[
                :, : str(data_start_year + int(proj_end_year - adoption.columns[j]))
            ]
            foo2.columns = foo.loc[:, str(adoption.columns[j]) :].columns

            adopt_row = pd.concat([pd.DataFrame(adopt_row), foo2])

        adopt_row.iloc[0] = adopt_row.sum().values
        adoption2 = pd.concat(
            [pd.DataFrame(adoption2), pd.DataFrame(adopt_row.iloc[0]).T]
        )

    adoption = adoption2
    adoption.index.names = flux2.index.names
    adoption.columns = adoption.columns.astype(int)
    adoption = adoption.parallel_apply(
        lambda x: x.multiply(flux2.loc[x.name[0], x.name[1]].values), axis=1
    )

    # endregion

    # estimate emissions mitigated by avoided pathways

    # region
    tnc_avoided_pathways_input = pd.read_csv("podi/data/tnc_avoided_pathways_input.csv")

    avoid = (
        pd.DataFrame(
            tnc_avoided_pathways_input.drop(
                columns=[
                    "Model",
                    "Initial Extent (Mha)",
                    "Mitigation (Mg CO2/ha)",
                ]
            )
        )
        .set_index(
            [
                "Scenario",
                "Region",
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

    avoid.loc[:, :data_end_year] = 0

    avoid.loc[:, data_end_year + 1 :] = -avoid.loc[
        :, data_end_year + 1 :
    ].parallel_apply(
        lambda x: x.subtract(
            avoid.loc[x.name[0], x.name[1], x.name[2], :][data_end_year + 1].values[0]
        ),
        axis=1,
    )

    avoid_per = -avoid.parallel_apply(
        lambda x: ((x[data_end_year] - x) / x.max()).fillna(0), axis=1
    )

    """
    avoid_per = avoid.parallel_apply(lambda x: ((x[data_end_year] - x) / x[data_end_year]).fillna(0), axis=1)

    avoid_per = (
        (
            avoid.parallel_apply(lambda x: x * 0, axis=1)
            .parallel_apply(lambda x: x + x.name[3], axis=1)
            .cumsum(axis=1)
            .parallel_apply(lambda x: -x - x.name[2], axis=1)
        )
        .clip(lower=0)
        .parallel_apply(
            lambda x: pd.Series(
                np.where(x.name[3] > 0, (-x + 1), (x * 0)), index=x.index
            ),
            axis=1,
        )
    ).clip(lower=0)
    """

    # endregion

    # combine dfs and reformat index to regions

    # region

    # make placeholder for Animal Mgmt CH4
    adoption_am = pd.concat(
        [adoption.loc[slice(None), "Cropland Soil Health", :] * 0],
        keys=["Animal Mgmt"],
        names=["Subvector"],
    ).reorder_levels(["Region", "Subvector"])

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
            pd.DataFrame(adoption.loc[slice(None), [subv], :])
        )

    co2_fw = pd.concat([co2_fw], names=["Sector"], keys=["Forests & Wetlands"])
    co2_fw = pd.concat([co2_fw], names=["Scenario"], keys=[scenario])
    co2_fw = pd.concat([co2_fw], names=["Gas"], keys=["CO2"])
    co2_fw = co2_fw.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

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
            pd.DataFrame(adoption.loc[slice(None), [subv], :])
        )

    co2_ag = pd.concat([co2_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    co2_ag = pd.concat([co2_ag], names=["Scenario"], keys=[scenario])
    co2_ag = pd.concat([co2_ag], names=["Gas"], keys=["CO2"])
    co2_ag = co2_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # CH4 Agriculture

    ch4_ag = []

    for subv in ["Improved Rice", "Animal Mgmt"]:
        ch4_ag = pd.DataFrame(ch4_ag).append(
            pd.DataFrame(adoption.loc[slice(None), [subv], :])
        )

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
    ch4_ag.loc[slice(None), ["Improved Rice"], :].update(
        ch4_ag.loc[slice(None), ["Improved Rice"], :] * 0.58
    )

    ch4_ag = pd.concat([ch4_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    ch4_ag = pd.concat([ch4_ag], names=["Scenario"], keys=[scenario])
    ch4_ag = pd.concat([ch4_ag], names=["Gas"], keys=["CH4"])
    ch4_ag = ch4_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    # N2O Agriculture

    n2o_ag = []

    for subv in [
        "Improved Rice",
        "Nitrogen Fertilizer Management",
    ]:
        n2o_ag = pd.DataFrame(n2o_ag).append(
            pd.DataFrame(adoption.loc[slice(None), [subv], :])
        )

    # Improved rice mitigation is 58% from CH4 and 42% from N2O (see NCS)
    n2o_ag.loc[slice(None), ["Improved Rice"], :].update(
        n2o_ag.loc[slice(None), ["Improved Rice"], :] * 0.42
    )

    n2o_ag = pd.concat([n2o_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    n2o_ag = pd.concat([n2o_ag], names=["Scenario"], keys=[scenario])
    n2o_ag = pd.concat([n2o_ag], names=["Gas"], keys=["N2O"])
    n2o_ag = n2o_ag.reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

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
            pd.DataFrame(per_adoption.loc[slice(None), [subv], :])
        )

    per_fw = pd.concat([per_fw], names=["Sector"], keys=["Forests & Wetlands"])
    per_fw = pd.concat([per_fw], names=["Scenario"], keys=[scenario])
    per_fw = per_fw.reorder_levels(["Region", "Sector", "Subvector", "Scenario"])

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
            pd.DataFrame(per_adoption.loc[slice(None), [subv], :])
        )

    per_ag = pd.concat([per_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    per_ag = pd.concat([per_ag], names=["Scenario"], keys=[scenario])
    per_ag = per_ag.reorder_levels(["Region", "Sector", "Subvector", "Scenario"])

    # endregion

    # add mitigation to hist/projected emissions to get net emissions

    # region

    # historical emissions
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
        .groupby(["Region", "Sector", "Metric", "Gas"])
        .sum()
    )

    afolu_em_hist.columns = afolu_em_hist.columns.astype(int)
    afolu_em_hist = afolu_em_hist.loc[:, data_start_year:]

    # estimated mitigation
    afolu_em_mit = -(pd.concat([co2_fw, co2_ag, ch4_ag, n2o_ag]))
    afolu_em_mit.columns = afolu_em_mit.columns.astype(int)
    afolu_em_mit.loc[:, :data_end_year] = 0

    # shift mitigation values by data_end_year+1 value
    afolu_em_mit = afolu_em_mit.parallel_apply(
        lambda x: x.subtract(
            (
                afolu_em_mit.loc[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]
                .loc[:, data_end_year + 1]
                .values[0]
            )
        ),
        axis=1,
    ).clip(upper=0)

    # combine emissions and mitigation

    afolu_em = (
        pd.concat(
            [
                afolu_em_mit.groupby(["Region", "Sector", "Subvector", "Gas"]).sum(),
                afolu_em_hist,
            ]
        )
        .groupby(["Region", "Sector", "Subvector", "Gas"])
        .sum()
    )

    afolu_em = pd.concat(
        [afolu_em], names=["Scenario"], keys=[scenario]
    ).reorder_levels(["Region", "Sector", "Subvector", "Gas", "Scenario"])

    per_adoption = pd.concat([per_fw, per_ag])

    # endregion

    if scenario == "baseline":
        afolu_em.loc[:, data_end_year:] = curve_smooth(
            afolu_em.loc[:, data_end_year:], "linear", 1
        )

    # create 16 region df for max extent

    max_extent3 = []

    for subv in [
        "Biochar",
        "Cropland Soil Health",
        "Improved Rice",
        "Nitrogen Fertilizer Management",
        "Optimal Intensity",
        "Silvopasture",
        "Trees in Croplands",
    ]:
        max_extent3 = pd.DataFrame(max_extent3).append(
            pd.DataFrame(max_extent2.loc[slice(None), [subv], :])
        )

    max_extent3 = pd.concat(
        [max_extent3], names=["Sector"], keys=["Regenerative Agriculture"]
    )
    max_extent3 = pd.concat([max_extent3], names=["Scenario"], keys=[scenario])
    max_extent3 = pd.concat([max_extent3], names=["Gas"], keys=["CO2"])
    max_extent3 = max_extent3.reorder_levels(
        ["Region", "Sector", "Subvector", "Gas", "Scenario"]
    )

    max_extent4 = []

    for subv in [
        "Coastal Restoration",
        "Improved Forest Mgmt",
        "Natural Regeneration",
        "Peat Restoration",
    ]:
        max_extent4 = pd.DataFrame(max_extent4).append(
            pd.DataFrame(max_extent2.loc[slice(None), [subv], :])
        )

    max_extent4 = pd.concat(
        [max_extent4], names=["Sector"], keys=["Forests & Wetlands"]
    )
    max_extent4 = pd.concat([max_extent4], names=["Scenario"], keys=[scenario])
    max_extent4 = pd.concat([max_extent4], names=["Gas"], keys=["CO2"])
    max_extent4 = max_extent4.reorder_levels(
        ["Region", "Sector", "Subvector", "Gas", "Scenario"]
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
        ]
        .parallel_apply(
            lambda x: x.multiply(
                pd.concat([max_extent3, max_extent4]).loc[
                    x.name[0], x.name[1], x.name[2]
                ]
            ),
            axis=1,
        )
        .fillna(0)
    )

    return afolu_em, per_adoption, per_max
