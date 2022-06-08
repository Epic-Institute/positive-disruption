# region

from matplotlib.pyplot import axis, title, xlabel
import pandas as pd
from podi.adoption_projection import adoption_projection
from numpy import NaN, divide
import numpy as np
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import pyam
import panel as pn
import holoviews as hv
import hvplot.pandas

hvplot.extension("plotly")

pandarallel.initialize()

# endregion


def afolu(scenario, data_start_year, data_end_year, proj_end_year):

    ##################################
    #  LOAD HISTORICAL NCS ADOPTION  #
    ##################################

    recalc_afolu_historical = True
    # region
    def step2curve(name, variable):

        # Load the 'Input Data' tab of TNC's 'Positive Disruption NCS Vectors' google spreadsheet
        name = (
            pd.read_csv("podi/data/afolu_max_extent_and_flux2.csv")
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

        # If Duration 1 is 'NA' or longer than proj_end_year - data_end_year, set to proj_end_year - data_end_year
        name["Duration 1 (Years)"] = np.where(
            (
                (name["Duration 1 (Years)"].isna())
                | (name["Duration 1 (Years)"] > proj_end_year - data_end_year)
            ),
            proj_end_year - data_end_year,
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
            name["Duration 3 (Years)"].isna(),
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
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            dtype=float,
        )

        # Define a function that places values in each timeseries for the durations specified, and interpolates
        def rep(x):
            x0 = x
            x0.loc[data_start_year] = x.name[5]
            x0.loc[data_start_year + x.name[6]] = x.name[7]
            x0.loc[data_start_year + x.name[6] + x.name[8]] = x.name[9]
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

    if recalc_afolu_historical == True:
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

        # Create a 'variable' column that concatenates the 'Subvector' and 'Metric' columns
        afolu_historical["variable"] = afolu_historical.apply(
            lambda x: "|".join([x["Subvector"], x["Metric"]]), axis=1
        )
        afolu_historical.drop(columns=["Subvector", "Metric"], inplace=True)

        # Set the index to IAMC format
        afolu_historical = afolu_historical.set_index(pyam.IAMC_IDX)

        afolu_historical.columns = afolu_historical.columns.astype(int)

        # For rows with no historical data prior to data_start_year, set data_start_year to zero
        afolu_historical.update(
            afolu_historical.loc[
                afolu_historical.loc[:, :data_start_year].isna().all(axis=1), :
            ]
            .loc[:, data_start_year]
            .fillna(0)
        )

        # Set first year to 0 to allow for interpolation
        afolu_historical.update(afolu_historical.iloc[:, 0].fillna(0))

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

        # Plot

        # region

        df = afolu_historical.droplevel(["model", "scenario"])
        df = pd.melt(
            df.reset_index(),
            id_vars=["region", "variable", "unit"],
            var_name="year",
            value_name="Adoption",
        ).dropna()

        select_region = pn.widgets.Select(
            options=df.region.unique().tolist(), name="Region"
        )

        # for units in ['m3','Mha','Tg dm']:
        df = df[df.unit == "m3"].drop(columns="unit")

        @pn.depends(select_region)
        def exp_plot(select_region):
            return (
                df[df.region == select_region]
                .sort_values(by="year")
                .hvplot(x="year", y="Adoption", by=["variable"])
            )

        pn.Column(select_region, exp_plot)

        # endregion

        # Create a timeseries of maximum extent of each subvertical
        # region
        max_extent = step2curve("max_extent", "Max extent")

        # Plot
        max_extentplot = max_extent.copy()
        max_extentplot.columns = max_extentplot.columns - data_start_year
        max_extentplot[
            max_extentplot.index.get_level_values(3).isin(
                [
                    "Coastal Restoration|Max extent",
                    "Cropland Soil Health|Max extent",
                    "Improved Rice|Max extent",
                    "Natural Regeneration|Max extent",
                    "Nitrogen Fertilizer Management|Max extent",
                    "Optimal Intensity|Max extent",
                    "Peat Restoration|Max extent",
                    "Silvopasture|Max extent",
                    "Trees in Croplands|Max extent",
                    "Avoided Peat Impacts|Max extent",
                    "Agroforestry|Max extent",
                ]
            )
        ].T.plot(
            legend=False,
            title="Maximum Extent [MHa]",
            xlabel="Years from implementation",
        )

        max_extentplot[
            max_extentplot.index.get_level_values(3).isin(
                ["Improved Forest Mgmt|Max extent"]
            )
        ].T.plot(
            legend=False,
            title="Maximum Extent [m3]",
            xlabel="Years from implementation",
        )

        max_extentplot[
            max_extentplot.index.get_level_values(3).isin(["Biochar|Max extent"])
        ].T.plot(
            legend=False,
            title="Maximum Extent [Tgdm]",
            xlabel="Years from implementation",
        )

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
        index = pyam.IAMC_IDX

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

    recalc_afolu_baseline = True
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

        afolu_baseline.to_csv("podi/data/afolu_output.csv")
    else:
        index = pyam.IAMC_IDX

        afolu_baseline = pd.DataFrame(
            pd.read_csv("podi/data/afolu_output.csv")
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
    fluxplot = flux.copy()
    fluxplot.columns = fluxplot.columns - data_start_year
    fluxplot[
        fluxplot.index.get_level_values(3).isin(
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
    ].T.plot(
        legend=False,
        title="Avg Mitigation Flux [tCO2e/ha/yr]",
        xlabel="Years from implementation",
    )

    fluxplot[
        fluxplot.index.get_level_values(3).isin(
            ["Improved Forest Mgmt|Avg mitigation potential flux"]
        )
    ].T.plot(
        legend=False,
        title="Avg Mitigation Flux [tCO2e/m3/yr]",
        xlabel="Years from implementation",
    )

    fluxplot[
        fluxplot.index.get_level_values(3).isin(
            ["Biochar|Avg mitigation potential flux"]
        )
    ].T.plot(
        legend=False,
        title="Avg Mitigation Flux [tCO2e/Tgdm/yr]",
        xlabel="Years from implementation",
    )

    # endregion

    # Compute adoption curves of the set of historical analogs that have been supplied to estimate the potential future growth of subverticals

    # region

    afolu_analogs = (
        pd.DataFrame(pd.read_csv("podi/data/afolu_analogs.csv"))
        .drop(columns=["Note", "unit", "Actual start year"])
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

    # Plot
    afolu_analogs.T.plot(title="Historical Analog Adoption [%]")

    # endregion

    # Match historical analogs to each subvertical

    # region

    subvertical = pd.DataFrame(
        pd.read_csv(
            "podi/data/afolu_categories.csv", usecols=["variable", "Analog Name"]
        )
    ).set_index(["variable"])

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

    # Plot
    afolu_output.T.plot(legend=False, title="AFOLU Adoption [%]")

    # endregion

    # Multiply this by the estimated maximum extent and average mitigation potential flux to get emissions mitigated

    afolu_output.update(
        afolu_output.parallel_apply(
            lambda x: x.multiply(
                max_extent.loc[
                    slice(None),
                    slice(None),
                    [x.name[2]],
                    [x.name[3].replace("Observed adoption", "Max extent")],
                ]
            ).squeeze(),
            axis=1,
        ).fillna(0)
    )

    emissions_afolu_mitigated = afolu_output.copy()
    emissions_afolu_mitigated.update(
        emissions_afolu_mitigated.parallel_apply(
            lambda x: x.multiply(
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
            ).squeeze(),
            axis=1,
        ).fillna(0)
    )

    # Plot
    afolu_output.T.plot(legend=False, title="AFOLU Adoption [% of max extent]")
    emissions_afolu_mitigated.T.plot(
        legend=False, title="AFOLU Adoption [tCO2e mitigated]"
    )

    # Estimate emissions mitigated by avoided pathways

    # region

    emissions_afolu_avoided = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_avoided_pathways_input.csv").drop(
                columns=[
                    "Initial Extent (Mha)",
                    "Mitigation (Mg CO2/ha)",
                ]
            )
        )
        .set_index(
            [
                "model",
                "scenario",
                "region",
                "variable",
                "unit",
                "Initial Loss Rate (%)",
                "Rate of Improvement",
            ]
        )
        .loc[slice(None), [scenario], slice(None), slice(None), slice(None), :]
    )

    emissions_afolu_avoided.columns = emissions_afolu_avoided.columns.astype(int)
    emissions_afolu_avoided = emissions_afolu_avoided.loc[:, :proj_end_year]
    emissions_afolu_avoided.loc[:, :data_end_year] = 0

    emissions_afolu_avoided.loc[:, data_end_year + 1 :] = -emissions_afolu_avoided.loc[
        :, data_end_year + 1 :
    ].parallel_apply(
        lambda x: x.subtract(
            emissions_afolu_avoided.loc[x.name[0], x.name[1], x.name[2], x.name[3], :][
                data_end_year + 1
            ].values[0]
        ),
        axis=1,
    )

    avoided_adoption = -emissions_afolu_avoided.parallel_apply(
        lambda x: ((x[data_end_year] - x) / x.max()).fillna(0), axis=1
    )
    emissions_afolu_avoided = emissions_afolu_avoided.droplevel(
        [
            "Initial Loss Rate (%)",
            "Rate of Improvement",
        ]
    )
    avoided_adoption = avoided_adoption.droplevel(
        [
            "Initial Loss Rate (%)",
            "Rate of Improvement",
        ]
    )

    # Plot
    avoided_adoption.T.plot(legend=False, title="Avoided Emissions [% of max extent]")
    emissions_afolu_avoided.T.plot(legend=False, title="Avoided Emissions [tCO2e]")

    # endregion

    # Combine 'avoided_adoption' pathways with other pathways
    afolu_output = pd.concat([afolu_baseline, afolu_output, avoided_adoption])

    emissions_afolu_mitigated = pd.concat(
        [emissions_afolu_mitigated, emissions_afolu_avoided]
    )

    # endregion

    #################################
    #  UPDATE REGION & UNIT LABELS  #
    #################################

    # region

    # Replace unit label with MtCO2e
    emissions_afolu_mitigated.update(emissions_afolu_mitigated / 1e6)
    emissions_afolu_mitigated.rename(
        index={
            "Mha": "MtCO2e",
            "Tg dm": "MtCO2e",
            "m3": "MtCO2e",
        },
        inplace=True,
    )

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

        # Add Sector, Product_long, Flow_category, Flow_long indices
        each["product_long"] = each["variable"].str.split("|", expand=True)[0].values

        def addsector(x):
            if x["product_long"] in [
                "Biochar",
                "Cropland Soil Health",
                "Nitrogen Fertilizer Management",
                "Silvopasture",
                "Trees in Croplands",
                "Improved Rice",
                "Optimal Intensity",
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
                "Silvopasture",
                "Trees in Croplands",
                "Optimal Intensity",
            ]:
                return "CO2"
            if x["product_long"] in [
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Peat Restoration",
                "Improved Rice",
            ]:
                return "CH4"
            if x["product_long"] in [
                "Improved Rice",
                "Nitrogen Fertilizer Management",
            ]:
                return "N2O"

        each["flow_long"] = each.apply(lambda x: addgas(x), axis=1)

        each = each.set_index(
            [
                "model",
                "scenario",
                "region",
                "sector",
                "product_long",
                "flow_category",
                "flow_long",
                "unit",
            ]
        ).drop(columns=["variable"])

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
    emissions_afolu_mitigated = addindices(emissions_afolu_mitigated)

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    # AFOLU adoption
    afolu_output.to_csv("podi/data/output/afolu_output.csv")

    # AFOLU emissions mitigated
    emissions_afolu_mitigated.to_csv("podi/data/emissions_afolu_mitigated.csv")

    # endregion

    return
