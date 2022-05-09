# region

from operator import index
from matplotlib.pyplot import axis, title
import pandas as pd
from validators import Max
from podi.adoption_projection import adoption_projection
from numpy import NaN, divide, empty_like
import numpy as np
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import pyam

pandarallel.initialize()

# endregion


def afolu(scenario, data_start_year, data_end_year, proj_end_year):

    ##################################
    #  LOAD HISTORICAL NCS ADOPTION  #
    ##################################

    recalc_afolu_historical = False
    # region
    def step2curve(name, variable):
        name = pd.read_csv(
            "podi/data/afolu_max_extent_and_flux.csv",
            usecols=[
                "model",
                "scenario",
                "region",
                "variable",
                "unit",
                "Value 1",
                "Value 2",
                "Value 3",
                "Duration 1 (Years)",
                "Duration 2 (Years)",
                "Duration 3 (Years)",
            ],
        )

        name = name[name["variable"].str.contains(variable)]

        name["Value 2"] = np.where(
            name["Value 2"].isna(), name["Value 1"], name["Value 2"]
        )

        name["Value 3"] = np.where(
            name["Value 3"].isna(), name["Value 2"], name["Value 3"]
        )

        name["Duration 1 (Years)"] = np.where(
            (
                (name["Duration 1 (Years)"].isna())
                | (name["Duration 1 (Years)"] > proj_end_year - data_end_year)
            ),
            proj_end_year - data_end_year,
            name["Duration 1 (Years)"],
        )

        name["Duration 2 (Years)"] = np.where(
            (name["Duration 2 (Years)"].isna()),
            name["Duration 1 (Years)"],
            name["Duration 2 (Years)"],
        )

        name["Duration 3 (Years)"] = np.where(
            name["Duration 3 (Years)"].isna(),
            name["Duration 2 (Years)"],
            name["Duration 3 (Years)"],
        )

        name = pd.DataFrame(
            index=[
                name["model"],
                name["scenario"],
                name["region"],
                name["variable"],
                name["unit"],
                name["Value 1"],
                name["Duration 1 (Years)"],
                name["Value 2"],
                name["Duration 2 (Years)"],
                name["Value 3"],
                name["Duration 3 (Years)"],
            ],
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            dtype=float,
        )

        def rep(x):
            x0 = x
            x0.loc[data_start_year] = x.name[5]
            x0.loc[data_start_year + x.name[6]] = x.name[7]
            x0.loc[data_start_year + x.name[6] + x.name[8]] = x.name[9]
            x0.interpolate(axis=0, limit_area="inside", inplace=True)
            x.update(x0)
            return x

        name.update(name.apply(rep, axis=1))

        name = name.droplevel(
            [
                "Value 1",
                "Duration 1 (Years)",
                "Value 2",
                "Duration 2 (Years)",
                "Value 3",
                "Duration 3 (Years)",
            ]
        ).fillna(0)
        return name

    if recalc_afolu_historical == True:
        afolu_historical = pd.DataFrame(
            pd.read_csv("podi/data/afolu_historical.csv")
        ).set_index(pyam.IAMC_IDX)

        afolu_historical.columns = afolu_historical.columns.astype(int)
        afolu_historical = afolu_historical.loc[:, data_start_year:]

        # For rows with no historical data prior to data_start_year, set data_start_year to zero
        afolu_historical.update(
            afolu_historical.loc[
                afolu_historical.loc[:, :data_start_year].isna().all(axis=1), :
            ]
            .loc[:, data_start_year]
            .fillna(0)
        )

        # For rows with no historical data prior to data_end_year, set data_end_year to 0
        afolu_historical.update(
            afolu_historical.loc[
                afolu_historical.loc[:, data_start_year + 1 : data_end_year]
                .isna()
                .all(axis=1),
                :,
            ]
            .loc[:, data_end_year]
            .fillna(0)
        )

        # Interpolate to fill historical data gaps
        afolu_historical.interpolate(axis=1, limit_area="inside", inplace=True)

        # Create a timeseries of maximum extent of each subvertical
        # region
        max_extent = step2curve("max_extent", "Max extent")

        # Plot
        max_extent.T.plot(legend=False, title="Maximum Extent [MHa, Tgdm, m3]")

        # endregion

        # Drop 'Avoided' subverticals (which will be addressed later)
        afolu_historical = afolu_historical[
            afolu_historical.index.get_level_values(3).str.contains(
                "Biochar|Coastal Restoration|Cropland Soil Health|Improved Forest Mgmt|Improved Rice|Natural Regeneration|Nitrogen Fertilizer Management|Optimal Intensity|Peat Restoration|Silvopasture|Trees in Croplands|Agroforestry"
            )
        ]

        # For rows that are all NaN (mostly due to zero values for max extent or average mitigation flux), set all data to zero
        afolu_historical.update(
            afolu_historical.loc[
                afolu_historical.loc[:, data_start_year:data_end_year]
                .isna()
                .all(axis=1),
                :,
            ]
            .loc[:, data_start_year:data_end_year]
            .fillna(0)
        )

        # Save
        afolu_historical.to_csv("podi/data/afolu_historical_postprocess.csv")
    else:
        index = ["model", "scenario", "region", "variable", "unit"]

        afolu_historical = pd.DataFrame(
            pd.read_csv("podi/data/afolu_historical_postprocess.csv")
        ).set_index(index)
        afolu_historical.columns = afolu_historical.columns.astype(int)

        max_extent = step2curve("max_extent", "Max extent")

    # Plot
    afolu_historical.T.plot(legend=False, title="AFOLU Historical [MHa, Tgdm, m3]")

    # Calculate afolu_historical as a % of max_extent. For Improved Forest Mgmt, which has a time-varying max extent over ten years, % of max extent is measured relative to the first year, but the mitigation flux will be reduced to account for this time-varying decrease in max_extent
    afolu_historical = (
        afolu_historical.apply(
            lambda x: x.divide(
                max_extent[
                    (max_extent.index.get_level_values(2) == x.name[2])
                    & (max_extent.index.get_level_values(3).str.contains(x.name[3]))
                ]
                .squeeze()
                .loc[:data_end_year]
            ),
            axis=1,
        )
        .replace(np.inf, NaN)
        .dropna(axis=0, how="all")
    )

    # Plot as % of max extent
    afolu_historical.T.plot(legend=False, title="AFOLU Historical [% of max extent]")

    # endregion

    ####################################
    #  ESTIMATE BASELINE NCS ADOPTION  #
    ####################################

    recalc_afolu_baseline = False
    # region

    if recalc_afolu_baseline == True:
        afolu_baseline = afolu_historical.copy()

        parameters = pd.read_csv("podi/data/tech_parameters_afolu.csv").sort_index()

        # Remove clip(upper=1) here to allow % to go beyond max_extent
        afolu_baseline = afolu_baseline.parallel_apply(
            lambda x: adoption_projection(
                input_data=x,
                output_start_date=data_end_year + 1,
                output_end_date=proj_end_year,
                change_model="linear",
                change_parameters=parameters[
                    (parameters.scenario == "baseline")
                    & (parameters.variable.str.contains(x.name[3]))
                ],
            ),
            axis=1,
        ).clip(upper=1)

        afolu_baseline.to_csv("podi/data/afolu_baseline.csv")
    else:
        index = ["scenario", "region", "Subvector"]

        afolu_baseline = pd.DataFrame(
            pd.read_csv("podi/data/afolu_baseline.csv")
        ).set_index(index)
        afolu_baseline.columns = afolu_baseline.columns.astype(int)

    afolu_baseline.T.plot(legend=False, title="AFOLU Baseline [% of max extent]")

    # endregion

    ##################################
    #  ESTIMATE PATHWAY NCS ADOPTION #
    ##################################

    # region

    # Create a timeseries of average mitigation potential flux of each subvertical

    # region

    flux = step2curve("flux", "Avg mitigation potential flux")

    # Change flux units [ha] to [Mha] to match max extent
    flux.update(flux.divide(1e6))

    # Plot
    flux[
        flux.index.get_level_values(3).isin(
            [
                "Coastal Restoration|Avg mitigation potential flux",
                "Cropland Soil Health|Avg mitigation potential flux",
                "Improved Rice|Avg mitigation potential flux",
                "Natural Regeneration|Avg mitigation potential flux",
                "Nitrogen Fertilizer Management|Avg mitigation potential flux",
                "Optimal Intensity|Avg mitigation potential flux",
                "Peat Restoration|Avg mitigation potential flux",
                "Silvopasture|Avg mitigation potential flux",
                "Trees in Croplands|Avg mitigation potential flux",
                "Avoided Peat Impacts|Avg mitigation potential flux",
                "Agroforestry|Avg mitigation potential flux",
            ]
        )
    ].T.plot(legend=False, title="Avg Mitigation Flux [tCO2e/ha/yr]")

    flux[
        flux.index.get_level_values(3).isin(
            ["Improved Forest Mgmt|Avg mitigation potential flux"]
        )
    ].T.plot(legend=False, title="Avg Mitigation Flux [tCO2e/m3/yr]")

    flux[
        flux.index.get_level_values(3).isin(["Biochar|Avg mitigation potential flux"])
    ].T.plot(
        legend=False,
        title="Avg Mitigation Flux [tCO2e/Tgdm/yr]",
    )

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
        data_start_year, data_start_year + len(afolu_analogs.columns), 1
    )

    afolu_analogs2 = pd.DataFrame(
        columns=np.arange(data_start_year, proj_end_year + 1, 1),
        index=afolu_analogs.index,
    )

    afolu_analogs2.update(afolu_analogs)
    afolu_analogs = afolu_analogs2.astype(float)

    parameters = pd.read_csv("podi/data/tech_parameters_afolu.csv").sort_index()

    afolu_analogs = afolu_analogs.apply(
        lambda x: adoption_projection(
            input_data=x,
            output_start_date=data_end_year + 1,
            output_end_date=proj_end_year,
            change_model="logistic",
            change_parameters=parameters[
                (parameters.scenario == scenario)
                & (parameters.variable.str.contains(x.name[0]))
            ],
        ),
        axis=1,
    ).droplevel("Max (Mha)")

    afolu_analogs.T.plot(title="Historical Analog Adoption [%]")

    # endregion

    # Match historical analogs to each subvertical

    # region

    subvertical = pd.DataFrame(
        pd.read_csv(
            "podi/data/afolu_categories.csv", usecols=["variable", "Analog Name"]
        )
    ).set_index(["variable"])

    afolu_adoption = (
        (
            afolu_baseline.reset_index()
            .set_index(["variable"])
            .merge(subvertical, left_on="variable", right_on="variable")
        )
        .set_index(["model", "scenario", "region", "unit", "Analog Name"], append=True)
        .reorder_levels(
            ["model", "scenario", "region", "variable", "unit", "Analog Name"]
        )
    ).rename(index={"baseline": scenario})

    # Join historical analog model with historical data at point where projection curve results in smooth growth (since historical analogs are at different points on their modeled adoption curve than the NCS pathways to which they are being compared)

    def rep(x):
        x0 = x
        x0 = x0.update(
            afolu_analogs.loc[x.name[5]][
                afolu_analogs.loc[x.name[5]] >= x.loc[data_end_year]
            ].rename(x.name)
        )
        x.update(x0)
        return x

    afolu_adoption.update(afolu_adoption.apply(rep, result_type="broadcast", axis=1))
    afolu_adoption = afolu_adoption.droplevel("Analog Name")

    afolu_adoption.T.plot(legend=False, title="AFOLU Adoption [%]")
    afolu_adoption_per = afolu_adoption
    # endregion

    # Multiply this by the estimated maximum extent and average mitigation potential flux to get emissions mitigated
    afolu_adoption.update(
        afolu_adoption.parallel_apply(
            lambda x: x.multiply(
                max_extent.loc[
                    slice(None),
                    slice(None),
                    [x.name[2]],
                    [x.name[3].replace("Observed adoption", "Max extent")],
                ]
            )
            .squeeze()
            .multiply(
                flux.loc[
                    slice(None),
                    slice(None),
                    [x.name[2]],
                    [
                        x.name[3].replace(
                            "Observed adoption", "Avg mitigation potential flux"
                        )
                    ],
                ]
            )
            .squeeze(),
            axis=1,
        ).fillna(0)
    )

    afolu_adoption.T.plot(legend=False, title="AFOLU Adoption [tCO2e mitigated]")

    # Estimate emissions mitigated by avoided pathways

    # region

    avoided = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_avoided_pathways_input.csv").drop(
                columns=[
                    "model",
                    "Initial Extent (Mha)",
                    "Mitigation (Mg CO2/ha)",
                ]
            )
        )
        .set_index(
            [
                "scenario",
                "region",
                "variable",
                "unit",
                "Initial Loss Rate (%)",
                "Rate of Improvement",
            ]
        )
        .loc[scenario, slice(None), slice(None), slice(None), :]
    )

    avoided.loc[:, "Avoided Forest Conversion|Observed adoption", :] = (
        avoided.loc[:, "Avoided Forest Conversion|Observed adoption", :] / 1e1
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

    avoided.T.plot(legend=False, title="Avoided [Mha]")
    avoided_per.T.plot(legend=False, title="Avoided Percent [%]")

    # endregion

    # Combine 'avoided' pathways with other pathways
    afolu_adoption = pd.concat([afolu_baseline, afolu_adoption, avoided])

    # endregion

    ##########################
    #  UPDATE REGION LABELS  #
    ##########################

    # region

    # Replace ISO code with WEB region labels
    regions = pd.DataFrame(
        pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["ISO", "WEB Region"],
        )
        .dropna(axis=0)
        .rename(columns={"WEB Region": "region"})
    ).set_index(["ISO"])
    regions.index = regions.index.str.lower()
    regions["region"] = regions["region"].str.lower()

    afolu_adoption = (
        afolu_adoption.reset_index()
        .set_index(["region"])
        .merge(regions, left_on=["region"], right_on=["ISO"])
    ).set_index(pyam.IAM_IDX)

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    # AFOLU net emissions
    afolu_adoption.to_csv("podi/data/afolu_adoption.csv")

    # endregion

    return
