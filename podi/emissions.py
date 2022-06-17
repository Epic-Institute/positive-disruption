# region

import pandas as pd
from numpy import NaN, concatenate
import numpy as np
import pyam
import os.path
import traceback
import matplotlib.pyplot as plt
import silicone.database_crunchers
from silicone.utils import download_or_load_sr15
import aneris
from pandarallel import pandarallel
import globalwarmingpotentials as gwp
from podi.afolu import afolu

pandarallel.initialize(nb_workers=4)

# endregion


def emissions(
    scenario,
    energy_output,
    emissions_afolu_mitigated,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    #########################################
    #  CALCULATE CO2 EMISSIONS FROM ENERGY  #
    #########################################

    recalc_emissions_energy = False
    # region
    if recalc_emissions_energy == True:
        # Load emissions factors (currently a manually produced file)
        emission_factors = pd.read_csv("podi/data/emission_factors.csv").set_index(
            pyam.IAMC_IDX
        )
        emission_factors = emission_factors[~emission_factors.index.duplicated()]
        emission_factors.columns = emission_factors.columns.astype(int)
        emission_factors = emission_factors.loc[:, data_start_year:proj_end_year]

        # Multiply energy by emission factors to get emissions estimates. Note that emission factors for non-energy use flows are set to 0
        emissions_energy = energy_output.parallel_apply(
            lambda x: x
            * (
                (
                    emission_factors.loc[
                        x.name[0],
                        x.name[1],
                        x.name[2],
                        "|".join([x.name[6], x.name[9]]),
                    ]
                ).squeeze()
            ),
            axis=1,
        )

        emissions_energy.index = emissions_energy.index.set_levels(
            emissions_energy.index.levels[10].str.replace("TJ", "MtCO2"), level=10
        )

        # Save to CSV file
        emissions_energy.to_csv("podi/data/emissions_energy.csv")

    index = [
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

    emissions_energy = pd.DataFrame(
        pd.read_csv("podi/data/emissions_energy.csv")
    ).set_index(index)
    emissions_energy.columns = emissions_energy.columns.astype(int)

    # endregion

    ########################################
    #  CALCULATE GHG EMISSIONS FROM AFOLU  #
    ########################################

    # region

    # Create emissions factors using timeseries of average mitigation potential flux of each subvertical
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

    flux = piecewise_to_continuous("Avg mitigation potential flux")

    # Define the flux of 'Avoided Coastal Impacts' and 'Avoided Forest Conversion'
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
        .apply(
            lambda x: x[flux.columns[0:]].fillna(x["Mitigation (Mg CO2/ha)"]),
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

    # Change flux units from tCO2e/ha to tCO2e/Mha to match max extent
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

    # Plot
    fluxplot = flux.copy()
    fluxplot.columns = fluxplot.columns - flux.columns[0]

    for subvertical in (
        fluxplot[(fluxplot.reset_index().unit == "tCO2e/Mha/yr").values]
        .reset_index()
        .variable.unique()
    ):
        fluxplot[fluxplot.index.get_level_values(3).isin([subvertical])].T.plot(
            legend=False,
            title="Avg Mitigation Flux, "
            + subvertical.replace("|Avg mitigation potential flux", ""),
            xlabel="Years from implementation",
            ylabel="tCO2e/Mha/yr",
        )

    fluxplot[
        fluxplot.index.get_level_values(3).isin(
            ["Improved Forest Mgmt|Avg mitigation potential flux"]
        )
    ].T.plot(
        legend=False,
        title="Avg Mitigation Flux, "
        + subvertical.replace("|Avg mitigation potential flux", ""),
        xlabel="Years from implementation",
        ylabel="tCO2e/m3/yr",
    )

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
    emissions_afolu.columns = emissions_afolu.columns.str.replace("Y", "")

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

    emissions_afolu["sector"] = emissions_afolu.apply(lambda x: addsector(x), axis=1)

    # Split Emissions and Gas into separate columns
    def splitgas(x):
        if x["flow_category"] in ["Emissions (CO2)"]:
            return "CO2"
        elif x["flow_category"] in ["Emissions (CH4)"]:
            return "CH4"
        elif x["flow_category"] in ["Emissions (N2O)"]:
            return "N2O"

    emissions_afolu["flow_long"] = emissions_afolu.apply(lambda x: splitgas(x), axis=1)

    emissions_afolu["flow_category"] = "Emissions"

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
                "product_long",
                "flow_category",
                "flow_long",
                "unit",
            ]
        )
        .rename_axis(index={"WEB Region": "region"})
    ).drop(columns="region")

    # Select data between data_start_year and proj_end_year
    emissions_afolu.columns = emissions_afolu.columns.astype(int)
    emissions_afolu = emissions_afolu.loc[:, data_start_year:proj_end_year]

    # Change unit from kt to Mt
    emissions_afolu.update(emissions_afolu / 1e3)
    emissions_afolu = emissions_afolu.rename(index={"kilotonnes": "Mt"})

    # Drop rows with NaN in index and/or all year columns, representing duplicate regions and/or emissions
    emissions_afolu = emissions_afolu[
        ~(
            (emissions_afolu.index.get_level_values(3).isna())
            | (emissions_afolu.index.get_level_values(6).isna())
            | (emissions_afolu.isna().all(axis=1))
        )
    ]

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_afolu[np.arange(2021, 2030, 1)] = NaN
    emissions_afolu[np.arange(2031, proj_end_year, 1)] = NaN
    emissions_afolu = emissions_afolu.sort_index(axis=1)
    emissions_afolu.interpolate(method="linear", axis=1, inplace=True)
    emissions_afolu.fillna(method="bfill", inplace=True)

    # Plot emissions_afolu [Mt]
    for subvertical in emissions_afolu.reset_index().product_long.unique():
        emissions_afolu[
            emissions_afolu.index.get_level_values(4).isin([subvertical])
        ].T.plot(
            legend=False,
            title="Emissions, " + subvertical,
            ylabel="Mt",
        )

    # endregion

    # Multiply afolu_output by emissions factors to get emissions estimates.
    # region

    # Calculate emissions mitigated by multiplying adoption by avg mitigtation potential flux for each year. Average mitigation potential flux is unique to each year vintage.
    emissions_afolu_mitigated = pd.DataFrame(
        index=afolu_output.index, columns=afolu_output.columns
    )
    emissions_afolu_mitigated.reset_index(inplace=True)
    emissions_afolu_mitigated.unit = emissions_afolu_mitigated.unit.str.replace(
        "Mha", "tCO2e"
    ).replace("m3", "tCO2e")
    emissions_afolu_mitigated.set_index(afolu_output.index.names, inplace=True)

    for year in afolu_output.columns:

        # Find new adoption in year, multiply by flux and a 'baseline' copy of flux
        emissions_afolu_mitigated_year = (
            pd.concat([flux, flux.rename(index={scenario: "baseline"}, level=1)])
            .parallel_apply(
                lambda x: x
                * (
                    afolu_output.loc[
                        slice(None),
                        [x.name[1]],
                        [x.name[2]],
                        slice(None),
                        [x.name[3].replace("|Avg mitigation potential flux", "")],
                    ].loc[:, year]
                ).squeeze(),
                axis=1,
            )
            .fillna(0)
        )

        # Update variable and unit indices
        emissions_afolu_mitigated_year.reset_index(inplace=True)
        emissions_afolu_mitigated_year.variable = (
            emissions_afolu_mitigated_year.variable.str.replace(
                "Avg mitigation potential flux", "Observed adoption"
            )
        )
        emissions_afolu_mitigated_year.unit = (
            emissions_afolu_mitigated_year.unit.str.replace(
                "tCO2e/m3/yr", "tCO2e"
            ).replace("tCO2e/Mha/yr", "tCO2e")
        )
        emissions_afolu_mitigated_year.set_index(pyam.IAMC_IDX, inplace=True)

        # Update timerseries to start at 'year'
        emissions_afolu_mitigated_year.columns = np.arange(
            year, year + len(flux.columns), 1
        )

        # Add to cumulative count
        emissions_afolu_mitigated = emissions_afolu_mitigated_year.fillna(0).add(
            emissions_afolu_mitigated, fill_value=0
        )

    # Cut output to data_start_year : proj_end_year
    emissions_afolu_mitigated = emissions_afolu_mitigated.loc[
        :, data_start_year:proj_end_year
    ]

    # Replace unit label with MtCO2e
    emissions_afolu_mitigated.update(emissions_afolu_mitigated.divide(1e6))
    emissions_afolu_mitigated.rename(
        index={"tCO2e": "MtCO2e"},
        inplace=True,
    )

    # Add missing GWP values to gwp
    # Choose version of GWP values
    version = "AR6GWP100"  # Choose from ['SARGWP100', 'AR4GWP100', 'AR5GWP100', 'AR5CCFGWP100', 'AR6GWP100', 'AR6GWP20', 'AR6GWP500', 'AR6GTP100']

    gwp.data[version].update(
        {
            "CO2": 1,
            "BC": 2240,
            "CO": 0,
            "NH3": 0,
            "NMVOC": 0,
            "NOx": 0,
            "OC": 0,
            "SO2": 0,
        }
    )

    # Convert units from MtCO2e to Mt
    emissions_afolu_mitigated.update(
        emissions_afolu_mitigated[
            (emissions_afolu_mitigated.reset_index().flow_long != "CO2").values
        ].apply(lambda x: x.divide(gwp.data[version][x.name[6]]), axis=1)
    )

    emissions_afolu_mitigated.rename(index={"MtCO2e": "Mt"}, inplace=True)

    # Plot emissions_afolu_mitigated [tCO2]
    emissions_afolu_mitigated_outputplot = emissions_afolu_mitigated.copy()

    for (
        scenario
    ) in emissions_afolu_mitigated_outputplot.reset_index().scenario.unique():
        for (
            subvertical
        ) in emissions_afolu_mitigated_outputplot.reset_index().variable.unique():
            emissions_afolu_mitigated_outputplot[
                (
                    emissions_afolu_mitigated_outputplot.index.get_level_values(3).isin(
                        [subvertical]
                    )
                )
                & (
                    emissions_afolu_mitigated_outputplot.index.get_level_values(1).isin(
                        [scenario]
                    )
                )
            ].T.plot(
                legend=False,
                title="AFOLU Adoption, "
                + subvertical.replace("|Observed adoption", "")
                + ", "
                + scenario.capitalize(),
                ylabel="tCO2 mitigated",
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
    emissions_afolu["product_category"] = "Emissions"
    emissions_afolu["product_short"] = "EM"
    emissions_afolu["flow_short"] = "AFOLU"

    emissions_afolu = emissions_afolu.reset_index().set_index(
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
    def addsector(x):
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

    emissions_additional["sector"] = emissions_additional.apply(
        lambda x: addsector(x), axis=1
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

    # Create projections by applying most durrent data value to all future years
    emissions_additional[np.arange(data_end_year, proj_end_year + 1, 1)] = NaN
    emissions_additional = emissions_additional.sort_index(axis=1)
    emissions_additional.fillna(method="ffill", axis=1, inplace=True)

    # Drop double counted emissions
    def remove_doublcount(x):
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
            "1A3di_International-shipping" "1A4a_Commercial-institutional",
            "1A4b_Residential",
            "1A4c_Agriculture-forestry-fishing",
            "1A5_Other-unspecified",
        ] and x.name[6] in ["CO2"]:
            x.rename(
                ("NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"), inplace=True
            )

        # Drop CO2, CH4, N2O that was already estimated in FAO historical data
        if x.name[4] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ] and x.name[6] in ["CO2", "CH4", "N2O"]:
            x.rename(
                ("NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN", "NaN"), inplace=True
            )

        return x

    emissions_additional = emissions_additional.apply(
        lambda x: remove_doublcount(x), axis=1
    )
    emissions_additional = emissions_additional.loc[
        emissions_additional.index.dropna(how="any"), :
    ]

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
    def addsector(x):
        if x["product_long"] in [
            "Metal Industry",
            "Other Product Manufacture and Use",
            "Electronics Industry",
            "Chemical Industry",
            "Product Uses as Substitutes for Ozone Depleting Substances",
        ]:
            return "Industrial"

    emissions_additional_fgas["sector"] = emissions_additional_fgas.apply(
        lambda x: addsector(x), axis=1
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
    emissions_additional_fgas[np.arange(2021, 2030, 1)] = NaN
    emissions_additional_fgas[np.arange(2031, proj_end_year + 1, 1)] = NaN
    emissions_additional_fgas = emissions_additional_fgas.sort_index(axis=1)
    emissions_additional_fgas.interpolate(method="linear", axis=1, inplace=True)
    emissions_additional_fgas.fillna(method="bfill", inplace=True)

    # Combine all additional gases
    emissions_additional = pd.concat([emissions_additional, emissions_additional_fgas])

    # Create baseline and pathway scenarios
    emissions_additional = pd.concat(
        [
            emissions_additional,
            emissions_additional.rename(index={"baseline": scenario}),
        ]
    )

    # Project additional emissions using percent change in energy emissions in the Industrial sector
    percent_change = (
        emissions_energy.groupby(["model", "scenario", "region", "sector"])
        .mean()
        .loc[slice(None), slice(None), slice(None), "Industrial"]
        .loc[:, data_end_year:]
        .pct_change(axis=1)
        .replace(NaN, 0)
        .divide(100)
        .add(1)
    )

    emissions_additional = (
        emissions_additional.loc[:, data_start_year:data_end_year]
        .reset_index()
        .set_index(["model", "scenario", "region"])
        .merge(
            percent_change.loc[:, data_end_year + 1 :],
            on=["model", "scenario", "region"],
        )
        .set_index(
            ["sector", "product_long", "flow_category", "flow_long", "unit"],
            append=True,
        )
    )

    emissions_additional.loc[:, data_end_year:] = emissions_additional.loc[
        :, data_end_year:
    ].cumprod(axis=1)

    # Rename product_long values
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

    emissions_additional = (
        emissions_additional.rename(index=detailed_index)
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

    emissions_additional = emissions_additional.reset_index().set_index(
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

    # endregion

    ##############################################################
    #  LOAD HISTORICAL EMISSIONS & COMPARE TO MODELED EMISSIONS  #
    ##############################################################

    # region

    # Combine emissions from energy, afolu, and additional sources
    emissions_output = pd.concat(
        [emissions_energy, emissions_afolu, emissions_additional]
    )

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
    emissions_historical["Tonnes Co2e"] = emissions_historical["Tonnes Co2e"] / 1e6

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
    def addsector(x):
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

    emissions_historical["sector"] = emissions_historical.apply(
        lambda x: addsector(x), axis=1
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

    # Update units from 'MtCO2' to 'Mt'
    emissions_output_co2e_new = emissions_output_co2e_new.replace("MtCO2", "Mt")

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

    emissions_output_co2e = emissions_output_co2e.apply(
        lambda x: x.mul(gwp.data[version][x.name[8]]), axis=1
    )

    # Update all flow_long values to 'CO2e'
    emissions_output_co2e = emissions_output_co2e.droplevel("flow_long").reset_index()
    emissions_output_co2e["flow_long"] = "CO2e"

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
        (emissions_historical_compare - emissions_output_co2e_compare)
        / emissions_historical_compare
    )

    # Plot
    emissions_error.T.plot(
        legend=False, title="Error between PD22 and ClimateTRACE emissions", ylabel="%"
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
