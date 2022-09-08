# region

import os
import pandas as pd
import numpy as np
from numpy import NaN
from scipy.optimize import differential_evolution
import plotly.io as pio
import plotly.graph_objects as go

from pandarallel import pandarallel

pandarallel.initialize(progress_bar=True, nb_workers=6)

show_figs = False
save_figs = False

# endregion


def energy(model, scenario, data_start_year, data_end_year, proj_end_year):

    ############################
    #  LOAD HISTORICAL ENERGY  #
    ############################

    # region

    regions = pd.read_csv("podi/data/IEA/Regions.txt").squeeze("columns")
    energy_historical2 = pd.DataFrame([])
    data_end_year_df2 = pd.DataFrame([])
    for region in regions:
        # Handle "x", "c", ".." qualifiers. IEA documentation is not clear on what "x" represents; "c" represents "confidential", ".." represents "not available"
        energy_historical = (
            pd.DataFrame(
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
                    names=[
                        "region",
                        "product_short",
                        "year",
                        "flow_short",
                        "unit",
                        "value",
                    ],
                )
            )
            .replace(["c"], NaN)
            .replace([".."], NaN)
            .replace(["x"], NaN)
        )

        # Change values to float
        energy_historical["value"] = energy_historical["value"].astype(float)

        # Change from all caps to lowercase
        energy_historical["region"] = energy_historical["region"].str.lower()

        # Format as a dataframe with timeseries as rows
        energy_historical = pd.pivot_table(
            energy_historical,
            values="value",
            index=["region", "product_short", "flow_short", "unit"],
            columns="year",
        )

        # Not all regions have placeholders for all years, so they need to be created
        energy_historical = pd.DataFrame(
            index=energy_historical.index,
            columns=np.arange(data_start_year, data_end_year + 1, 1),
            data=NaN,
        ).combine_first(energy_historical)

        # Save a dataframe that records the last_valid_index for each timeseries, then extrapolate all timeseries to data_end_year
        data_end_year_df = energy_historical.parallel_apply(
            lambda x: x.last_valid_index(), axis=1
        ).to_frame()
        data_end_year_df2 = pd.concat([data_end_year_df2, data_end_year_df])

        # Backfill missing data using oldest data point
        energy_historical = energy_historical.fillna(method="backfill", axis=1)

        # For rows with data only prior to data_start_year, front fill to data_start_year
        energy_historical.update(
            energy_historical[energy_historical.loc[:, data_start_year].isna()]
            .loc[:, :data_start_year]
            .fillna(method="ffill", axis=1)
        )

        # Remove duplicate regions created due to name overlaps
        energy_historical = energy_historical.loc[[region.lower()], :]

        # Filter for data start_year and data_end_year, which can be different depending on region/product/flow because data becomes available at different times
        energy_historical = energy_historical.loc[:, data_start_year:data_end_year]

        # Build dataframe consisting of all regions
        energy_historical2 = pd.concat([energy_historical2, energy_historical])

    energy_historical = energy_historical2
    data_end_year_df = data_end_year_df2

    # Add model and scenario indices
    energy_historical = pd.concat(
        [pd.concat([energy_historical], keys=["baseline"], names=["scenario"])],
        keys=["PD22"],
        names=["model"],
    )

    # Filter product categories that are redundant or unused
    products = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/IEA/Other/IEA_Product_Definitions.csv",
                usecols=["product_category", "product_long", "product_short"],
            )
        )
        .set_index("product_category")
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
    )["product_short"]

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
                usecols=["flow_category", "flow_short", "flow_short"],
            )
        )
        .set_index("flow_category")
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
    )["flow_short"]

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
                "TOTENGY",
                "OWNUSE",
            ]
        )
    ]

    energy_historical = energy_historical.loc[
        slice(None), slice(None), slice(None), products, flows
    ]

    # Add IRENA data for select electricity technologies by downloading for all regions, all technologies, and all years from https://pxweb.irena.org/pxweb/en/IRENASTAT/IRENASTAT__Power%20Capacity%20and%20Generation/RE-ELECGEN_2022_cycle2.px/. Select the download option 'Comma delimited with heading' and save as a csv file in podi/data/IRENA/ . Change the header in column A from 'Region/country/area' to 'region'. Double check that the filename is 'RE-ELECGEN_20220805-204524.csv' and if not, update the filename below.

    # region
    irena = pd.read_csv("podi/data/IRENA/RE-ELECGEN_20220805-204524.csv", header=2)

    # Filter for technologies that are not overlapping, and rename 'Technology' index to 'product_short'
    irena = irena.loc[
        irena["Technology"].isin(["Onshore wind energy", "Offshore wind energy"])
    ].replace(
        {
            "Technology": {
                "Onshore wind energy": "ONSHORE",
                "Offshore wind energy": "OFFSHORE",
            }
        }
    )
    irena.rename(columns={"Technology": "product_short"}, inplace=True)

    # Add index flow_short
    irena["flow_short"] = "ELMAINE"

    # Replace ".." with NaN
    irena.replace("..", 0, inplace=True)

    # Add index labels for model, scenario, unit (in GWh but will be converted to TJ later in this section with the other 'Electricity Ouput' variables)
    irena["model"] = model
    irena["scenario"] = "baseline"
    irena["unit"] = "TJ"
    irena.set_index(
        ["model", "scenario", "region", "product_short", "flow_short", "unit"],
        inplace=True,
    )

    # Add WEB region names
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "IRENA Region"],
            ).dropna(axis=0)
        )
        .set_index(["IRENA Region"])
        .rename_axis(index={"IRENA Region": "region"})
    )

    irena = (
        irena.reset_index()
        .merge(regions, left_on=["region"], right_on=["region"])
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
                "region",
                "product_short",
                "flow_short",
                "unit",
            ]
        )
        .droplevel("region")
        .rename_axis(index={"WEB Region": "region"})
    )
    irena.index = irena.index.set_levels(irena.index.levels[2].str.lower(), level=2)

    # Set column type
    irena.columns = irena.columns.astype(int)

    # Add missing years between first_valid_index and data_start_year
    irena[np.arange(data_start_year, irena.columns.min(), 1)] = 0
    irena = irena.reindex(sorted(irena.columns), axis=1)

    # Filter for data_start_year and data_end_year
    irena = irena.loc[:, data_start_year:data_end_year]

    # IRENA data starts at 2000, so if data_start_year is <2000, use IEA data for WIND, assuming it is onshore. Then. Drop IEA WIND and SOLARPV to avoid duplication with IRENA ONSHORE/OFFSHORE
    energy_historical = pd.concat(
        [
            energy_historical.drop(labels="WIND", level=3),
            pd.concat(
                [
                    energy_historical[
                        energy_historical.index.get_level_values(3).isin(["WIND"])
                    ]
                    .loc[:, :2000]
                    .rename(index={"WIND": "ONSHORE"}),
                    irena[irena.index.get_level_values(3).isin(["ONSHORE"])].loc[
                        :, 2001:
                    ],
                ],
                axis=1,
            ),
            irena[irena.index.get_level_values(3).isin(["OFFSHORE"])],
        ]
    )

    # endregion

    # Add product and flow labels to energy_historical

    labels = pd.DataFrame(
        pd.read_csv(
            "podi/data/product_flow_labels.csv",
            usecols=[
                "product_short",
                "flow_short",
                "sector",
                "EIA Product",
                "hydrogen",
                "flexible",
                "nonenergy",
            ],
        )
    ).set_index(["product_short", "flow_short"])

    energy_historical = (
        (
            energy_historical.reset_index()
            .set_index(["product_short", "flow_short"])
            .merge(labels, on=["product_short", "flow_short"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "region",
                "sector",
                "product_short",
                "flow_short",
                "unit",
                "EIA Product",
                "hydrogen",
                "flexible",
                "nonenergy",
            ]
        )
    )

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

    # Create Two- and three-wheeled Flow (TTROAD) using estimate of the fraction of ROAD that is Two- and three-wheeled
    ttroad = (
        energy_historical[(energy_historical.reset_index().flow_short == "ROAD").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Two- and three-wheeled"
                ].values
            ),
            axis=1,
        )
        .rename(index={"ROAD": "TTROAD"})
    )

    # Create Light-duty Flow (LIGHTROAD) using estimate of the fraction of ROAD that is Light-duty vehicles
    lightroad = (
        energy_historical[(energy_historical.reset_index().flow_short == "ROAD").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Light"
                ].values
            ),
            axis=1,
        )
        .rename(index={"ROAD": "LIGHTROAD"})
    )

    # Create Medium-duty Flow (MEDIUMROAD) using estimate of the fraction of ROAD that is Medium-duty vehicles (Buses and Vans)
    mediumroad = (
        energy_historical[(energy_historical.reset_index().flow_short == "ROAD").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Medium"
                ].values
            ),
            axis=1,
        )
        .rename(index={"ROAD": "MEDIUMROAD"})
    )

    # Create Heavy-duty Flow (HEAVYROAD) using estimate of the fraction of ROAD that is Heavy-duty vehicles (Trucks)
    heavyroad = (
        energy_historical[(energy_historical.reset_index().flow_short == "ROAD").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "ROAD", "baseline", x.name[3], "Heavy"
                ].values
            ),
            axis=1,
        )
        .rename(index={"ROAD": "HEAVYROAD"})
    )

    # Drop ROAD Flow and add TTROAD, LIGHTROAD, MEDIUMROAD, HEAVYROAD
    energy_historical = pd.concat(
        [
            energy_historical.drop(labels=["ROAD"], level=5),
            ttroad,
            lightroad,
            mediumroad,
            heavyroad,
        ]
    )

    # endregion

    # Split DOMESAIR Flow into Short-range, Long-range

    # region

    # Create Short-range Flow (SDOMESAIR) using estimate of the fraction of DOMESAIR that is Short-range
    sdomesair = (
        energy_historical[
            (energy_historical.reset_index().flow_short == "DOMESAIR").values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "DOMESAIR", "baseline", x.name[3], "Light"
                ].values
            ),
            axis=1,
        )
        .rename(index={"DOMESAIR": "SDOMESAIR"})
    )

    # Create Long-range Flow (LDOMESAIR) using estimate of the fraction of DOMESAIR that is Long-range
    ldomesair = (
        energy_historical[
            (energy_historical.reset_index().flow_short == "DOMESAIR").values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "DOMESAIR", "baseline", x.name[3], "Heavy"
                ].values
            ),
            axis=1,
        )
        .rename(index={"DOMESAIR": "LDOMESAIR"})
    )

    # Drop DOMESAIR Flow and add SDOMESAIR and LDOMESAIR
    energy_historical = pd.concat(
        [energy_historical.drop(labels=["DOMESAIR"], level=5), sdomesair, ldomesair]
    )

    # endregion

    # Split RAIL Flow into Light-duty, Heavy-duty

    # region

    # Create Light-duty Flow (LIGHTRAIL) using estimate of the fraction of RAIL that is Light-duty
    lightrail = (
        energy_historical[(energy_historical.reset_index().flow_short == "RAIL").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "RAIL", "baseline", x.name[3], "Light"
                ].values
            ),
            axis=1,
        )
        .rename(index={"RAIL": "LIGHTRAIL"})
    )

    # Create Heavy-duty Flow (HEAVYRAIL) using estimate of the fraction of RAIL that is Heavy-duty
    heavyrail = (
        energy_historical[(energy_historical.reset_index().flow_short == "RAIL").values]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    x.name[2], "RAIL", "baseline", x.name[3], "Heavy"
                ].values
            ),
            axis=1,
        )
        .rename(index={"RAIL": "HEAVYRAIL"})
    )

    # Drop RAIL Flow and add LIGHTRAIL and HEAVYRAIL
    energy_historical = pd.concat(
        [energy_historical.drop(labels=["RAIL"], level=5), lightrail, heavyrail]
    )

    # endregion

    # Split HEAT & HEATNS Products into LHEAT/LHEATNS (low temperature) and HHEAT/HHEATNS (high temperature) heat

    # region

    # Create Low Temperature Heat Product (LHEAT) using estimate of the fraction of HEAT that is low temperature
    lheat = (
        energy_historical[
            (
                (energy_historical.reset_index().product_short == "HEAT")
                | (energy_historical.reset_index().product_short == "HEATNS")
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    "world", x.name[4], "baseline", x.name[5], "Low Temperature"
                ].values
            ),
            axis=1,
        )
        .rename(index={"HEAT": "LHEAT", "HEATNS": "LHEATNS"})
    )

    # Create High Temperature Heat Product (HHEAT) using estimate of the fraction of HEAT that is high temperature
    hheat = (
        energy_historical[
            (
                (energy_historical.reset_index().product_short == "HEAT")
                | (energy_historical.reset_index().product_short == "HEATNS")
            ).values
        ]
        .parallel_apply(
            lambda x: x
            * (
                1
                - subsector_props.loc[
                    "world", x.name[4], "baseline", x.name[5], "Low Temperature"
                ].values
            ),
            axis=1,
        )
        .rename(index={"HEAT": "HHEAT", "HEATNS": "HHEATNS"})
    )

    # Drop HEAT, HEATNS Products and add LHEAT, LHEATNS, HHEAT, HHEATNS
    energy_historical = pd.concat(
        [energy_historical.drop(labels=["HEAT", "HEATNS"], level=4), lheat, hheat]
    )

    # endregion

    # Split NONCRUDE Product into HYDROGEN and NONCRUDE

    # region

    # Create HYDROGEN Product (HYDROGEN) using estimate of the fraction of NONCRUDE that is Hydrogen
    hydrogen = (
        energy_historical[
            (energy_historical.reset_index().product_short == "NONCRUDE").values
        ]
        .parallel_apply(
            lambda x: x
            * (
                subsector_props.loc[
                    "world", x.name[4], "baseline", x.name[5], "Hydrogen"
                ].values
            ),
            axis=1,
        )
        .rename(index={"NONCRUDE": "HYDROGEN"})
    )

    # Update NONCRUDE Product to be reduced by the estimate of HYDROGEN
    noncrude = energy_historical[
        (energy_historical.reset_index().product_short == "NONCRUDE").values
    ].parallel_apply(
        lambda x: x
        * (
            1
            - subsector_props.loc[
                "world", x.name[4], "baseline", x.name[5], "Hydrogen"
            ].values
        ),
        axis=1,
    )

    # Drop old NONCRUDE Product and add HYDROGEN and new NONCRUDE
    energy_historical = pd.concat(
        [energy_historical.drop(labels=["NONCRUDE"], level=4), hydrogen, noncrude]
    )

    # endregion

    # Split SOLARPV Product into ROOFTOP and SOLARPV (utility) scale solar pv

    # region
    energy_historical.update(
        energy_historical[
            (energy_historical.reset_index().product_short == "SOLARPV").values
        ].parallel_apply(lambda x: x * 0.6, axis=1)
    )

    energy_historical = pd.concat(
        [
            energy_historical,
            (
                energy_historical[
                    (energy_historical.reset_index().product_short == "SOLARPV").values
                ].parallel_apply(lambda x: x * 0.4, axis=1)
            ).rename(
                index={
                    "SOLARPV": "ROOFTOP",
                    "Solar photovoltaics": "Rooftop solar photovoltaics",
                }
            ),
        ]
    )

    # endregion

    # Add EIA region labels to energy_historical in order to match EIA regional projected growth of each product

    # region

    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "EIA Region"],
            ).dropna(axis=0)
        )
        .set_index(["WEB Region"])
        .rename_axis(index={"WEB Region": "region"})
    )
    regions.index = regions.index.str.lower()

    energy_historical = (
        (
            energy_historical.reset_index()
            .set_index(["region"])
            .merge(regions, on=["region"])
        )
        .reset_index()
        .set_index(["EIA Region"])
    )

    # endregion

    # Add categories and long names for products and flows

    # region

    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_Product_Definitions.csv",
        usecols=["product_category", "product_long", "product_short"],
    )

    energy_historical["product_category"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["product_short"] == x["product_short"]][
            "product_category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_historical["product_long"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["product_short"] == x["product_short"]][
            "product_long"
        ].squeeze("rows"),
        axis=1,
    )

    longnames = pd.read_csv(
        "podi/data/IEA/Other/IEA_Flow_Definitions.csv",
        usecols=["flow_category", "flow_long", "flow_short"],
    )

    energy_historical["flow_category"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["flow_short"] == x["flow_short"]][
            "flow_category"
        ].squeeze("rows"),
        axis=1,
    )

    energy_historical["flow_long"] = energy_historical.parallel_apply(
        lambda x: longnames[longnames["flow_short"] == x["flow_short"]][
            "flow_long"
        ].squeeze("rows"),
        axis=1,
    )

    energy_historical = energy_historical.reset_index().set_index(
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
            "hydrogen",
            "flexible",
            "nonenergy",
            "EIA Region",
            "EIA Product",
        ]
    )

    # endregion

    # Convert Electricity output flow category from GWh to TJ
    energy_historical = energy_historical.astype(float)
    energy_historical.update(
        energy_historical[
            energy_historical.index.get_level_values(7) == "Electricity output"
        ].multiply(3.6)
    )

    # Diagnostic check for Energy Balance
    # region

    region = slice(None)
    start_year = data_start_year
    df = energy_historical

    # Filter for region and year
    energy_balance = (
        df.loc[slice(None), slice(None), region]
        .loc[:, [data_start_year]]
        .groupby(
            [
                "sector",
                "product_category",
                "product_long",
                "flow_category",
                "flow_long",
            ]
        )
        .sum()
    )

    # Create energy balance table structure
    energy_balance = (
        energy_balance.groupby(
            ["product_category", "product_long", "flow_category", "flow_long"]
        )
        .sum()
        .reset_index()
        .pivot(
            index=["flow_category", "flow_long"],
            columns=["product_category", "product_long"],
            values=start_year,
        )
        .fillna(0)
        .reindex(
            axis="index",
            level=0,
            labels=[
                "Supply",
                "Transformation processes",
                "Energy industry own use and Losses",
                "Final consumption",
            ],
        )
        .reindex(
            axis="columns",
            level=0,
            labels=[
                "Coal",
                "Crude, NGL, refinery feedstocks",
                "Oil products",
                "Natural gas",
                "Biofuels and Waste",
                "Electricity and Heat",
            ],
        )
        .astype(int)
    )

    # Create Product categories (columns)
    energy_balance = pd.concat(
        [
            energy_balance.groupby("product_category", axis="columns")
            .sum()[
                [
                    "Coal",
                    "Crude, NGL, refinery feedstocks",
                    "Oil products",
                    "Natural gas",
                    "Biofuels and Waste",
                ]
            ]
            .rename(columns={"Crude, NGL, refinery feedstocks": "Crude oil"}),
            energy_balance.loc[:, "Electricity and Heat"].loc[
                :,
                [
                    "Nuclear",
                    "Hydro",
                    "Electricity",
                    "Heat – High Temperature",
                    "Heat – Low Temperature",
                ],
            ],
            energy_balance.loc[:, "Electricity and Heat"]
            .drop(
                [
                    "Electricity",
                    "Heat – High Temperature",
                    "Heat – Low Temperature",
                    "Nuclear",
                    "Hydro",
                ],
                1,
            )
            .sum(axis=1)
            .to_frame()
            .rename(columns={0: "Wind, solar, etc."}),
        ],
        axis=1,
    ).reindex(
        axis="columns",
        labels=[
            "Coal",
            "Crude oil",
            "Oil products",
            "Natural gas",
            "Nuclear",
            "Hydro",
            "Wind, solar, etc.",
            "Biofuels and Waste",
            "Electricity",
            "Heat – High Temperature",
            "Heat – Low Temperature",
        ],
    )

    energy_balance = pd.concat(
        [
            energy_balance,
            pd.DataFrame(energy_balance.sum(axis=1)).rename(columns={0: "Total"}),
        ],
        axis=1,
    )

    # Create Flow categories (rows)
    bunkers = (
        energy_balance.loc["Supply", :]
        .loc[
            energy_balance.loc["Supply", :]
            .index.get_level_values(0)
            .isin(
                [
                    "International marine bunkers",
                    "International aviation bunkers",
                ]
            ),
            :,
        ]
        .iloc[::-1]
    )

    electricity_plants = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Autoproducer electricity plants",
                    "Main activity producer electricity plants",
                    "Chemical heat for electricity production",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Electricity plants"})
    )

    chp_plants = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(["Autoproducer CHP", "Main activity producer CHP plants"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "CHP plants"})
    )

    heat_plants = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Autoproducer heat plants",
                    "Main activity producer heat plants",
                    "Electric boilers",
                    "Heat pumps",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Heat plants"})
    )

    gas_works = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(["Gas works", "For blended natural gas"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Gas works"})
    )
    gas_works["Natural gas"] = gas_works["Natural gas"] * 0.5
    gas_works["Total"] = gas_works.loc[:, ["Coal", "Natural gas"]].sum(1)

    oil_refineries = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(["Oil refineries"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Oil refineries"})
    )

    coal_transformation = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Blast furnaces",
                    "Coke ovens",
                    "Patent fuel plants",
                    "BKB/peat briquette plants",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Coal transformation"})
    )

    liquifaction_plants = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(["Gas-to-liquids (GTL) plants", "Coal liquefaction plants"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Liquifaction plants"})
    )

    other_transformation = (
        energy_balance.loc["Transformation processes", :]
        .loc[
            energy_balance.loc["Transformation processes", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Non-specified (transformation)",
                    "Charcoal production plants",
                    "Petrochemical plants",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Other transformation"})
    )

    own_use = (
        energy_balance.loc["Energy industry own use and Losses", :]
        .loc[
            energy_balance.loc["Energy industry own use and Losses", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Energy industry own use",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Energy industry own use"})
    )

    losses = (
        energy_balance.loc["Energy industry own use and Losses", :]
        .loc[
            energy_balance.loc["Energy industry own use and Losses", :]
            .index.get_level_values(0)
            .isin(["Losses"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Losses"})
    )

    industry = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Chemical and petrochemical",
                    "Construction",
                    "Food and tobacco",
                    "Industry not elsewhere specified",
                    "Iron and steel",
                    "Machinery",
                    "Mining and quarrying",
                    "Non-ferrous metals",
                    "Non-metallic minerals",
                    "Paper, pulp, and print",
                    "Textile and leather",
                    "Transport equipment",
                    "Wood and wood products",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Industry"})
    )

    transport = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Domestic aviation",
                    "Domestic navigation",
                    "Pipeline transport",
                    "Rail",
                    "Road",
                    "Transport not elsewhere specified",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Transport"})
    )

    residential = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(["Residential"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Residential"})
    )

    commercial = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(["Commercial and public services"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Commercial and public services"})
    )

    agriculture = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(["Agriculture/forestry"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Agriculture / forestry"})
    )

    fishing = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(["Fishing"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Fishing"})
    )

    nonspecified = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(["Final consumption not elsewhere specified"]),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Non-specified"})
    )

    nonenergyuse = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
            .index.get_level_values(0)
            .isin(
                [
                    "Non-energy use in other",
                    "Non-energy use in transport",
                    "Non-energy use industry/transformation/energy",
                ]
            ),
            :,
        ]
        .sum()
        .to_frame()
        .T.rename(index={0: "Non-energy use"})
    )

    energy_balance = pd.concat(
        [
            bunkers,
            electricity_plants,
            chp_plants,
            heat_plants,
            gas_works,
            oil_refineries,
            coal_transformation,
            liquifaction_plants,
            other_transformation,
            own_use,
            losses,
            industry,
            transport,
            residential,
            commercial,
            agriculture,
            fishing,
            nonspecified,
            nonenergyuse,
        ]
    )

    energy_balance.astype(int)

    # endregion

    # Convert AVBUNK & MARBUNK to be positive (they were negative by convention representing an 'export' to an international region WORLDAV and WORLDMAR) and change their flow_category to Final consumption,
    energy_historical[
        energy_historical.index.get_level_values(9).isin(["AVBUNK", "MARBUNK"])
    ] = energy_historical[
        energy_historical.index.get_level_values(9).isin(["AVBUNK", "MARBUNK"])
    ].abs()

    energy_historical_index = energy_historical.index.names
    energy_historical.reset_index(inplace=True)
    energy_historical = energy_historical.replace("Supply", "Final consumption")
    energy_historical.set_index(energy_historical_index, inplace=True)

    # Some flows in flow_category 'Transformation processes' are negative, representing the ‘loss’ of a product as it transforms into another product. This is switched to be consistent with positive values representing the consumption of a product. Values that were already positive (representing production of a product) are dropped to avoid double counting with flow_category 'Final consumption'.
    energy_historical[
        (energy_historical.index.get_level_values(7).isin(["Transformation processes"]))
        & (energy_historical.sum(axis=1) > 0)
    ] = 0

    energy_historical[
        energy_historical.index.get_level_values(7).isin(["Transformation processes"])
    ] = energy_historical[
        energy_historical.index.get_level_values(7).isin(["Transformation processes"])
    ].abs()

    # All flows in flow_category 'Energy industry own use and Losses' are negative, representing the 'loss' of a product as the energy industry uses it to transform one product into another. This is switched to be consistent with positive values representing the consumption of a product.
    energy_historical[
        energy_historical.index.get_level_values(7).isin(
            ["Energy industry own use and Losses"]
        )
    ] = energy_historical[
        energy_historical.index.get_level_values(7).isin(
            ["Energy industry own use and Losses"]
        )
    ].abs()

    # Change non-energy use flows from flow_category value 'Final consumption' to 'Non-energy use'.
    energy_historical_nonenergy = energy_historical[
        (
            energy_historical.reset_index().flow_short.isin(
                [
                    "NECHEM",
                    "NECONSTRUC",
                    "NEFOODPRO",
                    "NEIND",
                    "NEINONSPEC",
                    "NEINTREN",
                    "NEIRONSTL",
                    "NEMACHINE",
                    "NEMINING",
                    "NENONFERR",
                    "NENONMET",
                    "NEOTHER",
                    "NEPAPERPRO",
                    "NETEXTILES",
                    "NETRANS",
                    "NETRANSEQ",
                    "NEWOODPRO",
                    "NONENUSE",
                ]
            )
        ).values
    ]
    energy_historical = energy_historical.drop(energy_historical_nonenergy.index)

    energy_historical_nonenergy.reset_index(inplace=True)
    energy_historical_nonenergy.flow_category = "Non-energy use"
    energy_historical_nonenergy.set_index(energy_historical.index.names, inplace=True)
    energy_historical = (
        pd.concat([energy_historical, energy_historical_nonenergy])
        .loc[:, data_start_year:data_end_year]
        .sort_index()
    )

    # Plot energy_historical
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # ELECTRICITY CONSUMPTION BY SECTOR #
        #####################################

        # region

        start_year = data_start_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit_val[0]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ####################################
        # ELECTRICITY GENERATION BY SOURCE #
        ####################################

        # region

        # Breakdown 'Electricity and Heat' product_category

        # region

        energy_historical_plot = energy_historical[
            (
                energy_historical.reset_index().product_category
                == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_historical_plot["product_category"] = energy_historical_plot[
            "product_long"
        ]

        energy_historical_plot.set_index(energy_historical.index.names, inplace=True)

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_historical[
                    ~(
                        energy_historical.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_historical_plot,
            ]
        )
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # ENERGY INDUSTRY OWN USE AND LOSSES BY SOURCE #
        ################################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Energy industry own use and Losses"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Energy industry own use and Losses, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ############################################################
        # ENERGY CONSUMPTION IN TRANSFORMATION PROCESSES BY SOURCE #
        ############################################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Transformation processes"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Energy consumption in Transformation processes, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ##################
        # NON-ENERGY USE #
        ##################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_historical
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Non-energy use"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Non-Energy Use, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    #############################
    #  PROJECT BASELINE ENERGY  #
    #############################

    # region

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
        (
            pd.DataFrame(energy_projection).set_index(
                ["EIA Region", "sector", "EIA Product"]
            )
        )
        .pct_change(axis=1)
        .replace(NaN, 0)
        + 1
    ).loc[:, data_end_year + 1 :]

    # Merge historical and projected energy
    energy_baseline = (
        (
            energy_historical.reset_index()
            .set_index(["EIA Region", "sector", "EIA Product"])
            .merge(energy_projection, on=["EIA Region", "sector", "EIA Product"])
        )
        .reset_index()
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
                "hydrogen",
                "flexible",
                "nonenergy",
                "EIA Region",
                "EIA Product",
            ]
        )
        .droplevel(["EIA Region", "EIA Product"])
    ).sort_index()

    energy_baseline = energy_baseline.parallel_apply(
        lambda x: pd.concat(
            [x.loc[: data_end_year - 1], x.loc[data_end_year:].cumprod()]
        ),
        axis=1,
    )

    # Save to CSV file
    if os.path.exists("podi/data/energy_baseline.csv"):
        os.remove("podi/data/energy_baseline.csv")
    energy_baseline.to_csv("podi/data/energy_baseline.csv")

    # Plot energy_baseline
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", Baseline",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_long"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", Baseline",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # ELECTRICITY CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[1], unit_val[1]]

        start_year = data_start_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", Baseline",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ####################################
        # ELECTRICITY GENERATION BY SOURCE #
        ####################################

        # region

        # Breakdown 'Electricity and Heat' product_category

        # region

        energy_baseline_plot = energy_baseline[
            (
                energy_baseline.reset_index().product_category == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_baseline_plot["product_category"] = energy_baseline_plot["product_long"]

        energy_baseline_plot.set_index(energy_baseline.index.names, inplace=True)

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_baseline[
                    ~(
                        energy_baseline.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_baseline_plot,
            ]
        )
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", Baseline",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #######################################
        # ELECTRICITY GENERATION BY SOURCE, % #
        #######################################

        # region

        elec_supply = energy_baseline[
            (
                (
                    energy_baseline.reset_index().flow_category == "Electricity output"
                ).values
            )
            & ((energy_baseline.reset_index().nonenergy == "N").values)
        ]

        per_elec_supply = elec_supply.parallel_apply(
            lambda x: x.divide(elec_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
            axis=1,
        ).fillna(0)

        start_year = data_start_year
        df = per_elec_supply.loc[slice(None), ["baseline"], ["usa"]]
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * 100

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", Baseline, "
                + "USA",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "%"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # ENERGY INDUSTRY OWN USE AND LOSSES BY SOURCE #
        ################################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Energy industry own use and Losses"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Energy industry own use and Losses, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + "Baseline"
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ############################################################
        # ENERGY CONSUMPTION IN TRANSFORMATION PROCESSES BY SOURCE #
        ############################################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Transformation processes"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Energy consumption in Transformation processes, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ##################
        # NON-ENERGY USE #
        ##################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_baseline
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Non-energy use"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Non-Energy Use, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    ##############################################
    #  ESTIMATE ENERGY REDUCTIONS & FUEL SHIFTS  #
    ##############################################

    # region

    # Calculate 'electrification factors' that scale down energy over time due to the lower energy required to produce an equivalent amount of work via electricity

    # region

    # Load saturation points for energy reduction ratios
    ef_ratio = (
        pd.DataFrame(
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
        )
        .set_index(["region", "product_short", "scenario", "sector", "metric"])
        .loc[
            energy_baseline.index.get_level_values(2).unique(),
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

    # Clear energy_adoption_curves.csv, and run adoption_projection_demand() to calculate logistics curves for energy reduction ratios

    # Clear energy_adoption_curves.csv and energy_ef_ratio.csv
    if os.path.exists("podi/data/energy_adoption_curves.csv"):
        os.remove("podi/data/energy_adoption_curves.csv")
    if os.path.exists("podi/data/energy_ef_ratios.csv"):
        os.remove("podi/data/energy_ef_ratios.csv")

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
            "saturation point"
        ].value.astype(float)

        y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(parameters.loc["parameter a min"].value),
                pd.to_numeric(parameters.loc["parameter a max"].value),
            ),
            (
                pd.to_numeric(parameters.loc["parameter b min"].value),
                pd.to_numeric(parameters.loc["parameter b max"].value),
            ),
            (
                pd.to_numeric(parameters.loc["saturation point"].value),
                pd.to_numeric(parameters.loc["saturation point"].value),
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
                min(0.0018, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
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
            "podi/data/energy_adoption_curves.csv",
            mode="a",
            header=None,
            index=False,
        )

        return

    ef_ratio.parallel_apply(
        lambda x: adoption_projection_demand(
            parameters=parameters.loc[x.name[0], x.name[1], x.name[2], x.name[3]],
            input_data=x,
            scenario=scenario,
            data_end_year=data_end_year + 1,
            saturation_year=2050,
            proj_end_year=proj_end_year,
        ),
        axis=1,
    )

    ef_ratios = (
        pd.DataFrame(pd.read_csv("podi/data/energy_adoption_curves.csv", header=None))
        .set_axis(
            pd.concat(
                [
                    pd.DataFrame(
                        np.array(["region", "product_short", "scenario", "sector"])
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
        .set_index(["region", "sector", "product_short", "scenario"])
    ).sort_index()

    # Prepare df for multiplication with energy
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
    ef_ratios = ef_ratios.loc[:, : energy_baseline.columns[-1]]
    ef_ratios = ef_ratios.sort_index()

    ef_ratios.to_csv("podi/data/energy_ef_ratios.csv")

    # Add labels to ef_ratios
    labels = (
        (
            pd.DataFrame(
                pd.read_csv(
                    "podi/data/product_flow_labels.csv",
                    usecols=[
                        "product_short",
                        "flow_short",
                        "sector",
                        "WWS EF Product",
                        "WWS Upstream Product",
                        "WWS Addtl Efficiency",
                    ],
                )
            ).set_index(["sector", "WWS EF Product"])
        )
        .rename_axis(index={"WWS EF Product": "product_short"})
        .rename(columns={"product_short": "IEA Product"})
    ).sort_index()

    ef_ratios = (
        (
            ef_ratios.reset_index()
            .set_index(["sector", "product_short"])
            .merge(labels, on=["sector", "product_short"])
            .set_index(
                [
                    "region",
                    "scenario",
                    "IEA Product",
                    "flow_short",
                    "WWS Upstream Product",
                    "WWS Addtl Efficiency",
                ],
                append=True,
            )
        )
        .droplevel(["product_short", "scenario"])
        .reorder_levels(
            [
                "region",
                "sector",
                "IEA Product",
                "flow_short",
                "WWS Upstream Product",
                "WWS Addtl Efficiency",
            ]
        )
    )

    # Remove duplicate indices
    ef_ratios = ef_ratios[~ef_ratios.index.duplicated()]

    # endregion

    # Calculate 'upstream ratios' that scale down energy over time due to the lower energy required for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing. Note that not all upstream fossil energy is eliminiated, since some upstream energy is expected to remain to produce fossil fuel flows for non-energy use.

    # region

    upstream_ratios = ef_ratios.copy()

    upstream_ratios.update(
        upstream_ratios[upstream_ratios.index.get_level_values(4) == "Y"]
        .parallel_apply(lambda x: 1 - (x.max() - x) / (x.max() - x.min()), axis=1)
        .fillna(0)
    )

    # Set upstream ratios in ef_ratios to 1 so upstream reduction is not double counted
    ef_ratios[ef_ratios.index.get_level_values(4) == "Y"] = 1
    ef_ratios = ef_ratios.sort_index()

    upstream_ratios[upstream_ratios.index.get_level_values(4) == "N"] = 1
    upstream_ratios = upstream_ratios.sort_index()

    # endregion

    # Reduce energy by the upstream energy reductions from fossil fuel/biofuel/bioenergy/uranium mining/transport/processing

    # region

    energy_post_upstream = energy_baseline.parallel_apply(
        lambda x: x.mul(
            upstream_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]].squeeze()
        ),
        axis=1,
    )
    energy_post_upstream.rename(index={"baseline": scenario}, inplace=True)

    # endregion

    # Apply percentage reduction attributed to additional energy efficiency measures

    # region

    addtl_eff = pd.DataFrame(pd.read_csv("podi/data/energy_ef_ratios.csv")).set_index(
        ["scenario", "region", "sector", "product_short"]
    )
    addtl_eff.columns = addtl_eff.columns.astype(int)

    labels = (
        labels.reset_index()
        .drop(columns=["WWS Upstream Product", "product_short"])
        .set_index(["sector", "WWS Addtl Efficiency"])
        .rename_axis(index={"WWS Addtl Efficiency": "product_short"})
        .rename(columns={"product_short": "IEA Product"})
    )

    addtl_eff = (
        (
            addtl_eff.reset_index()
            .set_index(["sector", "product_short"])
            .merge(labels, on=["sector", "product_short"])
            .set_index(
                [
                    "region",
                    "scenario",
                    "IEA Product",
                    "flow_short",
                ],
                append=True,
            )
        )
        .droplevel(["product_short", "scenario"])
        .reorder_levels(["region", "sector", "IEA Product", "flow_short"])
    )

    addtl_eff = addtl_eff.groupby(
        ["region", "sector", "IEA Product", "flow_short"]
    ).mean()

    # Remove duplicate indices
    addtl_eff = addtl_eff[~addtl_eff.index.duplicated()]
    addtl_eff = addtl_eff.sort_index()

    energy_post_addtl_eff = energy_post_upstream.parallel_apply(
        lambda x: x.mul(
            addtl_eff.loc[x.name[2], x.name[3], x.name[6], x.name[9]].squeeze()
        ),
        axis=1,
    )

    # endregion

    # Estimate energy reduction and fuel shifts due to electrification

    # region

    # Isolate the energy that gets replaced with (a reduced amount of) energy from electricity. Each row of energy is multiplied by ((ef[0] - ef[i]) / (ef[0] - ef[-1]), which represents the percent of energy that undergoes electrification in each year. This does not count preexisting electricity, except for nuclear, which is estimated to shift to renewables, and is treated in subsequent steps.
    energy_electrified = energy_post_addtl_eff.parallel_apply(
        lambda x: x.mul(
            (
                (
                    ef_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]]
                    .squeeze()
                    .iloc[0]
                    - ef_ratios.loc[
                        x.name[2], x.name[3], x.name[6], x.name[9]
                    ].squeeze()
                )
                / (
                    ef_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]]
                    .squeeze()
                    .iloc[0]
                    - ef_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]]
                    .squeeze()
                    .iloc[-1]
                )
            ).fillna(0)
        ),
        axis=1,
    )

    # Find the reduced amount of electrical energy that represents an equivalent amount of work to that of the energy that undergoes electrification.
    energy_reduced_electrified = energy_electrified.parallel_apply(
        lambda x: x.mul(
            ef_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]].squeeze().iloc[-1]
        ),
        axis=1,
    )

    # Find the electrical energy from fossil fuels assumed to shift to renewables
    renewables = [
        "GEOTHERM",
        "HYDRO",
        "SOLARPV",
        "ROOFTOP",
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
                "model",
                "scenario",
                "region",
                "sector",
                "flow_category",
                "flow_long",
                "flow_short",
                "unit",
                "hydrogen",
                "flexible",
                "nonenergy",
            ]
        )
        .sum()
        .reset_index()
    )

    energy_reduced_electrified_e = energy_reduced_electrified2[
        energy_reduced_electrified2["hydrogen"] == "N"
    ]
    energy_reduced_electrified_e["product_category"] = "Electricity and Heat"
    energy_reduced_electrified_e["product_long"] = "Renewable Electricity"
    energy_reduced_electrified_e["product_short"] = "RELECTR"

    energy_reduced_electrified_h = energy_reduced_electrified2[
        energy_reduced_electrified2["hydrogen"] == "Y"
    ]
    energy_reduced_electrified_h["product_category"] = "Hydrogen"
    energy_reduced_electrified_h["product_long"] = "Hydrogen"
    energy_reduced_electrified_h["product_short"] = "HYDROGEN"

    energy_reduced_electrified3 = pd.concat(
        [energy_reduced_electrified_e, energy_reduced_electrified_h]
    )

    energy_reduced_electrified3.set_index(
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
            "hydrogen",
            "flexible",
            "nonenergy",
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
                "hydrogen",
                "flexible",
                "nonenergy",
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
    elec_supply = energy_post_electrification[
        (
            (
                energy_post_electrification.reset_index().flow_category
                == "Electricity output"
            ).values
        )
        & ((energy_post_electrification.reset_index().nonenergy == "N").values)
    ]

    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total electricity consumption met by each renewable product to estimate projected percent of total electricity consumption each meets
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["region", "product_short", "scenario", "sector", "metric", "value"],
    ).set_index(["region", "product_short", "scenario", "sector", "metric"])
    parameters = parameters.sort_index()

    def adoption_projection(
        input_data, saturation_date, output_end_date, change_model, change_parameters
    ):
        def linear(x, a, b, c, d):
            return a * x + d

        def logistic(x, a, b, c, d):
            return c / (1 + np.exp(-a * (x - b))) + d

        # Take 10 years prior data to fit logistic function
        x_data = np.arange(0, output_end_date - input_data.last_valid_index() + 11, 1)
        y_data = np.zeros((1, len(x_data)))
        y_data[:, :] = np.NaN
        y_data = y_data.squeeze().astype(float)
        y_data[:11] = input_data.loc[
            input_data.last_valid_index() - 10 : input_data.last_valid_index()
        ]
        y_data[saturation_date - input_data.last_valid_index()] = change_parameters.loc[
            "saturation point"
        ].value.astype(float)

        # Handle cases where saturation point is below current value, by making saturation point equidistant from current value but in positive direction
        if y_data[10] > y_data[-1]:
            y_data[-1] = y_data[10] + abs(y_data[-1] - y_data[10])

        y_data = np.array((pd.DataFrame(y_data).interpolate(method="linear")).squeeze())

        # Load search bounds for logistic function parameters
        search_bounds = [
            (
                pd.to_numeric(change_parameters.loc["parameter a min"].value),
                pd.to_numeric(change_parameters.loc["parameter a max"].value),
            ),
            (
                pd.to_numeric(change_parameters.loc["parameter b min"].value),
                pd.to_numeric(change_parameters.loc["parameter b max"].value),
            ),
            (
                pd.to_numeric(change_parameters.loc["saturation point"].value),
                pd.to_numeric(change_parameters.loc["saturation point"].value),
            ),
            (
                y_data[10],
                y_data[10],
            ),
        ]

        # Define sum of squared error function
        def sum_of_squared_error(change_parameters):
            return np.sum((y_data - logistic(x_data, *change_parameters)) ** 2.0)

        # Generate genetic_parameters. For baseline scenarios, projections are linear
        if change_model == "linear":
            y = linear(
                x_data,
                min(0.04, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
                0,
                0,
                y_data[10],
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

            y = np.array(logistic(np.arange(0, 500, 1), *genetic_parameters))

        # Rejoin with input data at point where projection curve results in smooth growth
        y = np.concatenate(
            [
                input_data.loc[: input_data.last_valid_index()].values,
                y[y >= input_data.loc[input_data.last_valid_index()]].squeeze(),
            ]
        )[: (output_end_date + 1 - input_data.first_valid_index())]

        return pd.Series(
            data=y[
                : len(np.arange(input_data.first_valid_index(), output_end_date + 1, 1))
            ],
            index=np.arange(input_data.first_valid_index(), output_end_date + 1, 1),
            name=input_data.name,
        )

    per_elec_supply.update(
        per_elec_supply[per_elec_supply.index.get_level_values(6).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_projection(
                input_data=x.loc[:data_end_year],
                saturation_date=2070,
                output_end_date=proj_end_year,
                change_model="logistic",
                change_parameters=parameters.loc[
                    x.name[2], x.name[6], scenario, x.name[3]
                ],
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
                    .groupby("region")
                    .sum()
                    .loc[x.name[2]]
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
                    .groupby("region")
                    .sum()
                    .loc[x.name[2]]
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
                    .groupby("region")
                    .sum()
                    .loc[x.name[2]]
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
                    .groupby("region")
                    .sum()
                    .loc[x.name[2]]
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

    # Set renewables generation to meet RELECTR in the proportion estimated by adoption_projection(), and nonrenewable electricity generation that shifts to renewable generation
    elec_supply.update(
        pd.concat(
            [
                elec_supply[elec_supply.index.get_level_values(6).isin(renewables)].loc[
                    :, :data_end_year
                ],
                +per_elec_supply[
                    per_elec_supply.index.get_level_values(6).isin(renewables)
                ]
                .parallel_apply(
                    lambda x: x.multiply(
                        nonrenewable_to_renewable.groupby("region")
                        .sum(0)
                        .loc[x.name[2]]
                        + elec_supply.groupby("region").sum(0).loc[x.name[2]]
                    ),
                    axis=1,
                )
                .loc[:, data_end_year + 1 :],
            ],
            axis=1,
        )
    )

    # Recast RELECTR to ELECTR in Final consumption
    energy_post_electrification.reset_index(inplace=True)
    energy_post_electrification[
        (energy_post_electrification["product_short"] == "RELECTR")
        & (energy_post_electrification["flow_category"] == "Final consumption")
    ] = (
        energy_post_electrification[
            (energy_post_electrification["product_short"] == "RELECTR")
            & (energy_post_electrification["flow_category"] == "Final consumption")
        ]
        .replace({"RELECTR": "ELECTR"})
        .replace({"Renewable Electricity": "Electricity"})
    )

    energy_post_electrification.set_index(
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
            "hydrogen",
            "flexible",
            "nonenergy",
        ]
    )

    energy_post_electrification = energy_post_electrification.groupby(
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
            "hydrogen",
            "flexible",
            "nonenergy",
        ]
    ).sum()

    energy_post_electrification.drop(labels="RELECTR", level=6, inplace=True)

    # Drop RELECTR now that it has been reallocated to the specific set of renewables
    elec_supply.drop(labels="RELECTR", level=6, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Recalculate elec_supply to cover energy_post_electrification product_long = "Electricity" flow_category = "Final consumption"
    elec_supply = per_elec_supply.parallel_apply(
        lambda x: x.multiply(
            energy_post_electrification[
                (
                    (
                        energy_post_electrification.reset_index().product_long
                        == "Electricity"
                    ).values
                )
                & (
                    (
                        energy_post_electrification.reset_index().flow_category
                        == "Final consumption"
                    ).values
                )
                & ((energy_post_electrification.reset_index().nonenergy == "N").values)
            ]
            .groupby(["model", "scenario", "region"])
            .sum()
            .loc[x.name[0], x.name[1], x.name[2]]
        ),
        axis=1,
    )

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(elec_supply)

    # Plot energy_post_electrification
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # TOTAL FINAL CONSUMPTION BY SOURCE, W/ WEDGES #
        ################################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit[1]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit[0],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit[1]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit[0],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit[1]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit[0],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit[0]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit[0]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World")
                + ", "
                + str(scenario).capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # ELECTRICITY CONSUMPTION BY SECTOR #
        #####################################

        # region

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                    ["N"],
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ####################################
        # ELECTRICITY GENERATION BY SOURCE #
        ####################################

        # region

        # Breakdown 'Electricity and Heat' product_category

        # region

        energy_post_electrification_plot = energy_post_electrification[
            (
                energy_post_electrification.reset_index().product_category
                == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_post_electrification_plot[
            "product_category"
        ] = energy_post_electrification_plot["product_long"]

        energy_post_electrification_plot.set_index(
            energy_post_electrification.index.names, inplace=True
        )

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_post_electrification[
                    ~(
                        energy_post_electrification.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_post_electrification_plot,
            ]
        )
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #######################################
        # ELECTRICITY GENERATION BY SOURCE, % #
        #######################################

        # region

        start_year = data_start_year
        df = per_elec_supply.loc[slice(None), ["pathway"], ["usa"]]
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_long"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * 100

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(fig, id_vars="year", var_name=[groupby], value_name="TFC, %")

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, %"],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(scenario).capitalize()
                + ", USA",
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "%"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # ELECTRICITY CONSUMPTION BY SECTOR, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    ##############################
    # ESTIMATE UPDATED HEAT MIX  #
    ##############################

    # region

    renewables = ["GEOTHERM", "SOLARTH"]

    # For each region, for each subsector ('Low Temperature', 'High Temperature'), find the percent of total heat consumption met by each renewable product. heat_supply is 'Heat output' from the 'Electricity and Heat' product category, plus other products that are consumed within residential, commercial, and industrial sectors directly for heat.
    heat_supply = energy_post_electrification[
        (
            (
                energy_post_electrification.reset_index().flow_category == "Heat output"
            ).values
        )
        & ((energy_post_electrification.reset_index().nonenergy == "N").values)
    ]

    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total heat consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_heat_supply.update(
        per_heat_supply[per_heat_supply.index.get_level_values(6).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_projection(
                input_data=x.loc[:data_end_year],
                saturation_date=2040,
                output_end_date=proj_end_year,
                change_model="logistic",
                parameters=parameters.loc[x.name[2], x.name[6], scenario, x.name[3]],
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
                .groupby(["region"])
                .sum(0)
                .loc[x.name[2]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(heat_supply)

    # Plot energy_post_electrification
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # TOTAL FINAL CONSUMPTION BY SOURCE, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[2]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World")
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[2]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ##############################
        # HEAT CONSUMPTION BY SECTOR #
        ##############################

        # region

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = [
            "Solar thermal",
            "Heat – High Temperature",
            "Heat – Low Temperature",
            "Heat output from non-specified combustible fuels – High Temperature",
            "Heat output from non-specified combustible fuels – Low Temperature",
        ]
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Heat Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #############################
        # HEAT GENERATION BY SOURCE #
        #############################

        # region

        # Breakdown 'Electricity and Heat' product_category

        # region

        energy_post_electrification_plot = energy_post_electrification[
            (
                energy_post_electrification.reset_index().product_category
                == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_post_electrification_plot[
            "product_category"
        ] = energy_post_electrification_plot["product_long"]

        energy_post_electrification_plot.set_index(
            energy_post_electrification.index.names, inplace=True
        )

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_post_electrification[
                    ~(
                        energy_post_electrification.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_post_electrification_plot,
            ]
        )
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Heat output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Heat Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #########################################
        # HEAT CONSUMPTION BY SECTOR, W/ WEDGES #
        #########################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = [
            "Solar thermal",
            "Heat – High Temperature",
            "Heat – Low Temperature",
            "Heat output from non-specified combustible fuels – High Temperature",
            "Heat output from non-specified combustible fuels – Low Temperature",
        ]
        flow_category = ["Final consumption"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Heat Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    ###############################################
    # ESTIMATE UPDATED NONELECTRIC TRANSPORT MIX  #
    ###############################################

    # region

    renewables = ["HYDROGEN"]

    # For each region, find the percent of total nonelectric energy consumption met by each product.
    transport_supply = energy_post_electrification[
        ((energy_post_electrification.reset_index().sector == "Transportation").values)
        & (
            (
                energy_post_electrification.reset_index().flow_category
                == "Final consumption"
            ).values
        )
        & ((energy_post_electrification.reset_index().nonenergy == "N").values)
    ]

    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total nonelectric transport consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_transport_supply.update(
        per_transport_supply[
            per_transport_supply.index.get_level_values(6).isin(renewables)
        ]
        .parallel_apply(
            lambda x: adoption_projection(
                input_data=x.loc[:data_end_year],
                saturation_date=2040,
                output_end_date=proj_end_year,
                change_model="logistic",
                parameters=parameters.loc[x.name[2], x.name[6], scenario, x.name[3]],
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
                .groupby(["region"])
                .sum(0)
                .loc[x.name[2]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(transport_supply)

    # Plot energy_post_electrification
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # TOTAL FINAL CONSUMPTION BY SOURCE, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[2]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World")
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[2]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # ELECTRICITY CONSUMPTION BY SECTOR #
        #####################################

        # region

        start_year = data_start_year
        df = energy_post_electrification
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    slice(None),
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ####################################
        # ELECTRICITY GENERATION BY SOURCE #
        ####################################

        # region

        # Breakdown 'Electricity and Heat' product_category

        # region

        energy_post_electrification_plot = energy_post_electrification[
            (
                energy_post_electrification.reset_index().product_category
                == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_post_electrification_plot[
            "product_category"
        ] = energy_post_electrification_plot["product_long"]

        energy_post_electrification_plot.set_index(
            energy_post_electrification.index.names, inplace=True
        )

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_post_electrification[
                    ~(
                        energy_post_electrification.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_post_electrification_plot,
            ]
        )
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        ################################################
        # ELECTRICITY CONSUMPTION BY SECTOR, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_post_electrification
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    #############################
    # ESTIMATE STORAGE CAPACITY #
    #############################
    """
    # region

    # Current setting to 20% of electricity generation

    energy_storage = pd.concat(
        [
            pd.concat(
                [
                    energy_post_electrification[
                        (
                            energy_post_electrification.reset_index().flow_category
                            == "Electricity output"
                        ).values
                    ]
                    .groupby(energy_post_electrification.index.names)
                    .sum()
                    .multiply(0.2)
                    .loc[:, :data_end_year],
                    energy_baseline[
                        (
                            energy_baseline.reset_index().flow_category
                            == "Electricity output"
                        ).values
                    ]
                    .groupby(energy_baseline.index.names)
                    .sum()
                    .multiply(0.2),
                ]
            ),
            pd.concat(
                [
                    energy_post_electrification[
                        (
                            energy_post_electrification.reset_index().flow_category
                            == "Electricity output"
                        ).values
                    ]
                    .groupby(energy_post_electrification.index.names)
                    .sum()
                    .multiply(0.2)
                    .multiply(
                        energy_post_electrification[
                            (
                                energy_post_electrification.reset_index().flow_category
                                == "Electricity output"
                            ).values
                        ]
                        .groupby(energy_post_electrification.index.names)
                        .sum()
                        .multiply(0.2)
                        .pct_change()
                        .fillna(0)
                        .replace(np.inf, 0)
                        .add(1)
                        .cumprod()
                    ),
                    energy_baseline[
                        (
                            energy_baseline.reset_index().flow_category
                            == "Electricity output"
                        ).values
                    ]
                    .groupby(energy_baseline.index.names)
                    .sum()
                    .multiply(0.2)
                    .multiply(
                        energy_baseline[
                            (
                                energy_baseline.reset_index().flow_category
                                == "Electricity output"
                            ).values
                        ]
                        .groupby(energy_baseline.index.names)
                        .sum()
                        .multiply(0.1)
                        .pct_change()
                        .fillna(0)
                        .replace(np.inf, 0)
                        .add(1)
                        .cumprod()
                    ),
                ]
            ).loc[:, data_end_year + 1 :],
        ],
        axis=1,
    ).reset_index()

    energy_storage["product_category"] = "Storage"
    energy_storage["product_long"] = "Storage"
    energy_storage["product_short"] = "STOR"

    energy_storage.set_index(energy_post_electrification.index.names, inplace=True)

    energy_storage = energy_storage.groupby(energy_storage.index.names).sum()

    energy_post_electrification = pd.concat(
        [energy_post_electrification, energy_storage]
    )

    # Plot energy_post_electrification
    if show_figs is True:
        #######################
        # ELECTRICITY STORAGE #
        #######################

        # region

        start_year = data_start_year
        df = energy_storage
        model = "PD22"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = slice(None)
        flow_category = slice(None)
        groupby = ["scenario", "product_long"]

        fig = (
            df.loc[
                model,
                slice(None),
                region,
                sector,
                product_category,
                product_long,
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby(groupby)
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=groupby, value_name="TFC, " + unit_name[1]
        )

        for scenario in fig2["scenario"].unique():
            fig = go.Figure()

            for sub in fig2["product_long"].unique():
                fig.add_trace(
                    go.Scatter(
                        name=sub,
                        line=dict(
                            width=0.5,
                        ),
                        x=fig2["year"],
                        y=fig2[
                            (fig2["scenario"] == scenario)
                            & (fig2["product_long"] == sub)
                        ]["TFC, " + unit_name[1]],
                        fill="tonexty",
                        stackgroup="1",
                    )
                )

            fig.update_layout(
                title={
                    "text": "Energy Storage, "
                    + str(sector).replace("slice(None, None, None)", "All Sectors")
                    + ", "
                    + str(region)
                    .replace("slice(None, None, None)", "World")
                    .capitalize()
                    + ", "
                    + str(scenario).capitalize(),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.99,
                },
                yaxis={"title": "TFC, " + unit_name[1]},
                margin_b=0,
                margin_t=20,
                margin_l=10,
                margin_r=10,
            )

            fig.show()

        # endregion

    # endregion
    """
    #################
    #  SAVE OUTPUT  #
    #################

    # region

    # Drop rows that have all zeros
    energy_post_upstream = energy_post_upstream[energy_post_upstream.sum(axis=1) != 0]
    energy_post_addtl_eff = energy_post_addtl_eff[
        energy_post_addtl_eff.sum(axis=1) != 0
    ]
    energy_electrified = energy_electrified[energy_electrified.sum(axis=1) != 0]
    energy_reduced_electrified = energy_reduced_electrified[
        energy_reduced_electrified.sum(axis=1) != 0
    ]
    energy_post_electrification = energy_post_electrification[
        energy_post_electrification.sum(axis=1) != 0
    ]
    per_elec_supply = per_elec_supply[per_elec_supply.sum(axis=1) != 0]
    per_heat_supply = per_heat_supply[per_heat_supply.sum(axis=1) != 0]
    per_transport_supply = per_transport_supply[per_transport_supply.sum(axis=1) != 0]

    # Combine percent output for electricity, heat, transport
    energy_percent = pd.concat([per_elec_supply, per_heat_supply, per_transport_supply])

    # Combine baseline and pathway energy output:
    energy_output = pd.concat([energy_baseline, energy_post_electrification])
    energy_output.index = energy_output.index.droplevel(
        ["hydrogen", "flexible", "nonenergy"]
    )

    # Drop 'hydrogen', 'flexible', 'nonenergy' flags and save
    for output in [
        (energy_post_upstream, "energy_post_upstream"),
        (energy_post_addtl_eff, "energy_post_addtl_eff"),
        (energy_electrified, "energy_electrified"),
        (energy_reduced_electrified, "energy_reduced_electrified"),
        (energy_output, "energy_output"),
        (energy_percent, "energy_percent"),
    ]:
        output[0].groupby(
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
        ).sum().sort_index().to_csv("podi/data/" + output[1] + ".csv")

    energy_output = (
        energy_output.groupby(
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

    # Plot energy_output
    if show_figs is True:
        #####################################
        # TOTAL FINAL CONSUMPTION BY SOURCE #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        df = energy_output
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
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
                    "./charts/energy-TFC-productcategory-" + str(scenario) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        # endregion

        ################################################
        # TOTAL FINAL CONSUMPTION BY SOURCE, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_output
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "product_category"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[2]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_output.loc[slice(None), ["baseline"], :])
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[2]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[2],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[2]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[2]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World")
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[2]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

        #####################################
        # TOTAL FINAL CONSUMPTION BY SECTOR #
        #####################################

        # region

        unit_name = ["TJ", "TWh", "GW"]
        unit_val = [1, 0.0002777, 0.2777 / 8760]
        unit = [unit_name[0], unit_val[0]]

        start_year = data_start_year
        end_year = data_end_year
        df = energy_output
        model = "PD22"
        scenario = scenario
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit[0]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit[0]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Total Final Consumption, "
                + str(product_category).replace(
                    "slice(None, None, None)", "All Sources"
                )
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + scenario.capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit[0]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=("./charts/energy-TFC-sector-" + str(scenario) + ".html").replace(
                    " ", ""
                ),
                auto_open=False,
            )

        # endregion

        #####################################
        # ELECTRICITY CONSUMPTION BY SECTOR #
        #####################################

        # region

        start_year = data_start_year
        df = energy_output
        model = "PD22"
        scenario = scenario
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "sector"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + scenario.capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
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
                    "./charts/energy-electricity-sector-" + str(scenario) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        # endregion

        ####################################
        # ELECTRICITY GENERATION BY SOURCE #
        ####################################

        # region

        # Breakdown 'Electricity and Heat' product_category
        # region

        energy_output_plot = energy_output[
            (
                energy_output.reset_index().product_category == "Electricity and Heat"
            ).values
        ].reset_index()

        energy_output_plot["product_category"] = energy_output_plot["product_long"]

        energy_output_plot.set_index(energy_output.index.names, inplace=True)

        # endregion

        start_year = data_start_year
        df = pd.concat(
            [
                energy_output[
                    ~(
                        energy_output.reset_index().product_category
                        == "Electricity and Heat"
                    ).values
                ],
                energy_output_plot,
            ]
        )
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        flow_category = ["Electricity output"]
        groupby = "product_category"

        fig = (
            df.loc[
                model,
                scenario,
                region,
                sector,
                product_category,
                slice(None),
                slice(None),
                flow_category,
                slice(None),
                slice(None),
                slice(None),
            ]
            .groupby([groupby])
            .sum()
        ).loc[:, start_year:] * unit_val[1]

        fig = fig.T
        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Generation, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
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
                    "./charts/energy-electricity-product-" + str(scenario) + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

        # endregion

        ################################################
        # ELECTRICITY CONSUMPTION BY SECTOR, W/ WEDGES #
        ################################################

        # region

        start_year = data_start_year
        end_year = proj_end_year
        df = energy_output
        model = "PD22"
        scenario = "pathway"
        region = slice(None)
        sector = slice(None)
        product_category = slice(None)
        product_long = "Electricity"
        flow_category = ["Final consumption"]
        groupby = "flow_long"

        fig = (
            (
                df.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        fig.index.name = "year"
        fig.reset_index(inplace=True)
        fig2 = pd.melt(
            fig, id_vars="year", var_name=[groupby], value_name="TFC, " + unit_name[1]
        )

        bwedges = (
            (
                energy_electrified.loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    slice(None),
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        bwedges.index.name = "year"
        bwedges.reset_index(inplace=True)
        bwedges2 = pd.melt(
            bwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        addtleffwedges = (
            (
                (energy_post_upstream - energy_post_addtl_eff)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        addtleffwedges.index.name = "year"
        addtleffwedges.reset_index(inplace=True)
        addtleffwedges2 = pd.melt(
            addtleffwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        upstreamwedges = (
            (
                (energy_post_upstream - energy_baseline)
                .loc[
                    model,
                    scenario,
                    region,
                    sector,
                    product_category,
                    product_long,
                    slice(None),
                    flow_category,
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby([groupby])
                .sum()
            ).loc[:, start_year:end_year]
            * unit_val[1]
        ).T

        upstreamwedges.index.name = "year"
        upstreamwedges.reset_index(inplace=True)
        upstreamwedges2 = pd.melt(
            upstreamwedges,
            id_vars="year",
            var_name=[groupby],
            value_name="TFC, " + unit_name[1],
        )

        fig = go.Figure()

        for sub in fig2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name=sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=fig2["year"],
                    y=fig2[fig2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in bwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=bwedges2["year"],
                    y=bwedges2[bwedges2[groupby] == sub]["TFC, " + unit_name[1]],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in addtleffwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Efficiency reduction of " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=addtleffwedges2["year"],
                    y=addtleffwedges2[addtleffwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        for sub in upstreamwedges2[groupby].unique():
            fig.add_trace(
                go.Scatter(
                    name="Avoided use of upstream " + sub,
                    line=dict(
                        width=0.5,
                    ),
                    x=upstreamwedges2["year"],
                    y=upstreamwedges2[upstreamwedges2[groupby] == sub][
                        "TFC, " + unit_name[1]
                    ],
                    fill="tonexty",
                    stackgroup="1",
                )
            )

        fig.update_layout(
            title={
                "text": "Electricity Consumption, "
                + str(sector).replace("slice(None, None, None)", "All Sectors")
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TFC, " + unit_name[1]},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        fig.show()

        # endregion

    # endregion

    return
