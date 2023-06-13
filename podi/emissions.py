# region

import os
import re

import globalwarmingpotentials as gwp
import numpy as np
import pandas as pd
import pyam
from numpy import NaN
from pandarallel import pandarallel
from scipy.optimize import differential_evolution

pandarallel.initialize(progress_bar=True)

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

    # Load emissions factors from
    # https://www.ipcc-nggip.iges.or.jp/EFDB/find_ef.php?reset= , select 'Energy' and
    # then 'Export to XLS' and save as emissions_factors.csv in podi/data/external/.
    # Emissions factors attribute emissions to the sector where the emissions are
    # generated, e.g. electricity use in Buildings/Industry is zero emissions since
    # those emissions are attributed to the Electric Power sector. Heat not
    # produced on-site in Buildings/Industry is zero emissions since those emissions
    # are attributed to the Industrial sector.

    # Load new df with index matching energy_output
    emissions_factors = pd.DataFrame(
        index=energy_output[
            ~(
                energy_output.reset_index().flow_category == "Non-energy use"
            ).values
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
                (x[x.first_valid_index()] * 0.01)
                * (
                    np.arange(data_start_year, proj_end_year + 1)
                    - data_start_year
                ),
                index=x.index,
            ).rename(x.name)
        ).clip(lower=0),
        axis=1,
    )

    # Multiply energy by emission factors to get emissions estimates. Note that
    # emission factors for non-energy use flows are set to 0
    emissions_energy = energy_output[
        ~(energy_output.reset_index().flow_category == "Non-energy use").values
    ].parallel_apply(
        lambda x: x.multiply(emissions_factors.loc[x.name])
        .fillna(0)
        .squeeze(),
        axis=1,
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

    # Set product_short to 'CO2' for all rows, representing the transformation of the product to CO2
    emissions_energy_reset = emissions_energy.reset_index()
    emissions_energy_reset.iloc[:, 6] = "CO2"
    emissions_energy = emissions_energy_reset.set_index(
        emissions_energy.index.names
    )

    # Save
    emissions_energy.columns = emissions_energy.columns.astype(str)
    emissions_energy.to_parquet(
        "podi/data/emissions_energy.parquet", compression="brotli"
    )
    emissions_energy.columns = emissions_energy.columns.astype(int)

    # endregion

    ########################################
    #  CALCULATE GHG EMISSIONS FROM AFOLU  #
    ########################################

    # region

    # Create emissions factors using timeseries of average mitigation potential flux
    # of each subvertical
    # region

    # Define a function that takes piecewise functions as input and outputs a
    # continuous timeseries (this is used for input data provided for (1) maximum
    # extent, and (2) average mitigation potential flux)
    def piecewise_to_continuous(variable):
        # Load the 'Input Data' tab of TNC's 'Positive Disruption NCS Vectors'
        # google spreadsheet
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

        # Create a 'variable' column that concatenates the 'Subvertical' and
        # 'Metric' columns
        name["variable"] = name.parallel_apply(
            lambda x: "|".join([x["Subvertical"], x["Metric"]]), axis=1
        )
        name.drop(columns=["Subvertical", "Metric"], inplace=True)

        # Filter for rows that have 'variable' (either 'Max extent' or 'Avg
        # mitigation potential flux')
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
        # afolu_output.columns[0], set to proj_end_year - afolu_output.columns[0]
        name["Duration 1 (Years)"] = np.where(
            (
                (name["Duration 1 (Years)"].isna())
                | (
                    name["Duration 1 (Years)"]
                    > proj_end_year - int(afolu_output.columns[0])
                )
            ),
            proj_end_year - int(afolu_output.columns[0]),
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
            columns=np.arange(
                int(afolu_output.columns[0]), proj_end_year + 1, 1
            ),
            dtype=float,
        )

        # Define a function that places values in each timeseries for the
        # durations specified, and interpolates
        def rep(x):
            x0 = x
            x0.loc[int(afolu_output.columns[0])] = x.name[5]
            x0.loc[int(afolu_output.columns[0]) + x.name[6]] = x.name[7]
            x0.loc[
                min(
                    int(afolu_output.columns[0]) + x.name[6] + x.name[8],
                    proj_end_year - int(afolu_output.columns[0]),
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

    flux = piecewise_to_continuous(
        "Avg mitigation potential flux"
    ).sort_index()

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

    # Update Mitigation units from MtCO2e/ha to tCO2e/ha
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
            lambda x: x[flux.columns[0:]].fillna(
                x["Mitigation (MtCO2e/ha)"], limit=1
            ),
            axis=1,
        )
        .fillna(0)
        .multiply(1e6)
        .rename(
            index={
                "Avoided Coastal Impacts": "Coastal Impacts|Avg mitigation potential flux",
                "Avoided Forest Conversion": "Net Forest Conversion|Avg mitigation potential flux",
                "Mha": "tCO2e/ha/yr",
            }
        )
    ).fillna(0)

    flux = flux.rename(
        index={
            "Biochar|Avg mitigation potential flux": "Biochar as Ag Soil Amendment|Avg mitigation potential flux",
            "Improved Rice|Avg mitigation potential flux": "Rice Cultivation|Avg mitigation potential flux",
            "Avoided Peat Impacts|Avg mitigation potential flux": "Peat Impacts|Avg mitigation potential flux",
        }
    )

    # Add flux for new markets
    flux_new_markets = pd.DataFrame(
        pd.read_csv("podi/data/APL/flux.csv")
    ).set_index(pyam.IAMC_IDX)
    flux_new_markets.columns = flux_new_markets.columns.astype(int)
    flux_new_markets = flux_new_markets.loc[:, data_start_year:proj_end_year]

    # Combine flux estimates
    flux = pd.concat([flux, flux_avoided, flux_new_markets])

    # Change flux units for Nitrogen Fertilizer Management from MtCO2e/percentile
    # improvement to tCO2e/percentile improvement, to match other subverticals
    flux = pd.concat(
        [
            flux[
                ~(
                    flux.reset_index().unit.isin(
                        ["MtCO2e/percentile improvement"]
                    )
                ).values
            ],
            flux[
                (
                    flux.reset_index().unit.isin(
                        ["MtCO2e/percentile improvement"]
                    )
                ).values
            ]
            .multiply(1e6)
            .rename(
                index={
                    "MtCO2e/percentile improvement": "tCO2e/percentile improvement"
                }
            ),
        ]
    )

    # Change flux units for tCO2e/ha to tCO2e/Mha, which matches the current units
    # for afolu_output (Mha)
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
        (
            flux.reset_index()
            .set_index(["region"])
            .merge(regions, on=["region"])
        )
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

    flux.to_csv("podi/data/TNC/flux_output.csv")

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
                "Item": "flow_long",
                "Element": "product_category",
                "Unit": "unit",
            }
        )
        .set_index("region")
    )
    emissions_afolu.columns = emissions_afolu.columns.str.replace(
        "Y", "", regex=True
    )

    # Drop redundant emissions
    emissions_afolu = emissions_afolu[
        (
            emissions_afolu.product_category.isin(
                [
                    "Emissions (CH4)",
                    "Emissions (N2O)",
                    "Emissions (CO2)",
                ]
            )
        )
        & (~emissions_afolu.flow_long.isin(["Forestland"]))
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
        if x["flow_long"] in [
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
        elif x["flow_long"] in [
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
        if x["product_category"] in ["Emissions (CO2)"]:
            return "CO2 (from AFOLU)"
        elif x["product_category"] in ["Emissions (CH4)"]:
            return "CH4 (from AFOLU)"
        elif x["product_category"] in ["Emissions (N2O)"]:
            return "N2O (from AFOLU)"

    emissions_afolu["product_long"] = emissions_afolu.parallel_apply(
        lambda x: splitgas(x), axis=1
    )

    # replace "Drained organic soils (CO2)" and "Drained organic soils (N2O)" with "Drained organic soils"
    emissions_afolu["flow_long"] = emissions_afolu["flow_long"].replace(
        {
            "Drained organic soils (CO2)": "Drained organic soils",
            "Drained organic soils (N2O)": "Drained organic soils",
        }
    )

    emissions_afolu["flow_category"] = "AFOLU Emissions"
    emissions_afolu["product_category"] = "AFOLU Emissions"
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

    # Drop rows with NaN in index and/or all year columns, representing duplicate
    # regions and/or emissions
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

    # Have emissions decrease by 1% per year from data_end_year to proj_end_year
    emissions_afolu = emissions_afolu.parallel_apply(
        lambda x: x.subtract(
            pd.Series(
                (x[x.first_valid_index()] * 0.01)
                * (
                    np.arange(data_start_year, proj_end_year + 1)
                    - data_start_year
                ),
                index=x.index,
            ).rename(x.name)
        ).clip(lower=0),
        axis=1,
    )

    # Relabel Net forest conversion, Drained organic soils, synthetic fertilizers, rice cultivation, fires, crop residues, burning crop residues; these have associated NCS negative emissions that effectively reduce them.
    emissions_afolu = emissions_afolu.rename(
        index={
            "Net Forest conversion": "Net Forest Conversion",
            "Avoided Forest Conversion": "Net Forest Conversion",
            "Drained organic soils": "Coastal Impacts",
            "Avoided Coastal Impacts": "Coastal Impacts",
            "Synthetic Fertilizers": "Nitrogen Fertilizer Management",
            "Improved Rice": "Rice Cultivation",
            "Fires in humid tropical forests": "Net Forest Conversion",
            "Fires in organic soils": "Peat Impacts",
            "Avoided Peat Impacts": "Peat Impacts",
            "Forest fires": "Net Forest Conversion",
            # "Crop Residues": "Biochar as Ag Soil Amendment",
            # "Burning - Crop residues": "Biochar as Ag Soil Amendment",
        }
    )

    afolu_output = afolu_output.rename(
        index={
            "Net Forest conversion": "Net Forest Conversion",
            "Avoided Forest Conversion": "Net Forest Conversion",
            "Drained organic soils": "Coastal Impacts",
            "Avoided Coastal Impacts": "Coastal Impacts",
            "Synthetic Fertilizers": "Nitrogen Fertilizer Management",
            "Improved Rice": "Rice Cultivation",
            "Fires in humid tropical forests": "Net Forest Conversion",
            "Fires in organic soils": "Peat Impacts",
            "Avoided Peat Impacts": "Peat Impacts",
            "Forest fires": "Net Forest Conversion",
            # "Crop Residues": "Biochar as Ag Soil Amendment",
            # "Burning - Crop residues": "Biochar as Ag Soil Amendment",
        }
    )

    # endregion

    # Multiply afolu_output by emissions factors to get emissions estimates
    # region

    # Calculate emissions mitigated by multiplying adoption in each year by avg
    # mitigtation potential flux (over the entire range of year to proj_end_year), to
    # represent the time-dependent mitigation flux for adoption in each year
    afolu_output.columns = afolu_output.columns.astype(int)

    emissions_afolu_mitigated = pd.DataFrame(
        index=afolu_output.index, columns=afolu_output.columns
    )
    # drop index level unit
    emissions_afolu_mitigated.index = (
        emissions_afolu_mitigated.index.droplevel("unit")
    )

    for year in afolu_output.loc[
        :, data_start_year + 1 : proj_end_year
    ].columns:
        # Find new adoption in year, multiply by flux and a 'baseline' copy of flux
        emissions_afolu_mitigated_year = afolu_output.droplevel(
            "unit"
        ).parallel_apply(
            lambda x: max((x.loc[year] - x.loc[year - 1]), 0)
            * (
                pd.concat(
                    [flux.rename(index={scenario: "baseline"}, level=1), flux]
                ).loc[
                    slice(None),
                    [x.name[1]],
                    [x.name[2]],
                    [x.name[8] + "|Avg mitigation potential flux"],
                ]
            )
            .squeeze()
            .rename(x.name),
            axis=1,
        )

        # Update timerseries to start at 'year'
        emissions_afolu_mitigated_year.columns = np.arange(
            year, year + len(afolu_output.columns), 1
        )

        # Add to cumulative count
        emissions_afolu_mitigated = emissions_afolu_mitigated_year.add(
            emissions_afolu_mitigated, fill_value=0
        )

    # Cut output to data_start_year : proj_end_year
    emissions_afolu_mitigated = emissions_afolu_mitigated.loc[
        :, data_start_year:proj_end_year
    ].fillna(0)

    # add back in the unit index level
    emissions_afolu_mitigated.reset_index(inplace=True)
    emissions_afolu_mitigated["unit"] = "tCO2e"
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

    # Scale Rice Cultivation mitigation to be 58% from CH4 and 42% from N2O
    def improvedrice(each):
        each[
            (
                (each.reset_index().flow_long == "Rice Cultivation")
                & (each.reset_index().product_short == "CH4 (from AFOLU)")
            ).values
        ] = (
            each[
                (
                    (each.reset_index().flow_long == "Rice Cultivation")
                    & (each.reset_index().product_short == "CH4 (from AFOLU)")
                ).values
            ]
            * 0.58
        )

        each[
            (
                (each.reset_index().flow_long == "Rice Cultivation")
                & (each.reset_index().product_short == "N2O (from AFOLU)")
            ).values
        ] = (
            each[
                (
                    (each.reset_index().flow_long == "Rice Cultivation")
                    & (each.reset_index().product_short == "N2O (from AFOLU)")
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
    version = "AR6GWP100"
    # Choose from ['SARGWP100', 'AR4GWP100', 'AR5GWP100', 'AR5CCFGWP100', 'AR6GWP100',
    # 'AR6GWP20', 'AR6GWP500', 'AR6GTP100']

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
        lambda x: x.divide(
            gwp.data[version][re.sub(r"\s\(.*?\)", "", x.name[5])]
        ),
        axis=1,
    )

    emissions_afolu_mitigated.reset_index(inplace=True)
    emissions_afolu_mitigated["product_category"] = "AFOLU Emissions"
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

    # 'Avoided' emissions should be cumulative (Peat Impacts already does this so it is not included here)
    emissions_afolu_mitigated.update(
        emissions_afolu_mitigated[
            (
                emissions_afolu_mitigated.reset_index().flow_long.isin(
                    [
                        "Net Forest Conversion",
                        "Coastal Impacts",
                        "Peat Impacts",
                    ]
                )
            ).values
        ].cumsum(axis=1)
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
    emissions_afolu["product_category"] = "AFOLU Emissions"

    # make product_short the gas in product_long CO2, CH4, N2O
    emissions_afolu[
        "product_short"
    ] = emissions_afolu.product_long.str.extract(r"(\w+)")

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
    emissions_afolu = (
        emissions_afolu.groupby(
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
        .sum()
        .sort_index()
    )

    # endregion

    #########################################
    #  ADD IN ADDITIONAL EMISSIONS SOURCES  #
    #########################################

    # region

    # Load historical addtional emissions datasets
    gas_ceds = [
        "BC",
        "CO",
        "OC",
        "CH4",
        "CO2",
        "N2O",
        "NH3",
        "NOx",
        "SO2",
        "NMVOC",
    ]

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
    emissions_additional.columns = emissions_additional.columns.str.replace(
        "X", ""
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
    regions.index = (regions.index).str.lower()

    # Add Model, Scenario, and Flow_category indices
    emissions_additional["model"] = "PD22"
    emissions_additional["scenario"] = "baseline"
    emissions_additional["flow_category"] = "Additional Emissions"

    # Change sector index to flow_long and 'em' to 'product_long'
    emissions_additional.rename(
        columns={"sector": "flow_long", "em": "product_long"}, inplace=True
    )

    # add string "(additional emissions)" to all product_long values
    emissions_additional["product_long"] = (
        emissions_additional["product_long"] + " (additional emissions)"
    )

    # Add Sector index
    def addsector2(x):
        if x["flow_long"] in [
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
        elif x["flow_long"] in [
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
        elif x["flow_long"] in ["1A4b_Residential"]:
            return "Residential"
        elif x["flow_long"] in ["1A4a_Commercial-institutional"]:
            return "Commercial"
        elif x["flow_long"] in [
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
        elif x["flow_long"] in [
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
    emissions_additional = emissions_additional.loc[
        :, data_start_year:proj_end_year
    ]

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

    # Save last valid index for emissions_additional (it changes, but the value here
    # is used later)
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
        if x.name[6] in [
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
        ] and re.sub(r"\s\(.*?\)", "", x.name[4]) in ["CO2"]:
            x = x.multiply(0)

        # Drop CO2, CH4, N2O that was already estimated in FAO historical data
        if x.name[6] in [
            "3B_Manure-management",
            "3D_Rice-Cultivation",
            "3D_Soil-emissions",
            "3E_Enteric-fermentation",
            "3I_Agriculture-other",
        ] and re.sub(r"\s\(.*?\)", "", x.name[4]) in ["CO2", "CH4", "N2O"]:
            x = x.multiply(0)

        return x

    emissions_additional = emissions_additional.parallel_apply(
        lambda x: remove_doublecount(x), axis=1
    )

    # Get F-Gas data (Difference between EDGAR and FAIR: No HFC-41 or HFC-143, HFC-43-10-mee is HFC-4310mee)
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

        emissions_additional_fgas_new["product_long"] = (
            gas + " (additional emissions)"
        )

        emissions_additional_fgas = pd.concat(
            [emissions_additional_fgas, emissions_additional_fgas_new]
        )

    emissions_additional_fgas.columns = (
        emissions_additional_fgas.columns.str.replace("Y_", "")
    )
    emissions_additional_fgas.columns = (
        emissions_additional_fgas.columns.str.replace(
            "ipcc_code_2006_for_standard_report_name", "flow_long"
        )
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
        if x["flow_long"] in [
            "Metal Industry",
            "Other Product Manufacture and Use",
            "Electronics Industry",
            "Chemical Industry",
            "Product Uses as Substitutes for Ozone Depleting Substances",
        ]:
            return "Industrial"

    emissions_additional_fgas[
        "sector"
    ] = emissions_additional_fgas.parallel_apply(
        lambda x: addsector3(x), axis=1
    )

    emissions_additional_fgas["flow_category"] = "Additional F-Gas Emissions"

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
    emissions_additional_fgas.columns = (
        emissions_additional_fgas.columns.astype(int)
    )
    emissions_additional_fgas = emissions_additional_fgas.loc[
        :, data_start_year:proj_end_year
    ]

    # Change unit from kt to Mt
    emissions_additional_fgas.update(emissions_additional_fgas / 1e3)
    emissions_additional_fgas = emissions_additional_fgas.rename(
        index={"kT": "Mt"}
    )

    # Interpolate between data_end_year and projections in 2030, 2050
    emissions_additional_fgas[
        np.arange(emissions_additional_fgas.columns.max() + 1, 2031, 1)
    ] = NaN
    emissions_additional_fgas[np.arange(2031, proj_end_year + 1, 1)] = NaN
    emissions_additional_fgas = emissions_additional_fgas.sort_index(axis=1)
    emissions_additional_fgas.interpolate(
        method="linear", axis=1, inplace=True
    )
    emissions_additional_fgas.fillna(method="bfill", inplace=True)

    # Combine all additional gases
    emissions_additional = pd.concat(
        [emissions_additional, emissions_additional_fgas]
    )

    # Drop rows with all zero values
    emissions_additional = emissions_additional[
        emissions_additional.sum(axis=1) != 0
    ]

    # Create baseline and pathway scenarios
    emissions_additional = pd.concat(
        [
            emissions_additional,
            emissions_additional.rename(index={"baseline": scenario}),
        ]
    )

    # Project additional emissions using percent change in energy emissions in the
    # energy sector
    percent_change = (
        emissions_energy[
            (
                emissions_energy.reset_index().flow_category
                == "Electricity output"
            ).values
        ]
        .groupby(["model", "scenario", "region"], observed=True)
        .sum(numeric_only=True)
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
    ] = emissions_additional.loc[
        :, emissions_additional_last_valid_index:
    ].cumprod(
        axis=1
    )

    # Rename flow_long values
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
    """
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
    """
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
            ],
            observed=True,
        )
        .sum(numeric_only=True)
    )

    # Add indices product_category, product_long, product_short
    emissions_additional[
        "product_category"
    ] = "Additional Industrial Emissions"
    emissions_additional["flow_short"] = "ADEM"

    # make product_short the same as product_long without " (additional emissions)"
    emissions_additional.reset_index(inplace=True)
    emissions_additional["product_short"] = emissions_additional[
        "product_long"
    ].str.replace(" \(additional emissions\)", "")

    emissions_additional = emissions_additional.set_index(
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
    ).sort_index()

    # Split ROAD Flow into Two- and three-wheeled, Light, Medium (Buses), Heavy (Trucks)

    # region

    subsector_props = pd.DataFrame(
        pd.read_csv(
            "podi/data/tech_parameters.csv",
            usecols=[
                "region",
                "product_short",
                "scenario",
                "sector",
                "metric",
                "value",
            ],
        ),
    ).set_index(["region", "product_short", "scenario", "sector", "metric"])

    # Create Two- and three-wheeled Flow (TTROAD) using estimate of the fraction of
    # ROAD that is Two- and three-wheeled
    ttroad = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Road Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2],
                    "ROAD",
                    "baseline",
                    x.name[3],
                    "Two- and three-wheeled",
                ].values
            ),
            axis=1,
        )
        .rename(index={"Road Transport": "Road - 2&3-wheel"})
    )

    # Create Light-duty Flow (LIGHTROAD) using estimate of the fraction of ROAD that is
    # Light-duty vehicles
    lightroad = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Road Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Light"
                ].values
            ),
            axis=1,
        )
        .rename(index={"Road Transport": "Road - Light-duty vehicles"})
    )

    # Create Medium-duty Flow (MEDIUMROAD) using estimate of the fraction of ROAD that
    # is Medium-duty vehicles (Buses and Vans)
    mediumroad = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Road Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Medium"
                ].values
            ),
            axis=1,
        )
        .rename(index={"Road Transport": "Road - Buses&Vans"})
    )

    # Create Heavy-duty Flow (HEAVYROAD) using estimate of the fraction of ROAD that is
    # Heavy-duty vehicles (Trucks)
    heavyroad = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Road Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Heavy"
                ].values
            ),
            axis=1,
        )
        .rename(index={"Road Transport": "Road - Trucks"})
    )

    # Drop ROAD Flow and add TTROAD, LIGHTROAD, MEDIUMROAD, HEAVYROAD
    emissions_additional = pd.concat(
        [
            emissions_additional.drop(labels=["Road Transport"], level=8),
            ttroad,
            lightroad,
            mediumroad,
            heavyroad,
        ]
    )

    # endregion

    # Split RAIL Flow into Light-duty, Heavy-duty

    # region

    # Create Light-duty Flow (LIGHTRAIL) using estimate of the fraction of RAIL that is
    # Light-duty
    lightrail = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Rail Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "RAIL", "baseline", x.name[3], "Light"
                ].values
            ),
            axis=1,
        )
        .rename(index={"Rail Transport": "Rail - Light-duty"})
    )

    # Create Heavy-duty Flow (HEAVYRAIL) using estimate of the fraction of RAIL that is
    # Heavy-duty
    heavyrail = (
        emissions_additional[
            (
                emissions_additional.reset_index().flow_long
                == "Rail Transport"
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "RAIL", "baseline", x.name[3], "Heavy"
                ].values
            ),
            axis=1,
        )
        .rename(index={"Rail Transport": "Rail - Heavy-duty"})
    )

    # Drop RAIL Flow and add LIGHTRAIL and HEAVYRAIL
    emissions_additional = pd.concat(
        [
            emissions_additional.drop(labels=["Rail Transport"], level=8),
            lightrail,
            heavyrail,
        ]
    )

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

    # for positive-negative emissions 'pairs', clip the net emissions at zero
    emissions_output.update(
        emissions_output[
            (
                emissions_output.reset_index().flow_long.isin(
                    [
                        "Net Forest Conversion",
                        "Coastal Impacts",
                        "Peat Impacts",
                        "Nitrogen Fertilizer Management",
                        "Rice Cultivation",
                    ]
                )
            ).values
        ].clip(lower=0)
    )

    # Group modeled emissions into CO2e
    emissions_output_co2e = emissions_output.copy()

    # Change gas names to match naming in gwp library
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

    emissions_output_co2e = emissions_output_co2e.parallel_apply(
        lambda x: x.mul(gwp.data[version][x.name[6]]), axis=1
    )

    # Change back gas names to match original
    emissions_output_co2e = emissions_output_co2e.rename(
        index={
            "HCFC141b": "HCFC-141b",
            "HCFC142b": "HCFC-142b",
            "HFC125": "HFC-125",
            "HFC134a": "HFC-134a",
            "HFC143a": "HFC-143a",
            "HFC152a": "HFC-152a",
            "HFC227ea": "HFC-227ea",
            "HFC245fa": "HFC-245fa",
            "HFC32": "HFC-32",
            "HFC365mfc": "HFC-365mfc",
            "HFC23": "HFC-23",
            "cC4F8": "c-C4F8",
            "HFC134": "HFC-134",
            "HFC143": "HFC-143",
            "HFC236fa": "HFC-236fa",
            "HFC41": "HFC-41",
            "HFC43-10-mee": "HFC-4310mee",
        }
    )

    # endregion

    # endregion

    #################################
    #  REDUCE ENTERIC FERMENTATION  #
    #################################

    # region

    # Calculate reduction factors that scale down enteric fermentation over time

    # Load saturation points for reduction ratios
    ef_ratio = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters_afolu.csv",
            )
        )
        .set_index(["model", "scenario", "region", "variable"])
        .loc[
            slice(None),
            "pathway",
            slice(None),
            [
                "Enteric Fermentation|Floor",
                "Enteric Fermentation|Max annual growth",
                "Enteric Fermentation|parameter a max",
                "Enteric Fermentation|parameter a min",
                "Enteric Fermentation|parameter b max",
                "Enteric Fermentation|parameter b min",
                "Enteric Fermentation|saturation point",
            ],
        ]
    )

    parameters = ef_ratio

    ef_ratio = ef_ratio[
        ef_ratio.index.get_level_values(3) == "Enteric Fermentation|Floor"
    ].sort_index()

    # Clear afolu_adoption_curves.csv, and run adoption_projection_demand() to
    # calculate logistics curves for afolu reduction ratios

    # Clear afolu_adoption_curves.csv and afolu_ef_ratio.csv
    if os.path.exists("podi/data/afolu_adoption_curves.csv"):
        os.remove("podi/data/afolu_adoption_curves.csv")
    if os.path.exists("podi/data/afolu_ef_ratios.csv"):
        os.remove("podi/data/afolu_ef_ratios.csv")

    def adoption_projection_demand(
        parameters,
        input_data,
        scenario,
        data_end_year,
        saturation_year,
        proj_end_year,
    ):
        def linear(x, a, b, c, d):
            return a * x + d

        def logistic(x, a, b, c, d):
            return c / (1 + np.exp(-a * (x - b))) + d

        # Create x array (year) and y array (linear scale from zero to saturation value)
        x_data = np.arange(0, proj_end_year - data_end_year + 1, 1)
        y_data = np.zeros((1, len(x_data)))
        y_data[:] = np.NaN
        y_data = y_data.squeeze().astype(float)
        y_data[0] = 0
        y_data[saturation_year - data_end_year] = parameters.loc[
            "Enteric Fermentation|saturation point",
        ].values[0]

        y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|parameter a min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|parameter a max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|parameter b min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|parameter b max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|saturation point"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Enteric Fermentation|saturation point"
                    ].value
                ),
            ),
            (
                0,
                0,
            ),
        ]

        # Define sum of squared error function
        def sum_of_squared_error(parameters):
            return np.sum((y_data - logistic(x_data, *parameters)) ** 2.0)

        # Generate genetic_parameters. For baseline scenarios, projections are linear
        if scenario == "baseline":
            y = linear(
                x_data,
                min(
                    0.0018,
                    max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data))),
                ),
                (y_data[-1]),
            )
            genetic_parameters = [0, 0, 0, 0]
        else:
            genetic_parameters = differential_evolution(
                sum_of_squared_error,
                search_bounds,
                seed=3,
                polish=False,
                updating="immediate",
                mutation=(0, 1),
            ).x

        y = np.array(logistic(x_data, *genetic_parameters))

        pd.concat(
            [
                pd.DataFrame(
                    np.array(
                        [
                            input_data.name[0],
                            input_data.name[1],
                            input_data.name[2],
                            input_data.name[3],
                        ]
                    )
                ).T,
                pd.DataFrame(y).T,
            ],
            axis=1,
        ).to_csv(
            "podi/data/afolu_adoption_curves.csv",
            mode="a",
            header=None,
            index=False,
        )

        return

    ef_ratio.apply(
        lambda x: adoption_projection_demand(
            parameters=parameters.loc[x.name[0], x.name[1], x.name[2]],
            input_data=x,
            scenario=scenario,
            data_end_year=data_end_year + 1,
            saturation_year=2043,
            proj_end_year=proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_adoption_curves.csv", header=None)
        )
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(
                            ["model", "scenario", "region", "product_short"]
                        )
                    ).T,
                    pd.DataFrame(
                        np.linspace(
                            data_end_year + 1,
                            proj_end_year,
                            proj_end_year - data_end_year,
                        ).astype(int)
                    ).T,
                ],
                axis=1,
            ).squeeze(),
            axis=1,
        )
        .set_index(["model", "scenario", "region", "product_short"])
    ).sort_index()

    # Prepare df for multiplication with emissions
    ef_ratios = ef_ratios.parallel_apply(
        lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
    )

    ef_ratios = (
        pd.DataFrame(
            1,
            index=ef_ratios.index,
            columns=np.arange(data_start_year, data_end_year + 1, 1),
        )
    ).join(ef_ratios)
    ef_ratios = ef_ratios.loc[:, : emissions_output_co2e.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/afolu_ef_ratios.csv")

    ef_ratios.update(
        ef_ratios.parallel_apply(
            lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1
        ).fillna(0)
    )

    emissions_output_co2e.update(
        emissions_output_co2e[
            (
                 (
                    emissions_output_co2e.reset_index().flow_long
                    == "Enteric Fermentation"
                )
            ).values
        ]
        .loc[:, data_end_year:]
        .parallel_apply(
            lambda x: x.mul(ef_ratios.loc[:, data_end_year:].squeeze().values),
            axis=1,
        )
    )

    # endregion

    ###################################
    #  REDUCE MANURE LEFT ON PASTURE  #
    ###################################

    # region

    # Calculate reduction factors that scale down Manure left on Pasture over time

    # Load saturation points for reduction ratios
    ef_ratio = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters_afolu.csv",
            )
        )
        .set_index(["model", "scenario", "region", "variable"])
        .loc[
            slice(None),
            "pathway",
            slice(None),
            [
                "Manure left on Pasture|Floor",
                "Manure left on Pasture|Max annual growth",
                "Manure left on Pasture|parameter a max",
                "Manure left on Pasture|parameter a min",
                "Manure left on Pasture|parameter b max",
                "Manure left on Pasture|parameter b min",
                "Manure left on Pasture|saturation point",
            ],
        ]
    )

    parameters = ef_ratio

    ef_ratio = ef_ratio[
        ef_ratio.index.get_level_values(3) == "Manure left on Pasture|Floor"
    ].sort_index()

    # Clear afolu_adoption_curves.csv, and run adoption_projection_demand() to
    # calculate logistics curves for afolu reduction ratios

    # Clear afolu_adoption_curves.csv and afolu_ef_ratio.csv
    if os.path.exists("podi/data/afolu_adoption_curves.csv"):
        os.remove("podi/data/afolu_adoption_curves.csv")
    if os.path.exists("podi/data/afolu_ef_ratios.csv"):
        os.remove("podi/data/afolu_ef_ratios.csv")

    def adoption_projection_demand(
        parameters,
        input_data,
        scenario,
        data_end_year,
        saturation_year,
        proj_end_year,
    ):
        def linear(x, a, b, c, d):
            return a * x + d

        def logistic(x, a, b, c, d):
            return c / (1 + np.exp(-a * (x - b))) + d

        # Create x array (year) and y array (linear scale from zero to saturation value)
        x_data = np.arange(0, proj_end_year - data_end_year + 1, 1)
        y_data = np.zeros((1, len(x_data)))
        y_data[:] = np.NaN
        y_data = y_data.squeeze().astype(float)
        y_data[0] = 0
        y_data[saturation_year - data_end_year] = parameters.loc[
            "Manure left on Pasture|saturation point",
        ].values[0]

        y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|parameter a min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|parameter a max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|parameter b min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|parameter b max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|saturation point"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure left on Pasture|saturation point"
                    ].value
                ),
            ),
            (
                0,
                0,
            ),
        ]

        # Define sum of squared error function
        def sum_of_squared_error(parameters):
            return np.sum((y_data - logistic(x_data, *parameters)) ** 2.0)

        # Generate genetic_parameters. For baseline scenarios, projections are linear
        if scenario == "baseline":
            y = linear(
                x_data,
                min(
                    0.0018,
                    max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data))),
                ),
                (y_data[-1]),
            )
            genetic_parameters = [0, 0, 0, 0]
        else:
            genetic_parameters = differential_evolution(
                sum_of_squared_error,
                search_bounds,
                seed=3,
                polish=False,
                updating="immediate",
                mutation=(0, 1),
            ).x

        y = np.array(logistic(x_data, *genetic_parameters))

        pd.concat(
            [
                pd.DataFrame(
                    np.array(
                        [
                            input_data.name[0],
                            input_data.name[1],
                            input_data.name[2],
                            input_data.name[3],
                        ]
                    )
                ).T,
                pd.DataFrame(y).T,
            ],
            axis=1,
        ).to_csv(
            "podi/data/afolu_adoption_curves.csv",
            mode="a",
            header=None,
            index=False,
        )

        return

    ef_ratio.apply(
        lambda x: adoption_projection_demand(
            parameters=parameters.loc[x.name[0], x.name[1], x.name[2]],
            input_data=x,
            scenario=scenario,
            data_end_year=data_end_year + 1,
            saturation_year=2043,
            proj_end_year=proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_adoption_curves.csv", header=None)
        )
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(
                            ["model", "scenario", "region", "product_short"]
                        )
                    ).T,
                    pd.DataFrame(
                        np.linspace(
                            data_end_year + 1,
                            proj_end_year,
                            proj_end_year - data_end_year,
                        ).astype(int)
                    ).T,
                ],
                axis=1,
            ).squeeze(),
            axis=1,
        )
        .set_index(["model", "scenario", "region", "product_short"])
    ).sort_index()

    # Prepare df for multiplication with emissions
    ef_ratios = ef_ratios.parallel_apply(
        lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
    )

    ef_ratios = (
        pd.DataFrame(
            1,
            index=ef_ratios.index,
            columns=np.arange(data_start_year, data_end_year + 1, 1),
        )
    ).join(ef_ratios)
    ef_ratios = ef_ratios.loc[:, : emissions_output_co2e.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/afolu_ef_ratios.csv")

    ef_ratios.update(
        ef_ratios.parallel_apply(
            lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1
        ).fillna(0)
    )

    emissions_output_co2e.update(
        emissions_output_co2e[
            (
                 (
                    emissions_output_co2e.reset_index().flow_long
                    == "Manure left on Pasture"
                )
            ).values
        ]
        .loc[:, data_end_year:]
        .parallel_apply(
            lambda x: x.mul(ef_ratios.loc[:, data_end_year:].squeeze().values),
            axis=1,
        )
    )

    # endregion

    ##############################
    #  REDUCE MANURE MANAGEMENT  #
    ##############################

    # region

    # Calculate reduction factors that scale down Manure Management over time

    # Load saturation points for reduction ratios
    ef_ratio = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters_afolu.csv",
            )
        )
        .set_index(["model", "scenario", "region", "variable"])
        .loc[
            slice(None),
            "pathway",
            slice(None),
            [
                "Manure Management|Floor",
                "Manure Management|Max annual growth",
                "Manure Management|parameter a max",
                "Manure Management|parameter a min",
                "Manure Management|parameter b max",
                "Manure Management|parameter b min",
                "Manure Management|saturation point",
            ],
        ]
    )

    parameters = ef_ratio

    ef_ratio = ef_ratio[
        ef_ratio.index.get_level_values(3) == "Manure Management|Floor"
    ].sort_index()

    # Clear afolu_adoption_curves.csv, and run adoption_projection_demand() to
    # calculate logistics curves for afolu reduction ratios

    # Clear afolu_adoption_curves.csv and afolu_ef_ratio.csv
    if os.path.exists("podi/data/afolu_adoption_curves.csv"):
        os.remove("podi/data/afolu_adoption_curves.csv")
    if os.path.exists("podi/data/afolu_ef_ratios.csv"):
        os.remove("podi/data/afolu_ef_ratios.csv")

    def adoption_projection_demand(
        parameters,
        input_data,
        scenario,
        data_end_year,
        saturation_year,
        proj_end_year,
    ):
        def linear(x, a, b, c, d):
            return a * x + d

        def logistic(x, a, b, c, d):
            return c / (1 + np.exp(-a * (x - b))) + d

        # Create x array (year) and y array (linear scale from zero to saturation value)
        x_data = np.arange(0, proj_end_year - data_end_year + 1, 1)
        y_data = np.zeros((1, len(x_data)))
        y_data[:] = np.NaN
        y_data = y_data.squeeze().astype(float)
        y_data[0] = 0
        y_data[saturation_year - data_end_year] = parameters.loc[
            "Manure Management|saturation point",
        ].values[0]

        y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(
                    parameters.loc["Manure Management|parameter a min"].value
                ),
                pd.to_numeric(
                    parameters.loc["Manure Management|parameter a max"].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc["Manure Management|parameter b min"].value
                ),
                pd.to_numeric(
                    parameters.loc["Manure Management|parameter b max"].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc["Manure Management|saturation point"].value
                ),
                pd.to_numeric(
                    parameters.loc["Manure Management|saturation point"].value
                ),
            ),
            (
                0,
                0,
            ),
        ]

        # Define sum of squared error function
        def sum_of_squared_error(parameters):
            return np.sum((y_data - logistic(x_data, *parameters)) ** 2.0)

        # Generate genetic_parameters. For baseline scenarios, projections are linear
        if scenario == "baseline":
            y = linear(
                x_data,
                min(
                    0.0018,
                    max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data))),
                ),
                (y_data[-1]),
            )
            genetic_parameters = [0, 0, 0, 0]
        else:
            genetic_parameters = differential_evolution(
                sum_of_squared_error,
                search_bounds,
                seed=3,
                polish=False,
                updating="immediate",
                mutation=(0, 1),
            ).x

        y = np.array(logistic(x_data, *genetic_parameters))

        pd.concat(
            [
                pd.DataFrame(
                    np.array(
                        [
                            input_data.name[0],
                            input_data.name[1],
                            input_data.name[2],
                            input_data.name[3],
                        ]
                    )
                ).T,
                pd.DataFrame(y).T,
            ],
            axis=1,
        ).to_csv(
            "podi/data/afolu_adoption_curves.csv",
            mode="a",
            header=None,
            index=False,
        )

        return

    ef_ratio.apply(
        lambda x: adoption_projection_demand(
            parameters=parameters.loc[x.name[0], x.name[1], x.name[2]],
            input_data=x,
            scenario=scenario,
            data_end_year=data_end_year + 1,
            saturation_year=2043,
            proj_end_year=proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_adoption_curves.csv", header=None)
        )
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(
                            ["model", "scenario", "region", "product_short"]
                        )
                    ).T,
                    pd.DataFrame(
                        np.linspace(
                            data_end_year + 1,
                            proj_end_year,
                            proj_end_year - data_end_year,
                        ).astype(int)
                    ).T,
                ],
                axis=1,
            ).squeeze(),
            axis=1,
        )
        .set_index(["model", "scenario", "region", "product_short"])
    ).sort_index()

    # Prepare df for multiplication with emissions
    ef_ratios = ef_ratios.parallel_apply(
        lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
    )

    ef_ratios = (
        pd.DataFrame(
            1,
            index=ef_ratios.index,
            columns=np.arange(data_start_year, data_end_year + 1, 1),
        )
    ).join(ef_ratios)
    ef_ratios = ef_ratios.loc[:, : emissions_output_co2e.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/afolu_ef_ratios.csv")

    ef_ratios.update(
        ef_ratios.parallel_apply(
            lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1
        ).fillna(0)
    )

    emissions_output_co2e.update(
        emissions_output_co2e[
            (
                 (
                    emissions_output_co2e.reset_index().flow_long
                    == "Manure Management"
                )
            ).values
        ]
        .loc[:, data_end_year:]
        .parallel_apply(
            lambda x: x.mul(ef_ratios.loc[:, data_end_year:].squeeze().values),
            axis=1,
        )
    )

    # endregion

    ####################################
    #  REDUCE MANURE APPLIED TO SOILS  #
    ####################################

    # region

    # Calculate reduction factors that scale down Manure applied to Soils over time

    # Load saturation points for reduction ratios
    ef_ratio = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters_afolu.csv",
            )
        )
        .set_index(["model", "scenario", "region", "variable"])
        .loc[
            slice(None),
            "pathway",
            slice(None),
            [
                "Manure applied to Soils|Floor",
                "Manure applied to Soils|Max annual growth",
                "Manure applied to Soils|parameter a max",
                "Manure applied to Soils|parameter a min",
                "Manure applied to Soils|parameter b max",
                "Manure applied to Soils|parameter b min",
                "Manure applied to Soils|saturation point",
            ],
        ]
    )

    parameters = ef_ratio

    ef_ratio = ef_ratio[
        ef_ratio.index.get_level_values(3) == "Manure applied to Soils|Floor"
    ].sort_index()

    # Clear afolu_adoption_curves.csv, and run adoption_projection_demand() to
    # calculate logistics curves for afolu reduction ratios

    # Clear afolu_adoption_curves.csv and afolu_ef_ratio.csv
    if os.path.exists("podi/data/afolu_adoption_curves.csv"):
        os.remove("podi/data/afolu_adoption_curves.csv")
    if os.path.exists("podi/data/afolu_ef_ratios.csv"):
        os.remove("podi/data/afolu_ef_ratios.csv")

    def adoption_projection_demand(
        parameters,
        input_data,
        scenario,
        data_end_year,
        saturation_year,
        proj_end_year,
    ):
        def linear(x, a, b, c, d):
            return a * x + d

        def logistic(x, a, b, c, d):
            return c / (1 + np.exp(-a * (x - b))) + d

        # Create x array (year) and y array (linear scale from zero to saturation value)
        x_data = np.arange(0, proj_end_year - data_end_year + 1, 1)
        y_data = np.zeros((1, len(x_data)))
        y_data[:] = np.NaN
        y_data = y_data.squeeze().astype(float)
        y_data[0] = 0
        y_data[saturation_year - data_end_year] = parameters.loc[
            "Manure applied to Soils|saturation point",
        ].values[0]

        y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|parameter a min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|parameter a max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|parameter b min"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|parameter b max"
                    ].value
                ),
            ),
            (
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|saturation point"
                    ].value
                ),
                pd.to_numeric(
                    parameters.loc[
                        "Manure applied to Soils|saturation point"
                    ].value
                ),
            ),
            (
                0,
                0,
            ),
        ]

        # Define sum of squared error function
        def sum_of_squared_error(parameters):
            return np.sum((y_data - logistic(x_data, *parameters)) ** 2.0)

        # Generate genetic_parameters. For baseline scenarios, projections are linear
        if scenario == "baseline":
            y = linear(
                x_data,
                min(
                    0.0018,
                    max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data))),
                ),
                (y_data[-1]),
            )
            genetic_parameters = [0, 0, 0, 0]
        else:
            genetic_parameters = differential_evolution(
                sum_of_squared_error,
                search_bounds,
                seed=3,
                polish=False,
                updating="immediate",
                mutation=(0, 1),
            ).x

        y = np.array(logistic(x_data, *genetic_parameters))

        pd.concat(
            [
                pd.DataFrame(
                    np.array(
                        [
                            input_data.name[0],
                            input_data.name[1],
                            input_data.name[2],
                            input_data.name[3],
                        ]
                    )
                ).T,
                pd.DataFrame(y).T,
            ],
            axis=1,
        ).to_csv(
            "podi/data/afolu_adoption_curves.csv",
            mode="a",
            header=None,
            index=False,
        )

        return

    ef_ratio.apply(
        lambda x: adoption_projection_demand(
            parameters=parameters.loc[x.name[0], x.name[1], x.name[2]],
            input_data=x,
            scenario=scenario,
            data_end_year=data_end_year + 1,
            saturation_year=2043,
            proj_end_year=proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(
            pd.read_csv("podi/data/afolu_adoption_curves.csv", header=None)
        )
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(
                            ["model", "scenario", "region", "product_short"]
                        )
                    ).T,
                    pd.DataFrame(
                        np.linspace(
                            data_end_year + 1,
                            proj_end_year,
                            proj_end_year - data_end_year,
                        ).astype(int)
                    ).T,
                ],
                axis=1,
            ).squeeze(),
            axis=1,
        )
        .set_index(["model", "scenario", "region", "product_short"])
    ).sort_index()

    # Prepare df for multiplication with emissions
    ef_ratios = ef_ratios.parallel_apply(
        lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
    )

    ef_ratios = (
        pd.DataFrame(
            1,
            index=ef_ratios.index,
            columns=np.arange(data_start_year, data_end_year + 1, 1),
        )
    ).join(ef_ratios)
    ef_ratios = ef_ratios.loc[:, : emissions_output_co2e.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/afolu_ef_ratios.csv")

    ef_ratios.update(
        ef_ratios.parallel_apply(
            lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1
        ).fillna(0)
    )

    emissions_output_co2e.update(
        emissions_output_co2e[
            (
                (
                    emissions_output_co2e.reset_index().flow_long
                    == "Manure applied to Soils"
                )
            ).values
        ]
        .loc[:, data_end_year:]
        .parallel_apply(
            lambda x: x.mul(ef_ratios.loc[:, data_end_year:].squeeze().values),
            axis=1,
        )
    )

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    emissions_output.columns = emissions_output.columns.astype(str)
    for col in emissions_output.select_dtypes(include="float64").columns:
        emissions_output[col] = emissions_output[col].astype("float32")
    emissions_output.sort_index().to_parquet(
        "podi/data/emissions_output.parquet", compression="brotli"
    )

    emissions_output_co2e.columns = emissions_output_co2e.columns.astype(str)
    for col in emissions_output_co2e.select_dtypes(include="float64").columns:
        emissions_output_co2e[col] = emissions_output_co2e[col].astype(
            "float32"
        )
    emissions_output_co2e.sort_index().to_parquet(
        "podi/data/emissions_output_co2e.parquet", compression="brotli"
    )

    # endregion

    return
