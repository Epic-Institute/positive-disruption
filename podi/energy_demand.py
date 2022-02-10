#!/usr/bin/env python

# region

from multiprocessing.sharedctypes import Value
from unicodedata import category
import pandas as pd
import numpy as np
from numpy import NaN
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
    fc_cat = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/IEA/Other/IEA_WEB_definitions.csv",
                usecols=["Category", "Flow", "Short name"],
            )
        )
        .set_index("Category")
        .loc[
            [
                "Biofuels and Waste",
                "Coal",
                "Crude, NGL, refinery feedstocks",
                "Electricity and Heat",
                "Electricity output (GWh)",
                "Energy industry own use and Losses",
                "Final consumption",
                "Heat output",
                "Natural gas",
                "Oil products",
                "Oil shale",
                "Peat and peat products",
                "Supply",
                "Transformation processes",
            ]
        ]
    )["Short name"]

    fc_products = fc_cat[
        ~fc_cat.isin(
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

    fc_flows = fc_cat[
        ~fc_cat.isin(
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

    energy_demand_historical = energy_demand_historical.loc[
        slice(None), fc_products, fc_flows
    ].drop_duplicates()

    # endregion

    ###################################
    # PROJECT BASELINE ENERGY DEMAND  #
    ###################################

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

    # Add product and flow keys to energy_demand_historical
    metric_cat = pd.DataFrame(
        pd.read_csv(
            "podi/data/metric_categories.csv",
            usecols=["Product", "Flow", "Sector", "EIA Product"],
        )
    ).set_index(["Product", "Flow"])

    energy_demand_historical2 = (
        energy_demand_historical.reset_index()
        .set_index(["Product", "Flow"])
        .merge(metric_cat, on=["Product", "Flow"])
        .set_index(["Region", "Sector", "EIA Product"], append=True)
    )

    # Add region keys to energy_demand_historical
    region_cat = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "EIA Region"],
            ).dropna(axis=0)
        )
        .set_index(["WEB Region"])
        .rename_axis(index={"WEB Region": "Region"})
    )
    region_cat.index = region_cat.index.str.lower()

    energy_demand_historical2 = (
        (
            energy_demand_historical2.reset_index()
            .set_index(["Region"])
            .merge(region_cat, on=["Region"])
        )
        .reset_index()
        .set_index(["EIA Region"])
    )

    # Merge historical and projected energy demand
    energy_demand = (
        (
            energy_demand_historical2.reset_index()
            .set_index(["EIA Region", "Sector", "EIA Product"])
            .merge(energy_demand_projection, on=["EIA Region", "Sector", "EIA Product"])
        )
        .reset_index()
        .set_index(["Region", "Sector", "Product", "Flow", "EIA Region", "EIA Product"])
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

    # Add keys to ef_ratios
    metric_cat = (
        (
            pd.DataFrame(
                pd.read_csv(
                    "podi/data/metric_categories.csv",
                    usecols=[
                        "Product",
                        "Flow",
                        "Sector",
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
            .merge(metric_cat, on=["Sector", "Product"])
            .set_index(
                [
                    "Region",
                    "Scenario",
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
                "IEA Product",
                "Flow",
                "WWS Upstream Product",
                "WWS Addtl Efficiency",
            ]
        )
    )

    # Filter energy_demand to match ef_ratios index
    energy_demand = energy_demand.loc[
        ef_ratios.index.get_level_values(0).unique().values,
        ef_ratios.index.get_level_values(1).unique().values,
        ef_ratios.index.get_level_values(2).unique().values,
        ef_ratios.index.get_level_values(3).unique().values,
    ]

    # Apply percentage reduction attributed to eliminating energy used for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    ef_ratios.loc[
        slice(None), slice(None), slice(None), slice(None), "Y", slice(None)
    ] = (
        ef_ratios.loc[
            slice(None), slice(None), slice(None), slice(None), "Y", slice(None)
        ]
        .apply(lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1)
        .values
    )

    """
    # ef ratios with no projected reduction adopt projection for 'ONONSPEC'
    ef_ratios.loc[ef_ratios.iloc[:, 1].isna()] = (
        ef_ratios.loc[ef_ratios.iloc[:, 1].isna()]
    ).apply(
        lambda x: x + ef_ratios.loc[
            "world", "Transportation", "ONONSPEC", "PIPELINE", slice(None)
        ].values,
        axis=1,
    )
    """

    ef_ratios = ef_ratios.droplevel("WWS Upstream Product")

    # Multiply ef_ratios by energy_demand
    energy_demand_post_ef_upstream = energy_demand.apply(
        lambda x: x.mul(
            ef_ratios.loc[
                x.name[0], x.name[1], x.name[2], x.name[3], slice(None)
            ].squeeze()
        ),
        axis=1,
    )

    # Apply percentage reduction attributed to additional energy efficiency measures
    addtl_eff = pd.DataFrame(pd.read_csv("podi/data/ef_ratios.csv")).set_index(
        ["Region", "Sector", "Product", "Scenario"]
    )
    addtl_eff.columns = addtl_eff.columns.astype(int)

    metric_cat = (
        metric_cat.reset_index()
        .drop(columns=["WWS Upstream Product", "Product"])
        .set_index(["Sector", "WWS Addtl Efficiency"])
        .rename_axis(index={"WWS Addtl Efficiency": "Product"})
        .rename(columns={"Product": "IEA Product"})
    )

    addtl_eff = (
        (
            addtl_eff.reset_index()
            .set_index(["Sector", "Product"])
            .merge(metric_cat, on=["Sector", "Product"])
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

    energy_demand_post_addtl_eff = energy_demand_post_ef_upstream.apply(
        lambda x: x.mul(addtl_eff.loc[x.name[0], x.name[1], x.name[2], x.name[3]]),
        axis=1,
    )

    energy_demand_post_addtl_eff = energy_demand_post_addtl_eff.replace(NaN, 0)

    # endregion

    #################################
    # ADD LABELS FOR END-USE TYPE   #
    #################################

    # region

    # Add scenario
    energy_demand_post_addtl_eff["Scenario"] = scenario

    # Add category and long names for Products and Flows
    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_WEB_definitions.csv",
        usecols=["Category", "Flow", "Short name"],
    )

    energy_demand_post_addtl_eff[
        "Product_category"
    ] = energy_demand_post_addtl_eff.apply(
        lambda x: longnames[longnames["Short name"] == x.name[2]]["Category"].squeeze(),
        axis=1,
    )

    energy_demand_post_addtl_eff["Flow_category"] = energy_demand_post_addtl_eff.apply(
        lambda x: longnames[longnames["Short name"] == x.name[3]]["Category"].squeeze(),
        axis=1,
    )

    energy_demand_post_addtl_eff["Product_long"] = energy_demand_post_addtl_eff.apply(
        lambda x: longnames[longnames["Short name"] == x.name[2]]["Flow"].squeeze(),
        axis=1,
    )

    energy_demand_post_addtl_eff["Flow_long"] = energy_demand_post_addtl_eff.apply(
        lambda x: longnames[longnames["Short name"] == x.name[3]]["Flow"].squeeze(),
        axis=1,
    )

    energy_demand_post_addtl_eff = energy_demand_post_addtl_eff.set_index(
        ["Product_long", "Flow_long", "Product_category", "Flow_category", "Scenario"],
        append=True,
    ).reorder_levels(
        [
            "Scenario",
            "Region",
            "Sector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
        ]
    )

    """
    # Electricity/heat for low/high temp heating
    energy_demand_post_addtl_eff["lt_heat"] = []

    energy_demand_post_addtl_eff["ht_heat"] = []

    # h2
    energy_demand_post_addtl_eff["h2"] = []

    # flexible/inflexible
    energy_demand_post_addtl_eff["flexible"] = []
    """
    # endregion

    ##########################################
    #  FILTER AND GROUP FOR AGGREGATE STATS  #
    ##########################################

    # region
    """
    category = pd.read_csv(
        "podi/data/IEA/Other/IEA_WEB_definitions.csv",
        usecols=["Category", "Short name"],
    )

    # Final consumption group
    final_consumption = category[category["Category"] == "Final consumption"][
        "Short name"
    ]

    energy_demand_finalconsumption = energy_demand_post_addtl_eff.loc[
        slice(None), slice(None), slice(None), final_consumption
    ]
    """
    #

    # endregion

    return (
        energy_demand,
        energy_demand_post_ef_upstream,
        energy_demand_post_addtl_eff,
        ef_ratios,
        addtl_eff,
    )
