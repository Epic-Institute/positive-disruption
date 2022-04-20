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

    ##################################
    #  LOAD HISTORICAL NCS ADOPTION  #
    ##################################

    # region

    # Load historical data of subvertical adoption (as % of max extent)

    afolu_historical = (
        pd.DataFrame(pd.read_csv("podi/data/afolu_historical.csv"))
        .drop(columns=["Region", "Model", "Scenario", "Metric", "Unit"])
        .set_index(["ISO", "Subvector"])
    )

    afolu_historical.columns = afolu_historical.columns.astype(int)
    afolu_historical = afolu_historical.loc[:, data_start_year:]
    afolu_historical.interpolate(axis=1, limit_area="inside", inplace=True)

    # Create a timeseries of maximum extent of each subvertical

    # region
    max_extent = pd.read_csv(
        "podi/data/afolu_max_extent_and_flux.csv",
        usecols=[
            "ISO",
            "Subvector",
            "Metric",
            "Value 1",
            "Value 2",
            "Value 3",
            "Duration 1 (Years)",
            "Duration 2 (Years)",
            "Duration 3 (Years)",
        ],
    )

    max_extent = max_extent[max_extent["Metric"] == "Max extent"]

    max_extent["Value 2"] = np.where(
        max_extent["Value 2"].isna(), max_extent["Value 1"], max_extent["Value 2"]
    )

    max_extent["Value 3"] = np.where(
        max_extent["Value 3"].isna(), max_extent["Value 2"], max_extent["Value 3"]
    )

    max_extent["Duration 1 (Years)"] = np.where(
        (
            (max_extent["Duration 1 (Years)"].isna())
            | (max_extent["Duration 1 (Years)"] > proj_end_year - data_end_year)
        ),
        proj_end_year - data_end_year,
        max_extent["Duration 1 (Years)"],
    )

    max_extent["Duration 2 (Years)"] = np.where(
        (max_extent["Duration 2 (Years)"].isna()),
        max_extent["Duration 1 (Years)"],
        max_extent["Duration 2 (Years)"],
    )

    max_extent["Duration 3 (Years)"] = np.where(
        max_extent["Duration 3 (Years)"].isna(),
        max_extent["Duration 2 (Years)"],
        max_extent["Duration 3 (Years)"],
    )

    max_extent = pd.DataFrame(
        index=[
            max_extent["ISO"],
            max_extent["Subvector"],
            max_extent["Value 1"],
            max_extent["Duration 1 (Years)"],
            max_extent["Value 2"],
            max_extent["Duration 2 (Years)"],
            max_extent["Value 3"],
            max_extent["Duration 3 (Years)"],
        ],
        columns=np.arange(data_start_year, proj_end_year + 1, 1),
        dtype=float,
    )

    def rep(x):
        x0 = x
        x0.loc[data_start_year] = x.name[2]
        x0.loc[data_start_year + x.name[3]] = x.name[4]
        x0.loc[data_start_year + x.name[3] + x.name[5]] = x.name[6]
        x0.interpolate(axis=0, limit_area="inside", inplace=True)
        x.update(x0)
        return x

    max_extent.update(max_extent.apply(rep, result_type="broadcast", axis=1))

    max_extent = max_extent.droplevel(
        [
            "Value 1",
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    ).fillna(0)

    # endregion

    # Change units to percent adoption
    afolu_historical = (
        (
            afolu_historical.loc[
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
                lambda x: x.divide(max_extent.loc[x.name[0], x.name[1]]),
                axis=1,
            )
        )
        .replace(0, NaN)
        .clip(upper=0.99)
    )

    # endregion

    ####################################
    #  ESTIMATE BASELINE NCS ADOPTION  #
    ####################################

    # region

    afolu = pd.concat(
        [afolu_historical.fillna(method="ffill", axis=1)],
        keys=["baseline"],
        names=["Scenario"],
    )

    # endregion

    ##################################
    #  ESTIMATE PATHWAY NCS ADOPTION #
    ##################################

    # region

    # Create a timeseries of average mitigation potential flux of each subvertical

    # region

    flux = pd.read_csv(
        "podi/data/afolu_max_extent_and_flux.csv",
        usecols=[
            "ISO",
            "Subvector",
            "Metric",
            "Value 1",
            "Value 2",
            "Value 3",
            "Duration 1 (Years)",
            "Duration 2 (Years)",
            "Duration 3 (Years)",
        ],
    )

    flux = flux[flux["Metric"] == "Avg mitigation potential flux"]

    flux["Value 2"] = np.where(flux["Value 2"].isna(), flux["Value 1"], flux["Value 2"])

    flux["Value 3"] = np.where(flux["Value 3"].isna(), flux["Value 2"], flux["Value 3"])

    flux["Duration 1 (Years)"] = np.where(
        (
            (flux["Duration 1 (Years)"].isna())
            | (flux["Duration 1 (Years)"] > proj_end_year - data_start_year)
        ),
        proj_end_year - data_start_year,
        flux["Duration 1 (Years)"],
    )

    flux["Duration 2 (Years)"] = np.where(
        (flux["Duration 2 (Years)"].isna())
        | (
            flux["Duration 2 (Years)"] + flux["Duration 1 (Years)"]
            > proj_end_year - data_start_year
        ),
        proj_end_year - data_start_year - flux["Duration 1 (Years)"],
        flux["Duration 2 (Years)"],
    )

    flux["Duration 3 (Years)"] = np.where(
        (flux["Duration 3 (Years)"].isna())
        | (
            flux["Duration 3 (Years)"]
            + flux["Duration 2 (Years)"]
            + flux["Duration 1 (Years)"]
            > proj_end_year - data_start_year
        ),
        proj_end_year
        - data_start_year
        - flux["Duration 1 (Years)"]
        - flux["Duration 2 (Years)"],
        flux["Duration 3 (Years)"],
    )

    flux = pd.DataFrame(
        index=[
            flux["ISO"],
            flux["Subvector"],
            flux["Value 1"],
            flux["Duration 1 (Years)"],
            flux["Value 2"],
            flux["Duration 2 (Years)"],
            flux["Value 3"],
            flux["Duration 3 (Years)"],
        ],
        columns=np.arange(data_start_year, proj_end_year + 1, 1),
        dtype=float,
    )

    def rep(x):
        x0 = x
        x0.loc[data_start_year] = x.name[2]
        x0.loc[data_start_year + x.name[3]] = x.name[4]
        x0.loc[data_start_year + x.name[3] + x.name[5]] = x.name[6]
        x0.interpolate(axis=0, limit_area="inside", inplace=True)
        x.update(x0)
        return x

    flux.update(flux.apply(rep, result_type="broadcast", axis=1))

    flux = flux.droplevel(
        [
            "Value 1",
            "Duration 1 (Years)",
            "Value 2",
            "Duration 2 (Years)",
            "Value 3",
            "Duration 3 (Years)",
        ]
    ).fillna(0)

    # endregion

    # Compute adoption curves of the set of historical analogs that have been supplied to estimate the potential future growth of subverticals

    # region
    afolu_analogs = (
        pd.DataFrame(pd.read_csv("podi/data/afolu_analogs.csv"))
        .drop(columns=["Note", "Units", "Actual start year"])
        .set_index(["Analog name", "Max (Mha)"])
    )
    afolu_analogs.columns.rename("Year", inplace=True)
    afolu_analogs.interpolate(axis=1, limit_area="inside", inplace=True)
    afolu_analogs = afolu_analogs.parallel_apply(
        lambda x: x / x.name[1], axis=1
    ).parallel_apply(lambda x: x - x.min(), axis=1)
    afolu_analogs.columns = np.arange(
        data_end_year - 10, data_end_year - 10 + len(afolu_analogs.columns), 1
    )
    afolu_analogs = pd.concat(
        [
            pd.DataFrame(
                index=afolu_analogs.index,
                columns=np.arange(data_start_year, data_end_year - 10, 1),
            ).fillna(0),
            afolu_analogs,
        ],
        axis=1,
    )

    parameters = pd.read_csv(
        "podi/data/tech_parameters_afolu.csv",
        usecols=["Product", "Metric", "Value"],
    ).set_index(["Product", "Metric"])
    parameters = parameters.sort_index()

    afolu_analogs = afolu_analogs.parallel_apply(
        lambda x: adoption_curve(
            parameters.loc[x.name[0]],
            x,
            scenario,
            data_start_year,
            data_end_year,
            proj_end_year,
        ),
        axis=1,
    ).droplevel("Max (Mha)")

    # endregion

    # Match historical analogs to each subvertical

    # region
    subvector = pd.DataFrame(
        pd.read_csv(
            "podi/data/afolu_categories.csv", usecols=["Subvector", "Analog Name"]
        )
    ).set_index(["Subvector"])

    afolu = (
        (
            afolu.reset_index()
            .set_index(["Subvector"])
            .merge(subvector, left_on="Subvector", right_on="Subvector")
        )
        .set_index(["Scenario", "ISO", "Analog Name"], append=True)
        .reorder_levels(["Scenario", "ISO", "Subvector", "Analog Name"])
    ).rename(index={"baseline": scenario})

    afolu.loc[:, data_start_year] = 0
    afolu0 = afolu[afolu.loc[:, :data_end_year].sum(axis=1) <= 0.0]
    afolu = afolu[afolu.loc[:, :data_end_year].sum(axis=1) > 0.0]
    afolu0.loc[:, data_end_year] = 0.0
    afolu = pd.concat([afolu, afolu0])
    afolu.interpolate(axis=1, limit_area="inside", inplace=True)
    afolu_baseline = afolu
    # Join with historical data at point where projection curve results in smooth growth

    def rep(x):
        x0 = x
        x0 = x0.update(
            afolu_analogs.loc[x.name[3]][
                afolu_analogs.loc[x.name[3]] >= x.loc[data_end_year]
            ]
            .subtract(
                afolu_analogs.loc[x.name[3]][
                    afolu_analogs.loc[x.name[3]] >= x.loc[data_end_year]
                ]
                .squeeze()
                .min()
                - x.loc[data_end_year + 1]
            )
            .rename(x.name)
        )
        x.update(x0)
        return x

    afolu.update(afolu.apply(rep, result_type="broadcast", axis=1))
    afolu = afolu.droplevel("Analog Name")
    afolu_percent = afolu
    # endregion

    # Multiply this by the estimated maximum extent and average mitigation potential flux to get emissions mitigated
    afolu.update(
        afolu.parallel_apply(
            lambda x: x.multiply(max_extent.loc[x.name[1], x.name[2]]).multiply(
                flux.loc[x.name[1], x.name[2]]
            ),
            axis=1,
        ).fillna(0)
    )

    # Estimate emissions mitigated by avoided pathways

    # region
    avoided = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_avoided_pathways_input.csv").drop(
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

    avoided.loc[:, "Avoided Forest Conversion", :] = (
        avoided.loc[:, "Avoided Forest Conversion", :] / 1e1
    ).values

    avoided.columns = avoided.columns.astype(int)

    avoided = avoided.loc[:, :proj_end_year]

    avoided.loc[:, :data_end_year] = 0

    avoided.loc[:, data_end_year + 1 :] = -avoided.loc[
        :, data_end_year + 1 :
    ].parallel_apply(
        lambda x: x.subtract(
            avoided.loc[x.name[0], x.name[1], x.name[2], :][data_end_year + 1].values[0]
        ),
        axis=1,
    )

    avoided_per = -avoided.parallel_apply(
        lambda x: ((x[data_end_year] - x) / x.max()).fillna(0), axis=1
    )
    avoided = avoided.droplevel(
        [
            "Initial Loss Rate (%)",
            "Rate of Improvement",
        ]
    )
    avoided_per = avoided_per.droplevel(
        [
            "Initial Loss Rate (%)",
            "Rate of Improvement",
        ]
    )
    # endregion

    # make placeholder for Animal Mgmt CH4
    adoption_am = pd.concat(
        [adoption.loc[slice(None), "Cropland Soil Health", :] * 0],
        keys=["Animal Mgmt"],
        names=["Subvector"],
    ).reorder_levels(["Region", "Subvector"])

    adoption = pd.concat([adoption, adoption_am, avoided])
    per_adoption = pd.concat([afolu, avoided_per]).fillna(0)

    # Add labels to percent adoption

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
        per_fw = pd.concat(
            [
                pd.DataFrame(per_fw),
                pd.DataFrame(per_adoption.loc[slice(None), [subv], :]),
            ]
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
        per_ag = pd.concat(
            [
                pd.DataFrame(per_ag),
                pd.DataFrame(per_adoption.loc[slice(None), [subv], :]),
            ]
        )

    per_ag = pd.concat([per_ag], names=["Sector"], keys=["Regenerative Agriculture"])
    per_ag = pd.concat([per_ag], names=["Scenario"], keys=[scenario])
    per_ag = per_ag.reorder_levels(["Region", "Sector", "Subvector", "Scenario"])

    per_adoption = pd.concat([per_fw, per_ag])

    # endregion

    ##########################
    #  UPDATE REGION LABELS  #
    ##########################

    # region

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["WEB Region", "ISO"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "Region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["Region"] = regions["Region"].str.lower()

    co2 = (
        co2.reset_index()
        .set_index(["Region"])
        .merge(regions, left_on=["Region"], right_on=["ISO"])
    ).set_index(["Region", "Sector"])

    # endregion

    ##############################
    #  SAVE OUTPUT TO CSV FILES  #
    ##############################

    # region

    # AFOLU net emissions
    pd.concat([afolu_baseline, afolu]).to_csv("podi/data/afolu_adoption.csv")

    # endregion

    return
