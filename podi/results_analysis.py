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

    # Plot pdindex_output
    # region

    ########################################
    # PD INDEX, STACKED, ELECTRICITY [%] # (V1)
    ########################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "product_category",
        "product_long",
    ]  # 'sector', 'product_category', 'product_long', 'flow_long'

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    ).reindex(
        axis="index",
        level=2,
        labels=[
            "Nuclear",
            "Hydro",
            "Onshore wind energy",
            "Offshore wind energy",
            "Utility solar photovoltaics",
            "Rooftop solar photovoltaics",
            "Solar thermal",
            "Tide, wave and ocean",
            "Geothermal",
        ],
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

    fig = pd.concat([electricity]).T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        if (fig2.columns.values == "flow_long").any():
            for flow in fig2["flow_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=flow,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector) & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=flow,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=flow,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_long").any():
            for product in fig2["product_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_category").any():
            for product in fig2["product_category"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-"
                    + str("-".join(groupby))
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ###########################################
    # PD INDEX, STACKED, TRANSPORTATION [%] # (V2)
    ###########################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Transportation"],
            product_category,
            slice(None),
            ["ELECTR", "HYDROGEN"],
            flow_category,
            [
                "Road – 2&3-wheel",
                "Road – Buses&Vans",
                "Road – Light-duty vehicles",
                "Road – Trucks",
                "Rail – Heavy-duty",
                "Rail – Light-duty",
                "Transport not elsewhere specified",
                "Domestic navigation",
                "International marine bunkers",
                "Domestic aviation – Long-range",
                "Domestic aviation – Short-range",
                "International aviation bunkers",
                "Non-energy use in transport",
                "Pipeline transport",
                "Losses",
                "Memo: Non-energy use in transport equipment",
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Transportation"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                [
                    "Road – 2&3-wheel",
                    "Road – Buses&Vans",
                    "Road – Light-duty vehicles",
                    "Road – Trucks",
                    "Rail – Heavy-duty",
                    "Rail – Light-duty",
                    "Transport not elsewhere specified",
                    "Domestic navigation",
                    "International marine bunkers",
                    "Domestic aviation – Long-range",
                    "Domestic aviation – Short-range",
                    "International aviation bunkers",
                    "Non-energy use in transport",
                    "Pipeline transport",
                    "Losses",
                    "Memo: Non-energy use in transport equipment",
                ],
            ]
            .loc[:, end_year]
            .groupby(["sector", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # For Transport
    fig = transport[transport.sum(axis=1) > 0.05].T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for flow_long in fig2["flow_long"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(flow_long)
                    .replace("Domestic navigation", "Shipping")
                    .replace("Domestic aviation", "Aviation")
                    .replace("Transport not elsewhere specified", "Other"),
                    line=dict(width=1, 
                    x=fig2[
                        (fig2["sector"] == sector) & (fig2["flow_long"] == flow_long)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector) & (fig2["flow_long"] == flow_long)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow_long) + ", ",
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow_long)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow_long)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow_long).replace("na", ""),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Projected Transport Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(title_text="% of 2050 Total Transport Energy Demand")

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-marketdata-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ######################################
    # PD INDEX, STACKED, BUILDINGS [%] # (V3)
    ######################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "product_long",
        "flow_long",
    ]  # 'sector',  'product_category', 'product_long', 'flow_long'

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
                model,
                scenario,
                region,
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )

    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")
    fig2["sector"] = "Buildings"

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in np.array(
            [
                "Municipal waste (renewable)",
                "Geothermal",
                "Solar thermal",
                "Electricity",
            ],
            dtype=object,
        ):

            for flow in fig2["flow_long"].unique():

                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=str(flow).replace(
                            "Commercial and public services", "Commercial"
                        )
                        + ", "
                        + str(product).replace("na", "All"),
                        line=dict(
                            width=1,
                        ),
                        x=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=str(flow).replace(
                            "Commercial and public services", "Commercial"
                        )
                        + ", "
                        + str(product).replace("na", "All"),
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=str(product).replace("na", ""),
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Projected Building Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(title_text="% of Total Building Energy Demand")

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #####################################
    # PD INDEX, STACKED, INDUSTRY [%] # (V4)
    #####################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "flow_long",
    ]  # 'sector',  'product_category', 'product_long', 'flow_long'

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
                "Machinery",
                "Non-ferrous metals",
                "Final consumption not elsewhere specified",
                "Food and tobacco",
                "Agriculture/forestry",
                "Non-metallic minerals",
                "Chemical and petrochemical",
                "Iron and steel",
                "Industry not elsewhere specified",
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
    ).sort_values(by=[2050], axis=0)

    industry_other = (
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
                "Paper, pulp, and print",
                "Fishing",
                "Wood and wood products",
                "Transport equipment",
                "Textile and leather",
                "Construction",
                "Mining and quarrying",
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector"])
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
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby("sector")
            .sum()
            .sum(0)
        )
        * 100
    )
    industry_other = pd.concat(
        [industry_other], keys=["Other"], names=["flow_long"]
    ).reorder_levels(["sector", "flow_long"])

    fig = pd.concat([industry, industry_other]).T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        if (fig2.columns.values == "flow_long").any():
            for flow in fig2["flow_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=flow,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector) & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=flow,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=flow,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_long").any():
            for product in fig2["product_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_category").any():
            for product in fig2["product_category"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-"
                    + str("-".join(groupby))
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ######################################
    # PD INDEX, STACKED, AGRICULTURE [%] # (V5)
    ######################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_long = slice(None)
    flow_category = slice(None)
    flow_long = slice(None)
    unit = slice(None)

    groupby = ["sector", "product_long"]

    # Percent of Agriculture land area that has adopted regenerative practices
    agriculture = afolu_output.loc[
        model, scenario, region, sector, product_long, flow_category, flow_long, unit
    ]

    fig = agriculture.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        if (fig2.columns.values == "flow_long").any():
            for flow in fig2["flow_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=flow,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector) & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=flow,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=flow,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_long").any():
            for product in fig2["product_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_category").any():
            for product in fig2["product_category"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-"
                    + str("-".join(groupby))
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ########################################
    # PD INDEX, STACKED, ELECTRICITY [TWh] # (V1)
    ########################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "product_category",
        "product_long",
    ]  # 'sector',  'product_category', 'product_long', 'flow_long'

    # Electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
    ).reindex(
        axis="index",
        level=2,
        labels=[
            "Nuclear",
            "Hydro",
            "Onshore wind energy",
            "Offshore wind energy",
            "Utility solar photovoltaics",
            "Rooftop solar photovoltaics",
            "Solar thermal",
            "Tide, wave and ocean",
            "Geothermal",
        ],
    ) * 0.0002778

    fig = pd.concat([electricity]).T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        if (fig2.columns.values == "flow_long").any():
            for flow in fig2["flow_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=flow,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector) & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=flow,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=flow,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_long").any():
            for product in fig2["product_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_category").any():
            for product in fig2["product_category"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TWh"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-"
                    + str("-".join(groupby))
                    + "-TJ"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ###########################################
    # PD INDEX, STACKED, TRANSPORTATION [TJ] # (V2)
    ###########################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Transportation"],
            product_category,
            slice(None),
            ["ELECTR", "HYDROGEN"],
            flow_category,
            [
                "Road – 2&3-wheel",
                "Road – Buses&Vans",
                "Road – Light-duty vehicles",
                "Road – Trucks",
                "Rail – Heavy-duty",
                "Rail – Light-duty",
                "Transport not elsewhere specified",
                "Domestic navigation",
                "International marine bunkers",
                "Domestic aviation – Long-range",
                "Domestic aviation – Short-range",
                "International aviation bunkers",
                "Non-energy use in transport",
                "Pipeline transport",
                "Losses",
                "Memo: Non-energy use in transport equipment",
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "flow_long"])
        .sum()
    )

    # For Transport
    fig = transport[transport.sum(axis=1) > 0.05].T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for flow_long in fig2["flow_long"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(flow_long)
                    .replace("Domestic navigation", "Shipping")
                    .replace("Domestic aviation", "Aviation")
                    .replace("Transport not elsewhere specified", "Other"),
                    line=dict(width=1, 
                    x=fig2[
                        (fig2["sector"] == sector) & (fig2["flow_long"] == flow_long)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector) & (fig2["flow_long"] == flow_long)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow_long) + ", ",
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow_long)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow_long)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow_long).replace("na", ""),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Total Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(title_text="TJ")

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-marketdata-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-TJ"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ######################################
    # PD INDEX, STACKED, BUILDINGS [TJ] # (V3)
    ######################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "product_long",
        "flow_long",
    ]  # 'sector',  'product_category', 'product_long', 'flow_long'

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
    )

    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")
    fig2["sector"] = "Buildings"

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in np.array(
            [
                "Municipal waste (renewable)",
                "Geothermal",
                "Solar thermal",
                "Electricity",
            ],
            dtype=object,
        ):

            for flow in fig2["flow_long"].unique():

                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=str(flow).replace(
                            "Commercial and public services", "Commercial"
                        )
                        + ", "
                        + str(product).replace("na", "All"),
                        line=dict(
                            width=1,
                        ),
                        x=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=str(flow).replace(
                            "Commercial and public services", "Commercial"
                        )
                        + ", "
                        + str(product).replace("na", "All"),
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=str(product).replace("na", ""),
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Total Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(title_text="TJ")

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-TJ"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #####################################
    # PD INDEX, STACKED, INDUSTRY [TJ] # (V4)
    #####################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    groupby = [
        "sector",
        "flow_long",
    ]  # 'sector',  'product_category', 'product_long', 'flow_long'

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
                "Machinery",
                "Non-ferrous metals",
                "Final consumption not elsewhere specified",
                "Food and tobacco",
                "Agriculture/forestry",
                "Non-metallic minerals",
                "Chemical and petrochemical",
                "Iron and steel",
                "Industry not elsewhere specified",
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(groupby)
        .sum()
    ).sort_values(by=[2050], axis=0)

    industry_other = (
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
                "Paper, pulp, and print",
                "Fishing",
                "Wood and wood products",
                "Transport equipment",
                "Textile and leather",
                "Construction",
                "Mining and quarrying",
            ],
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector"])
        .sum()
    )
    industry_other = pd.concat(
        [industry_other], keys=["Other"], names=["flow_long"]
    ).reorder_levels(["sector", "flow_long"])

    fig = pd.concat([industry, industry_other]).T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name=groupby, value_name="% Adoption")

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        if (fig2.columns.values == "flow_long").any():
            for flow in fig2["flow_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=flow,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector) & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=flow,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=flow,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_long").any():
            for product in fig2["product_long"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_long"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )
        elif (fig2.columns.values == "product_category").any():
            for product in fig2["product_category"].unique():
                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=product,
                        line=dict(
                            width=1,
                        ),
                        x=fig2["year"].unique(),
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=product,
                        showlegend=True,
                    )
                )

                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2["year"].unique()[fig2["year"].unique() <= data_end_year],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "TJ"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + "-"
                    + str("-".join(groupby))
                    + "-TJ"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ######################
    # PD INDEX BY SECTOR #
    ######################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category"])
            .sum()
            .sum(0)
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Transportation"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "flow_long"])
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
        .groupby(["sector", "product_category", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category", "flow_long"])
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
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # For Electricity
    fig = electricity.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category"],
        value_name="% Adoption",
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=product,
                    line=dict(
                        width=1,
                    ),
                    x=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=product,
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=product,
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-sector-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Transport
    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(flow),
                    line=dict(
                        width=1,
                    ),
                    x=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "year"
                    ],
                    y=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "% Adoption"
                    ],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow) + "-" + str(product).replace("na", "All"),
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-sector-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Buildings
    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()
    i = 0
    for product in fig2["product_category"].unique():

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(product) + "-" + str(flow),
                    line=dict(width=1),
                    x=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(product) + "-" + str(flow),
                    showlegend=True,
                )
            )
            i = i + 1
            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total Adoption, Buildings, "
            + str(region).replace("slice(None, None, None)", "World").capitalize()
            + ", "
            + str(scenario).capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "% Adoption"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/acurves-sector-"
                + scenario
                + "-"
                + str(region).replace("slice(None, None, None)", "World")
                + "-"
                + str("Buildings").replace("slice(None, None, None)", "All")
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    # For Industry
    fig = industry.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )
    i = 0

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():

            for flow in fig2["flow_long"].unique():

                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=str(product) + "-" + str(flow),
                        line=dict(width=1),
                        x=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=str(product) + "-" + str(flow),
                        showlegend=True,
                    )
                )
                i = i + 1
                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=str(flow),
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-sector-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ################################
    # PD INDEX BY PRODUCT CATEGORY #
    ################################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)

    product_category = slice(None)
    flow_category = slice(None)

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
            ],
            ["Electricity output"],
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category"])
            .sum()
            .sum(0)
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Transportation"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "flow_long"])
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
        .groupby(["sector", "product_category", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category", "flow_long"])
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
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # For Electricity
    fig = electricity.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category"],
        value_name="% Adoption",
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=product,
                    line=dict(
                        width=1,
                    ),
                    x=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=product,
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=product,
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-custom-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Transport
    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(flow),
                    line=dict(
                        width=1,
                    ),
                    x=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "year"
                    ],
                    y=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "% Adoption"
                    ],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow) + "-" + str(product).replace("na", "All"),
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-custom-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Buildings
    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()
    i = 0
    for product in fig2["product_category"].unique():

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(product) + "-" + str(flow),
                    line=dict(width=1),
                    x=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(product) + "-" + str(flow),
                    showlegend=True,
                )
            )
            i = i + 1
            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total Adoption, Buildings, "
            + str(region).replace("slice(None, None, None)", "World").capitalize()
            + ", "
            + str(scenario).capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "% Adoption"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/acurves-custom-"
                + scenario
                + "-"
                + str(region).replace("slice(None, None, None)", "World")
                + "-"
                + str("Buildings").replace("slice(None, None, None)", "All")
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    # For Industry
    fig = industry.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )
    i = 0

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():

            for flow in fig2["flow_long"].unique():

                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=str(product) + "-" + str(flow),
                        line=dict(width=1),
                        x=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=str(product) + "-" + str(flow),
                        showlegend=True,
                    )
                )
                i = i + 1
                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=str(flow),
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-sector-productcategory-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #######################
    # PD INDEX BY PRODUCT #
    #######################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)

    product_category = slice(None)
    flow_category = slice(None)

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
            ],
            ["Electricity output"],
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_long"])
            .sum()
            .sum(0)
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Transportation"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_long"])
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
        .rename(index={"Residential": "Buildings", "Commercial": "Buildings"})
        .groupby(["sector", "product_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .rename(index={"Residential": "Buildings", "Commercial": "Buildings"})
            .groupby(["sector", "product_long"])
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_long"])
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
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    fig = pd.concat([electricity, transport, buildings, industry]).T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_long"],
        value_name="% Adoption",
    )

    for vertical in fig2["sector"].unique():

        fig = go.Figure()

        for subvertical in fig2["product_long"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=subvertical,
                    line=dict(
                        width=1,,
                    ),
                    x=fig2[
                        (fig2["sector"] == vertical)
                        & (fig2["product_long"] == subvertical)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == vertical)
                        & (fig2["product_long"] == subvertical)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=subvertical,
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == vertical)
                        & (fig2["product_long"] == subvertical)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == vertical)
                        & (fig2["product_long"] == subvertical)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=subvertical,
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Adoption by Fuel Type, "
                + vertical
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        pio.write_html(
            fig,
            file=(
                "./charts/acurves-product-"
                + scenario
                + "-"
                + str(region).replace("slice(None, None, None)", "World")
                + "-"
                + str(vertical).replace("slice(None, None, None)", "All")
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    # endregion

    ####################
    # PD INDEX BY FLOW #
    ####################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)

    product_category = slice(None)
    flow_category = slice(None)

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            model,
            scenario,
            region,
            ["Electric Power"],
            product_category,
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category"])
            .sum()
            .sum(0)
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Transportation"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "flow_long"])
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
        .groupby(["sector", "product_category", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                model,
                scenario,
                region,
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
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
            slice(None),
        ]
        .loc[:, start_year:end_year]
        .groupby(["sector", "product_category", "flow_long"])
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
                slice(None),
            ]
            .loc[:, start_year:end_year]
            .groupby(["sector", "product_category", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # For Electricity
    fig = electricity.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category"],
        value_name="% Adoption",
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():
            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=product,
                    line=dict(
                        width=1,
                    ),
                    x=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=product,
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_category"] == product)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=product,
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-custom-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Transport
    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(flow),
                    line=dict(
                        width=1,
                    ),
                    x=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "year"
                    ],
                    y=fig2[(fig2["sector"] == sector) & (fig2["flow_long"] == flow)][
                        "% Adoption"
                    ],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow) + "-" + str(product).replace("na", "All"),
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-custom-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # For Buildings
    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()
    i = 0
    for product in fig2["product_category"].unique():

        for flow in fig2["flow_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(product) + "-" + str(flow),
                    line=dict(width=1),
                    x=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(product) + "-" + str(flow),
                    showlegend=True,
                )
            )
            i = i + 1
            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["product_category"] == product)
                        & (fig2["flow_long"] == flow)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(flow),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title={
            "text": "Percent of Total Adoption, Buildings, "
            + str(region).replace("slice(None, None, None)", "World").capitalize()
            + ", "
            + str(scenario).capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "% Adoption"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/acurves-custom-"
                + scenario
                + "-"
                + str(region).replace("slice(None, None, None)", "World")
                + "-"
                + str("Buildings").replace("slice(None, None, None)", "All")
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
        )

    # For Industry
    fig = industry.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "flow_long"],
        value_name="% Adoption",
    )
    i = 0

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_category"].unique():

            for flow in fig2["flow_long"].unique():

                # Make projected trace
                fig.add_trace(
                    go.Scatter(
                        name=str(product) + "-" + str(flow),
                        line=dict(width=1),
                        x=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        fill="tonexty",
                        stackgroup="two",
                        legendgroup=str(product) + "-" + str(flow),
                        showlegend=True,
                    )
                )
                i = i + 1
                # Make historical trace
                fig.add_trace(
                    go.Scatter(
                        name="Historical",
                        line=dict(width=1, color="#1c352d"),
                        x=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["year"],
                        y=fig2[
                            (fig2["year"] <= data_end_year)
                            & (fig2["sector"] == sector)
                            & (fig2["product_category"] == product)
                            & (fig2["flow_long"] == flow)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=str(flow),
                        showlegend=False,
                    )
                )

        fig.update_layout(
            title={
                "text": "Percent of Total Adoption, "
                + sector
                + ", "
                + str(region).replace("slice(None, None, None)", "World").capitalize()
                + ", "
                + str(scenario).capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "% Adoption"},
            margin_b=0,
            margin_t=20,
            margin_l=10,
            margin_r=10,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-sector-productcategory-flow-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ###############################################
    # PD INDEX, STACKED, W DATA OVERLAY [%] # (V2)
    ###############################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # For Transport
    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_long"],
        value_name="% Adoption",
    )

    for sector in fig2["sector"].unique():

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Make Units Shipped line for Sector = 'Transportation' , Product_long = 'Electricity' , Flow_long = 'Road'
        fig.add_trace(
            go.Scatter(
                name="EV Stock (RHS)",
                line=dict(width=1, color="#1c352d"),
                x=fig2["year"].unique(),
                y=adoption_historical.loc[:, start_year:end_year]
                .fillna(0)
                .groupby(["sector", "product_long", "flow_long"])
                .sum()
                .loc[sector, "Electricity", "Road"],
                fill="none",
                stackgroup="EV Stock",
                legendgroup="EV Stock",
                showlegend=True,
            ),
            secondary_y=True,
        )

        for product in fig2["product_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(product),
                    line=dict(width=1),
                    x=fig2[
                        (fig2["sector"] == sector) & (fig2["product_long"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector) & (fig2["product_long"] == product)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(product),
                    showlegend=True,
                ),
                secondary_y=False,
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_long"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_long"] == product)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(product),
                    showlegend=False,
                ),
                secondary_y=False,
            )

        fig.update_layout(
            title={
                "text": "Projected EV Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            yaxis=dict(range=[0, 110]),
            yaxis2=dict(range=[0, 6.6e8], dtick=7.2e8 / 6),
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(
            title_text="% of Total Vehicle Energy Demand", secondary_y=False
        )
        fig.update_yaxes(title_text="EV Stock", secondary_y=True)

        fig.add_annotation(
            text="<b>Historical EV stock data source:</b> IEA <br><b>Projected EV stock:</b> Positive Disruption model</br><b>Historical vehicle energy demand data source:</b> IEA <br><b>Projected vehicle energy demand:</b> Positive Disruption model",
            xref="paper",
            yref="paper",
            x=0,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=0,
            borderwidth=2,
            bgcolor="#ffffff",
            opacity=1,
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-marketdata-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ####################################################
    # PD INDEX, STACKED, W TOPLINE TOTAL EVS [%] # (V2)
    ####################################################

    # region

    start_year = 2010
    end_year = proj_end_year
    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # For Transport
    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_long"],
        value_name="% Adoption",
    )

    for sector in fig2["sector"].unique():

        fig = go.Figure()

        for product in fig2["product_long"].unique():

            # Make projected trace
            fig.add_trace(
                go.Scatter(
                    name=str(product),
                    line=dict(width=1),
                    x=fig2[
                        (fig2["sector"] == sector) & (fig2["product_long"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["sector"] == sector) & (fig2["product_long"] == product)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(product),
                    showlegend=True,
                )
            )

            # Make historical trace
            fig.add_trace(
                go.Scatter(
                    name="Historical",
                    line=dict(width=1, color="#1c352d"),
                    x=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_long"] == product)
                    ]["year"],
                    y=fig2[
                        (fig2["year"] <= data_end_year)
                        & (fig2["sector"] == sector)
                        & (fig2["product_long"] == product)
                    ]["% Adoption"],
                    stackgroup="one",
                    legendgroup=str(product),
                    showlegend=False,
                )
            )

        fig.update_layout(
            title={
                "text": "Projected EV Adoption, "
                + str(region).replace("slice(None, None, None)", "World").capitalize(),
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            margin_b=100,
            margin_t=20,
            margin_l=10,
            margin_r=10,
            legend={"traceorder": "reversed"},
        )

        fig.update_yaxes(title_text="% of Total Vehicle Energy Demand")

        fig.add_annotation(
            text="<b>Historical EV stock data source:</b> IEA <br><b>Projected EV stock:</b> Positive Disruption model</br><b>Historical vehicle energy demand data source:</b> IEA <br><b>Projected vehicle energy demand:</b> Positive Disruption model",
            xref="paper",
            yref="paper",
            x=0,
            y=-0.27,
            showarrow=False,
            font=dict(size=10, color="#2E3F5C"),
            align="left",
            borderpad=0,
            borderwidth=2,
            bgcolor="#ffffff",
            opacity=1,
        )

        # Make Units Shipped line for Sector = 'Transportation' , Product_long = 'Electricity' , Flow_long = 'Road'
        fig.add_trace(
            go.Scatter(
                name="EV Adoption",
                line=dict(width=2, color="#1c352d"),
                x=fig2["year"].unique(),
                y=fig2.groupby(["year"]).sum().squeeze(),
                fill="none",
                stackgroup="EV Stock",
                legendgroup="EV Stock",
                showlegend=True,
            )
        )

        if show_figs is True:
            fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/acurves-marketdata-"
                    + scenario
                    + "-"
                    + str(region).replace("slice(None, None, None)", "World")
                    + "-"
                    + str(sector).replace("slice(None, None, None)", "All")
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    # endregion

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
