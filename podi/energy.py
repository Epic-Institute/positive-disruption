#!/usr/bin/env python

# region

import pandas as pd
import numpy as np
from numpy import NaN
from podi.adoption_curve_demand import adoption_curve_demand
from podi.adoption_curve import adoption_curve
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import os

pandarallel.initialize(nb_workers=4)

# These are diagnostic files for adoption curve fitting and will be removed soon
file = open("podi/data/y_data.csv", "w")
file.close()
file = open("podi/data/y_data2.csv", "w")
file.close()

# endregion


def energy(scenario, data_start_year, data_end_year, proj_end_year):

    ############################
    #  LOAD HISTORICAL ENERGY  #
    ############################

    # region

    recalc_energy_historical = False
    if recalc_energy_historical is True:
        regions = pd.read_csv("podi/data/IEA/Regions.txt").squeeze("columns")
        energy_historical2 = pd.DataFrame([])
        for region in regions:
            energy_historical = pd.DataFrame(
                pd.read_fwf(
                    str("podi/data/IEA/" + region + ".txt"),
                    colspecs=[
                        (0, 15),
                        (16, 31),
                        (32, 47),
                        (48, 63),
                        (64, 70),
                        (71, -1),
                    ],
                    names=["Region", "Product", "Year", "Flow", "Unit", "Value"],
                )
            ).replace(["x", "c", ".."], 0)

            # Filter for data start_year
            energy_historical = energy_historical[
                (energy_historical["Year"] >= data_start_year)
                & (energy_historical["Year"] < data_end_year)
            ]

            # Change values to float
            energy_historical["Value"] = energy_historical["Value"].astype(float)

            # Drop unit column since all values are in TJ
            energy_historical.drop("Unit", axis=1, inplace=True)

            # Change from all caps to lowercase
            energy_historical["Region"] = energy_historical["Region"].str.lower()

            # Format as a dataframe with timeseries as rows
            energy_historical = pd.pivot_table(
                energy_historical,
                values="Value",
                index=["Region", "Product", "Flow"],
                columns="Year",
            ).replace(NaN, 0)

            # Remove duplicate regions created due to name overlaps
            energy_historical = energy_historical.loc[[region.lower()], :]

            # Build dataframe consisting of all regions
            energy_historical2 = pd.concat([energy_historical2, energy_historical])
        energy_historical = energy_historical2

        energy_historical.to_csv("podi/data/energy_historical.csv")
    else:
        energy_historical = pd.DataFrame(
            pd.read_csv("podi/data/energy_historical.csv")
        ).set_index(["Region", "Product", "Flow"])

    energy_historical.columns = energy_historical.columns.astype(int)

    # Filter product categories that are redundant or unused
    products = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/IEA/Other/IEA_Product_Definitions.csv",
                usecols=["Product Category", "Product", "Short name"],
            )
        )
        .set_index("Product Category")
        .loc[
            [
                "Biofuels and Waste",
                "Coal",
                "Crude, NGL, refinery feedstocks",
                "Electricity and Heat",
                "Natural gas",
                "Oil products",
                "Oil shale",
                "Peat and peat products",
            ]
        ]
    )["Short name"]

    # Filter out products that are summations of other products
    products = products[
        ~products.isin(
            [
                "TOTAL",
                "TOTPRODS",
                "SOLWIND",
                "MTOTSOLID",
                "MTOTOIL",
                "MTOTOTHER",
                "MRENEW",
                "CRNGFEED",
                "COMRENEW",
            ]
        )
    ]

    # Filter out flow categories that are redundant or unused
    flows = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/IEA/Other/IEA_Flow_Definitions.csv",
                usecols=["Flow Category", "Flow", "Short name"],
            )
        )
        .set_index("Flow Category")
        .loc[
            [
                "Energy industry own use and Losses",
                "Electricity output",
                "Final consumption",
                "Heat output",
                "Supply",
                "Transformation processes",
            ]
        ]
    )["Short name"]

    # Filter out flows that are summations of other products or for energy balance purposes (exports, imports, statistical differences, stock changes, transfers)
    flows = flows[
        ~flows.isin(
            [
                "ELOUTPUT",
                "EXPORTS",
                "HEATOUT",
                "IMPORTS",
                "INDPROD",
                "LIQUEFAC",
                "NONENUSE",
                "STATDIFF",
                "STOCKCHA",
                "TES",
                "TFC",
                "TRANSFER",
                "TOTIND",
                "TOTTRANF",
                "TOTTRANS",
                "OWNUSE",
            ]
        )
    ]

    energy_historical = energy_historical.loc[slice(None), products, flows]

    # Add IRENA data for select electricity technologies

    # region
    irena = pd.read_csv(
        "podi/data/IRENA/electricity_supply_historical.csv", index_col="Region"
    )

    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "IRENA Region"],
            ).dropna(axis=0)
        )
        .set_index(["IRENA Region"])
        .rename_axis(index={"IRENA Region": "Region"})
    )

    irena = (
        irena.merge(regions, on=["Region"])
        .reset_index()
        .set_index(["WEB Region", "Region"])
        .droplevel("Region")
        .rename_axis(index={"WEB Region": "Region"})
    )
    irena.index = irena.index.str.lower()
    irena = irena.reset_index().set_index(
        [
            "Region",
            "Product",
            "Flow",
        ]
    )

    irena.columns = irena.columns.astype(int)
    irena = irena.loc[:, data_start_year:data_end_year]

    # Drop IEA WIND and SOLARPV to avoid duplication with IRENA ONSHORE/OFFSHORE/ROOFTOP/SOLARPV
    energy_historical.drop(labels="WIND", level=1, inplace=True)
    energy_historical.drop(labels="SOLARPV", level=1, inplace=True)

    energy_historical = pd.concat(
        [
            energy_historical,
            irena[
                irena.index.get_level_values(1).isin(
                    ["ONSHORE", "OFFSHORE", "ROOFTOP", "SOLARPV"]
                )
            ],
        ]
    )

    # endregion

    # endregion

    ###############################
    #  ADD LABELS & RECATEGORIZE  #
    ###############################

    # region

    # Add product and flow labels to energy_historical
    labels = pd.DataFrame(
        pd.read_csv(
            "podi/data/product_flow_labels.csv",
            usecols=[
                "Product",
                "Flow",
                "Sector",
                "Subsector",
                "EIA Product",
                "Hydrogen",
                "Flexible",
                "Non-Energy Use",
            ],
        )
    ).set_index(["Product", "Flow"])

    energy_historical = (
        (
            energy_historical.reset_index()
            .set_index(["Product", "Flow"])
            .merge(labels, on=["Product", "Flow"])
        )
        .reset_index()
        .set_index(
            [
                "Region",
                "Sector",
                "Subsector",
                "Product",
                "Flow",
                "EIA Product",
                "Hydrogen",
                "Flexible",
                "Non-Energy Use",
            ]
        )
    )

    # Drop rows with NaN index, representing the product/flow combination does not exist in historical data for any region
    energy_historical = energy_historical[
        ~energy_historical.index.get_level_values(1).isna()
    ]

    # For Transportation flows ROAD/DOMESAIR/RAIL that were duplicated to make Two- and three-wheeled/Light-Duty/Medium-Duty/Heavy-Duty flows, scale their energy so the sum of subflows is equal to the original energy estimate

    # region

    subsector_props = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters.csv",
                usecols=[
                    "Region",
                    "Product",
                    "Scenario",
                    "Sector",
                    "Metric",
                    "Value",
                ],
            ),
        )
        .set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
        .loc[
            slice(None),
            slice(None),
            scenario,
            slice(None),
            [
                "Two- and three-wheeled",
                "Light",
                "Medium",
                "Heavy",
                "Hydrogen",
                "Non-Hydrogen",
            ],
        ]
    )

    energy_historical.update(
        energy_historical.loc[
            slice(None),
            ["Transportation"],
            slice(None),
            slice(None),
            ["ROAD", "DOMESAIR", "RAIL"],
        ].parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[0], x.name[4], scenario, "Transportation", x.name[2]
                ].values
            ),
            axis=1,
        )
    )

    # endregion

    # For products HEAT/HEATNS that were duplicated to make Low Temperature/High Temperature products, scale their energy so the sum of the subproducts is equal to the original energy estimate

    # region

    subsector_props = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters.csv",
                usecols=[
                    "Region",
                    "Product",
                    "Scenario",
                    "Sector",
                    "Metric",
                    "Value",
                ],
            ),
        )
        .set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
        .loc[
            slice(None),
            slice(None),
            scenario,
            slice(None),
            ["Low Temperature", "High Temperature"],
        ]
    )

    energy_historical.update(
        energy_historical.loc[
            slice(None),
            slice(None),
            slice(None),
            ["HEAT", "HEATNS"],
        ].parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    "world", x.name[3], scenario, x.name[4], x.name[2]
                ].values
            ),
            axis=1,
        )
    )

    # endregion

    # For Product NONCRUDE that was duplicated to make Hydrogen/Non-Hydrogen products and flows, scale their energy so the sum of the subflows is equal to the original energy estimate.

    # region
    subsector_props = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters.csv",
                usecols=[
                    "Region",
                    "Product",
                    "Scenario",
                    "Sector",
                    "Metric",
                    "Value",
                ],
            ),
        )
        .set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
        .loc[
            slice(None),
            slice(None),
            scenario,
            slice(None),
            ["Hydrogen", "Non-Hydrogen"],
        ]
    )

    energy_historical.update(
        energy_historical.loc[
            slice(None), slice(None), ["Hydrogen", "Non-Hydrogen"], ["NONCRUDE"]
        ].parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    "world", x.name[3], scenario, x.name[4], x.name[2]
                ].values
            ),
            axis=1,
        )
    )

    # Recast Product from NONCRUDE to HYDROGEN
    energy_historical.reset_index(inplace=True)
    energy_historical[
        (energy_historical["Subsector"] == "Hydrogen")
        & (energy_historical["Product"] == "NONCRUDE")
    ] = (
        energy_historical[
            (energy_historical["Subsector"] == "Hydrogen")
            & (energy_historical["Product"] == "NONCRUDE")
        ]
        .replace({"Hydrogen": "na"})
        .replace({"NONCRUDE": "HYDROGEN"})
    )

    energy_historical.set_index(
        [
            "Region",
            "Sector",
            "Subsector",
            "Product",
            "Flow",
            "EIA Product",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ],
        inplace=True,
    )

    # endregion

    # Add EIA region labels to energy_historical in order to match EIA regional projected growth of each product
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "EIA Region"],
            ).dropna(axis=0)
        )
        .set_index(["WEB Region"])
        .rename_axis(index={"WEB Region": "Region"})
    )
    regions.index = regions.index.str.lower()

    energy_historical = (
        (
            energy_historical.reset_index()
            .set_index(["Region"])
            .merge(regions, on=["Region"])
        )
        .reset_index()
        .set_index(["EIA Region"])
    )

    # Add categories and long names for products and flows

    # region

    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_Product_Definitions.csv",
        usecols=["Product Category", "Product", "Short name"],
    )

    energy_historical["Product_category"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["Short name"] == x["Product"]][
            "Product Category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_historical["Product_long"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["Short name"] == x["Product"]]["Product"].squeeze(
            "rows"
        ),
        axis=1,
    )

    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_Flow_Definitions.csv",
        usecols=["Flow Category", "Flow", "Short name"],
    )

    energy_historical["Flow_category"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["Short name"] == x["Flow"]][
            "Flow Category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_historical["Flow_long"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["Short name"] == x["Flow"]]["Flow"].squeeze(
            "rows"
        ),
        axis=1,
    )

    # Add scenario
    energy_historical["Scenario"] = scenario

    energy_historical = energy_historical.reset_index().set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
            "EIA Region",
            "EIA Product",
        ]
    )

    # endregion

    # Convert Electricity output flow category from GWh to TJ
    energy_historical.update(
        energy_historical[
            energy_historical.index.get_level_values(7) == "Electricity output"
        ].multiply(3.6)
    )

    # Convert AVBUNK & AVMAR to be positive (they were negative by convention representing an 'export' to an international region WORLDAV and WORLDMAR)
    energy_historical[
        energy_historical.index.get_level_values(9).isin(["AVBUNK", "MARBUNK"])
    ] = energy_historical[
        energy_historical.index.get_level_values(9).isin(["AVBUNK", "MARBUNK"])
    ].abs()

    # endregion

    #############################
    #  PROJECT BASELINE ENERGY  #
    #############################

    recalc_energy_baseline = False
    # region

    if recalc_energy_baseline == True:
        # Load EIA energy projections
        energy_projection = (
            pd.read_excel(
                pd.ExcelFile("podi/data/EIA/EIA_IEO.xlsx", engine="openpyxl"), header=0
            )
            .dropna(axis="index", how="all")
            .dropna(axis="columns", thresh=2)
        ).loc[:, :proj_end_year]

        # Strip preceding space in EIA Sector values
        energy_projection["EIA Product"] = energy_projection["EIA Product"].str.strip()

        # create dataframe of energy projections as annual % change
        energy_projection = (
            pd.DataFrame(energy_projection).set_index(
                ["EIA Region", "Sector", "EIA Product"]
            )
        ).pct_change(axis=1).replace(NaN, 0) + 1
        energy_projection.iloc[:, 0] = energy_projection.iloc[:, 1]

        # Merge historical and projected energy
        energy_baseline = (
            (
                energy_historical.reset_index()
                .set_index(["EIA Region", "Sector", "EIA Product"])
                .merge(energy_projection, on=["EIA Region", "Sector", "EIA Product"])
            )
            .reset_index()
            .set_index(
                [
                    "Scenario",
                    "Region",
                    "Sector",
                    "Subsector",
                    "Product_category",
                    "Product_long",
                    "Product",
                    "Flow_category",
                    "Flow_long",
                    "Flow",
                    "Hydrogen",
                    "Flexible",
                    "Non-Energy Use",
                    "EIA Region",
                    "EIA Product",
                ]
            )
            .droplevel(["EIA Region", "EIA Product"])
        )

        # Calculate projections by cumulative product
        energy_baseline = energy_baseline.loc[:, : data_end_year - 2].join(
            energy_baseline.loc[:, data_end_year - 1 :].cumprod(axis=1).fillna(0)
        )

        # Curve smooth projections
        energy_baseline = energy_baseline.loc[:, : data_end_year - 1].join(
            curve_smooth(energy_baseline.loc[:, data_end_year:], "linear", 2)
        )

        # Save to csv file
        energy_baseline.rename(index={scenario: "baseline"}).to_csv(
            "podi/data/energy_baseline.csv"
        )
    else:
        index = [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]

    energy_baseline = pd.DataFrame(
        pd.read_csv("podi/data/energy_baseline.csv")
    ).set_index(index)
    energy_baseline.columns = energy_baseline.columns.astype(int)

    # endregion

    ##############################################
    #  ESTIMATE ENERGY REDUCTIONS & FUEL SHIFTS  #
    ##############################################

    # region

    # Calculate 'electrification factors' that scale down energy over time due to the lower energy required to produce an equivalent amount of work via electricity

    # Load saturation points for energy reduction ratios
    ef_ratio = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/tech_parameters.csv",
                usecols=[
                    "Region",
                    "Product",
                    "Scenario",
                    "Sector",
                    "Metric",
                    "Value",
                ],
            ),
        )
        .set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
        .loc[
            energy_baseline.index.get_level_values(1).unique(),
            [
                "biofuels_waste ef ratio",
                "biofuels_waste addtl eff",
                "coal ef ratio",
                "coal addtl eff",
                "electricity ef ratio",
                "electricity addtl eff",
                "heat ef ratio",
                "heat addtl eff",
                "hydrogen ef ratio",
                "na",
                "natural gas ef ratio",
                "natural gas addtl eff",
                "nuclear ef ratio",
                "oil ef ratio",
                "oil addtl eff",
                "wws heat ef ratio",
                "wws heat addtl eff",
            ],
            scenario,
            slice(None),
            [
                "floor",
                "parameter a max",
                "parameter a min",
                "parameter b max",
                "parameter b min",
                "saturation point",
            ],
        ]
    ).sort_index()

    parameters = ef_ratio

    ef_ratio = ef_ratio[ef_ratio.index.get_level_values(4) == "floor"].sort_index()

    # Clear adoption curve demand file before running adoption_curve_demand()
    file = open("podi/data/energy_adoption_curves.csv", "w")
    file.close()

    # Run adoption_curve_demand() to calculate logistics curves for energy reduction ratios
    ef_ratio.parallel_apply(
        lambda x: adoption_curve_demand(
            parameters.loc[x.name[0], x.name[1], x.name[2], x.name[3]],
            x,
            scenario,
            data_start_year,
            data_end_year,
            proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(pd.read_csv("podi/data/energy_adoption_curves.csv", header=None))
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(["Region", "Product", "Scenario", "Sector"])
                    ).T,
                    pd.DataFrame(
                        np.linspace(
                            data_end_year,
                            proj_end_year,
                            proj_end_year - data_end_year + 1,
                        ).astype(int)
                    ).T,
                ],
                axis=1,
            ).squeeze(),
            axis=1,
        )
        .set_index(["Region", "Sector", "Product", "Scenario"])
    )

    # Prepare df for multiplication with energy
    ef_ratios = ef_ratios.parallel_apply(
        lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
    )

    ef_ratios = (
        pd.DataFrame(
            1,
            index=ef_ratios.index,
            columns=np.arange(data_start_year, data_end_year, 1),
        )
    ).join(ef_ratios)
    ef_ratios = ef_ratios.loc[:, : energy_baseline.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/ef_ratios.csv")

    # Add labels to ef_ratios
    labels = (
        (
            pd.DataFrame(
                pd.read_csv(
                    "podi/data/product_flow_labels.csv",
                    usecols=[
                        "Product",
                        "Flow",
                        "Sector",
                        "Subsector",
                        "WWS EF Product",
                        "WWS Upstream Product",
                        "WWS Addtl Efficiency",
                    ],
                )
            ).set_index(["Sector", "WWS EF Product"])
        )
        .rename_axis(index={"WWS EF Product": "Product"})
        .rename(columns={"Product": "IEA Product"})
    ).sort_index()

    ef_ratios = (
        (
            ef_ratios.reset_index()
            .set_index(["Sector", "Product"])
            .merge(labels, on=["Sector", "Product"])
            .set_index(
                [
                    "Region",
                    "Scenario",
                    "Subsector",
                    "IEA Product",
                    "Flow",
                    "WWS Upstream Product",
                    "WWS Addtl Efficiency",
                ],
                append=True,
            )
        )
        .droplevel(["Product", "Scenario"])
        .reorder_levels(
            [
                "Region",
                "Sector",
                "Subsector",
                "IEA Product",
                "Flow",
                "WWS Upstream Product",
                "WWS Addtl Efficiency",
            ]
        )
    )

    # Remove duplicate indices
    ef_ratios = ef_ratios[~ef_ratios.index.duplicated()]

    # Calculate 'upstream ratios' that scale down energy over time due to the lower energy required for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing. Note that not all upstream fossil energy is eliminiated, since some upstream energy is expected to remain to produce fossil fuel flows for non-energy use.
    upstream_ratios = ef_ratios.copy()

    upstream_ratios.update(
        upstream_ratios[upstream_ratios.index.get_level_values(5) == "Y"]
        .parallel_apply(lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1)
        .fillna(0)
    )

    # Set upstream ratios in ef_ratios to 1 so upstream reduction is not double counted
    ef_ratios[ef_ratios.index.get_level_values(5) == "Y"] = 1
    ef_ratios = ef_ratios.sort_index()

    upstream_ratios[upstream_ratios.index.get_level_values(5) == "N"] = 1
    upstream_ratios = upstream_ratios.sort_index()

    # Reduce energy by the upstream energy reductions from fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    energy_post_upstream = energy_baseline.parallel_apply(
        lambda x: x.mul(
            upstream_ratios.loc[
                x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]
            ].squeeze()
        ),
        axis=1,
    )
    energy_post_upstream.rename(index={"baseline": scenario}, inplace=True)

    # Apply percentage reduction attributed to additional energy efficiency measures
    addtl_eff = pd.DataFrame(pd.read_csv("podi/data/ef_ratios.csv")).set_index(
        ["Scenario", "Region", "Sector", "Product"]
    )
    addtl_eff.columns = addtl_eff.columns.astype(int)

    labels = (
        labels.reset_index()
        .drop(columns=["WWS Upstream Product", "Product", "Subsector"])
        .set_index(["Sector", "WWS Addtl Efficiency"])
        .rename_axis(index={"WWS Addtl Efficiency": "Product"})
        .rename(columns={"Product": "IEA Product"})
    )

    addtl_eff = (
        (
            addtl_eff.reset_index()
            .set_index(["Sector", "Product"])
            .merge(labels, on=["Sector", "Product"])
            .set_index(
                [
                    "Region",
                    "Scenario",
                    "IEA Product",
                    "Flow",
                ],
                append=True,
            )
        )
        .droplevel(["Product", "Scenario"])
        .reorder_levels(["Region", "Sector", "IEA Product", "Flow"])
    )

    addtl_eff = addtl_eff.groupby(["Region", "Sector", "IEA Product", "Flow"]).mean()

    # Remove duplicate indices
    addtl_eff = addtl_eff[~addtl_eff.index.duplicated()]
    addtl_eff = addtl_eff.sort_index()

    energy_post_addtl_eff = energy_post_upstream.parallel_apply(
        lambda x: x.mul(
            addtl_eff.loc[x.name[1], x.name[2], x.name[6], x.name[9]].squeeze()
        ),
        axis=1,
    )

    # Estimate energy reduction and fuel shifts due to electrification
    # region

    # Isolate the energy that gets replaced with (a reduced amount of) energy from electricity. Each row of energy is multiplied by ((ef[0] - ef[i]) / (ef[0] - ef[-1]), which represents the percent of energy that undergoes electrification in each year. This does not count preexisting electricity, except for nuclear, which is estimated to shift to renewables, and is treated in subsequent steps.
    energy_electrified = energy_post_addtl_eff.parallel_apply(
        lambda x: x.mul(
            (
                (
                    ef_ratios.loc[x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]]
                    .squeeze()
                    .iloc[0]
                    - ef_ratios.loc[
                        x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]
                    ].squeeze()
                )
                / (
                    ef_ratios.loc[x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]]
                    .squeeze()
                    .iloc[0]
                    - ef_ratios.loc[
                        x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]
                    ]
                    .squeeze()
                    .iloc[-1]
                )
            ).fillna(0)
        ),
        axis=1,
    )

    # Find the reduced amount of electrical energy that represents an equivalent amount of work to that of the energy that undergoes electrification.
    energy_reduced_electrified = energy_electrified[
        energy_electrified.index.get_level_values(7) != "Electricity output"
    ].parallel_apply(
        lambda x: x.mul(
            ef_ratios.loc[x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]]
            .squeeze()
            .iloc[-1]
        ),
        axis=1,
    )

    # Find the electrical energy from fossil fuels assumed to shift to renewables
    renewables = [
        "GEOTHERM",
        "HYDRO",
        "ROOFTOP",
        "SOLARPV",
        "SOLARTH",
        "OFFSHORE",
        "ONSHORE",
        "TIDE",
    ]

    energy_reduced_electrified = pd.concat(
        [
            energy_reduced_electrified,
            pd.concat(
                [
                    energy_post_addtl_eff[
                        ~energy_post_addtl_eff.index.get_level_values(6).isin(
                            renewables
                        )
                    ]
                    .loc[
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        ["Electricity output"],
                        :,
                    ]
                    .loc[:, :data_end_year]
                    * 0,
                    energy_post_addtl_eff[
                        ~energy_post_addtl_eff.index.get_level_values(6).isin(
                            renewables
                        )
                    ]
                    .loc[
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        slice(None),
                        ["Electricity output"],
                        :,
                    ]
                    .loc[:, data_end_year + 1 :]
                    .diff(axis=1)
                    .fillna(0)
                    .cumsum(axis=1),
                ],
                axis=1,
            ),
        ]
    )

    # Relabel reduced amount of energy as RELECTR or HYDROGEN
    energy_reduced_electrified2 = (
        energy_reduced_electrified.groupby(
            [
                "Scenario",
                "Region",
                "Sector",
                "Subsector",
                "Flow_category",
                "Flow_long",
                "Flow",
                "Hydrogen",
                "Flexible",
                "Non-Energy Use",
            ]
        )
        .sum()
        .reset_index()
    )

    energy_reduced_electrified_e = energy_reduced_electrified2[
        energy_reduced_electrified2["Hydrogen"] == "N"
    ]
    energy_reduced_electrified_e["Product_category"] = "Electricity and Heat"
    energy_reduced_electrified_e["Product_long"] = "Renewable Electricity"
    energy_reduced_electrified_e["Product"] = "RELECTR"

    energy_reduced_electrified_h = energy_reduced_electrified2[
        energy_reduced_electrified2["Hydrogen"] == "Y"
    ]
    energy_reduced_electrified_h["Product_category"] = "Hydrogen"
    energy_reduced_electrified_h["Product_long"] = "Hydrogen"
    energy_reduced_electrified_h["Product"] = "HYDROGEN"

    energy_reduced_electrified3 = pd.concat(
        [energy_reduced_electrified_e, energy_reduced_electrified_h]
    )

    energy_reduced_electrified3.set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ],
        inplace=True,
    )

    # Add this reduced level of electrical energy to overall energy, which is energy_post_addtl with the fossil fuel energy removed (energy_electrified)
    energy_post_electrification = (
        pd.concat(
            [
                energy_post_addtl_eff.subtract(energy_electrified),
                energy_reduced_electrified3,
            ]
        )
        .groupby(
            [
                "Scenario",
                "Region",
                "Sector",
                "Subsector",
                "Product_category",
                "Product_long",
                "Product",
                "Flow_category",
                "Flow_long",
                "Flow",
                "Hydrogen",
                "Flexible",
                "Non-Energy Use",
            ]
        )
        .sum()
    )
    # endregion

    # endregion

    #####################################
    # ESTIMATE UPDATED ELECTRICITY MIX  #
    #####################################

    # region
    # For each region, find the percent of total electricity consumption met by each renewable product.
    elec_supply = energy_post_electrification.loc[
        [scenario],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["Electricity output"],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["N"],
        :,
    ]

    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[1]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total electricity consumption met by each renewable product to estimate projected percent of total electricity consumption each meets
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
    parameters = parameters.sort_index()

    # Clear parameter output file before running adoption_curve()
    file = open("podi/data/adoption_curve_parameters.csv", "w")
    file.close()

    per_elec_supply.update(
        per_elec_supply[per_elec_supply.index.get_level_values(6).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[1], x.name[6], scenario, x.name[2]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Estimate the rate of nonrenewable electricity generation being replaced by renewable electricity generation
    nonrenewable_to_renewable = pd.concat(
        [
            elec_supply[
                ~elec_supply.index.get_level_values(6).isin(
                    pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                )
            ]
            .parallel_apply(
                lambda x: x.multiply(
                    per_elec_supply[
                        per_elec_supply.index.get_level_values(6).isin(
                            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                        )
                    ]
                    .groupby("Region")
                    .sum()
                    .loc[x.name[1]]
                ),
                axis=1,
            )
            .loc[:, :data_end_year]
            * 0,
            elec_supply[
                ~elec_supply.index.get_level_values(6).isin(
                    pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                )
            ]
            .parallel_apply(
                lambda x: x.multiply(
                    per_elec_supply[
                        per_elec_supply.index.get_level_values(6).isin(
                            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                        )
                    ]
                    .groupby("Region")
                    .sum()
                    .loc[x.name[1]]
                ),
                axis=1,
            )
            .loc[:, data_end_year + 1 :]
            .diff(axis=1)
            .fillna(0)
            .cumsum(axis=1),
        ],
        axis=1,
    )

    # Update nonrenewables electricity generation
    nonrenew = pd.concat(
        [
            elec_supply[
                ~elec_supply.index.get_level_values(6).isin(
                    pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                )
            ]
            .parallel_apply(
                lambda x: x.multiply(
                    1
                    - per_elec_supply[
                        per_elec_supply.index.get_level_values(6).isin(
                            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                        )
                    ]
                    .groupby("Region")
                    .sum()
                    .loc[x.name[1]]
                ),
                axis=1,
            )
            .loc[:, :data_end_year]
            * 0,
            elec_supply[
                ~elec_supply.index.get_level_values(6).isin(
                    pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                )
            ]
            .parallel_apply(
                lambda x: x.multiply(
                    1
                    - per_elec_supply[
                        per_elec_supply.index.get_level_values(6).isin(
                            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
                        )
                    ]
                    .groupby("Region")
                    .sum()
                    .loc[x.name[1]]
                ),
                axis=1,
            )
            .loc[:, data_end_year + 1 :]
            .diff(axis=1)
            .fillna(0)
            .cumsum(axis=1),
        ],
        axis=1,
    )

    elec_supply[
        ~elec_supply.index.get_level_values(6).isin(
            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
        )
    ] = elec_supply[
        ~elec_supply.index.get_level_values(6).isin(
            pd.concat([pd.Series(renewables), pd.Series("RELECTR")])
        )
    ].parallel_apply(
        lambda x: (x + nonrenew.loc[x.name]).clip(lower=0), axis=1
    )

    # Set renewables generation to meet RELECTR in the proportion estimated by adoption_curve(), and nonrenewable electricity generation that shifts to renewable generation
    elec_supply.update(
        pd.concat(
            [
                elec_supply[elec_supply.index.get_level_values(6).isin(renewables)].loc[
                    :, :data_end_year
                ],
                + per_elec_supply[
                    per_elec_supply.index.get_level_values(6).isin(renewables)
                ]
                .parallel_apply(
                    lambda x: x.multiply(
                        nonrenewable_to_renewable.groupby("Region")
                        .sum(0)
                        .loc[x.name[1]]
                        + elec_supply.groupby("Region")
                        .sum(0)
                        .loc[x.name[1]]
                    ),
                    axis=1,
                )
                .loc[:, data_end_year + 1 :],
            ],
            axis=1,
        )
    )

    # Drop RELECTR now that it has been reallocated to the specific set of renewables
    elec_supply.drop(labels="RELECTR", level=6, inplace=True)

    # Recast RELECTR to ELECTR in Final consumption
    energy_post_electrification.reset_index(inplace=True)
    energy_post_electrification[
        (energy_post_electrification["Product"] == "RELECTR")
        & (energy_post_electrification["Flow_category"] == "Final consumption")
    ] = (
        energy_post_electrification[
            (energy_post_electrification["Product"] == "RELECTR")
            & (energy_post_electrification["Flow_category"] == "Final consumption")
        ]
        .replace({"RELECTR": "ELECTR"})
        .replace({"Renewable Electricity": "Electricity"})
    )

    energy_post_electrification.set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]
    )

    energy_post_electrification = energy_post_electrification.groupby(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]
    ).sum()

    energy_post_electrification.drop(labels="RELECTR", level=6, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[1]]),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(elec_supply)

    # endregion

    ##############################
    # ESTIMATE UPDATED HEAT MIX  #
    ##############################

    # region

    renewables = ["GEOTHERM", "SOLARTH"]

    # For each region, for each subsector ('Low Temperature', 'High Temperature'), find the percent of total heat consumption met by each renewable product. heat_supply is 'Heat output' from the 'Electricity and Heat' product category, plus other products that are consumed within residential, commercial, and industrial sectors directly for heat.
    heat_supply = energy_post_electrification.loc[
        [scenario],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["Heat output"],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["N"],
        :,
    ]

    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(
            heat_supply.groupby(["Region", "Subsector"])
            .sum(0)
            .loc[x.name[1], x.name[3]]
        ),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total heat consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_heat_supply.update(
        per_heat_supply[per_heat_supply.index.get_level_values(6).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[1], x.name[6], scenario, x.name[2]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Set renewables heat generation to meet the amount estimated in Jacobson et al. (2016) to provide storage services.
    heat_supply.update(
        per_heat_supply[
            per_heat_supply.index.get_level_values(6).isin(renewables)
        ].parallel_apply(
            lambda x: x.multiply(
                heat_supply[heat_supply.index.get_level_values(6).isin(renewables)]
                .groupby(["Region", "Subsector"])
                .sum(0)
                .loc[x.name[1], x.name[3]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    """
    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(
            heat_supply.groupby(["Region", "Subsector"])
            .sum(0)
            .loc[x.name[1], x.name[3]]
        ),
        axis=1,
    ).fillna(0)
    """
    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(heat_supply)

    # endregion

    ###############################################
    # ESTIMATE UPDATED NONELECTRIC TRANSPORT MIX  #
    ###############################################

    # region

    renewables = ["HYDROGEN"]

    # For each region, for each subsector ('Light', 'Medium', 'Heavy', 'Two- and three-wheeled'), find the percent of total nonelectric energy consumption met by each product.

    transport_supply = energy_post_electrification.loc[
        [scenario],
        slice(None),
        ["Transportation"],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["Final consumption"],
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        ["N"],
        :,
    ]

    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(
            transport_supply.groupby(["Region", "Subsector"])
            .sum(0)
            .loc[x.name[1], x.name[3]]
        ),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total nonelectric transport consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_transport_supply.update(
        per_transport_supply[
            per_transport_supply.index.get_level_values(6).isin(renewables)
        ]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[1], x.name[6], scenario, x.name[2]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Set renewables nonelectric transport generation to meet the amount estimated
    transport_supply.update(
        per_transport_supply[
            per_transport_supply.index.get_level_values(6).isin(renewables)
        ].parallel_apply(
            lambda x: x.multiply(
                transport_supply[
                    transport_supply.index.get_level_values(6).isin(renewables)
                ]
                .groupby(["Region", "Subsector"])
                .sum(0)
                .loc[x.name[1], x.name[3]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(
            transport_supply.groupby(["Region", "Subsector"])
            .sum(0)
            .loc[x.name[1], x.name[3]]
        ),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(transport_supply)

    # endregion

    ##############################
    #  SAVE OUTPUT TO CSV FILES  #
    ##############################

    # region

    # Energy after removing upstream fossil fuel demand
    energy_post_upstream.to_csv("podi/data/energy_post_upstream.csv")

    # Energy after additional efficiency measure are applied
    energy_post_addtl_eff.to_csv("podi/data/energy_post_addtl_eff.csv")

    # Energy from fossil fuels that gets replaced by (a reduced amount of) electrical energy
    energy_electrified.to_csv("podi/data/energy_electrified.csv")

    # The reduced amount of electrical energy that represents an equivalent amount of work to combustion based energy
    energy_reduced_electrified.to_csv("podi/data/energy_reduced_electrified.csv")

    # Energy supply mix that meets energy_reduced_electrified
    energy_post_electrification.to_csv("podi/data/energy_" + scenario + ".csv")

    # Energy percent of total by region, electricity/heat/nonelectric transport, and subsector
    pd.concat([per_elec_supply, per_heat_supply, per_transport_supply]).to_csv(
        "podi/data/energy_percent.csv"
    )

    # endregion

    return
