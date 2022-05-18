# region

import pandas as pd
import numpy as np
from numpy import NaN
from podi.adoption_curve_demand import adoption_curve_demand
from podi.adoption_curve import adoption_curve
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import os
import pyam

pandarallel.initialize(nb_workers=4)

# endregion


def energy(scenario, data_start_year, data_end_year, proj_end_year):

    ############################
    #  LOAD HISTORICAL ENERGY  #
    ############################

    # region

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

        # Change from all caps to lowercase
        energy_historical["Region"] = energy_historical["Region"].str.lower()

        # Format as a dataframe with timeseries as rows
        energy_historical = pd.pivot_table(
            energy_historical,
            values="Value",
            index=["Region", "Product", "Flow", "Unit"],
            columns="Year",
        ).replace(NaN, 0)

        # Remove duplicate regions created due to name overlaps
        energy_historical = energy_historical.loc[[region.lower()], :]

        # Build dataframe consisting of all regions
        energy_historical2 = pd.concat([energy_historical2, energy_historical])
    energy_historical = energy_historical2

    # Add model and scenario indices
    energy_historical = pd.concat(
        [pd.concat([energy_historical], keys=["baseline"], names=["Scenario"])],
        keys=["PD22"],
        names=["Model"],
    )

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

    energy_historical = energy_historical.loc[
        slice(None), slice(None), slice(None), products, flows
    ]

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
        ["Model", "Scenario", "Region", "Product", "Flow", "Unit"]
    )

    irena.columns = irena.columns.astype(int)
    irena = irena.loc[:, data_start_year:data_end_year]

    # Drop IEA WIND and SOLARPV to avoid duplication with IRENA ONSHORE/OFFSHORE
    energy_historical = energy_historical.drop(labels="WIND", level=3)

    energy_historical = pd.concat(
        [
            energy_historical,
            irena[irena.index.get_level_values(3).isin(["ONSHORE", "OFFSHORE"])],
        ]
    )

    # endregion

    # Add product and flow labels to energy_historical

    labels = pd.DataFrame(
        pd.read_csv(
            "podi/data/product_flow_labels.csv",
            usecols=[
                "Product",
                "Flow",
                "Sector",
                "EIA Product",
                "Hydrogen",
                "Flexible",
                "Nonenergy",
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
                "Model",
                "Scenario",
                "Region",
                "Sector",
                "Product",
                "Flow",
                "Unit",
                "EIA Product",
                "Hydrogen",
                "Flexible",
                "Nonenergy",
            ]
        )
    )

    # Split ROAD Flow into Two- and three-wheeled, Light, Medium (Buses), Heavy (Trucks)

    # region

    subsector_props = pd.DataFrame(
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
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])

    # Create Two- and three-wheeled Flow (TTROAD) using estimate of the fraction of ROAD that is Two- and three-wheeled
    ttroad = (
        energy_historical[(energy_historical.reset_index().Flow == "ROAD").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "ROAD").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "ROAD").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "ROAD").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "DOMESAIR").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "DOMESAIR").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "RAIL").values]
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
        energy_historical[(energy_historical.reset_index().Flow == "RAIL").values]
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
                (energy_historical.reset_index().Product == "HEAT")
                | (energy_historical.reset_index().Product == "HEATNS")
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
                (energy_historical.reset_index().Product == "HEAT")
                | (energy_historical.reset_index().Product == "HEATNS")
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
            (energy_historical.reset_index().Product == "NONCRUDE").values
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
        (energy_historical.reset_index().Product == "NONCRUDE").values
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
            (energy_historical.reset_index().Product == "SOLARPV").values
        ].parallel_apply(lambda x: x * 0.6, axis=1)
    )

    energy_historical = pd.concat(
        [
            energy_historical,
            (
                energy_historical[
                    (energy_historical.reset_index().Product == "SOLARPV").values
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

    # endregion

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

    energy_historical = energy_historical.reset_index().set_index(
        [
            "Model",
            "Scenario",
            "Region",
            "Sector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Unit",
            "Hydrogen",
            "Flexible",
            "Nonenergy",
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

    # Save to CSV file
    energy_historical.to_csv("podi/data/energy_historical.csv")

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
                    "Model",
                    "Scenario",
                    "Region",
                    "Sector",
                    "Product_category",
                    "Product_long",
                    "Product",
                    "Flow_category",
                    "Flow_long",
                    "Flow",
                    "Unit",
                    "Hydrogen",
                    "Flexible",
                    "Nonenergy",
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

        # Save to CSV file
        energy_baseline.to_csv("podi/data/energy_baseline.csv")

    index = [
        "Model",
        "Scenario",
        "Region",
        "Sector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Unit",
        "Hydrogen",
        "Flexible",
        "Nonenergy",
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

    # Remove duplicate indices
    ef_ratios = ef_ratios[~ef_ratios.index.duplicated()]

    # Calculate 'upstream ratios' that scale down energy over time due to the lower energy required for fossil fuel/biofuel/bioenergy/uranium mining/transport/processing. Note that not all upstream fossil energy is eliminiated, since some upstream energy is expected to remain to produce fossil fuel flows for non-energy use.
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

    # Reduce energy by the upstream energy reductions from fossil fuel/biofuel/bioenergy/uranium mining/transport/processing
    energy_post_upstream = energy_baseline.parallel_apply(
        lambda x: x.mul(
            upstream_ratios.loc[x.name[2], x.name[3], x.name[6], x.name[9]].squeeze()
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
            addtl_eff.loc[x.name[2], x.name[3], x.name[6], x.name[9]].squeeze()
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
    energy_reduced_electrified = energy_electrified[
        energy_electrified.index.get_level_values(7) != "Electricity output"
    ].parallel_apply(
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
                "Model",
                "Scenario",
                "Region",
                "Sector",
                "Flow_category",
                "Flow_long",
                "Flow",
                "Unit",
                "Hydrogen",
                "Flexible",
                "Nonenergy",
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
            "Model",
            "Scenario",
            "Region",
            "Sector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Unit",
            "Hydrogen",
            "Flexible",
            "Nonenergy",
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
                "Model",
                "Scenario",
                "Region",
                "Sector",
                "Product_category",
                "Product_long",
                "Product",
                "Flow_category",
                "Flow_long",
                "Flow",
                "Unit",
                "Hydrogen",
                "Flexible",
                "Nonenergy",
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
                energy_post_electrification.reset_index().Flow_category
                == "Electricity output"
            ).values
        )
        & ((energy_post_electrification.reset_index().Nonenergy == "N").values)
    ]

    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
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
                parameters.loc[x.name[2], x.name[6], scenario, x.name[3]],
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
                    .groupby("Region")
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
                    .groupby("Region")
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
                    .groupby("Region")
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

    # Set renewables generation to meet RELECTR in the proportion estimated by adoption_curve(), and nonrenewable electricity generation that shifts to renewable generation
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
                        nonrenewable_to_renewable.groupby("Region")
                        .sum(0)
                        .loc[x.name[2]]
                        + elec_supply.groupby("Region").sum(0).loc[x.name[2]]
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
            "Model",
            "Scenario",
            "Region",
            "Sector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Unit",
            "Hydrogen",
            "Flexible",
            "Nonenergy",
        ]
    )

    energy_post_electrification = energy_post_electrification.groupby(
        [
            "Model",
            "Scenario",
            "Region",
            "Sector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Unit",
            "Hydrogen",
            "Flexible",
            "Nonenergy",
        ]
    ).sum()

    energy_post_electrification.drop(labels="RELECTR", level=6, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Drop RELECTR now that it has been reallocated to the specific set of renewables
    elec_supply.drop(labels="RELECTR", level=6, inplace=True)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(elec_supply)

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
                energy_post_electrification.reset_index().Flow_category == "Heat output"
            ).values
        )
        & ((energy_post_electrification.reset_index().Nonenergy == "N").values)
    ]

    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total heat consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_heat_supply.update(
        per_heat_supply[per_heat_supply.index.get_level_values(6).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[2], x.name[6], scenario, x.name[3]],
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
                .groupby(["Region"])
                .sum(0)
                .loc[x.name[2]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(heat_supply)

    # endregion

    ###############################################
    # ESTIMATE UPDATED NONELECTRIC TRANSPORT MIX  #
    ###############################################

    # region

    renewables = ["HYDROGEN"]

    # For each region, find the percent of total nonelectric energy consumption met by each product.
    transport_supply = energy_post_electrification[
        ((energy_post_electrification.reset_index().Sector == "Transportation").values)
        & (
            (
                energy_post_electrification.reset_index().Flow_category
                == "Final consumption"
            ).values
        )
        & ((energy_post_electrification.reset_index().Nonenergy == "N").values)
    ]

    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total nonelectric transport consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    per_transport_supply.update(
        per_transport_supply[
            per_transport_supply.index.get_level_values(6).isin(renewables)
        ]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[2], x.name[6], scenario, x.name[3]],
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
                .groupby(["Region"])
                .sum(0)
                .loc[x.name[2]]
            ),
            axis=1,
        )
    )

    # Recalculate percent of total consumption each technology meets
    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["Region"]).sum(0).loc[x.name[2]]),
        axis=1,
    ).fillna(0)

    # Update energy_post electrification with new renewables technology mix values
    energy_post_electrification.update(transport_supply)

    # endregion

    ########################
    #  ESTIMATE SHIPMENTS  #
    ########################

    # region

    # Load shipment historical data
    index = [
        "Model",
        "Scenario",
        "Region",
        "Sector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Unit",
        "Hydrogen",
        "Flexible",
        "Nonenergy",
        "Source",
    ]

    shipments = (
        pd.DataFrame(pd.read_csv("podi/data/shipments_historical.csv"))
        .set_index(index)
        .droplevel("Source")
        .dropna(axis=0, how="all")
    )
    shipments.columns = shipments.columns.astype(int)

    # Project future growth based on percentage growth of energy demand
    shipments = (
        pd.concat(
            [
                shipments.loc[:, data_start_year : data_end_year - 1],
                pd.concat(
                    [
                        shipments.loc[:, data_end_year],
                        energy_post_electrification.loc[:, data_end_year:]
                        .pct_change(axis=1)
                        .dropna(axis=1, how="all")
                        .add(1)
                        .clip(upper=2),
                    ],
                    axis=1,
                ).cumprod(axis=1),
            ],
            axis=1,
        )
        .replace(np.inf, 0)
        .replace(-np.inf, 0)
    )

    # endregion

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

    # Shipments
    shipments.to_csv("podi/data/shipments_projected.csv")

    # endregion

    ############################
    #  CONVERT TO IAMC FORMAT  #
    ############################

    # region

    # Concat Sector, Subsector, Product, Flow
    energy_post_electrification_pyam = pyam.IamDataFrame(
        energy_post_electrification.reset_index().drop(
            columns=[
                "Product_category",
                "Product_long",
                "Flow_category",
                "Flow_long",
                "Nonenergy",
            ]
        ),
        variable=["Sector", "Product", "Flow", "Hydrogen", "Flexible"],
    )

    # endregion

    return
