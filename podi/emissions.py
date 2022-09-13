# region

import pandas as pd
from numpy import NaN
import numpy as np
import pyam
from pandarallel import pandarallel
import globalwarmingpotentials as gwp
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

pandarallel.initialize(progress_bar=True, nb_workers=6)

show_figs = False
save_figs = False

# endregion


def emissions(
    scenario,
    energy_output,
    afolu_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    #########################################
    #  CALCULATE CO2 EMISSIONS FROM ENERGY  #
    #########################################

    # region

    # Load emissions factors from https://www.ipcc-nggip.iges.or.jp/EFDB/find_ef.php?reset= , select 'Energy' and then 'Export to XLS' and save as emissions_factors.csv in podi/data/external/.
    # Emissions factors attribute emissions to the sector where the emissions are generated, e.g. electricity use in Buildings/Industry is zero emissions since those emissions are attributed to the Electric Power sector. Heat not produced on-site in Buildings/Industry is zero emissions since those emissions are attributed to the Industrial sector.

    # Load new df with index matching energy_output
    emissions_factors = pd.DataFrame(
        index=energy_output[
            ~(energy_output.reset_index().flow_category == "Non-energy use").values
        ].index,
        columns=energy_output.columns,
    ).fillna(0)

    # Load EFDB emissions factors to fill into emissions_factors df
    emissions_factors_efdb = pd.read_csv(
        "podi/data/external/emissions_factors_efdb.csv",
        usecols=["product_long", "value"],
    )

    emissions_factors = emissions_factors.parallel_apply(
        lambda x: x.add(
            emissions_factors_efdb[
                emissions_factors_efdb["product_long"] == x.name[5]
            ].squeeze()["value"]
        ),
        axis=1,
    )

    # Have emissions factors decrease by 1% per year from data_end_year to proj_end_year
    emissions_factors = emissions_factors.parallel_apply(
        lambda x: x.subtract(
            pd.Series(
                (x[x.first_valid_index()] * 0.005)
                * (np.arange(data_start_year, proj_end_year + 1) - data_start_year),
                index=x.index,
            ).rename(x.name)
        ).clip(lower=0),
        axis=1,
    )

    # Multiply energy by emission factors to get emissions estimates. Note that emission factors for non-energy use flows are set to 0
    emissions_energy = energy_output[
        ~(energy_output.reset_index().flow_category == "Non-energy use").values
    ].parallel_apply(
        lambda x: x.multiply(emissions_factors.loc[x.name]).fillna(0).squeeze(), axis=1
    )

    emissions_energy.index = emissions_energy.index.set_levels(
        emissions_energy.index.levels[10].str.replace("TJ", "Mt"), level=10
    )

    # Drop flow_category 'Transformation processes' to avoid double counting
    emissions_energy.update(
        emissions_energy[
            (
                emissions_energy.reset_index().flow_category
                == "Transformation processes"
            ).values
        ].multiply(0)
    )

    # Drop flow_category 'Heat output' in sector 'Industry' to avoid double counting
    emissions_energy.update(
        emissions_energy[
            (
                (emissions_energy.reset_index().sector == "Industrial")
                & (emissions_energy.reset_index().flow_category == "Heat output")
            ).values
        ].multiply(0)
    )

    # Save to CSV file
    emissions_energy.to_csv("podi/data/emissions_energy.csv")

    # Plot emissions_energy
    # region
    if show_figs is True:
        #################
        # GHG EMISSIONS #
        #################

        # region

        scenario = "pathway"
        model = "PD22"

        fig = (
            emissions_energy.loc[model]
            .groupby(["scenario", "sector", "flow_long"])
            .sum()
            .T
        )
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "sector", "flow_long"],
            value_name="Emissions",
        )

        for scenario in fig2["scenario"].unique():

            for sector in fig2["sector"].unique():

                fig = go.Figure()

                for flow_long in fig2["flow_long"].unique():
                    fig.add_trace(
                        go.Scatter(
                            name=flow_long,
                            line=dict(width=0.5),
                            x=fig2["year"].unique(),
                            y=fig2[
                                (fig2["scenario"] == scenario)
                                & (fig2["sector"] == sector)
                                & (fig2["flow_long"] == flow_long)
                            ]["Emissions"],
                            fill="tonexty",
                            stackgroup="one",
                        )
                    )

                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=2, color="black"),
                        x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                        y=pd.Series(
                            emissions_energy.loc[model, scenario, slice(None), sector]
                            .loc[:, :data_end_year]
                            .sum(),
                            index=emissions_energy.columns,
                        ).loc[:data_end_year],
                        fill="none",
                        stackgroup="two",
                        showlegend=True,
                    )
                )

                fig.update_layout(
                    title={
                        "text": "Emissions, World"
                        + ", "
                        + str(sector).capitalize()
                        + ", "
                        + str(scenario).capitalize(),
                        "xanchor": "center",
                        "x": 0.5,
                        "y": 0.9,
                    },
                    yaxis={"title": "MtCO2e"},
                    legend=dict(font=dict(size=8)),
                )

                fig.show()

        # endregion

        ###################################
        # GHG EMISSIONS MITIGATION WEDGES #
        ###################################

        # region

        scenario = "pathway"
        model = "PD22"

        fig = (
            (
                emissions_energy.loc[model, "baseline"].subtract(
                    emissions_energy.loc[model, scenario]
                )
            )
            .groupby(["sector", "flow_long"])
            .sum()
        ).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["sector", "flow_long"],
            value_name="Emissions",
        )

        for sector in fig2["sector"].unique():

            fig = go.Figure()

            spacer = emissions_energy.loc[model, scenario, slice(None), sector].sum()

            fig.add_trace(
                go.Scatter(
                    name="",
                    line=dict(width=0),
                    x=spacer.index.values[spacer.index.values >= data_end_year],
                    y=spacer[spacer.index.values >= data_end_year],
                    fill="none",
                    stackgroup="one",
                    showlegend=False,
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=2, color="black"),
                    x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                    y=pd.Series(
                        emissions_energy.loc[model, scenario, slice(None), sector]
                        .loc[:, :data_end_year]
                        .sum(),
                        index=emissions_energy.columns,
                    ).loc[:data_end_year],
                    fill="none",
                    stackgroup="two",
                    showlegend=True,
                )
            )

            for flow_long in fig2["flow_long"].unique():
                fig.add_trace(
                    go.Scatter(
                        name=sector + ", " + flow_long,
                        line=dict(width=0.5),
                        x=fig2[fig2["year"] > data_end_year]["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow_long)
                            & (fig2["year"] > data_end_year)
                        ]["Emissions"],
                        fill="tonexty",
                        stackgroup="one",
                    )
                )

            fig.update_layout(
                title={
                    "text": "Emissions Mitigated, World"
                    + ", "
                    + str(sector).capitalize()
                    + ", "
                    + str(scenario).capitalize(),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.9,
                },
                yaxis={"title": "MtCO2e"},
                legend=dict(font=dict(size=8)),
            )

            fig.show()

        # endregion

    # endregion

    # endregion

    ########################################
    #  CALCULATE GHG EMISSIONS FROM AFOLU  #
    ########################################

    # region

    # Create emissions factors using timeseries of average mitigation potential flux of each subvertical
    # region

    # Define a function that takes piecewise functions as input and outputs a continuous timeseries (this is used for input data provided for (1) maximum extent, and (2) average mitigation potential flux)
    def piecewise_to_continuous(variable):

        # Load the 'Input Data' tab of TNC's 'Positive Disruption NCS Vectors' google spreadsheet
        name = (
            pd.read_csv("podi/data/TNC/flux.csv")
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

        # Create a 'variable' column that concatenates the 'Subvertical' and 'Metric' columns
        name["variable"] = name.parallel_apply(
            lambda x: "|".join([x["Subvertical"], x["Metric"]]), axis=1
        )
        name.drop(columns=["Subvertical", "Metric"], inplace=True)

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

        # If Duration 1 is 'NA' or longer than proj_end_year - afolu_output.columns[0], set to proj_end_year - afolu_output.columns[0]
        name["Duration 1 (Years)"] = np.where(
            (
                (name["Duration 1 (Years)"].isna())
                | (name["Duration 1 (Years)"] > proj_end_year - afolu_output.columns[0])
            ),
            proj_end_year - afolu_output.columns[0],
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
            columns=np.arange(afolu_output.columns[0], proj_end_year + 1, 1),
            dtype=float,
        )

        # Define a function that places values in each timeseries for the durations specified, and interpolates
        def rep(x):
            x0 = x
            x0.loc[afolu_output.columns[0]] = x.name[5]
            x0.loc[afolu_output.columns[0] + x.name[6]] = x.name[7]
            x0.loc[
                min(
                    afolu_output.columns[0] + x.name[6] + x.name[8],
                    proj_end_year - afolu_output.columns[0],
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

    flux = piecewise_to_continuous("Avg mitigation potential flux").sort_index()

    # Define the flux of 'Avoided Coastal Impacts' and 'Avoided Forest Conversion'
    afolu_avoided = (
        pd.DataFrame(
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
        )
        .fillna(0)
        .sort_index()
    )

    # FIX "Mitigation (MtCO2e/ha)" to be "(tCO2e/ha)" once TNC confirms that this is the correct unit (i.e. the data is already in tCO2e/ha, just mislabeled)
    flux_avoided = (
        pd.concat(
            [
                afolu_avoided.drop(
                    columns=[
                        "Initial Extent (Mha)",
                        "Initial Loss Rate (%)",
                        "Rate of Improvement",
                        "Duration",
                    ]
                ),
                pd.DataFrame(
                    columns=flux.columns,
                ),
            ]
        )
        .set_index(pyam.IAMC_IDX)
        .parallel_apply(
            lambda x: x[flux.columns[0:]].fillna(x["Mitigation (MtCO2e/ha)"]),
            axis=1,
        )
        .rename(
            index={
                "Avoided Coastal Impacts": "Avoided Coastal Impacts|Avg mitigation potential flux",
                "Avoided Forest Conversion": "Avoided Forest Conversion|Avg mitigation potential flux",
                "Mha": "tCO2e/ha/yr",
            }
        )
    )

    # Combine flux estimates
    flux = pd.concat([flux, flux_avoided])

    # Change flux units for Nitrogen Fertilizer Management from MtCO2e/percentile improvement to tCO2e/percentile improvement, to match other subverticals
    flux = pd.concat(
        [
            flux[
                ~(
                    flux.reset_index().unit.isin(["MtCO2e/percentile improvement"])
                ).values
            ],
            flux[
                (flux.reset_index().unit.isin(["MtCO2e/percentile improvement"])).values
            ]
            .multiply(1e6)
            .rename(
                index={"MtCO2e/percentile improvement": "tCO2e/percentile improvement"}
            ),
        ]
    )

    # Change flux units for tCO2e/ha to tCO2e/Mha, which matches the current units for afolu_output (Mha)
    flux = pd.concat(
        [
            flux[~(flux.reset_index().unit.isin(["tCO2e/ha/yr"])).values],
            flux[(flux.reset_index().unit.isin(["tCO2e/ha/yr"])).values]
            .multiply(1e6)
            .rename(index={"tCO2e/ha/yr": "tCO2e/Mha/yr"}),
        ]
    )

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "region"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    flux = (
        (flux.reset_index().set_index(["region"]).merge(regions, on=["region"]))
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "variable",
                "unit",
            ]
        )
        .rename_axis(index={"WEB Region": "region"})
    ).drop(columns="region")

    # Plot Average Mitigation Flux [tCO2e/Mha/yr, tCO2e/m3/yr, tCo2e/percentile improvement]
    # region
    if show_figs is True:
        fig = flux.droplevel(["model", "scenario", "unit"]).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["region", "variable"],
            value_name="Avg mitigation potential flux",
        )

        for subvertical in fig2["variable"].unique():

            fig = go.Figure()

            for region in fig2["region"].unique():

                # Make modeled trace
                fig.add_trace(
                    go.Scatter(
                        name=region,
                        line=dict(width=1),
                        x=fig2[(fig2["variable"] == subvertical)]["year"].unique()
                        - fig2[(fig2["variable"] == subvertical)]["year"]
                        .unique()
                        .min(),
                        y=fig2[
                            (fig2["variable"] == subvertical)
                            & (fig2["region"] == region)
                        ]["Avg mitigation potential flux"],
                        legendgroup=region,
                        showlegend=True,
                    )
                )

            fig.update_layout(
                title={
                    "text": "Average Mitigation Potential Flux, "
                    + subvertical.replace("|Avg mitigation potential flux", ""),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                yaxis={"title": "tCO2e/Mha/yr"},
                xaxis={"title": "Years from implementation"},
                margin_b=0,
                margin_t=20,
                margin_l=10,
                margin_r=10,
            )

            if (
                subvertical
                == "Improved Forest Management|Avg mitigation potential flux"
            ):
                fig.update_layout(yaxis={"title": "tCO2e/m3/yr"})

            if (
                subvertical
                == "Nitrogen Fertilizer Management|Avg mitigation potential flux"
            ):
                fig.update_layout(yaxis={"title": "tCO2e/percentile improvement"})

            if show_figs is True:
                fig.show()

            pio.write_html(
                fig,
                file=(
                    "./charts/afolu_flux-"
                    + str(
                        subvertical.replace("|Avg mitigation potential flux", "")
                    ).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    # endregion

    # Load historical and baseline emissions estimates (retrieved from FAOSTAT)
    # region
    emissions_afolu = (
        pd.read_csv("podi/data/FAO/Emissions_Totals_E_All_Data_NOFLAG.csv")
        .drop(
            columns=[
                "Area Code",
                "Item Code",
                "Element Code",
                "Source Code",
                "Source",
            ]
        )
        .rename(
            columns={
                "Area": "region",
                "Item": "product_long",
                "Element": "flow_category",
                "Unit": "unit",
            }
        )
        .set_index("region")
    )
    emissions_afolu.columns = emissions_afolu.columns.str.replace("Y", "", regex=True)

    # Drop redundant emissions
    emissions_afolu = emissions_afolu[
        (
            emissions_afolu.flow_category.isin(
                [
                    "Emissions (CH4)",
                    "Emissions (N2O)",
                    "Emissions (CO2)",
                ]
            )
        )
        & (~emissions_afolu.product_long.isin(["Forestland"]))
    ]

    # Change FAO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "FAO Region"],
            ).dropna(axis=0)
        )
        .set_index(["FAO Region"])
        .rename_axis(index={"FAO Region": "region"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add Model and Scenario indices
    emissions_afolu["model"] = "PD22"
    emissions_afolu["scenario"] = "baseline"

    # Add Sector index
    def addsector(x):
        if x["product_long"] in [
            "Enteric Fermentation",
            "Manure Management",
            "Rice Cultivation",
            "Synthetic Fertilizers",
            "Manure applied to Soils",
            "Manure left on Pasture",
            "Crop Residues",
            "Burning - Crop residues",
        ]:
            return "Agriculture"
        elif x["product_long"] in [
            "Net Forest conversion",
            "Forestland",
            "Savanna fires",
            "Fires in humid tropical forests",
            "Forest fires",
            "Fires in organic soils",
            "Drained organic soils (CO2)",
            "Drained organic soils (N2O)",
        ]:
            return "Forests & Wetlands"

    emissions_afolu["sector"] = emissions_afolu.parallel_apply(
        lambda x: addsector(x), axis=1
    )

    # Split Emissions and Gas into separate columns
    def splitgas(x):
        if x["flow_category"] in ["Emissions (CO2)"]:
            return "CO2"
        elif x["flow_category"] in ["Emissions (CH4)"]:
            return "CH4"
        elif x["flow_category"] in ["Emissions (N2O)"]:
            return "N2O"

    emissions_afolu["flow_long"] = emissions_afolu.parallel_apply(
        lambda x: splitgas(x), axis=1
    )

    emissions_afolu["flow_category"] = "Emissions"
    emissions_afolu["product_category"] = "AFOLU"
    emissions_afolu["product_short"] = emissions_afolu["product_long"]
    emissions_afolu["flow_short"] = emissions_afolu["flow_long"]

    emissions_afolu = (
        (
            emissions_afolu.reset_index()
            .set_index(["region"])
            .merge(regions, on=["region"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
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
        .rename_axis(index={"WEB Region": "region"})
    ).drop(columns="region")

    # Select data between data_start_year and proj_end_year
    emissions_afolu.columns = emissions_afolu.columns.astype(int)
    emissions_afolu = emissions_afolu.loc[:, data_start_year:proj_end_year]

    # Change unit from kt to Mt
    emissions_afolu = emissions_afolu.multiply(1e-3)
    emissions_afolu = emissions_afolu.rename(index={"kilotonnes": "Mt"})

    # Drop rows with NaN in index and/or all year columns, representing duplicate regions and/or emissions
    emissions_afolu = emissions_afolu[
        ~(
            (emissions_afolu.index.get_level_values(3).isna())
            | (emissions_afolu.isna().all(axis=1))
        )
    ]

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_afolu[np.arange(2021, 2030, 1)] = NaN
    emissions_afolu[np.arange(2031, 2050, 1)] = NaN
    if proj_end_year > 2050:
        emissions_afolu[proj_end_year] = emissions_afolu[2050]
        emissions_afolu[np.arange(2051, proj_end_year, 1)] = NaN
    emissions_afolu = emissions_afolu.sort_index(axis=1)
    emissions_afolu.loc[:, data_start_year] = emissions_afolu.loc[
        :, data_start_year
    ].where(~emissions_afolu.loc[:, data_start_year].isna(), 0)
    emissions_afolu.interpolate(method="linear", axis=1, inplace=True)
    emissions_afolu.fillna(method="bfill", inplace=True)

    # endregion

    # Multiply afolu_output by emissions factors to get emissions estimates
    # region

    # Calculate emissions mitigated by multiplying adoption in each year by avg mitigtation potential flux (over the entire range of year to proj_end_year), to represent the time-dependent mitigation flux for adoption in each year
    emissions_afolu_mitigated = pd.DataFrame(
        index=afolu_output.index, columns=afolu_output.columns
    )
    emissions_afolu_mitigated.reset_index(inplace=True)
    emissions_afolu_mitigated.unit = (
        emissions_afolu_mitigated.unit.str.replace("Mha", "tCO2e", regex=True)
        .replace("m3", "tCO2e", regex=True)
        .replace("Percent adoption", "tCO2e", regex=True)
    )
    emissions_afolu_mitigated.set_index(
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
        ],
        inplace=True,
    )

    for year in afolu_output.loc[:, data_start_year + 1 : proj_end_year].columns:

        # Find new adoption in year, multiply by flux and a 'baseline' copy of flux
        emissions_afolu_mitigated_year = afolu_output.parallel_apply(
            lambda x: (x.loc[year] - x.loc[year - 1])
            * (
                pd.concat(
                    [flux, flux.rename(index={scenario: "baseline"}, level=1)]
                ).loc[
                    slice(None),
                    [x.name[1]],
                    [x.name[2]],
                    [x.name[5] + "|Avg mitigation potential flux"],
                ]
            )
            .squeeze()
            .rename(x.name),
            axis=1,
        ).fillna(0)

        emissions_afolu_mitigated_year.reset_index(inplace=True)
        emissions_afolu_mitigated_year.unit = (
            emissions_afolu_mitigated_year.unit.str.replace("m3", "tCO2e", regex=True)
            .replace("Mha", "tCO2e", regex=True)
            .replace("Percent adoption", "tCO2e", regex=True)
        )

        emissions_afolu_mitigated_year.set_index(
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
            ],
            inplace=True,
        )

        # Update timerseries to start at 'year'
        emissions_afolu_mitigated_year.columns = np.arange(
            year, year + len(afolu_output.columns), 1
        )

        # Add to cumulative count
        emissions_afolu_mitigated = emissions_afolu_mitigated_year.fillna(0).add(
            emissions_afolu_mitigated, fill_value=0
        )

    # Cut output to data_start_year : proj_end_year
    emissions_afolu_mitigated = emissions_afolu_mitigated.loc[
        :, data_start_year:proj_end_year
    ]

    # Scale improved rice mitigation to be 58% from CH4 and 42% from N2O
    def improvedrice(each):
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

    emissions_afolu_mitigated = improvedrice(emissions_afolu_mitigated)

    # Convert from tCO2e to Mt
    emissions_afolu_mitigated = emissions_afolu_mitigated.multiply(1e-6)
    emissions_afolu_mitigated.rename(
        index={"tCO2e": "Mt"},
        inplace=True,
    )

    # Add missing GWP values to gwp
    # Choose version of GWP values
    version = "AR6GWP100"  # Choose from ['SARGWP100', 'AR4GWP100', 'AR5GWP100', 'AR5CCFGWP100', 'AR6GWP100', 'AR6GWP20', 'AR6GWP500', 'AR6GTP100']

    gwp.data[version].update(
        {
            "CO2": 1,
            "BC": 500,
            "CO": 0,
            "NH3": 0,
            "NMVOC": 0,
            "NOx": 0,
            "OC": 0,
            "SO2": 0,
        }
    )

    emissions_afolu_mitigated = emissions_afolu_mitigated.parallel_apply(
        lambda x: x.divide(gwp.data[version][x.name[8]]), axis=1
    )

    # Assume emissions mitigated start at current year
    emissions_afolu_mitigated.update(
        emissions_afolu_mitigated.loc[:, data_end_year:].parallel_apply(
            lambda x: x.subtract(x.loc[data_end_year]), axis=1
        )
    )
    emissions_afolu_mitigated.update(
        emissions_afolu_mitigated.loc[:, :data_end_year].multiply(0)
    )

    # endregion

    # Combine additional emissions sources with emissions mitigated from NCS
    emissions_afolu = pd.concat(
        [
            emissions_afolu,
            emissions_afolu.rename(index={"baseline": scenario}),
            -emissions_afolu_mitigated,
        ]
    )

    # Add indices product_category, product_short, flow_short
    emissions_afolu.reset_index(inplace=True)
    emissions_afolu["product_category"] = "Emissions"
    emissions_afolu["product_short"] = "EM"
    emissions_afolu["flow_short"] = "AFOLU"

    emissions_afolu = emissions_afolu.set_index(
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

    # SOME AFOLU RESULTS LOOK INCORRECT, FIX THEM HERE WHILE WAITING FOR TNC FEEDBACK
    fix_afolu = True
    if fix_afolu is True:
        # Avoided Coastal Impacts (flux looks too high by 10)
        emissions_afolu.update(
            emissions_afolu[
                (
                    emissions_afolu.reset_index().product_long
                    == "Avoided Coastal Impacts"
                ).values
            ].multiply(1e-1)
        )
        # Avoided Forest Conversion (looks too low by 10)
        emissions_afolu.update(
            emissions_afolu[
                (
                    emissions_afolu.reset_index().product_long
                    == "Avoided Forest Conversion"
                ).values
            ].multiply(1e1)
        )
        # Avoided Peat Impacts (looks too low by 1e5)
        emissions_afolu.update(
            emissions_afolu[
                (
                    emissions_afolu.reset_index().product_long == "Avoided Peat Impacts"
                ).values
            ].multiply(1e5)
        )
        # Avoided Cropland Soil Health (looks too low by 1e1)
        emissions_afolu.update(
            emissions_afolu[
                (
                    emissions_afolu.reset_index().product_long == "Cropland Soil Health"
                ).values
            ].multiply(1e1)
        )

    # Drop rows with NaN in all year columns, representing duplicate regions and/or emissions
    emissions_afolu = emissions_afolu[~((emissions_afolu.isna().all(axis=1)))]

    # Plot emissions_afolu
    # region

    #################
    # GHG EMISSIONS #
    #################

    # region

    scenario = scenario
    model = "PD22"

    fig = (
        emissions_afolu.loc[model]
        .groupby(["scenario", "sector", "product_long", "flow_long"])
        .sum()
        .T
    )
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["scenario", "sector", "product_long", "flow_long"],
        value_name="Emissions",
    )

    for gas in ["CO2", "CH4", "N2O"]:
        for scenario in fig2["scenario"].unique():

            for sector in fig2["sector"].unique():

                fig = go.Figure()

                for product_long in fig2.sort_values("Emissions", ascending=False)[
                    "product_long"
                ].unique():
                    fig.add_trace(
                        go.Scatter(
                            name=product_long,
                            line=dict(
                                width=0.5,
                                color=np.concatenate(
                                    (
                                        px.colors.qualitative.Dark24,
                                        px.colors.qualitative.Dark24,
                                    )
                                )[
                                    fig2["product_long"]
                                    .unique()
                                    .tolist()
                                    .index(product_long)
                                ],
                            ),
                            x=fig2["year"].unique(),
                            y=fig2[
                                (fig2["scenario"] == scenario)
                                & (fig2["sector"] == sector)
                                & (fig2["product_long"] == product_long)
                                & (fig2["flow_long"] == gas)
                            ]["Emissions"],
                            fill="tonexty",
                            stackgroup="one",
                        )
                    )

                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=2, color="black"),
                        x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                        y=pd.Series(
                            emissions_afolu[emissions_afolu.sum(axis=1) > 0]
                            .loc[
                                model,
                                scenario,
                                slice(None),
                                sector,
                                slice(None),
                                slice(None),
                                slice(None),
                                slice(None),
                                gas,
                            ]
                            .sum(),
                            index=emissions_afolu.columns,
                        ).loc[:data_end_year],
                        fill="none",
                        stackgroup="two",
                        showlegend=True,
                    )
                )

                fig.update_layout(
                    title={
                        "text": "Emissions, "
                        + "World, "
                        + gas
                        + ", "
                        + str(sector).capitalize()
                        + ", "
                        + str(scenario).capitalize(),
                        "xanchor": "center",
                        "x": 0.5,
                        "y": 0.9,
                    },
                    yaxis={"title": "Mt " + gas},
                    legend=dict(font=dict(size=8)),
                )

                if show_figs is True:
                    fig.show()

                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/emissions-"
                            + str(sector).capitalize()
                            + "-"
                            + str(gas)
                            + "-"
                            + str(scenario)
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )

    # endregion

    # endregion

    # endregion

    #########################################
    #  ADD IN ADDITIONAL EMISSIONS SOURCES  #
    #########################################

    # region

    # Load historical addtional emissions datasets
    gas_ceds = ["BC", "CO", "OC", "CH4", "CO2", "N2O", "NH3", "NOx", "SO2", "NMVOC"]

    emissions_additional = pd.DataFrame([])
    for gas in gas_ceds:
        emissions_additional = pd.concat(
            [
                emissions_additional,
                pd.read_csv(
                    "podi/data/CEDS/"
                    + gas
                    + "_CEDS_emissions_by_sector_country_2021_04_21.csv"
                ),
            ]
        )
    emissions_additional.columns = emissions_additional.columns.str.replace("X", "")

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "country"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()
    regions.index = (regions.index).str.lower()

    # Add Model, Scenario, and Flow_category indices
    emissions_additional["model"] = "PD22"
    emissions_additional["scenario"] = "baseline"
    emissions_additional["flow_category"] = "Emissions"

    # Change sector index to Product_long and 'em' to 'flow_long'
    emissions_additional.rename(
        columns={"sector": "product_long", "em": "flow_long"}, inplace=True
    )

    # Add Sector index
    def addsector2(x):
        if x["product_long"] in [
            "1A1a_Electricity-autoproducer",
            "1A1a_Electricity-public",
            "1A1a_Heat-production",
            "1A1bc_Other-transformation",
            "1B1_Fugitive-solid-fuels",
            "1B2_Fugitive-petr",
            "1B2b_Fugitive-NG-distr",
            "1B2b_Fugitive-NG-prod",
            "1B2d_Fugitive-other-energy",
            "7A_Fossil-fuel-fires",
        ]:
            return "Electric Power"
        elif x["product_long"] in [
            "1A3b_Road",
            "1A3c_Rail",
            "1A3di_Oil_Tanker_Loading",
            "1A3dii_Domestic-navigation",
            "1A3eii_Other-transp",
            "1A3ai_International-aviation",
            "1A3aii_Domestic-aviation",
            "1A3di_International-shipping",
        ]:
            return "Transportation"
        elif x["product_long"] in ["1A4b_Residential"]:
            return "Residential"
        elif x["product_long"] in ["1A4a_Commercial-institutional"]:
            return "Commercial"
        elif x["product_long"] in [
            "1A2a_Ind-Comb-Iron-steel",
            "1A2b_Ind-Comb-Non-ferrous-metals",
            "1A2c_Ind-Comb-Chemicals",
            "1A2d_Ind-Comb-Pulp-paper",
            "1A2e_Ind-Comb-Food-tobacco",
            "1A2f_Ind-Comb-Non-metalic-minerals",
            "1A2g_Ind-Comb-Construction",
            "1A2g_Ind-Comb-machinery",
            "1A2g_Ind-Comb-mining-quarying",
            "1A2g_Ind-Comb-other",
            "1A2g_Ind-Comb-textile-leather",
            "1A2g_Ind-Comb-transpequip",
            "1A2g_Ind-Comb-wood-products",
            "1A4c_Agriculture-forestry-fishing",
            "1A5_Other-unspecified",
            "2A1_Cement-production",
            "2A2_Lime-production",
            "2Ax_Other-minerals",
            "2B_Chemical-industry",
            "2B2_Chemicals-Nitric-acid",
            "2B3_Chemicals-Adipic-acid",
            "2C_Metal-production",
            "2D_Chemical-products-manufacture-processing",
            "2D_Degreasing-Cleaning",
            "2D_Other-product-use",
            "2D_Paint-application",
            "2H_Pulp-and-paper-food-beverage-wood",
            "2L_Other-process-emissions",
            "5A_Solid-waste-disposal",
            "5C_Waste-combustion",
            "5D_Wastewater-handling",
            "5E_Other-waste-handling",
            "6A_Other-in-total",
            "7BC_Indirect-N2O-non-agricultural-N",
        ]:
            return "Industrial"
        elif x["product_long"] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ]:
            return "Agriculture"

    emissions_additional["sector"] = emissions_additional.parallel_apply(
        lambda x: addsector2(x), axis=1
    )

    emissions_additional = (
        (
            emissions_additional.reset_index()
            .set_index(["country"])
            .merge(regions, on=["country"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "sector",
                "product_long",
                "flow_category",
                "flow_long",
                "units",
            ]
        )
        .rename_axis(index={"WEB Region": "region", "units": "unit"})
    ).drop(columns=["country", "index"])

    # Select data between data_start_year and proj_end_year
    emissions_additional.columns = emissions_additional.columns.astype(int)
    emissions_additional = emissions_additional.loc[:, data_start_year:proj_end_year]

    # Change unit from kt to Mt
    emissions_additional.update(emissions_additional / 1e3)
    emissions_additional = emissions_additional.rename(
        index={
            "ktC": "Mt",
            "ktCO": "Mt",
            "ktCH4": "Mt",
            "ktCO2": "Mt",
            "ktN2O": "Mt",
            "ktNH3": "Mt",
            "ktNO2": "Mt",
            "ktSO2": "Mt",
            "ktNMVOC": "Mt",
        }
    )

    # Drop rows with NaN in index and/or all year columns, representing duplicate regions and/or emissions
    emissions_additional = emissions_additional[
        ~(
            (emissions_additional.index.get_level_values(1).isna())
            | (emissions_additional.index.get_level_values(4).isna())
            | (emissions_additional.isna().all(axis=1))
        )
    ]

    # Save last valid index for emissions_additional (it changes, but the value here is used later)
    emissions_additional_last_valid_index = emissions_additional.columns.max()

    # Create projections by applying most current data value to all future years
    emissions_additional[
        np.arange(emissions_additional_last_valid_index, proj_end_year + 1, 1)
    ] = NaN
    emissions_additional = emissions_additional.sort_index(axis=1)
    emissions_additional.fillna(method="ffill", axis=1, inplace=True)

    # Drop double counted emissions
    def remove_doublecount(x):
        # Drop CO2 that was already estimated in energy module
        if x.name[4] in [
            "1A1a_Electricity-autoproducer",
            "1A1a_Electricity-public",
            "1A1a_Heat-production",
            "1A1bc_Other-transformation",
            "1A2a_Ind-Comb-Iron-steel",
            "1A2b_Ind-Comb-Non-ferrous-metals",
            "1A2c_Ind-Comb-Chemicals",
            "1A2d_Ind-Comb-Pulp-paper",
            "1A2e_Ind-Comb-Food-tobacco",
            "1A2f_Ind-Comb-Non-metalic-minerals",
            "1A2g_Ind-Comb-Construction",
            "1A2g_Ind-Comb-machinery",
            "1A2g_Ind-Comb-mining-quarying",
            "1A2g_Ind-Comb-other",
            "1A2g_Ind-Comb-textile-leather",
            "1A2g_Ind-Comb-transpequip",
            "1A2g_Ind-Comb-wood-products",
            "1A3b_Road",
            "1A3c_Rail",
            "1A3aii_Domestic-aviation",
            "1A3dii_Domestic-navigation",
            "1A3eii_Other-transp",
            "1A3ai_International-aviation",
            "1A3di_International-shipping",
            "1A4a_Commercial-institutional",
            "1A4b_Residential",
            "1A4c_Agriculture-forestry-fishing",
            "1A5_Other-unspecified",
        ] and x.name[6] in ["CO2"]:
            x = x.multiply(0)

        # Drop CO2, CH4, N2O that was already estimated in FAO historical data
        if x.name[4] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ] and x.name[6] in ["CO2", "CH4", "N2O"]:
            x = x.multiply(0)

        return x

    emissions_additional = emissions_additional.parallel_apply(
        lambda x: remove_doublecount(x), axis=1
    )

    # Get F-Gas data
    gas_edgar = [
        "C2F6",
        "C3F8",
        "C4F10",
        "C5F12",
        "C6F14",
        "c-C4F8",
        "CF4",
        "HCFC-141b",
        "HCFC-142b",
        "HFC-23",
        "HFC-32",
        "HFC-41",
        "HFC-43-10-mee",
        "HFC-125",
        "HFC-134",
        "HFC-134a",
        "HFC-143",
        "HFC-143a",
        "HFC-152a",
        "HFC-227ea",
        "HFC-236fa",
        "HFC-245fa",
        "HFC-365mfc",
        "NF3",
        "SF6",
    ]

    emissions_additional_fgas = pd.DataFrame([])
    for gas in gas_edgar:
        emissions_additional_fgas_new = pd.read_excel(
            io="podi/data/EDGAR/" + gas + "_1990_2018.xlsx",
            sheet_name="v6.0_EM_" + gas + "_IPCC2006",
            skiprows=9,
        ).drop(
            columns=[
                "IPCC_annex",
                "C_group_IM24_sh",
                "Name",
                "ipcc_code_2006_for_standard_report",
                "fossil_bio",
            ]
        )

        emissions_additional_fgas_new["flow_long"] = gas

        emissions_additional_fgas = pd.concat(
            [emissions_additional_fgas, emissions_additional_fgas_new]
        )

    emissions_additional_fgas.columns = emissions_additional_fgas.columns.str.replace(
        "Y_", ""
    )
    emissions_additional_fgas.columns = emissions_additional_fgas.columns.str.replace(
        "ipcc_code_2006_for_standard_report_name", "product_long"
    )

    # Add in column for units kT
    emissions_additional_fgas["unit"] = "kT"

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "Country_code_A3"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add Model and Scenario indices
    emissions_additional_fgas["model"] = "PD22"
    emissions_additional_fgas["scenario"] = "baseline"

    # Add Sector index
    def addsector3(x):
        if x["product_long"] in [
            "Metal Industry",
            "Other Product Manufacture and Use",
            "Electronics Industry",
            "Chemical Industry",
            "Product Uses as Substitutes for Ozone Depleting Substances",
        ]:
            return "Industrial"

    emissions_additional_fgas["sector"] = emissions_additional_fgas.parallel_apply(
        lambda x: addsector3(x), axis=1
    )

    emissions_additional_fgas["flow_category"] = "Emissions"

    emissions_additional_fgas = (
        (
            emissions_additional_fgas.reset_index()
            .set_index(["Country_code_A3"])
            .merge(regions, on=["Country_code_A3"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "sector",
                "product_long",
                "flow_category",
                "flow_long",
                "unit",
            ]
        )
        .rename_axis(index={"WEB Region": "region", "units": "unit"})
    ).drop(columns=["Country_code_A3", "index"])

    # Select data between data_start_year and proj_end_year
    emissions_additional_fgas.columns = emissions_additional_fgas.columns.astype(int)
    emissions_additional_fgas = emissions_additional_fgas.loc[
        :, data_start_year:proj_end_year
    ]

    # Change unit from kt to Mt
    emissions_additional_fgas.update(emissions_additional_fgas / 1e3)
    emissions_additional_fgas = emissions_additional_fgas.rename(index={"kT": "Mt"})

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_additional_fgas[
        np.arange(emissions_additional_fgas.columns.max() + 1, 2031, 1)
    ] = NaN
    emissions_additional_fgas[np.arange(2031, proj_end_year + 1, 1)] = NaN
    emissions_additional_fgas = emissions_additional_fgas.sort_index(axis=1)
    emissions_additional_fgas.interpolate(method="linear", axis=1, inplace=True)
    emissions_additional_fgas.fillna(method="bfill", inplace=True)

    # Combine all additional gases
    emissions_additional = pd.concat([emissions_additional, emissions_additional_fgas])

    # Drop rows with all zero values
    emissions_additional = emissions_additional[emissions_additional.sum(axis=1) != 0]

    # Create baseline and pathway scenarios
    emissions_additional = pd.concat(
        [
            emissions_additional,
            emissions_additional.rename(index={"baseline": scenario}),
        ]
    )

    # Project additional emissions using percent change in energy emissions in the energy sector
    percent_change = (
        emissions_energy[
            (
                emissions_energy.reset_index().flow_category == "Electricity output"
            ).values
        ]
        .groupby(["model", "scenario", "region"])
        .sum()
        .loc[:, emissions_additional_last_valid_index:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .replace(np.inf, 0)
        .add(1)
    )

    percent_change.update(
        percent_change.parallel_apply(
            lambda x: x.clip(
                upper=percent_change.loc[x.name[0], "baseline", x.name[2]]
                .squeeze()
                .rename(x.name)
            ),
            axis=1,
        )
    )

    emissions_additional = (
        emissions_additional.loc[
            :, data_start_year:emissions_additional_last_valid_index
        ]
        .reset_index()
        .set_index(["model", "scenario", "region"])
        .merge(
            percent_change.loc[:, emissions_additional_last_valid_index + 1 :],
            on=["model", "scenario", "region"],
        )
        .set_index(
            ["sector", "product_long", "flow_category", "flow_long", "unit"],
            append=True,
        )
    )

    emissions_additional.loc[
        :, emissions_additional_last_valid_index:
    ] = emissions_additional.loc[:, emissions_additional_last_valid_index:].cumprod(
        axis=1
    )

    # Rename product_long values
    """
    simple_index = {
        "Fossil fuels": "Fossil Fuel Heat",
        "1A1a_Electricity-autoproducer": "Fossil Fuels",
        "1A1a_Electricity-public": "Fossil Fuels",
        "1A1a_Heat-production": "Fossil Fuel Heat",
        "1A1bc_Other-transformation": "Other Fossil Transformation",
        "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
        "1B2_Fugitive-petr": "Fugitive Petroleum",
        "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
        "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
        "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
        "7A_Fossil-fuel-fires": "Fossil Fuel Fires",
        "1A2a_Ind-Comb-Iron-steel": "Other Industrial",
        "1A2b_Ind-Comb-Non-ferrous-metals": "Other Industrial",
        "1A2c_Ind-Comb-Chemicals": "Chemical Production",
        "1A2d_Ind-Comb-Pulp-paper": "Other Industrial",
        "1A2e_Ind-Comb-Food-tobacco": "Other Industrial",
        "1A2f_Ind-Comb-Non-metalic-minerals": "Other Industrial",
        "1A2g_Ind-Comb-Construction": "Other Industrial",
        "1A2g_Ind-Comb-machinery": "Other Industrial",
        "1A2g_Ind-Comb-mining-quarying": "Other Industrial",
        "1A2g_Ind-Comb-other": "Other Industrial",
        "1A2g_Ind-Comb-textile-leather": "Other Industrial",
        "1A2g_Ind-Comb-transpequip": "Other Industrial",
        "1A2g_Ind-Comb-wood-products": "Other Industrial",
        "1A4c_Agriculture-forestry-fishing": "Agriculture, Forestry, Fishing",
        "2A1_Cement-production": "Cement Production",
        "2A2_Lime-production": "Lime Production",
        "2Ax_Other-minerals": "Other Industrial",
        "2B_Chemical-industry": "Chemical Production",
        "2B2_Chemicals-Nitric-acid": "Other Industrial",
        "2B3_Chemicals-Adipic-acid": "Other Industrial",
        "2C_Metal-production": "Metal Production",
        "2D_Chemical-products-manufacture-processing": "Chemical Production",
        "2D_Degreasing-Cleaning": "Chemical Production",
        "2D_Other-product-use": "Chemical Production",
        "2D_Paint-application": "Chemical Production",
        "2H_Pulp-and-paper-food-beverage-wood": "Other Industrial",
        "2L_Other-process-emissions": "Other Industrial",
        "5A_Solid-waste-disposal": "Solid Waste Disposal",
        "5C_Waste-combustion": "Other Industrial",
        "5D_Wastewater-handling": "Wastewater Handling",
        "5E_Other-waste-handling": "Other Industrial",
        "7BC_Indirect-N2O-non-agricultural-N": "Other Industrial",
        "1A5_Other-unspecified": "Other Industrial",
        "6A_Other-in-total": "Other Industrial",
        "1A3b_Road": "Road Transport",
        "1A3c_Rail": "Rail Transport",
        "1A3di_Oil_Tanker_Loading": "Maritime Transport",
        "1A3dii_Domestic-navigation": "Maritime Transport",
        "1A3eii_Other-transp": "Other Transport",
        "1A4a_Commercial-institutional": "Commercial Buildings",
        "1A4b_Residential": "Residential Buildings",
        "3B_Manure-management": "Manure Management",
        "3D_Rice-Cultivation": "Rice Cultivation",
        "3D_Soil-emissions": "Fertilized Soils",
        "3E_Enteric-fermentation": "Enteric Fermentation",
        "3I_Agriculture-other": "Other Agricultural",
    }

    detailed_index = {
        "Fossil fuels": "Fossil fuel Heat",
        "1A1a_Electricity-autoproducer": "Fossil Fuels",
        "1A1a_Electricity-public": "Fossil Fuels",
        "1A1a_Heat-production": "Fossil fuel Heat",
        "1A1bc_Other-transformation": "Other Fossil Transformation",
        "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels",
        "1B2_Fugitive-petr": "Fugitive Petroleum",
        "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution",
        "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production",
        "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other",
        "7A_Fossil-fuel-fires": "Fossil Fuel Fires",
        "1A2a_Ind-Comb-Iron-steel": "Steel Production",
        "1A2b_Ind-Comb-Non-ferrous-metals": "Non-ferrous Metal Production",
        "1A2c_Ind-Comb-Chemicals": "Chemical Production",
        "1A2d_Ind-Comb-Pulp-paper": "Pulp-Paper Production",
        "1A2e_Ind-Comb-Food-tobacco": "Food Production",
        "1A2f_Ind-Comb-Non-metalic-minerals": "Non-metalic Mineral Production",
        "1A2g_Ind-Comb-Construction": "Construction",
        "1A2g_Ind-Comb-machinery": "Machinery",
        "1A2g_Ind-Comb-mining-quarying": "Mining, Quarying",
        "1A2g_Ind-Comb-other": "Other Industrial",
        "1A2g_Ind-Comb-textile-leather": "Textile, Leather Production",
        "1A2g_Ind-Comb-transpequip": "Transportation Equipment Production",
        "1A2g_Ind-Comb-wood-products": "Wood Production",
        "1A4c_Agriculture-forestry-fishing": "Agriculture, Forestry, Fishing",
        "2A1_Cement-production": "Cement Production",
        "2A2_Lime-production": "Lime Production",
        "2Ax_Other-minerals": "Other Mineral Production",
        "2B_Chemical-industry": "Chemical Production",
        "2B2_Chemicals-Nitric-acid": "Nitric Acid Production",
        "2B3_Chemicals-Adipic-acid": "Adipic Acid Production",
        "2C_Metal-production": "Metal Production",
        "2D_Chemical-products-manufacture-processing": "Chemical Production",
        "2D_Degreasing-Cleaning": "Chemical Production",
        "2D_Other-product-use": "Chemical Production",
        "2D_Paint-application": "Chemical Production",
        "2H_Pulp-and-paper-food-beverage-wood": "Food Production",
        "2L_Other-process-emissions": "Other Industrial",
        "5A_Solid-waste-disposal": "Solid Waste Disposal",
        "5C_Waste-combustion": "Waste Combustion",
        "5D_Wastewater-handling": "Wastewater Handling",
        "5E_Other-waste-handling": "Waste Combustion",
        "7BC_Indirect-N2O-non-agricultural-N": "Indirect N2O from Non-Ag N",
        "1A5_Other-unspecified": "Other Industrial",
        "6A_Other-in-total": "Other Industrial",
        "1A3b_Road": "Road Transport",
        "1A3c_Rail": "Rail Transport",
        "1A3di_Oil_Tanker_Loading": "Maritime Transport",
        "1A3dii_Domestic-navigation": "Maritime Transport",
        "1A3eii_Other-transp": "Other Transport",
        "1A4a_Commercial-institutional": "Commercial Buildings",
        "1A4b_Residential": "Residential Buildings",
        "3B_Manure-management": "Manure Management",
        "3D_Rice-Cultivation": "Rice Cultivation",
        "3D_Soil-emissions": "Fertilized Soils",
        "3E_Enteric-fermentation": "Enteric Fermentation",
        "3I_Agriculture-other": "Other Agricultural",
    }
    """
    detailed_index_with_addtl = {
        "Fossil fuels": "Fossil fuel Heat, Addtl Emissions",
        "1A1a_Electricity-autoproducer": "Fossil Fuels, Addtl Emissions",
        "1A1a_Electricity-public": "Fossil Fuels, Addtl Emissions",
        "1A1a_Heat-production": "Fossil fuel Heat, Addtl Emissions",
        "1A1bc_Other-transformation": "Other Fossil Transformation, Addtl Emissions",
        "1B1_Fugitive-solid-fuels": "Fugitive Solid Fuels, Addtl Emissions",
        "1B2_Fugitive-petr": "Fugitive Petroleum, Addtl Emissions",
        "1B2b_Fugitive-NG-distr": "Fugitive Natural Gas, Distribution, Addtl Emissions",
        "1B2b_Fugitive-NG-prod": "Fugitive Natural Gas, Production, Addtl Emissions",
        "1B2d_Fugitive-other-energy": "Fugitive Fossil Fuels, Other, Addtl Emissions",
        "7A_Fossil-fuel-fires": "Fossil Fuel Fires, Addtl Emissions",
        "1A2a_Ind-Comb-Iron-steel": "Steel Production, Addtl Emissions",
        "1A2b_Ind-Comb-Non-ferrous-metals": "Non-ferrous Metal Production, Addtl Emissions",
        "1A2c_Ind-Comb-Chemicals": "Chemical Production, Addtl Emissions",
        "1A2d_Ind-Comb-Pulp-paper": "Pulp-Paper Production, Addtl Emissions",
        "1A2e_Ind-Comb-Food-tobacco": "Food Production, Addtl Emissions",
        "1A2f_Ind-Comb-Non-metalic-minerals": "Non-metalic Mineral Production, Addtl Emissions",
        "1A2g_Ind-Comb-Construction": "Construction, Addtl Emissions",
        "1A2g_Ind-Comb-machinery": "Machinery, Addtl Emissions",
        "1A2g_Ind-Comb-mining-quarying": "Mining, Quarying, Addtl Emissions",
        "1A2g_Ind-Comb-other": "Other Industrial, Addtl Emissions",
        "1A2g_Ind-Comb-textile-leather": "Textile, Leather Production, Addtl Emissions",
        "1A2g_Ind-Comb-transpequip": "Transportation Equipment Production, Addtl Emissions",
        "1A2g_Ind-Comb-wood-products": "Wood Production, Addtl Emissions",
        "1A4c_Agriculture-forestry-fishing": "Agriculture, Forestry, Fishing, Addtl Emissions",
        "2A1_Cement-production": "Cement Production, Addtl Emissions",
        "2A2_Lime-production": "Lime Production, Addtl Emissions",
        "2Ax_Other-minerals": "Other Mineral Production, Addtl Emissions",
        "2B_Chemical-industry": "Chemical Production, Addtl Emissions",
        "2B2_Chemicals-Nitric-acid": "Nitric Acid Production, Addtl Emissions",
        "2B3_Chemicals-Adipic-acid": "Adipic Acid Production, Addtl Emissions",
        "2C_Metal-production": "Metal Production, Addtl Emissions",
        "2D_Chemical-products-manufacture-processing": "Chemical Production, Addtl Emissions",
        "2D_Degreasing-Cleaning": "Chemical Production, Addtl Emissions",
        "2D_Other-product-use": "Chemical Production, Addtl Emissions",
        "2D_Paint-application": "Chemical Production, Addtl Emissions",
        "2H_Pulp-and-paper-food-beverage-wood": "Food Production, Addtl Emissions",
        "2L_Other-process-emissions": "Other Industrial, Addtl Emissions",
        "5A_Solid-waste-disposal": "Solid Waste Disposal, Addtl Emissions",
        "5C_Waste-combustion": "Waste Combustion, Addtl Emissions",
        "5D_Wastewater-handling": "Wastewater Handling, Addtl Emissions",
        "5E_Other-waste-handling": "Waste Combustion, Addtl Emissions",
        "7BC_Indirect-N2O-non-agricultural-N": "Indirect N2O from Non-Ag N, Addtl Emissions",
        "1A5_Other-unspecified": "Other Industrial, Addtl Emissions",
        "6A_Other-in-total": "Other Industrial, Addtl Emissions",
        "1A3b_Road": "Road Transport, Addtl Emissions",
        "1A3c_Rail": "Rail Transport, Addtl Emissions",
        "1A3di_Oil_Tanker_Loading": "Maritime Transport, Addtl Emissions",
        "1A3dii_Domestic-navigation": "Maritime Transport, Addtl Emissions",
        "1A3eii_Other-transp": "Other Transport, Addtl Emissions",
        "1A4a_Commercial-institutional": "Addtl Emissions",
        "1A4b_Residential": "Addtl Emissions",
        "3B_Manure-management": "Manure Management, Addtl Emissions",
        "3D_Rice-Cultivation": "Rice Cultivation, Addtl Emissions",
        "3D_Soil-emissions": "Fertilized Soils, Addtl Emissions",
        "3E_Enteric-fermentation": "Enteric Fermentation, Addtl Emissions",
        "3I_Agriculture-other": "Other Agricultural, Addtl Emissions",
    }

    emissions_additional = (
        emissions_additional.rename(index=detailed_index_with_addtl)
        .groupby(
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
        )
        .sum()
    )

    # Add indices product_category, product_short, flow_short
    emissions_additional["product_category"] = "Emissions"
    emissions_additional["product_short"] = "EM"
    emissions_additional["flow_short"] = "IND"

    emissions_additional = (
        emissions_additional.reset_index()
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
        .sort_index()
    )

    # Plot emissions_additional
    # region
    if show_figs is True:
        #################
        # GHG EMISSIONS #
        #################

        # region

        scenario = "pathway"
        model = "PD22"
        df = emissions_additional.loc[
            model, slice(None), slice(None), ["Electric Power"]
        ]

        fig = df.groupby(["scenario", "sector", "product_long", "flow_long"]).sum().T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "sector", "product_long", "flow_long"],
            value_name="Emissions",
        )

        for gas in fig2["flow_long"].unique():
            for scenario in fig2["scenario"].unique():

                for sector in fig2["sector"].unique():

                    fig = go.Figure()

                    for product_long in fig2.sort_values("Emissions", ascending=False)[
                        "product_long"
                    ].unique():
                        fig.add_trace(
                            go.Scatter(
                                name=product_long + ", " + gas,
                                line=dict(width=0.5),
                                x=fig2["year"].unique(),
                                y=fig2[
                                    (fig2["scenario"] == scenario)
                                    & (fig2["sector"] == sector)
                                    & (fig2["product_long"] == product_long)
                                    & (fig2["flow_long"] == gas)
                                ]["Emissions"],
                                fill="tonexty",
                                stackgroup="one",
                            )
                        )

                    fig.add_trace(
                        go.Scatter(
                            name="Historical",
                            line=dict(width=2, color="black"),
                            x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                            y=fig2[
                                (fig2["scenario"] == scenario)
                                & (fig2["sector"] == sector)
                                & (fig2["flow_long"] == gas)
                                & (fig2["year"] <= data_end_year)
                            ]
                            .groupby(["year"])
                            .sum()["Emissions"],
                            fill="none",
                            stackgroup="two",
                            showlegend=True,
                        )
                    )

                    fig.update_layout(
                        title={
                            "text": "Emissions, "
                            + "World, "
                            + str(gas).capitalize()
                            + ", "
                            + str(sector).capitalize()
                            + ", "
                            + str(scenario).capitalize(),
                            "xanchor": "center",
                            "x": 0.5,
                            "y": 0.9,
                        },
                        yaxis={"title": "Mt"},
                        legend=dict(font=dict(size=8)),
                    )

                    fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/emissions-"
                        + str(scenario)
                        + "-"
                        + str(sector)
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

        # endregion

    # endregion

    # endregion

    ###########################
    #  COMBINE ALL EMISSIONS  #
    ###########################

    # region

    # Combine emissions from energy, afolu, and additional sources
    emissions_output = (
        pd.concat([emissions_energy, emissions_afolu, emissions_additional])
        .sort_index()
        .fillna(0)
    )

    # Make emissions_output_co2e
    # region

    # Group modeled emissions into CO2e
    emissions_output_co2e = emissions_output.copy()

    # Remove dashes from gas names to match naming in gwp library
    emissions_output_co2e = emissions_output_co2e.rename(
        index={
            "HCFC-141b": "HCFC141b",
            "HCFC-142b": "HCFC142b",
            "HFC-125": "HFC125",
            "HFC-134a": "HFC134a",
            "HFC-143a": "HFC143a",
            "HFC-152a": "HFC152a",
            "HFC-227ea": "HFC227ea",
            "HFC-245fa": "HFC245fa",
            "HFC-32": "HFC32",
            "HFC-365mfc": "HFC365mfc",
            "HFC-23": "HFC23",
            "c-C4F8": "cC4F8",
            "HFC-134": "HFC134",
            "HFC-143": "HFC143",
            "HFC-236fa": "HFC236fa",
            "HFC-41": "HFC41",
            "HFC-43-10-mee": "HFC4310mee",
        }
    )

    # Update emissions that don't list gas in flow_long (these are all CO2)
    emissions_output_co2e.reset_index(inplace=True)

    # Select CO2 emissions
    emissions_output_co2e_new = emissions_output_co2e[
        ~(
            emissions_output_co2e.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "BC",
                    "CO",
                    "NH3",
                    "NMVOC",
                    "NOx",
                    "OC",
                    "SO2",
                    "HCFC141b",
                    "HCFC142b",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC152a",
                    "HFC227ea",
                    "HFC245fa",
                    "HFC32",
                    "HFC365mfc",
                    "SF6",
                    "HFC23",
                    "C2F6",
                    "CF4",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "cC4F8",
                    "HFC134",
                    "HFC143",
                    "HFC236fa",
                    "HFC41",
                    "HFC4310mee",
                    "C5F12",
                    "C6F14",
                ]
            )
        ).values
    ]

    # Remove CO2 emissions from full emissions list
    emissions_output_co2e = emissions_output_co2e[
        (
            emissions_output_co2e.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "BC",
                    "CO",
                    "NH3",
                    "NMVOC",
                    "NOx",
                    "OC",
                    "SO2",
                    "HCFC141b",
                    "HCFC142b",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC152a",
                    "HFC227ea",
                    "HFC245fa",
                    "HFC32",
                    "HFC365mfc",
                    "SF6",
                    "HFC23",
                    "C2F6",
                    "CF4",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "cC4F8",
                    "HFC134",
                    "HFC143",
                    "HFC236fa",
                    "HFC41",
                    "HFC4310mee",
                    "C5F12",
                    "C6F14",
                ]
            )
        ).values
    ]

    # Replace 'flow_long' value with 'CO2'
    emissions_output_co2e_new.drop(columns="flow_long", inplace=True)
    emissions_output_co2e_new["flow_long"] = "CO2"

    # Add the updated subset back into the original df
    emissions_output_co2e = pd.concat(
        [emissions_output_co2e, emissions_output_co2e_new]
    )

    emissions_output_co2e = emissions_output_co2e.set_index(
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

    emissions_output_co2e = emissions_output_co2e.parallel_apply(
        lambda x: x.mul(gwp.data[version][x.name[8]]), axis=1
    )

    # Drop rows with all zero values
    emissions_output_co2e = emissions_output_co2e[
        emissions_output_co2e.sum(axis=1) != 0
    ].sort_index()

    # endregion

    # Plot emissions_output_co2e
    # region
    if show_figs is True:
        #################
        # GHG EMISSIONS #
        #################

        # region

        scenario = "pathway"
        model = "PD22"
        df = emissions_output_co2e

        fig = (
            df.loc[model]
            .groupby(["scenario", "sector", "product_long", "flow_long"])
            .sum()
            .T
        )
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "sector", "product_long", "flow_long"],
            value_name="Emissions",
        )

        for scenario in fig2["scenario"].unique():

            for sector in fig2["sector"].unique():

                fig = go.Figure()

                for product_long in (
                    fig2[fig2.scenario == scenario]
                    .groupby(["product_long"])
                    .sum()
                    .sort_values("Emissions", ascending=False)
                    .index.unique()
                ):

                    for flow_long in fig2["flow_long"].unique():

                        fig.add_trace(
                            go.Scatter(
                                name=product_long + ", " + flow_long,
                                line=dict(
                                    width=0.5,
                                    color=(px.colors.qualitative.Dark24 * 100)[
                                        fig2["product_long"]
                                        .unique()
                                        .tolist()
                                        .index(product_long)
                                        + fig2["flow_long"]
                                        .unique()
                                        .tolist()
                                        .index(flow_long)
                                    ],
                                ),
                                x=fig2["year"].unique(),
                                y=fig2[
                                    (fig2["scenario"] == scenario)
                                    & (fig2["sector"] == sector)
                                    & (fig2["product_long"] == product_long)
                                    & (fig2["flow_long"] == flow_long)
                                ]["Emissions"],
                                fill="tonexty",
                                stackgroup="one",
                                hovertemplate="<b>Year</b>: %{x}"
                                + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                            )
                        )

                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=2, color="black"),
                        x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                        y=fig2[
                            (fig2["scenario"] == scenario)
                            & (fig2["sector"] == sector)
                            & (fig2["year"] <= data_end_year)
                        ]
                        .groupby(["year"])
                        .sum()["Emissions"],
                        fill="none",
                        stackgroup="two",
                        showlegend=True,
                        hovertemplate="<b>Year</b>: %{x}"
                        + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                    )
                )

                fig.update_layout(
                    title={
                        "text": "Emissions, "
                        + "World"
                        + ", "
                        + str(sector).capitalize()
                        + ", "
                        + str(scenario).capitalize(),
                        "xanchor": "center",
                        "x": 0.5,
                        "y": 0.9,
                    },
                    yaxis={"title": "MtCO2e"},
                    legend=dict(font=dict(size=8)),
                )

                fig.show()

                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/emissions-"
                            + str(sector)
                            + "-"
                            + str(scenario)
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )

        # endregion

        ###################################
        # GHG EMISSIONS MITIGATION WEDGES #
        ###################################

        # region

        scenario = "pathway"
        model = "PD22"

        fig = (
            (
                emissions_output_co2e.loc[model, "baseline"].subtract(
                    emissions_output_co2e.loc[model, scenario]
                )
            )
            .groupby(["sector", "product_long"])
            .sum()
        ).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["sector", "product_long"],
            value_name="Emissions",
        )

        for sector in fig2["sector"].unique():

            fig = go.Figure()

            spacer = emissions_output_co2e.loc[
                model, scenario, slice(None), sector
            ].sum()

            fig.add_trace(
                go.Scatter(
                    name="",
                    line=dict(width=0),
                    x=spacer.index.values[spacer.index.values >= data_end_year],
                    y=spacer[spacer.index.values >= data_end_year],
                    fill="none",
                    stackgroup="one",
                    showlegend=False,
                    hovertemplate="<b>Year</b>: %{x}"
                    + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                )
            )

            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=2, color="black"),
                    x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                    y=pd.Series(
                        emissions_output_co2e.loc[model, scenario, slice(None), sector]
                        .loc[:, :data_end_year]
                        .sum(),
                        index=emissions_output_co2e.columns,
                    ).loc[:data_end_year],
                    fill="none",
                    stackgroup="two",
                    showlegend=True,
                    hovertemplate="<b>Year</b>: %{x}"
                    + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                )
            )

            for product_long in (
                fig2[fig2["sector"] == sector]
                .groupby(["product_long"])
                .sum()
                .sort_values("Emissions", ascending=False)
                .index.unique()
            ):
                fig.add_trace(
                    go.Scatter(
                        name=product_long,
                        line=dict(width=0.5),
                        x=fig2[fig2["year"] > data_end_year]["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product_long)
                            & (fig2["year"] > data_end_year)
                        ]["Emissions"],
                        fill="tonexty",
                        stackgroup="one",
                    )
                )

            fig.update_layout(
                title={
                    "text": "Emissions, "
                    + "World"
                    + ", "
                    + str(sector).capitalize()
                    + ", "
                    + str(scenario).capitalize(),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.9,
                },
                yaxis={"title": "MtCO2e"},
                legend=dict(font=dict(size=8)),
            )

            fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/emissions-wedges-"
                        + str(sector)
                        + "-"
                        + str(scenario)
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

        # endregion

        #############################
        # GHG EMISSIONS ALL SECTORS #
        #############################

        # region

        scenario = "pathway"
        model = "PD22"
        df = emissions_output_co2e

        fig = (
            df.loc[model]
            .groupby(["scenario", "sector", "product_long", "flow_long"])
            .sum()
            .T
        )
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["scenario", "sector", "product_long", "flow_long"],
            value_name="Emissions",
        )

        for scenario in fig2["scenario"].unique():

            fig = go.Figure()

            for sector in (
                fig2[fig2["scenario"] == scenario]
                .groupby(["sector", "product_long", "flow_long"])
                .sum()
                .sort_values("Emissions", ascending=False)
                .index.unique()
            ):

                for product_long in (
                    fig2[(fig2["scenario"] == scenario) & (fig2["sector"] == sector)]
                    .groupby(["product_long", "flow_long"])
                    .sum()
                    .sort_values("Emissions", ascending=False)
                    .index.unique()
                ):

                    for flow_long in (
                        fig2[
                            (fig2["scenario"] == scenario)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product_long)
                        ]
                        .groupby(["flow_long"])
                        .sum()
                        .sort_values("Emissions", ascending=False)
                        .index.unique()
                    ):

                        fig.add_trace(
                            go.Scatter(
                                name=sector + ", " + product_long + ", " + flow_long,
                                line=dict(width=0.5),
                                x=fig2["year"].unique(),
                                y=fig2[
                                    (fig2["scenario"] == scenario)
                                    & (fig2["sector"] == sector)
                                    & (fig2["product_long"] == product_long)
                                    & (fig2["flow_long"] == flow_long)
                                ]["Emissions"],
                                fill="tonexty",
                                stackgroup="one",
                                hovertemplate="<b>Year</b>: %{x}"
                                + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                            )
                        )

            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=2, color="black"),
                    x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                    y=fig2[
                        (fig2["scenario"] == scenario) & (fig2["year"] <= data_end_year)
                    ]
                    .groupby(["year"])
                    .sum()["Emissions"],
                    fill="none",
                    stackgroup="two",
                    showlegend=True,
                    hovertemplate="<b>Year</b>: %{x}"
                    + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                )
            )

            fig.update_layout(
                title={
                    "text": "Emissions, "
                    + "World"
                    + ", "
                    + "All Sectors"
                    + ", "
                    + str(scenario).capitalize(),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.9,
                },
                yaxis={"title": "MtCO2e"},
                legend=dict(font=dict(size=8)),
            )

            fig.show()

            if save_figs is True:
                pio.write_html(
                    fig,
                    file=(
                        "./charts/emissions-" + "All" + "-" + str(scenario) + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

        # endregion

        ###############################################
        # GHG EMISSIONS MITIGATION WEDGES ALL SECTORS #
        ###############################################

        # region

        scenario = "pathway"
        model = "PD22"

        fig = (
            (
                emissions_output_co2e.loc[model, "baseline"].subtract(
                    emissions_output_co2e.loc[model, scenario]
                )
            )
            .groupby(["sector", "product_long"])
            .sum()
        ).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["sector", "product_long"],
            value_name="Emissions",
        )

        fig = go.Figure()

        spacer = emissions_output_co2e.loc[model, scenario, slice(None)].sum()

        fig.add_trace(
            go.Scatter(
                name="",
                line=dict(width=0),
                x=spacer.index.values[spacer.index.values >= data_end_year],
                y=spacer[spacer.index.values >= data_end_year],
                fill="none",
                stackgroup="one",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=2, color="black"),
                x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                y=pd.Series(
                    emissions_output_co2e.loc[model, scenario, slice(None)]
                    .loc[:, :data_end_year]
                    .sum(),
                    index=emissions_output_co2e.columns,
                ).loc[:data_end_year],
                fill="none",
                stackgroup="two",
                showlegend=True,
                hovertemplate="<b>Year</b>: %{x}"
                + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
            )
        )

        for sector in fig2["sector"].unique():

            for product_long in fig2["product_long"].unique():
                fig.add_trace(
                    go.Scatter(
                        name=product_long,
                        line=dict(width=0.5),
                        x=fig2[fig2["year"] > data_end_year]["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product_long)
                            & (fig2["year"] > data_end_year)
                        ]["Emissions"],
                        fill="tonexty",
                        stackgroup="one",
                        hovertemplate="<b>Year</b>: %{x}"
                        + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                    )
                )

        fig.update_layout(
            title={
                "text": "Emissions, "
                + "World"
                + ", "
                + "All"
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.9,
            },
            yaxis={"title": "MtCO2e"},
            legend=dict(font=dict(size=8)),
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/emissions-wedges-" + "All" + "-" + str(scenario) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        # endregion

        #########################################################
        # GHG EMISSIONS MITIGATION WEDGES ALL SECTORS ANIMATION #
        #########################################################
        """
        # region

        scenario = "pathway"
        model = "PD22"

        fig = (
            (
                emissions_output_co2e.loc[model, "baseline"].subtract(
                    emissions_output_co2e.loc[model, scenario]
                )
            )
            .groupby(["sector", "product_long"])
            .sum()
        ).T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig,
            id_vars="year",
            var_name=["sector", "product_long"],
            value_name="Emissions",
        )

        fig = go.Figure()

        spacer = emissions_output_co2e.loc[model, scenario, slice(None)].sum()

        fig.add_trace(
            go.Scatter(
                name="",
                line=dict(width=0),
                x=spacer.index.values[spacer.index.values >= data_end_year],
                y=spacer[spacer.index.values >= data_end_year],
                fill="none",
                stackgroup="one",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=2, color="black"),
                x=fig2[fig2["year"] <= data_end_year]["year"].unique(),
                y=pd.Series(
                    emissions_output_co2e.loc[model, scenario, slice(None)]
                    .loc[:, :data_end_year]
                    .sum(),
                    index=emissions_output_co2e.columns,
                ).loc[:data_end_year],
                fill="none",
                stackgroup="two",
                showlegend=True,
                hovertemplate="<b>Year</b>: %{x}"
                + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
            )
        )

        for sector in fig2["sector"].unique():

            for product_long in fig2["product_long"].unique():
                fig.add_trace(
                    go.Scatter(
                        name=product_long,
                        line=dict(width=0.5),
                        x=fig2[fig2["year"] > data_end_year]["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product_long)
                            & (fig2["year"] > data_end_year)
                        ]["Emissions"],
                        fill="tonexty",
                        stackgroup="one",
                        hovertemplate="<b>Year</b>: %{x}"
                        + "<br><b>Emissions</b>: %{y:,.0f} MtCO2e<br>",
                    )
                )

        fig.update_layout(
            title={
                "text": "Emissions, "
                + "World"
                + ", "
                + "All"
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.9,
            },
            yaxis={"title": "MtCO2e"},
            legend=dict(font=dict(size=8)),
        )

        # Play button and animation frames
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    buttons=[dict(label="Play", method="animate", args=[None])],
                )
            ],
            frames=[
                go.Frame(data=[go.Scatter(x=[1, 2], y=[1, 2])]),
                go.Frame(data=[go.Scatter(x=[1, 4], y=[1, 4])]),
                go.Frame(
                    data=[go.Scatter(x=[3, 4], y=[3, 4])],
                    layout=go.Layout(title_text="End Title"),
                ),
            ],
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/emissions-wedges-animation-"
                    + "All"
                    + "-"
                    + str(scenario)
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        # endregion
        """
    # endregion

    # endregion

    #########################################
    #  LOAD & COMPARE TO MODELED EMISSIONS  #
    #########################################

    # region

    # Harmonize modeled emissions projections with observed historical emissions

    # https://aneris.readthedocs.io/en/latest/index.html

    # Load historical emissions data from ClimateTRACE
    emissions_historical = pd.concat(
        [
            pd.read_csv(
                "podi/data/ClimateTRACE/climatetrace_emissions_by_subsector_timeseries_interval_year_since_2015_to_2020.csv",
                usecols=["Tonnes Co2e", "country", "sector", "subsector", "start"],
            ),
            pd.read_csv(
                "podi/data/ClimateTRACE/climatetrace_emissions_by_subsector_timeseries_sector_forests_since_2015_to_2020_interval_year.csv",
                usecols=["Tonnes Co2e", "country", "sector", "subsector", "start"],
            ),
        ]
    )

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "country"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add model, scenario, and flow_category indices
    emissions_historical["model"] = "PD22"
    emissions_historical["scenario"] = "baseline"
    emissions_historical["product_category"] = "Emissions"
    emissions_historical["product_short"] = "EM"
    emissions_historical["flow_category"] = "Emissions"
    emissions_historical["flow_long"] = "Emissions"
    emissions_historical["flow_short"] = "EM"
    emissions_historical["unit"] = "MtCO2e"

    # Change unit from t to Mt
    emissions_historical["Tonnes Co2e"] = emissions_historical["Tonnes Co2e"].divide(
        1e6
    )

    # Change 'sector' index to 'product_long' and 'subsector' to 'flow_long' and 'start' to 'year'
    emissions_historical.rename(
        columns={"Tonnes Co2e": "value", "subsector": "product_long", "start": "year"},
        inplace=True,
    )

    # Change 'year' format
    emissions_historical["year"] = (
        emissions_historical["year"].str.split("-", expand=True)[0].values.astype(int)
    )

    # Update Sector index
    def addsector4(x):
        if x["sector"] in ["power"]:
            return "Electric Power"
        elif x["sector"] in ["transport", "maritime"]:
            return "Transportation"
        elif x["sector"] in ["buildings"]:
            return "Buildings"
        elif x["sector"] in ["extraction", "manufacturing", "oil and gas", "waste"]:
            return "Industrial"
        elif x["sector"] in ["agriculture"]:
            return "Agriculture"
        elif x["sector"] in ["forests"]:
            return "Forests & Wetlands"

    emissions_historical["sector"] = emissions_historical.parallel_apply(
        lambda x: addsector4(x), axis=1
    )

    emissions_historical = (
        (
            emissions_historical.reset_index()
            .set_index(["country"])
            .merge(regions, on=["country"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
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
        .rename_axis(index={"WEB Region": "region"})
    ).drop(columns=["country", "index"])

    # Pivot from long to wide
    emissions_historical = emissions_historical.reset_index().pivot(
        index=[
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
        ],
        columns="year",
        values="value",
    )

    # Select data between data_start_year and data_end_year
    emissions_historical.columns = emissions_historical.columns.astype(int)
    emissions_historical = emissions_historical.loc[:, data_start_year:data_end_year]

    # Match modeled (emissions_output_co2e) and observed emissions (emissions_historical) categories across 'model', 'region', 'sector'

    emissions_output_co2e_compare = (
        emissions_output_co2e.rename(
            index={"Residential": "Buildings", "Commercial": "Buildings"}
        )
        .groupby(["model", "region", "sector"])
        .sum()
    )
    emissions_historical_compare = emissions_historical.groupby(
        ["model", "region", "sector"]
    ).sum()

    # Calculate error between modeled and observed
    emissions_error = abs(
        (
            emissions_historical_compare
            - emissions_output_co2e_compare.loc[:, emissions_historical_compare.columns]
        )
        / emissions_historical_compare.loc[:, emissions_historical_compare.columns]
    )

    # Drop observed emissions that are all zero
    emissions_error.replace([np.inf, -np.inf], np.nan, inplace=True)
    emissions_error.dropna(how="all", inplace=True)

    # Plot difference in modeled and measured emissions [%]
    emissions_error.multiply(100).T.plot(
        legend=False,
        title="Difference between PD22 and ClimateTRACE emissions",
        ylabel="%",
    )
    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    emissions_output.to_csv("podi/data/emissions_output.csv")
    emissions_output_co2e.to_csv("podi/data/emissions_output_co2e.csv")

    # endregion

    return
