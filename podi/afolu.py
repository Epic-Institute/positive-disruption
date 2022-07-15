# region

from matplotlib.pyplot import axis, title, xlabel, ylabel
import pandas as pd
from podi.adoption_projection import adoption_projection
from numpy import NaN, cumsum, divide
import numpy as np
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import pyam
import panel as pn
import holoviews as hv
import hvplot.pandas
import plotly.io as pio
import plotly.graph_objects as go

hvplot.extension("plotly")

pandarallel.initialize()

show_figs = True
save_figs = True

# endregion


def afolu(scenario, data_start_year, data_end_year, proj_end_year):

    ##################################
    #  LOAD HISTORICAL NCS ADOPTION  #
    ##################################

    # region

    # Load the 'Historical Observations' tab of TNC's 'Positive Disruption NCS Vectors' google spreadsheet
    afolu_historical = (
        pd.DataFrame(pd.read_csv("podi/data/afolu_historical.csv"))
        .drop(columns=["Region", "Country"])
        .rename(
            columns={
                "iso": "region",
                "Model": "model",
                "Scenario": "scenario",
                "Unit": "unit",
            }
        )
        .replace("Pathway", scenario)
    )

    # 'Avoided Peat Impacts', 'Avoided Forest Conversion', and 'Avoided Coastal Impacts' subverticals do not have historical adoption data, so these are set to zero
    afolu_historical.update(
        afolu_historical[afolu_historical.Subvector.str.contains("Avoided")].fillna(0)
    )

    # Create a 'variable' column that concatenates the 'Subvector' and 'Metric' columns
    afolu_historical["variable"] = afolu_historical.apply(
        lambda x: "|".join([x["Subvector"], x["Metric"]]), axis=1
    )
    afolu_historical.drop(columns=["Subvector", "Metric"], inplace=True)

    # Set the index to IAMC format
    afolu_historical = afolu_historical.set_index(pyam.IAMC_IDX)

    afolu_historical.columns = afolu_historical.columns.astype(int)

    # For subvertical/region combos that have one data point, assume the first year of input data is 0, and interpolate, using the single historical data point as the most recent year for data
    afolu_historical.update(
        afolu_historical[afolu_historical.count(axis=1) == 1].iloc[:, 0].fillna(0)
    )

    # For subvertical/region combos that have at least two data points, interpolate between data points to fill data gaps
    afolu_historical.interpolate(axis=1, limit_area="inside", inplace=True)

    # Plot afolu_historical [Mha, m3]
    # region
    if show_figs is True:

        fig = afolu_historical.droplevel(["model", "scenario", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=["region", "variable"], value_name="Adoption"
        )

        for subvertical in fig2["variable"].unique():

            fig = go.Figure()

            for region in fig2["region"].unique():

                # Make modeled trace
                fig.add_trace(
                    go.Scatter(
                        name=region,
                        line=dict(width=1),
                        x=fig2[(fig2["variable"] == subvertical)]["year"].unique(),
                        y=fig2[
                            (fig2["variable"] == subvertical)
                            & (fig2["region"] == region)
                        ]["Adoption"],
                        legendgroup=region,
                        showlegend=True,
                    )
                )

            fig.update_layout(
                title={
                    "text": "Historical Adoption, "
                    + subvertical.replace("|Observed adoption", ""),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                yaxis={"title": "Mha"},
                margin_b=0,
                margin_t=20,
                margin_l=10,
                margin_r=10,
            )

            if subvertical == "Improved Forest Mgmt|Observed adoption":
                fig.update_layout(yaxis={"title": "m3"})

            fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/afolu_historical-"
                        + str(subvertical.replace("|Observed adoption", "")).replace(
                            "slice(None, None, None)", "All"
                        )
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

    # endregion

    # Create a timeseries of maximum extent of each subvertical
    # region

    # Define a function that takes piecewise functions as input and outputs a continuous timeseries (this is used for input data provided for (1) maximum extent, and (2) average mitigation potential flux)
    def piecewise_to_continuous(variable):
        """
        It takes a variable name as input, and returns a dataframe with the variable's values for each
        region, model, and scenario

        :param variable: the name of the variable you want to convert
        """

        # Load the 'Input Data' tab of TNC's 'Positive Disruption NCS Vectors' google spreadsheet
        name = (
            pd.read_csv("podi/data/afolu_max_extent_and_flux.csv")
            .drop(columns=["Region", "Country"])
            .rename(
                columns={
                    "iso": "region",
                    "Model": "model",
                    "Scenario": "scenario",
                    "Unit": "unit",
                }
            )
            .replace("Pathway", scenario)
        )

        # Create a 'variable' column that concatenates the 'Subvector' and 'Metric' columns
        name["variable"] = name.apply(
            lambda x: "|".join([x["Subvector"], x["Metric"]]), axis=1
        )
        name.drop(columns=["Subvector", "Metric"], inplace=True)

        # Filter for rows that have 'variable' (either 'Max extent' or 'Avg mitigation potential flux')
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

        # If Duration 1 is 'NA' or longer than proj_end_year - afolu_historical.columns[0], set to proj_end_year - afolu_historical.columns[0]
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

        # Define a function that places values in each timeseries for the durations specified, and interpolates
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

        name.update(name.apply(rep, axis=1))

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

    # Shift Improved Forest Mgmt's start year to 2018, all prior years to 2018 value
    max_extent.update(
        (
            max_extent[
                (
                    max_extent.reset_index().variable.str.contains(
                        "Improved Forest Mgmt"
                    )
                ).values
            ].loc[:, 2018:]
            * 0
        ).apply(
            lambda x: x
            + (
                max_extent[
                    (
                        max_extent.reset_index().variable.str.contains(
                            "Improved Forest Mgmt"
                        )
                    ).values
                ]
                .loc[x.name[0], x.name[1], x.name[2], x.name[3], x.name[4]]
                .iloc[0:33]
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
                        "Improved Forest Mgmt"
                    )
                ).values
            ].loc[:, :2018]
            * 0
        ).apply(
            lambda x: x
            + (
                max_extent[
                    (
                        max_extent.reset_index().variable.str.contains(
                            "Improved Forest Mgmt"
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
    afolu_avoided = pd.DataFrame(
        pd.read_csv("podi/data/afolu_avoided_pathways_input.csv")
        .drop(columns=["Region", "Country"])
        .rename(
            columns={
                "iso": "region",
                "Model": "model",
                "Scenario": "scenario",
                "Subvector": "variable",
                "Unit": "unit",
            }
        )
        .replace("Pathway", scenario)
    ).fillna(0)

    # Max extent is defined by the initial extent, which represents the amount of land that could be lost in future years.
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
                            "Mitigation (Mg CO2/ha)",
                            "Duration",
                        ]
                    ),
                    pd.DataFrame(
                        columns=max_extent.columns,
                    ),
                ]
            )
            .set_index(pyam.IAMC_IDX)
            .apply(
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

    # Combine max extents
    max_extent = pd.concat([max_extent, max_extent_avoided])

    # Plot max_extent [Mha, m3]
    # region
    if show_figs is True:

        fig = max_extent.droplevel(["model", "scenario", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["region", "variable"],
            value_name="Max Extent",
        )

        for subvertical in fig2["variable"].unique():

            fig = go.Figure()

            for region in fig2["region"].unique():

                # Make modeled trace
                fig.add_trace(
                    go.Scatter(
                        name=region,
                        line=dict(width=1),
                        x=fig2[(fig2["variable"] == subvertical)]["year"].unique(),
                        y=fig2[
                            (fig2["variable"] == subvertical)
                            & (fig2["region"] == region)
                        ]["Max Extent"],
                        legendgroup=region,
                        showlegend=True,
                    )
                )

            fig.update_layout(
                title={
                    "text": "Max Extent, " + subvertical.replace("|Max extent", ""),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                yaxis={"title": "Mha"},
                margin_b=0,
                margin_t=20,
                margin_l=10,
                margin_r=10,
            )

            if subvertical == "Improved Forest Mgmt|Max extent":
                fig.update_layout(yaxis={"title": "m3"})

            fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/afolu_max_extent-"
                        + str(subvertical.replace("|Max extent", "")).replace(
                            "slice(None, None, None)", "All"
                        )
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

    # endregion

    # endregion

    # Calculate afolu_historical as a % of max_extent
    afolu_historical = afolu_historical.apply(
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
    ).replace(np.inf, NaN)

    # Make Avoided Coastal Impacts and Avoided Forest Conversion all zero instead of NA, for consistency with Avoided Peat Impacts
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
    ].fillna(
        0
    )

    # List all historical values higher than max extent
    afolu_historical_toohigh = afolu_historical[
        (afolu_historical.values > 1).any(axis=1)
    ]

    # Plot afolu_historical [% of Max Extent]
    # region
    if show_figs is True:
        fig = afolu_historical.droplevel(["model", "scenario", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=["region", "variable"], value_name="Adoption"
        )

        for subvertical in fig2["variable"].unique():

            fig = go.Figure()

            for region in fig2["region"].unique():

                # Make modeled trace
                fig.add_trace(
                    go.Scatter(
                        name=region,
                        line=dict(width=1),
                        x=fig2[(fig2["variable"] == subvertical)]["year"].unique(),
                        y=fig2[
                            (fig2["variable"] == subvertical)
                            & (fig2["region"] == region)
                        ]["Adoption"]
                        * 100,
                        legendgroup=region,
                        showlegend=True,
                    )
                )

            fig.update_layout(
                title={
                    "text": "Historical Adoption, "
                    + subvertical.replace("|Observed adoption", ""),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                yaxis={"title": "% of Max Extent"},
                margin_b=0,
                margin_t=20,
                margin_l=10,
                margin_r=10,
            )

            fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/afolu_historical_percent-"
                        + str(subvertical.replace("|Observed adoption", "")).replace(
                            "slice(None, None, None)", "All"
                        )
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

    # endregion

    # endregion

    ###########################
    #  ESTIMATE NCS ADOPTION  #
    ###########################

    # region

    # Create afolu_baseline by copying afolu_historical and changing the scenario name to 'baseline'
    afolu_baseline = afolu_historical.copy()
    afolu_baseline.reset_index(inplace=True)
    afolu_baseline.scenario = afolu_baseline.scenario.str.replace(scenario, "baseline")
    afolu_baseline.set_index(pyam.IAMC_IDX, inplace=True)

    # For rows will all 'NA', replace with zeros
    afolu_baseline[afolu_baseline.isna().all(axis=1).values] = 0

    # Load input parameters for estimating NCS subvertical growth
    parameters = pd.read_csv("podi/data/tech_parameters_afolu.csv").sort_index()

    # Estimate 'baseline' scenario NCS subvertical grwoth. (Remove clip(upper=1) here to allow % to go beyond max_extent.)
    afolu_baseline = afolu_baseline.parallel_apply(
        lambda x: adoption_projection(
            input_data=x,
            output_start_date=x.last_valid_index(),
            output_end_date=proj_end_year,
            change_model="linear",
            change_parameters=parameters[
                (parameters.scenario == "baseline")
                & (
                    parameters.variable.str.contains(
                        x.name[3].replace("|Observed adoption", "")
                    )
                )
            ],
        ),
        axis=1,
    ).clip(upper=1)

    # Compute adoption curves of the set of historical analogs that have been supplied to estimate the potential future growth of subverticals

    # region

    afolu_analogs = (
        pd.DataFrame(pd.read_csv("podi/data/afolu_analogs.csv"))
        .drop(columns=["Note", "Unit", "Actual start year"])
        .set_index(["Analog Name", "Max Extent"])
    )
    afolu_analogs.columns.rename("Year", inplace=True)
    afolu_analogs.loc[:, afolu_analogs.columns[0]] = afolu_analogs.loc[
        :, afolu_analogs.columns[0]
    ].fillna(0)
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
            output_start_date=x.last_valid_index() + 1,
            output_end_date=proj_end_year,
            change_model="logistic",
            change_parameters=parameters[parameters.variable.str.contains(x.name[0])],
        ),
        axis=1,
    ).droplevel("Max Extent")

    # Add analogs for 'Avoided Coastal Impacts' and 'Avoided Forest Conversion'
    afolu_analogs_avoided = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_avoided_pathways_input.csv")
            .drop(
                columns=[
                    "Model",
                    "Scenario",
                    "iso",
                    "Region",
                    "Country",
                    "Unit",
                    "Duration",
                    "Initial Extent (Mha)",
                    "Initial Loss Rate (%)",
                    "Mitigation (Mg CO2/ha)",
                ]
            )
            .rename(columns={"Subvector": "Analog name"})
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
        .apply(
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

    # Plot afolu_analogs [% of max extent]
    # region
    if show_figs is True:
        fig2 = afolu_analogs.T

        fig = go.Figure()

        for analog in fig2.columns.unique():

            fig.add_trace(
                go.Scatter(
                    name=analog,
                    line=dict(width=1),
                    x=fig2.index.unique(),
                    y=fig2.loc[:, analog].multiply(100),
                    legendgroup=region,
                    showlegend=True,
                )
            )

        fig.update_layout(
            title={
                "text": "Historical Analog Adoption",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% of Max Extent"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=("./charts/afolu_historical_analogs.html"),
                auto_open=False,
            )
    # endregion

    # endregion

    # Match historical analogs to each subvertical

    # region
    subvertical = pd.DataFrame(
        pd.read_csv(
            "podi/data/afolu_categories.csv", usecols=["Subvertical", "Analog Name"]
        ).rename(columns={"Subvertical": "variable"})
    )
    subvertical["variable"] = subvertical["variable"] + "|Observed adoption"
    subvertical.set_index(["variable"], inplace=True)

    afolu_output = (
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

    afolu_output.update(afolu_output.apply(rep, result_type="broadcast", axis=1))
    afolu_output = afolu_output.droplevel("Analog Name")

    # endregion

    # Combine all scenarios
    afolu_output = pd.concat([afolu_baseline, afolu_output])

    # Plot afolu_output [% of max extent]
    # region
    if show_figs is True:
        fig = afolu_output.droplevel(["model", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "region", "variable"],
            value_name="Adoption",
        )

        for scenario in fig2["scenario"].unique():
            for subvertical in fig2["variable"].unique():

                fig = go.Figure()

                for region in fig2["region"].unique():

                    # Make modeled trace
                    fig.add_trace(
                        go.Scatter(
                            name=region,
                            line=dict(width=1),
                            x=fig2[(fig2["variable"] == subvertical)]["year"].unique(),
                            y=fig2[
                                (fig2["variable"] == subvertical)
                                & (fig2["region"] == region)
                                & (fig2["scenario"] == scenario)
                            ]["Adoption"]
                            * 100,
                            legendgroup=region,
                            showlegend=True,
                        )
                    )

                fig.update_layout(
                    title={
                        "text": "Adoption, "
                        + scenario.capitalize()
                        + ", "
                        + subvertical.replace("|Observed adoption", ""),
                        "xanchor": "center",
                        "x": 0.5,
                        "y": 0.99,
                    },
                    yaxis={"title": "% of Max Extent"},
                    margin_b=0,
                    margin_t=20,
                    margin_l=10,
                    margin_r=10,
                )

                fig.show()

                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/afolu_output_percent-"
                            + str(
                                subvertical.replace("|Observed adoption", "")
                            ).replace("slice(None, None, None)", "All")
                            + "-"
                            + scenario.capitalize()
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )

    # endregion

    # Multiply afolu_ouput by the estimated maximum extent to get afolu_output in units of land area & forest volume.

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

    # Plot afolu_output [Mha, m3]
    # region
    if show_figs is True:
        fig = afolu_output.droplevel(["model", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "region", "variable"],
            value_name="Adoption",
        )

        for scenario in fig2["scenario"].unique():
            for subvertical in fig2["variable"].unique():

                fig = go.Figure()

                for region in fig2["region"].unique():

                    # Make modeled trace
                    fig.add_trace(
                        go.Scatter(
                            name=region,
                            line=dict(width=1),
                            x=fig2[(fig2["variable"] == subvertical)]["year"].unique(),
                            y=fig2[
                                (fig2["variable"] == subvertical)
                                & (fig2["region"] == region)
                                & (fig2["scenario"] == scenario)
                            ]["Adoption"],
                            legendgroup=region,
                            showlegend=True,
                        )
                    )

                fig.update_layout(
                    title={
                        "text": "Adoption, "
                        + scenario.capitalize()
                        + ", "
                        + subvertical.replace("|Observed adoption", ""),
                        "xanchor": "center",
                        "x": 0.5,
                        "y": 0.99,
                    },
                    yaxis={"title": "Mha"},
                    margin_b=0,
                    margin_t=20,
                    margin_l=10,
                    margin_r=10,
                )

                if subvertical == "Improved Forest Mgmt|Observed adoption":
                    fig.update_layout(yaxis={"title": "m3"})

                fig.show()

                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/afolu_output-"
                            + str(
                                subvertical.replace("|Observed adoption", "")
                            ).replace("slice(None, None, None)", "All")
                            + "-"
                            + scenario.capitalize()
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )

        # endregion

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

        # Add sector, product_category, product_long, product_short, flow_category, flow_long, flow_short indices
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
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Peat Restoration",
            ]:
                return "Forests & Wetlands"

        each["sector"] = each.apply(lambda x: addsector(x), axis=1)

        each["flow_category"] = "Emissions"

        def addgas(x):
            if x["product_long"] in [
                "Biochar",
                "Cropland Soil Health",
                "Optimal Intensity",
                "Agroforestry",
                "Improved Forest Mgmt",
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

        each["flow_long"] = each.apply(lambda x: addgas(x), axis=1)
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

        # Scale improved rice mitigation to be 58% from CH4 and 42% from N2O

        each[
            (
                (each.reset_index().product_long == "Improved Rice")
                & (each.reset_index().flow_long == "CH4")
            ).values
        ] = (
            each[
                (
                    (each.reset_index().product_long == "Improved Rice")
                    & (each.reset_index().flow_long == "CH4")
                ).values
            ]
            * 0.58
        )

        each[
            (
                (each.reset_index().product_long == "Improved Rice")
                & (each.reset_index().flow_long == "N2O")
            ).values
        ] = (
            each[
                (
                    (each.reset_index().product_long == "Improved Rice")
                    & (each.reset_index().flow_long == "N2O")
                ).values
            ]
            * 0.42
        )
        return each

    afolu_output = addindices(afolu_output)

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region
    afolu_output.sort_index().to_csv("podi/data/afolu_output.csv")

    # endregion

    return
