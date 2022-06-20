#!/usr/bin/env python

# region

import pandas as pd

# endregion


def results_analysis(
    energy_output,
    afolu_output,
    emissions_output,
    emissions_output_co2e,
    cdr_output,
    climate_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ##############
    #  PD INDEX  #
    ##############

    # region

    # Percent of electric power that is renewables

    electricity = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Electric Power"],
            slice(None),
            slice(None),
            [
                "GEOTHERM",
                "HYDRO",
                "SOLARPV",
                "ROOFTOP",
                "SOLARTH",
                "OFFSHORE",
                "ONSHORE",
                "TIDE",
                "NUCLEAR",
            ],
            ["Electricity output"],
        ]
        .groupby(["model", "scenario", "region", "sector"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                slice(None),
                slice(None),
                ["Electric Power"],
                slice(None),
                slice(None),
                slice(None),
                ["Electricity output"],
            ]
            .groupby(["model", "scenario", "region", "sector"])
            .sum()
        )
        * 100
    )

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Transportation"],
            product_category,
            slice(None),
            ["BIODIESEL", "BIOGASOL", "BIOGASES", "OBIOLIQ", "ELECTR", "HYDROGEN"],
            flow_category,
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model, scenario, region, ["Transportation"], product_category
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of buildings energy that is electric or nonelectric renewables
    buildings = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Commercial", "Residential"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            flow_category,
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model, scenario, region, ["Commercial", "Residential"], product_category
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of industry energy that is electric or nonelectric renewables
    industry = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Industrial"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Agriculture/forestry",
                "Chemical and petrochemical",
                "Construction",
                "Final consumption not elsewhere specified",
                "Fishing",
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
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Industrial"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of agriculture mitigation compared to max extent
    agriculture = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Agriculture"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Agriculture/forestry",
                "Chemical and petrochemical",
                "Construction",
                "Final consumption not elsewhere specified",
                "Fishing",
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
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Agriculture"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of forests & wetlands mitigation compared to max extent
    forestswetlands = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Forests & Wetlands"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Agriculture/forestry",
                "Chemical and petrochemical",
                "Construction",
                "Final consumption not elsewhere specified",
                "Fishing",
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
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Forests & Wetlands"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of cdr sequestration compared to max extent
    cdr = (
        cdr_output.loc[
            model,
            scenario,
            region,
            ["CDR"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Agriculture/forestry",
                "Chemical and petrochemical",
                "Construction",
                "Final consumption not elsewhere specified",
                "Fishing",
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
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["CDR"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    # Combine all verticals
    pdindex_output = pd.concat(
        [
            "electricity",
            "transport",
            "buildings",
            "industry",
            "agriculture",
            "forestswetlands",
            "cdr",
        ]
    )

    # endregion

    ##############
    #  ADOPTION  #
    ##############

    # region

    # Load historical adoption data
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

    adoption_historical = (
        pd.DataFrame(pd.read_csv("podi/data/adoption_historical.csv"))
        .set_index(index)
        .dropna(axis=0, how="all")
    )
    adoption_historical.columns = adoption_historical.columns.astype(int)

    # Project future growth based on percentage growth of energy demand
    adoption_output = (
        pd.concat(
            [
                adoption_historical.loc[:, data_start_year : data_end_year - 1],
                pd.concat(
                    [
                        adoption_historical.loc[:, data_end_year],
                        energy_output.droplevel(["hydrogen", "flexible", "nonenergy"])
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
                            ]
                        )
                        .sum()
                        .loc[:, data_end_year:]
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

    #######################
    # MODELED VS MEASURED #
    #######################

    # region

    # Climate
    # region

    # endregion

    # endregion

    ####################
    # EMISSIONS WEDGES #
    ####################

    # region
    emissions_wedges = (
        emissions_output_co2e[
            (emissions_output_co2e.reset_index().scenario == "baseline").values
        ]
        .rename(index={"baseline": scenario}, level=1)
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
                "flow_short",
                "unit",
            ]
        )
        .sum()
        .subtract(
            emissions_output_co2e[
                (emissions_output_co2e.reset_index().scenario == scenario).values
            ]
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
                    "flow_short",
                    "unit",
                ]
            )
            .sum()
        )
    )

    # Add flow_long back into index
    emissions_wedges = emissions_wedges.reset_index()
    emissions_wedges["flow_long"] = "CO2e"

    emissions_wedges = emissions_wedges.set_index(
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

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    pdindex_output.to_csv("podi/data/pdindex_output.csv")

    adoption_output.to_csv("podi/data/adoption_output.csv")

    emissions_wedges.to_csv("podi/data/emissions_wedges.csv")

    # endregion

    return
