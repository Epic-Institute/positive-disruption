#!/usr/bin/env python

# region

from multiprocessing.sharedctypes import Value
from re import sub
from unicodedata import category
import pandas as pd
import numpy as np
from numpy import NaN, product
from podi.adoption_curve_demand import adoption_curve_demand
from podi.curve_smooth import curve_smooth

# endregion


def energy_demand(scenario, data_start_year, data_end_year, proj_end_year):

    ###################################
    #  LOAD HISTORICAL ENERGY DEMAND  #
    ###################################

    # region

    recalc_energy_demand_historical = False
    if recalc_energy_demand_historical is True:
        regions = pd.read_csv("podi/data/IEA/Regions.txt").squeeze("columns")
        energy_demand_historical2 = pd.DataFrame([])
        for region in regions:
            energy_demand_historical = pd.DataFrame(
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
            energy_demand_historical = energy_demand_historical[
                (energy_demand_historical["Year"] >= data_start_year)
                & (energy_demand_historical["Year"] < data_end_year)
            ]

            # Change values to float
            energy_demand_historical["Value"] = energy_demand_historical[
                "Value"
            ].astype(float)

            # Drop unit column since all values are in TJ
            energy_demand_historical.drop("Unit", axis=1, inplace=True)

            # Change from all caps to lowercase
            energy_demand_historical["Region"] = energy_demand_historical[
                "Region"
            ].str.lower()

            # Format as a dataframe with timeseries as rows
            energy_demand_historical = pd.pivot_table(
                energy_demand_historical,
                values="Value",
                index=["Region", "Product", "Flow"],
                columns="Year",
            ).replace(NaN, 0)

            # Remove duplicate regions created due to name overlaps
            energy_demand_historical = energy_demand_historical.loc[[region.lower()], :]

            # Build dataframe consisting of all regions
            energy_demand_historical2 = pd.concat(
                [energy_demand_historical2, energy_demand_historical]
            )
        energy_demand_historical = energy_demand_historical2

        energy_demand_historical.to_csv("podi/data/energy_demand_historical.csv")
    else:
        energy_demand_historical = pd.DataFrame(
            pd.read_csv("podi/data/energy_demand_historical.csv")
        ).set_index(["Region", "Product", "Flow"])

    energy_demand_historical.columns = energy_demand_historical.columns.astype(int)

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
                "Final consumption",
                "Supply",
                "Transformation processes",
            ]
        ]
    )["Short name"]

    # Filter out flows that are summations of other products or for energy balance purposes (exports, imports, statistical differences, stock changes, transfers)
    flows = flows[
        ~flows.isin(
            [
                "EXPORTS",
                "HEATOUT",
                "IMPORTS",
                "INDPROD",
                "LIQUEFAC",
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

    energy_demand_historical = energy_demand_historical.loc[
        slice(None), products, flows
    ]

    # endregion

    ###############################
    #  ADD LABELS & RECATEGORIZE  #
    ###############################

    # region

    # Add product and flow labels to energy_demand_historical
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

    energy_demand_historical = (
        (
            energy_demand_historical.reset_index()
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

    # For Transportation flows ROAD/DOMESAIR/RAIL that were duplicated to make Two- and three-wheeled/Light-Duty/Medium-Duty/Heavy-Duty flows, scale their energy demand so the sum of subflows is equal to the original energy demand estimate

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
            ["Two- and three-wheeled", "Light", "Medium", "Heavy"],
        ]
    )

    energy_demand_historical.loc[
        slice(None),
        "Transportation",
        slice(None),
        slice(None),
        ["ROAD", "DOMESAIR", "RAIL"],
    ] = energy_demand_historical.loc[
        slice(None),
        ["Transportation"],
        slice(None),
        slice(None),
        ["ROAD", "DOMESAIR", "RAIL"],
    ].apply(
        lambda x: x
        * (
            subsector_props.loc[
                x.name[0], x.name[4], scenario, "Transportation", x.name[2]
            ].values
        ),
        axis=1,
    )

    # endregion

    # For products HEAT/HEATNS that were duplicated to make Low Temperature/High Temperature products, scale their energy demand so the sum of the subproducts is equal to the original energy demand estimate

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

    energy_demand_historical.loc[
        slice(None), slice(None), slice(None), ["HEAT", "HEATNS"]
    ] = energy_demand_historical.loc[
        slice(None),
        slice(None),
        slice(None),
        ["HEAT", "HEATNS"],
    ].apply(
        lambda x: x
        * (
            subsector_props.loc[
                "world", x.name[3], scenario, x.name[4], x.name[2]
            ].values
        ),
        axis=1,
    )

    # endregion

    # For Product NONCRUDE that was duplicated to make Hydrogen/Non-Hydrogen products and flows, scale their energy demand so the sum of the subflows is equal to the original energy demand estimate.

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

    energy_demand_historical.loc[
        slice(None), slice(None), ["Hydrogen", "Non-Hydrogen"], ["NONCRUDE"]
    ] = energy_demand_historical.loc[
        slice(None), slice(None), ["Hydrogen", "Non-Hydrogen"], ["NONCRUDE"]
    ].apply(
        lambda x: x
        * (
            subsector_props.loc[
                "world", x.name[3], scenario, x.name[4], x.name[2]
            ].values
        ),
        axis=1,
    )

    # Recast Product from NONCRUDE to HYDROGEN
    energy_demand_historical.reset_index(inplace=True)
    energy_demand_historical[
        (energy_demand_historical["Subsector"] == "Hydrogen")
        & (energy_demand_historical["Product"] == "NONCRUDE")
    ] = energy_demand_historical[
        (energy_demand_historical["Subsector"] == "Hydrogen")
        & (energy_demand_historical["Product"] == "NONCRUDE")
    ].replace(
        {"NONCRUDE": "HYDROGEN"}
    )

    energy_demand_historical.set_index(
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

    # Add EIA region labels to energy_demand_historical in order to match EIA regional projected growth of each product
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

    energy_demand_historical = (
        (
            energy_demand_historical.reset_index()
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

    energy_demand_historical["Product_category"] = energy_demand_historical.apply(
        lambda x: longnames[longnames["Short name"] == x["Product"]][
            "Product Category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_demand_historical["Product_long"] = energy_demand_historical.apply(
        lambda x: longnames[longnames["Short name"] == x["Product"]]["Product"].squeeze(
            "rows"
        ),
        axis=1,
    )

    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_Flow_Definitions.csv",
        usecols=["Flow Category", "Flow", "Short name"],
    )

    energy_demand_historical["Flow_category"] = energy_demand_historical.apply(
        lambda x: longnames[longnames["Short name"] == x["Flow"]][
            "Flow Category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_demand_historical["Flow_long"] = energy_demand_historical.apply(
        lambda x: longnames[longnames["Short name"] == x["Flow"]]["Flow"].squeeze(
            "rows"
        ),
        axis=1,
    )

    # Add scenario
    energy_demand_historical["Scenario"] = scenario

    energy_demand_historical = energy_demand_historical.reset_index().set_index(
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

    # endregion

    ####################################
    #  PROJECT BASELINE ENERGY DEMAND  #
    ####################################

    # region

    # Load EIA energy demand projections
    energy_demand_projection = (
        pd.read_excel(
            pd.ExcelFile("podi/data/EIA/EIA_IEO.xlsx", engine="openpyxl"), header=0
        )
        .dropna(axis="index", how="all")
        .dropna(axis="columns", thresh=2)
    )

    # Strip preceding space in EIA Sector values
    energy_demand_projection["EIA Product"] = energy_demand_projection[
        "EIA Product"
    ].str.strip()

    # create dataframe of energy demand projections as annual % change
    energy_demand_projection = (
        pd.DataFrame(energy_demand_projection).set_index(
            ["EIA Region", "Sector", "EIA Product"]
        )
    ).pct_change(axis=1).replace(NaN, 0) + 1
    energy_demand_projection.iloc[:, 0] = energy_demand_projection.iloc[:, 1]

    # Merge historical and projected energy demand
    energy_demand_baseline = (
        (
            energy_demand_historical.reset_index()
            .set_index(["EIA Region", "Sector", "EIA Product"])
            .merge(energy_demand_projection, on=["EIA Region", "Sector", "EIA Product"])
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
    energy_demand_baseline = energy_demand_baseline.loc[:, : data_end_year - 2].join(
        energy_demand_baseline.loc[:, data_end_year - 1 :].cumprod(axis=1).fillna(0)
    )

    # Curve smooth projections
    energy_demand_baseline = energy_demand_baseline.loc[:, : data_end_year - 1].join(
        curve_smooth(energy_demand_baseline.loc[:, data_end_year:], "linear", 2)
    )

    # endregion

    #####################################################
    #  ESTIMATE ENERGY DEMAND REDUCTIONS & FUEL SHIFTS  #
    #####################################################

    # region

    # Calculate 'electrification factors' that scale down energy demand over time due to the lower energy demand required to produce an equivalent amount of work via electricity
    recalc_ef_ratios = False
    if recalc_ef_ratios is True:

        # Load saturation points for energy demand reduction ratios
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
                slice(None),
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
                    "oil ef ratio",
                    "oil addtl eff",
                    "wws heat ef ratio",
                    "wws heat addtl eff",
                ],
                scenario,
                slice(None),
                "floor",
            ]
        )

        # Run adoption_curve_demand.py to calculate logistics curves for energy demand reduction ratios
        ef_ratio = ef_ratio.apply(
            lambda x: adoption_curve_demand(
                x,
                x.name[0],
                scenario,
                x.name[3],
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )

        # Build df of energy demand reduction ratio timeseries
        ef_ratios = ef_ratio[0]
        for i in range(1, len(ef_ratio)):
            ef_ratios = pd.concat([ef_ratios, ef_ratio[i]])
        ef_ratios.set_index(["Region", "Sector", "Product", "Scenario"], inplace=True)

        # Prepare df for multiplication with energy_demand
        ef_ratios = ef_ratios.apply(
            lambda x: 1 - (1 - x.max()) * (x - x.min()) / x.max(), axis=1
        )

        ef_ratios = (
            pd.DataFrame(
                1,
                index=ef_ratios.index,
                columns=np.arange(data_start_year, data_end_year, 1),
            )
        ).join(ef_ratios)
        ef_ratios = ef_ratios.loc[:, : energy_demand_baseline.columns[-1]]

        ef_ratios.to_csv("podi/data/ef_ratios.csv")
    else:
        ef_ratios = pd.DataFrame(pd.read_csv("podi/data/ef_ratios.csv")).set_index(
            ["Region", "Sector", "Product", "Scenario"]
        )

    ef_ratios.columns = ef_ratios.columns.astype(int)

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
    )

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

    # Calculate 'upstream ratios' that scale down energy demand over time due to the lower energy demand required for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    upstream_ratios = ef_ratios.copy()

    upstream_ratios.loc[
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        "Y",
        slice(None),
    ] = (
        (
            upstream_ratios.loc[
                slice(None),
                slice(None),
                slice(None),
                slice(None),
                slice(None),
                "Y",
                slice(None),
            ].apply(lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1)
        )
        .fillna(0)
        .values
    )

    # Set upstream ratios in ef_ratios to 1 so upstream reduction is not double counted
    ef_ratios.loc[
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        "Y",
        slice(None),
    ] = 1

    upstream_ratios.loc[
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        "N",
        slice(None),
    ] = 1

    # Reduce energy demand by the upstream energy demand reductions from fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    energy_demand_post_upstream = energy_demand_baseline.apply(
        lambda x: x.mul(
            upstream_ratios.loc[
                x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]
            ].squeeze()
        ),
        axis=1,
    )

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

    energy_demand_post_addtl_eff = energy_demand_post_upstream.apply(
        lambda x: x.mul(
            addtl_eff.loc[x.name[1], x.name[2], x.name[6], x.name[9]].squeeze()
        ),
        axis=1,
    )

    # Isolate energy demand that gets replaced with (a reduced amount of) energy from electricity. Each row of energy demand is multiplied by ((ef[0] - ef[i]) / (ef[0] - ef[-1]), which represents the percent of energy demand that undergoes electrification. This does not count preexisting electricity demand.
    energy_demand_electrified = energy_demand_post_addtl_eff.apply(
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

    # Subtract energy demand that gets electrified from baseline energy demand after removal of upstream fossil energy demand and reduction attributed to additional energy efficiency measures
    energy_demand_subtract_electrified = energy_demand_post_addtl_eff.subtract(
        energy_demand_electrified
    )

    # Find the reduced amount of electrical energy that represents an equivalent amount of work to that of the energy demand that undergoes electrification
    energy_demand_reduced_electrified = energy_demand_electrified.apply(
        lambda x: x.mul(
            ef_ratios.loc[x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]]
            .squeeze()
            .iloc[-1]
        ),
        axis=1,
    )

    # Relabel reduced amount of energy as ELECTR or HYDROGEN
    energy_demand_reduced_electrified2 = (
        energy_demand_reduced_electrified.groupby(
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

    energy_demand_reduced_electrified_e = energy_demand_reduced_electrified2[
        energy_demand_reduced_electrified2["Hydrogen"] == "N"
    ]
    energy_demand_reduced_electrified_e["Product_category"] = "Electricity and Heat"
    energy_demand_reduced_electrified_e["Product_long"] = "Electricity"
    energy_demand_reduced_electrified_e["Product"] = "ELECTR"

    energy_demand_reduced_electrified_h = energy_demand_reduced_electrified2[
        energy_demand_reduced_electrified2["Hydrogen"] == "Y"
    ]
    energy_demand_reduced_electrified_h["Subsector"] = "Hydrogen"
    energy_demand_reduced_electrified_h["Product_category"] = "Hydrogen"
    energy_demand_reduced_electrified_h["Product_long"] = "Hydrogen"
    energy_demand_reduced_electrified_h["Product"] = "HYDROGEN"

    energy_demand_reduced_electrified2 = pd.concat(
        [energy_demand_reduced_electrified_e, energy_demand_reduced_electrified_h]
    )

    energy_demand_reduced_electrified2.set_index(
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

    # Relabel

    # Add this reduced level of electrical energy demand to overall energy demand
    energy_demand_post_electrification = (
        pd.concat(
            [energy_demand_subtract_electrified, energy_demand_reduced_electrified2]
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

    ##############################
    #  SAVE OUTPUT TO CSV FILES  #
    ##############################

    # region

    energy_demand_baseline.to_csv("podi/data/energy_demand_baseline.csv")
    energy_demand_post_upstream.to_csv("podi/data/energy_demand_post_upstream.csv")
    energy_demand_post_addtl_eff.to_csv("podi/data/energy_demand_post_addtl_eff.csv")
    energy_demand_electrified.to_csv("podi/data/energy_demand_electrified.csv")
    energy_demand_subtract_electrified.to_csv(
        "podi/data/energy_demand_subtract_electrified.csv"
    )
    energy_demand_reduced_electrified.to_csv(
        "podi/data/energy_demand_reduced_electrified.csv"
    )
    energy_demand_post_electrification.to_csv(
        "podi/data/energy_demand_" + scenario + ".csv"
    )
    # endregion

    return (energy_demand_baseline, energy_demand_post_electrification)
