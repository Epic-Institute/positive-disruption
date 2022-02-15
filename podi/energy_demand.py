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
        regions = pd.read_csv("podi/data/IEA/Regions.txt").squeeze()
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

            # Convert to MWh
            energy_demand_historical["Value"] = (
                energy_demand_historical["Value"].astype(float) * 0.27778
            )
            energy_demand_historical.drop("Unit", axis=1, inplace=True)

            # Change from all caps to lowercase
            energy_demand_historical["Region"] = energy_demand_historical[
                "Region"
            ].str.lower()

            # Format timeseries
            energy_demand_historical = pd.pivot_table(
                energy_demand_historical,
                values="Value",
                index=["Region", "Product", "Flow"],
                columns="Year",
            ).replace(NaN, 0)

            # Remove regions with name overlap
            energy_demand_historical = energy_demand_historical.loc[[region.lower()], :]

            # Build df of all regions
            energy_demand_historical2 = pd.concat(
                [energy_demand_historical2, energy_demand_historical]
            )
        energy_demand_historical = energy_demand_historical2
        energy_demand_historical.to_csv("podi/data/output_energy_demand.csv")
    else:
        energy_demand_historical = pd.DataFrame(
            pd.read_csv("podi/data/output_energy_demand.csv")
        ).set_index(["Region", "Product", "Flow"])

    energy_demand_historical.columns = energy_demand_historical.columns.astype(int)

    # Filter categories that are redundant or unused
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
                "Electricity output (GWh)",
                "Energy industry own use and Losses",
                "Final consumption",
                "Heat output",
                "Supply",
                "Transformation processes",
            ]
        ]
    )["Short name"]

    flows = flows[
        ~flows.isin(
            [
                "EXPORTS",
                "IMPORTS",
                "INDPROD",
                "STATDIFF",
                "STOCKCHA",
                "TES",
                "TRANSFER",
                "TOTIND",
                "TOTTRANF",
                "TOTTRANS",
                "OWNUSE",
            ]
        )
    ]

    energy_demand_historical = (
        energy_demand_historical.loc[slice(None), products, flows]
        .drop_duplicates()
        .abs()
    )

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

    # For Transportation sectors AVBUNK/DOMESAIR/DOMESNAV/MARBUNK/RAIL/ROAD/WORLDAV/WORLDMAR that were copied to make Light/Medium/Heavy Subsectors, scale their energy demand so the sum of Light/Medium/Heavy is equal to the original energy demand estimate

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
            ["Light", "Medium", "Heavy"],
        ]
    )

    energy_demand_historical.loc[
        slice(None),
        "Transportation",
        slice(None),
        slice(None),
        [
            "AVBUNK",
            "DOMESAIR",
            "DOMESNAV",
            "MARBUNK",
            "RAIL",
            "ROAD",
            "WORLDAV",
            "WORLDMAR",
        ],
    ] = energy_demand_historical.loc[
        slice(None),
        ["Transportation"],
        slice(None),
        slice(None),
        [
            "AVBUNK",
            "DOMESAIR",
            "DOMESNAV",
            "MARBUNK",
            "RAIL",
            "ROAD",
            "WORLDAV",
            "WORLDMAR",
        ],
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

    # For HEAT/HEATNS that were copied to make Low Temperature/High Temperature Subsectors, scale their energy demand so the sum of Low Temperature/High Temperature is equal to the original energy demand estimate

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

    # Add EIA region labels
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

    # Add category and long names for Products and Flows

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

    # Load energy demand projections
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

    # create df and convert to % change
    energy_demand_projection = (
        pd.DataFrame(energy_demand_projection).set_index(
            ["EIA Region", "Sector", "EIA Product"]
        )
    ).pct_change(axis=1).replace(NaN, 0) + 1
    energy_demand_projection.iloc[:, 0] = energy_demand_projection.iloc[:, 1]

    # Merge historical and projected energy demand
    energy_demand = (
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

    # Calculate projections as MWh by cumulative product
    energy_demand = energy_demand.loc[:, : data_end_year - 2].join(
        energy_demand.loc[:, data_end_year - 1 :].cumprod(axis=1).fillna(0)
    )

    # Curve smooth projections
    energy_demand = energy_demand.loc[:, : data_end_year - 1].join(
        curve_smooth(energy_demand.loc[:, data_end_year:], "linear", 2)
    )

    # endregion

    ########################################################
    #  ESTIMATE END-USE ENERGY DEMAND REDUCTIONS & SHIFTS  #
    ########################################################

    # region

    # Apply percentage reduction attributed to the higher [work output]:[energy input] ratio of electricity over combustion for EVs & H2 fuel cell vehicles, combustion for high-temperature industrial processes, and heat pumps for low-temperature heat

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
                    "renewables ef ratio",
                    "renewables addtl eff",
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
        ef_ratios = ef_ratios.loc[:, : energy_demand.columns[-1]]

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

    # Filter energy_demand to match ef_ratios index
    energy_demand = energy_demand.loc[
        slice(None),
        ef_ratios.index.get_level_values(0).unique().values,
        ef_ratios.index.get_level_values(1).unique().values,
        ef_ratios.index.get_level_values(2).unique().values,
        slice(None),
        slice(None),
        ef_ratios.index.get_level_values(3).unique().values,
        slice(None),
        slice(None),
        ef_ratios.index.get_level_values(4).unique().values,
    ]

    # Apply percentage reduction attributed to eliminating energy used for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    ef_ratios.loc[
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        "Y",
        slice(None),
    ] = (
        ef_ratios.loc[
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            "Y",
            slice(None),
        ]
        .apply(lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1)
        .values
    )

    ef_ratios = ef_ratios.droplevel("WWS Upstream Product")

    # Multiply ef_ratios by energy_demand
    energy_demand_post_ef_upstream = energy_demand.apply(
        lambda x: x.mul(
            ef_ratios.loc[
                x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]
            ].squeeze()
        ),
        axis=1,
    )

    # Apply percentage reduction attributed to additional energy efficiency measures
    addtl_eff = pd.DataFrame(pd.read_csv("podi/data/ef_ratios.csv")).set_index(
        ["Region", "Sector", "Product", "Scenario"]
    )
    addtl_eff.columns = addtl_eff.columns.astype(int)

    labels = (
        labels.reset_index()
        .drop(columns=["WWS Upstream Product", "Product"])
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
                    "Subsector",
                    "IEA Product",
                    "Flow",
                ],
                append=True,
            )
        )
        .droplevel(["Product", "Scenario"])
        .reorder_levels(["Region", "Sector", "Subsector", "IEA Product", "Flow"])
    )

    energy_demand_post_addtl_eff = energy_demand_post_ef_upstream.apply(
        lambda x: x.mul(
            addtl_eff.loc[x.name[1], x.name[2], x.name[3], x.name[6], x.name[9]]
        ),
        axis=1,
    )

    energy_demand_post_addtl_eff = energy_demand_post_addtl_eff.replace(NaN, 0)

    # endregion

    return (
        energy_demand,
        energy_demand_post_ef_upstream,
        energy_demand_post_addtl_eff,
        ef_ratios,
        addtl_eff,
    )
