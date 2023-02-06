# region

import pandas as pd
from numpy import NaN
import numpy as np
from pandarallel import pandarallel
import pyam

pandarallel.initialize(progress_bar=True, nb_workers=6)

# endregion


def afolu(scenario, data_start_year, data_end_year, proj_end_year):

    ##################################
    #  LOAD HISTORICAL NCS ADOPTION  #
    ##################################

    # region

    # Load the 'Historical Observations' tab of TNC's 'Positive Disruption NCS
    # Verticals' google spreadsheet
    afolu_historical = (
        pd.DataFrame(pd.read_csv("podi/data/TNC/historical_observations.csv"))
        .drop(columns=["Region Group", "Region"])
        .rename(
            columns={
                "ISO": "region",
                "Model": "model",
                "Scenario": "scenario",
                "Unit": "unit",
            }
        )
        .replace("Pathway", scenario)
    )

    # 'Avoided Peat Impacts', 'Avoided Forest Conversion', and 'Avoided Coastal Impacts'
    #  subverticals do not have historical adoption data, so these are set to zero
    afolu_historical.update(
        afolu_historical[afolu_historical.Subvertical.str.contains("Avoided")].fillna(0)
    )

    # Create a 'variable' column that concatenates the 'Subvertical' and 'Metric' columns
    afolu_historical["variable"] = afolu_historical.parallel_apply(
        lambda x: "|".join([x["Subvertical"], x["Metric"]]), axis=1
    )
    afolu_historical.drop(columns=["Subvertical", "Metric"], inplace=True)

    # Set the index to IAMC format
    afolu_historical = afolu_historical.set_index(pyam.IAMC_IDX)

    afolu_historical.columns = afolu_historical.columns.astype(int)

    # For subvertical/region combos that have at least two data points, interpolate
    # between data points to fill data gaps
    afolu_historical.interpolate(axis=1, limit_area="inside", inplace=True)

    # Create a timeseries of maximum extent of each subvertical
    # region

    # Define a function that takes piecewise functions as input and outputs a continuous
    # timeseries (this is used for input data provided for (1) maximum extent, and (2)
    # average mitigation potential flux)
    def piecewise_to_continuous(variable):
        # Load the 'Max Extent' tab of TNC's 'Positive Disruption NCS Verticals' google
        # spreadsheet
        name = (
            pd.read_csv("podi/data/TNC/max_extent.csv")
            .drop(columns=["Region Group", "Region"])
            .rename(
                columns={
                    "ISO": "region",
                    "Model": "model",
                    "Scenario": "scenario",
                    "Unit": "unit",
                }
            )
            .replace("Pathway", scenario)
        )

        # Create a 'variable' column that concatenates the 'Subvertical' and 'Metric'
        # columns
        name["variable"] = name.parallel_apply(
            lambda x: "|".join([x["Subvertical"], x["Metric"]]), axis=1
        )
        name.drop(columns=["Subvertical", "Metric"], inplace=True)

        # Filter for rows that have 'variable' (either 'Max extent' or 'Avg mitigation
        # potential flux')
        name = name[name["variable"].str.contains(variable)]

        # If Value 1 is 'NA', set to 0
        name["Value 1"] = np.where(name["Value 1"].isna(), 0, name["Value 1"])

        # If Value 2 is 'NA', set to Value 1
        name["Value 2"] = np.where(
            name["Value 2"].isna(), name["Value 1"], name["Value 2"]
        )

        # If Value 3 is 'NA', set to Value 2
        name["Value 3"] = np.where(
            name["Value 3"].isna(), name["Value 2"], name["Value 3"]
        )

        # If Duration 1 is 'NA' or longer than proj_end_year -
        # afolu_historical.columns[0], set to proj_end_year - afolu_historical.columns[0]
        name["Duration 1 (Years)"] = np.where(
            (
                (name["Duration 1 (Years)"].isna())
                | (
                    name["Duration 1 (Years)"]
                    > proj_end_year - afolu_historical.columns[0]
                )
            ),
            proj_end_year - afolu_historical.columns[0],
            name["Duration 1 (Years)"],
        )

        # If Duration 2 is 'NA', set to Duration 1
        name["Duration 2 (Years)"] = np.where(
            (name["Duration 2 (Years)"].isna()),
            name["Duration 1 (Years)"],
            name["Duration 2 (Years)"],
        )

        # If Duration 3 is 'NA', set to Duration 2
        name["Duration 3 (Years)"] = np.where(
            (name["Duration 3 (Years)"].isna()),
            name["Duration 2 (Years)"],
            name["Duration 3 (Years)"],
        )

        # Create dataframe with timeseries columns
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
            columns=np.arange(afolu_historical.columns[0], proj_end_year + 1, 1),
            dtype=float,
        )

        # Define a function that places values in each timeseries for the durations
        # specified, and interpolates
        def rep(x):
            x0 = x
            x0.loc[afolu_historical.columns[0]] = x.name[5]
            x0.loc[afolu_historical.columns[0] + x.name[6]] = x.name[7]
            x0.loc[
                min(
                    afolu_historical.columns[0] + x.name[6] + x.name[8],
                    proj_end_year - afolu_historical.columns[0],
                )
            ] = x.name[9]
            x0.interpolate(axis=0, limit_area="inside", inplace=True)
            x.update(x0)
            return x

        name.update(name.parallel_apply(rep, axis=1))

        # Drop 'Value' and 'Duration' columns now that the timeseries have been created
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

    max_extent = piecewise_to_continuous("Max extent")

    # Shift Improved Forest Management's start year to 2018, and give all years prior to
    # 2018 the value in 2018
    max_extent.update(
        (
            max_extent[
                (
                    max_extent.reset_index().variable.str.contains(
                        "Improved Forest Management"
                    )
                ).values
            ].loc[:, 2018:]
            * 0
        ).parallel_apply(
            lambda x: x
            + (
                max_extent[
                    (
                        max_extent.reset_index().variable.str.contains(
                            "Improved Forest Management"
                        )
                    ).values
                ]
                .loc[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]
                .iloc[0 : proj_end_year - 2018 + 1]
                .values
            ),
            axis=1,
        )
    )

    max_extent.update(
        (
            max_extent[
                (
                    max_extent.reset_index().variable.str.contains(
                        "Improved Forest Management"
                    )
                ).values
            ].loc[:, :2018]
            * 0
        ).parallel_apply(
            lambda x: x
            + (
                max_extent[
                    (
                        max_extent.reset_index().variable.str.contains(
                            "Improved Forest Management"
                        )
                    ).values
                ]
                .loc[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]
                .iloc[0]
            ),
            axis=1,
        )
    )

    # Define the max extent of 'Avoided Coastal Impacts' and 'Avoided Forest Conversion'
    # by loading the 'Avoided Subverticals Input' tab of TNC's 'Positive Disruption NCS
    # Verticals' google spreadsheet
    afolu_avoided = pd.DataFrame(
        pd.read_csv("podi/data/TNC/avoided_subverticals_input.csv")
        .drop(columns=["Region Group", "Region"])
        .rename(
            columns={
                "ISO": "region",
                "Model": "model",
                "Scenario": "scenario",
                "Subvertical": "variable",
                "Unit": "unit",
            }
        )
        .replace("Pathway", scenario)
    ).fillna(0)

    # Max extent is defined by the initial extent, which represents the amount of land
    # that could be lost in future years.
    max_extent_avoided = pd.concat(
        [
            pd.DataFrame(
                0,
                index=afolu_avoided.set_index(pyam.IAMC_IDX).index,
                columns=max_extent.columns[max_extent.columns <= data_end_year],
            ),
            pd.concat(
                [
                    afolu_avoided.drop(
                        columns=[
                            "Initial Loss Rate (%)",
                            "Rate of Improvement",
                            "Mitigation (MtCO2e/ha)",
                            "Duration",
                        ]
                    ),
                    pd.DataFrame(
                        columns=max_extent.columns,
                    ),
                ]
            )
            .set_index(pyam.IAMC_IDX)
            .parallel_apply(
                lambda x: x[max_extent.columns[0:]][
                    x[max_extent.columns[0:]].index > data_end_year
                ].fillna(x["Initial Extent (Mha)"]),
                axis=1,
            ),
        ],
        axis=1,
    ).rename(
        index={
            "Avoided Coastal Impacts": "Avoided Coastal Impacts|Max extent",
            "Avoided Forest Conversion": "Avoided Forest Conversion|Max extent",
        }
    )

    # Like 'Avoided Forest Conversion' and 'Avoided Coastal Impacts',
    # 'Avoided Peat Impacts' max extent should be set to zero for historical years
    max_extent.update(
        max_extent[
            (
                max_extent.reset_index().variable == "Avoided Peat Impacts|Max extent"
            ).values
        ]
        .loc[:, :data_end_year]
        .parallel_apply(lambda x: x * 0)
    )

    # Combine max extents
    max_extent = pd.concat([max_extent, max_extent_avoided])

    max_extent.to_csv("podi/data/TNC/max_extent_output.csv")

    # endregion

    # Calculate afolu_historical as a % of max_extent, excluding Nitrogen Fertilizer
    # Management, since its historical adoption is already reported in Percent adoption.
    afolu_historical[
        afolu_historical.index.get_level_values(3).str.contains(
            "Nitrogen Fertilizer Management"
        )
    ] = afolu_historical[
        afolu_historical.index.get_level_values(3).str.contains(
            "Nitrogen Fertilizer Management"
        )
    ].divide(
        100
    )

    afolu_historical[
        ~afolu_historical.index.get_level_values(3).str.contains(
            "Nitrogen Fertilizer Management"
        )
    ] = (
        afolu_historical[
            ~afolu_historical.index.get_level_values(3).str.contains(
                "Nitrogen Fertilizer Management"
            )
        ]
        .parallel_apply(
            lambda x: x.divide(
                max_extent[
                    (max_extent.index.get_level_values(2) == x.name[2])
                    & (
                        max_extent.index.get_level_values(3).str.contains(
                            x.name[3].replace("|Observed adoption", "")
                        )
                    )
                ]
                .loc[:, x.index.values]
                .fillna(0)
                .squeeze()
            ),
            axis=1,
        )
        .replace(np.inf, NaN)
    )

    # Make Avoided subverticals all zeros
    afolu_historical[
        (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Coastal Impacts"
            )
        )
        | (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Forest Conversion"
            )
        )
        | (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Peat Impacts"
            )
        )
    ] = afolu_historical[
        (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Coastal Impacts"
            )
        )
        | (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Forest Conversion"
            )
        )
        | (
            afolu_historical.index.get_level_values(3).str.contains(
                "Avoided Peat Impacts"
            )
        )
    ].fillna(
        0
    )

    # Set max extent to 1 (100%) for historical years
    afolu_historical = afolu_historical.clip(upper=1)

    # For rows will all 'NA', replace with zero at data_end_year
    afolu_historical.update(
        afolu_historical[afolu_historical.isna().all(axis=1).values]
        .loc[:, data_end_year]
        .fillna(0)
    )

    # For subvertical/region combos that have one data point, assume the prior year of
    # input data is 95% of this value. If the value is zero, set a minimum slope.
    afolu_historical.update(
        afolu_historical[afolu_historical.count(axis=1) == 1].parallel_apply(
            lambda x: x.update(
                pd.Series(
                    data=[
                        min(x.loc[x.first_valid_index()], 1e-3) * 0.95,
                        min(x.loc[x.first_valid_index()], 1e-3),
                    ],
                    index=[x.first_valid_index() - 1, x.first_valid_index()],
                )
            ),
            axis=1,
        )
    )

    # endregion

    ###########################
    #  ESTIMATE NCS ADOPTION  #
    ###########################

    # region

    # Compute adoption curves of the set of historical analogs that have been supplied
    # to estimate the potential future growth of subverticals

    # region
    afolu_analogs = pd.DataFrame(
        pd.read_csv("podi/data/TNC/analogs_modeled.csv")
    ).set_index(["Analog Name"])
    afolu_analogs.columns.rename("Year", inplace=True)
    afolu_analogs.columns = np.arange(
        data_start_year, data_start_year + len(afolu_analogs.columns), 1
    )

    afolu_analogs = afolu_analogs.astype(float)

    # Add analogs for 'Avoided Coastal Impacts' and 'Avoided Forest Conversion'
    afolu_analogs_avoided = (
        pd.DataFrame(
            pd.read_csv("podi/data/TNC/avoided_subverticals_input.csv")
            .drop(
                columns=[
                    "Model",
                    "Scenario",
                    "Region Group",
                    "ISO",
                    "Region",
                    "Unit",
                    "Duration",
                    "Initial Extent (Mha)",
                    "Initial Loss Rate (%)",
                    "Mitigation (MtCO2e/ha)",
                ]
            )
            .rename(columns={"Subvertical": "Analog name"})
        )
        .fillna(0)
        .drop_duplicates()
    )

    afolu_analogs_avoided = (
        pd.concat(
            [
                afolu_analogs_avoided,
                pd.DataFrame(
                    columns=afolu_analogs.columns,
                ),
            ]
        )
        .set_index("Analog name")
        .parallel_apply(
            lambda x: x[afolu_analogs.columns[0:]]
            .fillna(x["Rate of Improvement"])
            .cumsum(),
            axis=1,
        )
        .rename(
            index={
                "Avoided Coastal Impacts": "Avoided Coastal Impacts|90 percentile across countries",
                "Avoided Forest Conversion": "Avoided Forest Conversion|90 percentile across countries",
            }
        )
    )

    afolu_analogs = pd.concat([afolu_analogs, afolu_analogs_avoided])

    # endregion

    # Match historical analogs to each subvertical

    # region
    subvertical = pd.DataFrame(
        pd.read_csv(
            "podi/data/TNC/analog_mapping.csv", usecols=["Subvertical", "Analog Name"]
        ).rename(columns={"Subvertical": "variable"})
    )
    subvertical["variable"] = subvertical["variable"] + "|Observed adoption"
    subvertical.set_index(["variable"], inplace=True)

    afolu_output = (
        (
            afolu_historical.reset_index()
            .set_index(["variable"])
            .merge(subvertical, left_on="variable", right_on="variable")
        )
        .set_index(["model", "scenario", "region", "unit", "Analog Name"], append=True)
        .reorder_levels(
            ["model", "scenario", "region", "variable", "unit", "Analog Name"]
        )
    ).rename(index={"baseline": scenario})

    # Join historical analog model with historical data at point where projection curve
    # results in smooth growth (since historical analogs are at different points on
    # their modeled adoption curve than the NCS pathways to which they are being
    # compared)

    def rep(x):
        x0 = x
        if x0.isna().all():
            x0.iloc[-1] = 0
        x0 = (
            afolu_analogs.loc[x.name[5]][
                afolu_analogs.loc[x.name[5]]
                >= min(max(x0.loc[x0.last_valid_index()], 1e-5), 1)
            ]
            .iloc[: proj_end_year - x0.last_valid_index()]
            .reset_index()
            .set_index(np.arange(x0.last_valid_index() + 1, proj_end_year + 1, 1))
            .drop(columns=["index"])
            .squeeze()
            .rename(x.name)
        )

        x = x.combine_first(x0)

        if x.first_valid_index() > data_start_year:
            x1 = (
                afolu_analogs.loc[x.name[5]][
                    afolu_analogs.loc[x.name[5]]
                    <= min(max(x.loc[x.first_valid_index()], 1e-5), 1)
                ]
                .tail(x.first_valid_index() - x.index[0])
                .reset_index()
                .set_index(np.arange(x.index[0], x.first_valid_index(), 1))
                .drop(columns=["index"])
                .squeeze()
                .rename(x.name)
            )
            x = x.combine_first(x1)

        return x

    afolu_output = pd.DataFrame(data=afolu_output.parallel_apply(rep, axis=1))
    afolu_output = afolu_output.droplevel("Analog Name")

    # endregion

    # Create afolu_baseline by copying afolu_historical and changing the scenario name
    # to 'baseline'

    # region

    afolu_baseline = afolu_historical.copy()
    afolu_baseline.reset_index(inplace=True)
    afolu_baseline.scenario = afolu_baseline.scenario.str.replace(scenario, "baseline")
    afolu_baseline.set_index(pyam.IAMC_IDX, inplace=True)

    # Estimate 'baseline' scenario NCS subvertical growth
    def rep(x):
        x0 = pd.Series(
            data=max(
                0,
                afolu_output.loc[
                    x.name[0], scenario, x.name[2], x.name[3], x.name[4]
                ].loc[x.last_valid_index()]
                - afolu_output.loc[
                    x.name[0], scenario, x.name[2], x.name[3], x.name[4]
                ].loc[x.last_valid_index() - 1],
            ),
            index=np.arange(x.last_valid_index() + 1, proj_end_year + 1, 1),
            name=x.name,
        )
        x0 = pd.concat(
            [
                afolu_output.loc[
                    x.name[0], scenario, x.name[2], x.name[3], x.name[4]
                ].loc[: x.last_valid_index() - 1],
                pd.concat(
                    [
                        pd.Series(
                            data=afolu_output.loc[
                                x.name[0], scenario, x.name[2], x.name[3], x.name[4]
                            ].loc[x.last_valid_index()],
                            index=[x.last_valid_index()],
                            name=x.name,
                        ),
                        x0,
                    ]
                ).cumsum(),
            ]
        )

        x = x.combine_first(x0).rename(
            afolu_output.loc[x.name[0], scenario, x.name[2], x.name[3], x.name[4]].name
        )

        return x

    afolu_baseline = pd.DataFrame(data=afolu_baseline.parallel_apply(rep, axis=1)).clip(
        upper=1
    )

    # endregion

    # Combine all scenarios, updating historical data for afolu_baseline to match
    # afolu_output
    afolu_output = pd.concat([afolu_baseline, afolu_output])

    # Multiply afolu_ouput by the estimated maximum extent to get afolu_output in units
    # of land area & forest volume

    afolu_output = afolu_output.parallel_apply(
        lambda x: x.multiply(
            pd.concat(
                [max_extent, max_extent.rename(index={scenario: "baseline"}, level=1)]
            ).loc[
                slice(None),
                [x.name[1]],
                [x.name[2]],
                [x.name[3].replace("Observed adoption", "Max extent")],
            ]
        ).squeeze(),
        axis=1,
    ).fillna(0)

    # endregion

    #################################
    #  UPDATE REGION & UNIT LABELS  #
    #################################

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
    regions["region"] = regions["region"].str.lower()

    def addindices(each):
        each = (
            each.reset_index()
            .set_index(["region"])
            .merge(regions, left_on=["region"], right_on=["ISO"])
        )

        # Add sector, product_category, product_long, product_short, flow_category,
        # flow_long, flow_short indices
        each["product_category"] = "AFOLU"

        each["product_long"] = each["variable"].str.split("|", expand=True)[0].values
        each["product_short"] = each["product_long"]

        def addsector(x):
            if x["product_long"] in [
                "Biochar",
                "Cropland Soil Health",
                "Nitrogen Fertilizer Management",
                "Improved Rice",
                "Optimal Intensity",
                "Agroforestry",
            ]:
                return "Agriculture"
            elif x["product_long"] in [
                "Improved Forest Management",
                "Natural Regeneration",
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Peat Restoration",
            ]:
                return "Forests & Wetlands"

        each["sector"] = each.parallel_apply(lambda x: addsector(x), axis=1)

        each["flow_category"] = "Emissions"

        def addgas(x):
            if x["product_long"] in [
                "Biochar",
                "Cropland Soil Health",
                "Optimal Intensity",
                "Agroforestry",
                "Improved Forest Management",
                "Natural Regeneration",
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Peat Restoration",
            ]:
                return "CO2"
            if x["product_long"] in [
                "Improved Rice",
            ]:
                return "CH4"
            if x["product_long"] in [
                "Improved Rice",
                "Nitrogen Fertilizer Management",
            ]:
                return "N2O"

        each["flow_long"] = each.parallel_apply(lambda x: addgas(x), axis=1)
        each["flow_short"] = each["flow_long"]

        each = (
            each.reset_index()
            .set_index(
                [
                    "model",
                    "scenario",
                    "region",
                    "sector",
                    "product_category",
                    "product_long",
                    "product_short",
                    "flow_category",
                    "flow_long",
                    "flow_short",
                    "unit",
                ]
            )
            .drop(columns=["variable", "index"])
        )

        return each

    afolu_output = addindices(afolu_output)
    afolu_historical = addindices(afolu_historical)

    # Duplicate Improved Rice adoption and change gas from CH4 to N2O
    afolu_output = pd.concat(
        [
            afolu_output,
            afolu_output[
                (afolu_output.reset_index().product_long == "Improved Rice").values
            ].rename(index={"CH4": "N2O"}),
        ]
    )

    # Filter to data_start_year
    afolu_output = afolu_output.loc[:, data_start_year:proj_end_year]

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region
    afolu_historical.to_csv("podi/data/TNC/afolu_historical.csv")
    afolu_output.sort_index().to_csv("podi/data/afolu_output.csv")

    # endregion

    return
