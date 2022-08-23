# region

import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from numpy import NaN
import hvplot.pandas
import panel as pn
from plotly import graph_objects as go
from bokeh.resources import INLINE, CDN
import datapane as dp

from podi.curve_smooth import curve_smooth

show_figs = True
save_figs = True

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

    ######################
    # HISTORICAL ANALOGS #
    ######################

    # region

    # As percent of maximum value

    # region

    analog = pd.read_csv(
        "podi/data/external/CHATTING_SPLICED.csv",
        usecols=["label", "iso3c", "year", "value"],
    )

    labels = [
        "Combine harvesters - threshers in use",
        "Land agricultural land area 1000 ha",
        "Agricultural tractors in use",
        "Total vehicles (OICA)",
        "Aluminum primary production, in metric tons",
        "Land arable land area 1000 ha",
        "ATMs",
        "Air transport, passengers carried",
        "Civil aviation passenger-KM traveled",
        "Civil aviation ton-KM of cargo carried",
        "Households that subscribe to cable",
        "Cellular subscriptions",
        "Personal computers",
        "Electricity from coal (TWH)",
        "Electric power consumption (KWH)",
        "Electricity from gas (TWH)",
        "Electricity from hydro (TWH)",
        "Electricity from nuclear (TWH)",
        "Electricity from oil (TWH)",
        "Electricity from other renewables (TWH)",
        "Electricity from solar (TWH)",
        "Electricity from wind (TWH)",
        "Gross output of electric energy (TWH)",
        "Electricity Generating Capacity, 1000 kilowatts",
        "Fertilizer ammonium nitrate (AN) agricultural use tonnes",
        "Fertilizer ammonium sulphate agricultural use tonnes",
        "Fertilizer diammonium phosphate (DAP) agricultural use tonnes",
        "Fertilizer potassium chloride (muriate of potash) (MOP) agricultural use tonnes",
        "Fertilizer NPK fertilizers agricultural use tonnes",
        "Fertilizer other NP compounds agricultural use tonnes",
        "Fertilizer superphosphates above 35 percent agricultural use tonnes",
        "Fertilizer potassium sulphate (sulphate of potash) (SOP) agricultural use tonnes",
        "Aggregate kg of fertilizer consumed",
        "Fertilizer urea agricultural use tonnes",
        "Land naturally regenerating forest area 1000 ha",
        "Land planted forest area 1000 ha",
        "People with internet access",
        "Area equipped to provide water to crops",
        "Automatic looms",
        "Ordinary and automatic looms",
        "Items mailed or received",
        "% Arable land share in agricultural land",
        "% Irrigated area as a share of cultivated land",
        "Pesticide fungicides and bactericides agricultural use tonnes",
        "Pesticide herbicides agricultural use tonnes",
        "Pesticide insecticides agricultural use tonnes",
        "Pesticide mineral oils agricultural use tonnes",
        "Pesticide other pesticides nes agricultural use tonnes",
        "Pesticide rodenticides agricultural use tonnes",
        "Total metric tons of pesticides in agricultural use",
        "Radios",
        "Geographical/route lengths of line open at the end of the year",
        "Rail lines (total route-km)",
        "Thousands of passenger journeys by railway",
        "Passenger journeys by railway (passenger-km)",
        "Metric tons of freight carried on railways (excluding livestock and passenger baggage)",
        "Freight carried on railways (excluding livestock and passenger baggage) (ton-km)",
        "Length of Paved Road (km)",
        "Secure internet servers",
        "Ships of all kinds",
        "Tonnage of ships of all kinds",
        "Tonnage of sail ships",
        "Tonnage of steam ships",
        "Tonnage of steam and motor ships",
        "Mule spindles",
        "Ring spindles",
        "Steel demand in thousand metric tons",
        "Steel production in thousand metric tons",
        "Stainless steel production",
        "Telegrams",
        "Fixed telephone subscriptions",
        "Television sets",
        "Weight of artificial fibers in spindles",
        "Weight of other fibers in spindles",
        "Weight of synthetic fibers in spindles",
        "Weight of all fibers in spindles",
        "Passenger car vehicles",
        "Passenger cars (BTS)",
        "Commercial vehicles (bus, taxi)",
        "Commercial vehicles (BTS)",
        "Total vehicles (BTS)",
    ]

    def percent_change(x):
        xnew = (
            x.value
            / analog[(analog.label == x.label) & (analog.iso3c == x.iso3c)].value.max()
        ) * 100
        x.value = xnew
        return x

    analog = analog[(analog.iso3c == "USA") & (analog.label.isin(labels))].apply(
        percent_change, axis=1
    )

    fig = go.Figure()

    for label in analog["label"].unique():

        # Make modeled trace
        fig.add_trace(
            go.Scatter(
                name=label,
                line=dict(width=1),
                mode="lines",
                x=analog[(analog["label"] == label)]["year"].unique(),
                y=analog[(analog["label"] == label)]["value"],
                legendgroup=label,
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Historical Analogs",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "% of max"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend=dict(yanchor="top", y=-0.1, xanchor="left", x=0.01),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list(
                    [
                        dict(
                            args=[{"yaxis.type": "linear"}],
                            label="LINEAR",
                            method="relayout",
                        ),
                        dict(
                            args=[{"yaxis.type": "log"}], label="LOG", method="relayout"
                        ),
                    ]
                ),
            )
        ]
    )

    fig.show()

    pio.write_html(
        fig,
        file=("./charts/historicalanalogs-percent.html").replace(" ", ""),
        auto_open=False,
    )

    # endregion

    # As absolute value

    # region

    analog = pd.read_csv(
        "podi/data/external/CHATTING_SPLICED.csv",
        usecols=["label", "iso3c", "year", "value"],
    )

    analog = analog[(analog.iso3c == "USA") & (analog.label.isin(labels))]

    fig = go.Figure()

    for label in analog["label"].unique():

        # Make modeled trace
        fig.add_trace(
            go.Scatter(
                name=label,
                line=dict(width=1),
                mode="lines",
                x=analog[(analog["label"] == label)]["year"].unique(),
                y=analog[(analog["label"] == label)]["value"],
                legendgroup=label,
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Historical Analogs",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "various"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend=dict(yanchor="top", y=-0.1, xanchor="left", x=0.01),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list(
                    [
                        dict(
                            args=[{"yaxis.type": "linear"}],
                            label="LINEAR",
                            method="relayout",
                        ),
                        dict(
                            args=[{"yaxis.type": "log"}], label="LOG", method="relayout"
                        ),
                    ]
                ),
            )
        ]
    )

    fig.show()

    pio.write_html(
        fig,
        file=("./charts/historicalanalogs-absolutevalue.html").replace(" ", ""),
        auto_open=False,
    )

    # endregion

    # As percent change

    # region

    analog = pd.read_csv(
        "podi/data/external/CHATTING_SPLICED.csv",
        usecols=["label", "iso3c", "year", "value"],
    )

    analog = analog[(analog.iso3c == "USA") & (analog.label.isin(labels))]

    fig = go.Figure()

    for label in analog["label"].unique():

        # Make modeled trace
        fig.add_trace(
            go.Scatter(
                name=label,
                line=dict(width=1),
                mode="lines",
                x=analog[(analog["label"] == label)]["year"].unique(),
                y=analog[(analog["label"] == label)]["value"].pct_change() * 100,
                legendgroup=label,
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Historical Analogs",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "%"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend=dict(yanchor="top", y=-0.1, xanchor="left", x=0.01),
    )

    # Add Linear and Log buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list(
                    [
                        dict(
                            args=[{"yaxis.type": "linear"}],
                            label="LINEAR",
                            method="relayout",
                        ),
                        dict(
                            args=[{"yaxis.type": "log"}], label="LOG", method="relayout"
                        ),
                    ]
                ),
            )
        ]
    )

    fig.show()

    pio.write_html(
        fig,
        file=("./charts/historicalanalogs-percentchange.html").replace(" ", ""),
        auto_open=False,
    )

    # endregion

    # endregion

    ##########################
    #  MARKET ADOPTION DATA  #
    ##########################

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

    ##############
    #  PD INDEX  #
    ##############

    # region

    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_category", "product_long"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
                ["Electric Power"],
                product_category,
                slice(None),
                slice(None),
                ["Electricity output"],
            ]
            .loc[:, data_start_year:proj_end_year]
            .groupby(["sector", "product_category", "product_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
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
            .loc[:, proj_end_year]
            .groupby(["sector", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of buildings energy that is electric or nonelectric renewables
    buildings = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
            ["Commercial", "Residential"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            flow_category,
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
                ["Commercial", "Residential"],
                product_category,
                slice(None),
                slice(None),
                slice(None),
                slice(None),
            ]
            .loc[:, data_start_year:proj_end_year]
            .groupby(["sector", "product_long", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    )

    # Percent of industry energy that is electric or nonelectric renewables
    industry = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "flow_long"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
                ["Industrial"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .loc[:, data_start_year:proj_end_year]
            .groupby(["sector", "flow_long"])
            .sum()
            .sum(0)
        )
        * 100
    ).sort_values(by=[2050], axis=0)

    industry_other = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector"])
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
                ["Industrial"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
                slice(None),
            ]
            .loc[:, data_start_year:proj_end_year]
            .groupby("sector")
            .sum()
            .sum(0)
        )
        * 100
    )
    industry_other = pd.concat(
        [industry_other], keys=["Other"], names=["flow_long"]
    ).reorder_levels(["sector", "flow_long"])

    industry = pd.concat([industry, industry_other])

    # Percent of agriculture mitigation compared to max extent
    agriculture = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Agriculture"]]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long"])
        .sum()
        .apply(
            lambda x: x.divide(
                afolu_output.loc[slice(None), scenario, slice(None), ["Agriculture"]]
                .loc[:, data_start_year:proj_end_year]
                .groupby(["sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ),
            axis=1,
        )
        * 100
    )

    # Percent of forests & wetlands mitigation compared to max extent
    forestswetlands = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Forests & Wetlands"]]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long"])
        .sum()
        .apply(
            lambda x: x.divide(
                afolu_output.loc[
                    slice(None), scenario, slice(None), ["Forests & Wetlands"]
                ]
                .loc[:, data_start_year:proj_end_year]
                .groupby(["sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ),
            axis=1,
        )
        * 100
    )

    # Percent of cdr sequestration compared to max extent
    """
    cdr = (
        cdr_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .groupby(groupby)
        .sum()
        .divide(
            energy_output.loc[
                slice(None),
                scenario,
                slice(None),
                ["CDR"],
                product_category,
                slice(None),
                slice(None),
                "Final consumption",
            ]
            .groupby(groupby)
            .sum()
            .sum(0)
        )
        * 100
    )
    """

    # Combine all verticals
    pdindex_output = pd.concat(
        [
            electricity,
            transport,
            buildings,
            industry,
            agriculture,
            forestswetlands,
            # "cdr",
        ]
    )

    # Plot pdindex_output
    # region

    ######################################
    # PD INDEX, STACKED, ELECTRICITY [%] #
    ######################################

    # region

    model = "PD22"
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    fig = electricity.reindex(
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
    ).T

    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_category", "product_long"],
        value_name="% Adoption",
    )

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
            xaxis={"range": [data_start_year, proj_end_year]},
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
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #########################################
    # PD INDEX, STACKED, TRANSPORTATION [%] #
    #########################################

    # region
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
                    line=dict(width=1),
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
                ),
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
            xaxis={"range": [data_start_year, proj_end_year]},
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

    ####################################
    # PD INDEX, STACKED, BUILDINGS [%] #
    ####################################

    # region
    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["sector", "product_long", "flow_long"],
        value_name="% Adoption",
    )
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

    ###################################
    # PD INDEX, STACKED, INDUSTRY [%] #
    ###################################

    # region
    fig = industry.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig, id_vars="year", var_name=["sector", "flow_long"], value_name="% Adoption"
    )

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
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ######################################
    # PD INDEX, STACKED, AGRICULTURE [%] #
    ######################################

    # region
    fig = agriculture.T
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
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #############################################
    # PD INDEX, STACKED, FORESTS & WETLANDS [%] #
    #############################################

    # region
    fig = forestswetlands.T
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
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ########################################
    # PD INDEX, STACKED, ELECTRICITY [TWh] #
    ########################################

    # region

    data_start_year = data_start_year
    proj_end_year = proj_end_year
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
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
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
    )

    fig = electricity.T * 0.0002778
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

    ##########################################
    # PD INDEX, STACKED, TRANSPORTATION [TJ] #
    ##########################################

    # region

    start_year = 2010
    end_year = proj_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
                    line=dict(width=1),
                    x=fig2["year"].unique(),
                    y=fig2[
                        (fig2["sector"] == sector) & (fig2["flow_long"] == flow_long)
                    ]["% Adoption"],
                    fill="tonexty",
                    stackgroup="two",
                    legendgroup=str(flow_long),
                    showlegend=True,
                ),
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

    #####################################
    # PD INDEX, STACKED, BUILDINGS [TJ] #
    #####################################

    # region

    data_start_year = 2010
    proj_end_year = proj_end_year
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
            slice(None),
            scenario,
            slice(None),
            ["Commercial", "Residential"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            flow_category,
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .loc[:, data_start_year:proj_end_year]
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

    ####################################
    # PD INDEX, STACKED, INDUSTRY [TJ] #
    ####################################

    # region

    data_start_year = data_start_year
    proj_end_year = proj_end_year
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
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
        .groupby(groupby)
        .sum()
    ).sort_values(by=[2050], axis=0)

    industry_other = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .loc[:, data_start_year:proj_end_year]
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

    ########################################
    # PD INDEX, STACKED, AGRICULTURE [MHA] #
    ########################################

    # region

    agriculture = curve_smooth(
        afolu_output.loc[slice(None), scenario, slice(None), ["Agriculture"]]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long"])
        .sum(),
        "quadratic",
        29,
    )

    fig = agriculture.T
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
            yaxis={"title": "MHa"},
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
                    + "-MHA"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ###############################################
    # PD INDEX, STACKED, FORESTS & WETLANDS [MHA] #
    ###############################################

    # region

    forestswetlands = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Forests & Wetlands"]]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long"])
        .sum()
    )

    fig = forestswetlands.T
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
            yaxis={"title": "MHA"},
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
                    + "-MHA"
                    + ".html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    #########################################
    # PD INDEX, STACKED, W DATA OVERLAY [%] #
    #########################################

    # region

    data_start_year = 2010
    proj_end_year = proj_end_year
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
                y=adoption_historical.loc[:, data_start_year:proj_end_year]
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

    ##############################################
    # PD INDEX, STACKED, W TOPLINE TOTAL EVS [%] #
    ##############################################

    # region

    data_start_year = 2010
    proj_end_year = proj_end_year
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

    ###########################
    #  FIND PD INDEX LEADERS  #
    ###########################

    # region

    ###############################
    # PD INDEX, ELECTRICITY [TJ] #
    ###############################

    # region

    start_year = data_start_year
    end_year = proj_end_year
    df = energy_output
    scenario = "pathway"
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    electricity = (
        df.loc[
            slice(None),
            scenario,
            slice(None),
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
        .groupby(["region", "sector", "product_category", "product_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    electricity_sorted = (
        electricity.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    electricity = electricity.reindex(electricity_sorted.index)

    fig = electricity.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "product_category", "product_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()

    for index in (
        fig2[["region", "sector", "product_category", "product_long"]]
        .drop_duplicates()
        .index
    ):
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["product_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["product_long"] == fig2.iloc[index]["product_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["product_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Electricity"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "TJ"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [start_year, end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-" + scenario + "-" + "Electricity" + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

    # endregion

    ################################
    # PD INDEX,TRANSPORTATION [TJ] #
    ################################

    # region

    start_year = data_start_year
    end_year = data_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    transport = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .groupby(["region", "sector", "flow_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    transport_sorted = (
        transport.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    transport = transport.reindex(transport_sorted.index)

    fig = transport.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "flow_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()

    for index in fig2[["region", "sector", "flow_long"]].drop_duplicates().index:
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["flow_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["flow_long"] == fig2.iloc[index]["flow_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["flow_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Transportation"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "TJ"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [data_start_year, data_end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-" + scenario + "-" + "Transportation" + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

    # endregion

    ############################
    # PD INDEX, BUILDINGS [TJ] #
    ############################

    # region

    start_year = data_start_year
    end_year = data_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    buildings = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
            ["Commercial", "Residential"],
            product_category,
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            flow_category,
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .loc[:, start_year:end_year]
        .groupby(["region", "sector", "product_long", "flow_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    buildings_sorted = (
        buildings.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    buildings = buildings.reindex(buildings_sorted.index)

    fig = buildings.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "product_long", "flow_long"],
        value_name="% Adoption",
    )
    fig2["sector"] = "Buildings"

    fig = go.Figure()

    for index in (
        fig2[["region", "sector", "product_long", "flow_long"]].drop_duplicates().index
    ):
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["product_long"]
                + ", "
                + fig2.iloc[index]["flow_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["product_long"] == fig2.iloc[index]["product_long"])
                    & (fig2["flow_long"] == fig2.iloc[index]["flow_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["product_long"]
                + ", "
                + fig2.iloc[index]["flow_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Buildings"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "TJ"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [start_year, end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-" + scenario + "-" + "Buildings" + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

    # endregion

    ###########################
    # PD INDEX, INDUSTRY [TJ] #
    ###########################

    # region

    start_year = data_start_year
    end_year = data_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    industry = (
        energy_output.loc[
            slice(None),
            scenario,
            slice(None),
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
        .groupby(["region", "sector", "flow_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    industry_sorted = (
        industry.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    industry = industry.reindex(industry_sorted.index)

    fig = industry.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "flow_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()

    for index in fig2[["region", "sector", "flow_long"]].drop_duplicates().index:
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["flow_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["flow_long"] == fig2.iloc[index]["flow_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["flow_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Industry"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "TJ"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [start_year, end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-" + scenario + "-" + "Industry" + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

    # endregion

    ###############################
    # PD INDEX, AGRICULTURE [MHA] #
    ###############################

    # region

    start_year = data_start_year
    end_year = data_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    agriculture = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Agriculture"]]
        .loc[:, start_year:end_year]
        .groupby(["region", "sector", "product_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    agriculture_sorted = (
        agriculture.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    agriculture = agriculture.reindex(agriculture_sorted.index)

    fig = agriculture.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "product_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()

    for index in fig2[["region", "sector", "product_long"]].drop_duplicates().index:
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["product_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["product_long"] == fig2.iloc[index]["product_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["product_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Agriculture"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "Mha"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [start_year, end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-" + scenario + "-" + "Agriculture" + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

    # endregion

    ######################################
    # PD INDEX, FORESTS & WETLANDS [MHA] #
    ######################################

    # region

    start_year = data_start_year
    end_year = data_end_year
    scenario = scenario
    region = slice(None)
    sector = slice(None)
    product_category = slice(None)
    flow_category = slice(None)

    forestswetlands = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Forests & Wetlands"]]
        .loc[:, start_year:end_year]
        .groupby(["region", "sector", "product_long"])
        .sum()
    )

    # Sort by slope from first nonzero year to data_end_year
    forestswetlands_sorted = (
        forestswetlands.replace(0, NaN)
        .dropna(how="all")
        .apply(
            lambda x: (
                x.replace(0, NaN)[x.replace(0, NaN).last_valid_index()]
                - x.replace(0, NaN)[x.replace(0, NaN).first_valid_index()]
            )
            / (
                x.replace(0, NaN).last_valid_index()
                - x.replace(0, NaN).first_valid_index()
            ),
            axis=1,
        )
        .fillna(0)
        .to_frame()
        .sort_values(0, ascending=True)
    )

    forestswetlands = forestswetlands.reindex(forestswetlands_sorted.index)

    fig = forestswetlands.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region", "sector", "product_long"],
        value_name="% Adoption",
    )

    fig = go.Figure()

    for index in fig2[["region", "sector", "product_long"]].drop_duplicates().index:
        # Make projected trace
        fig.add_trace(
            go.Scatter(
                name=fig2.iloc[index]["region"].capitalize()
                + ", "
                + fig2.iloc[index]["product_long"],
                line=dict(
                    width=1,
                ),
                x=fig2["year"].unique(),
                y=fig2[
                    (fig2["region"] == fig2.iloc[index]["region"])
                    & (fig2["product_long"] == fig2.iloc[index]["product_long"])
                ]["% Adoption"],
                legendgroup=fig2.iloc[index]["region"]
                + ", "
                + fig2.iloc[index]["product_long"],
                showlegend=True,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Adoption, "
            + "Forests & Wetlands"
            + ", "
            + "All Countries"
            + ", "
            + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 1,
        },
        yaxis={"title": "Mha"},
        margin_b=0,
        margin_t=20,
        margin_l=10,
        margin_r=10,
        legend={"traceorder": "reversed"},
        xaxis={"range": [start_year, end_year]},
    )

    if show_figs is True:
        fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=(
                "./charts/pdindexleaders-"
                + scenario
                + "-"
                + "Forests&wetlands"
                + ".html"
            ).replace(" ", ""),
            auto_open=True,
        )

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

    #####################################
    # GHG EMISSIONS MITIGATION BARCHART #
    #####################################

    # region

    ndcs = [
        [(2030, 2050), (24, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [
            (2030, 2050),
            (3.32, 0),
            (
                "determined through linear extrapolation using the<br>U.S’s 2005 emissions and the NDC set in 2015, which set an emissions goal for 2025.",
                "of net zero emissions, <br>which was set in President Biden’s climate plan.",
            ),
        ],
        (0, 0),
        [
            (2030, 2050),
            (0.94, 0),
            (
                "set in Brazil’s 2015 NDC.",
                "determined through linear extrapolation using Brazil’s 2025 and <br>2030 emissions goals set in their 2015 NDC.",
            ),
        ],
        [(2030, 2050), (2.4, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [
            (2030, 2050),
            (0.398, 0),
            (
                "set in South Africa’s 2015 NDC.",
                "determined through linear extrapolation using South Africa’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030. South Africa submitted a Low Emission <br>Development Scenario in 2020, but the scenario does not specify a 2050 emissions goal.",
            ),
        ],
        (0, 0),
        [
            (2030, 2050),
            (2.17, 0),
            (
                "set in Russia’s 2015 NDC.",
                "determined through linear extrapolation using Russia’s 1990 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030.",
            ),
        ],
        (0, 0),
        [
            (2030, 2050),
            (12.96, 0),
            (
                "determined by China’s 2020<br>NDC update to peak emissions before 2030.",
                "of net zero emissions, which<br>was announced by President Xi Jinping in September 2020.",
            ),
        ],
        [
            (2030, 2050),
            (9.14, 0),
            (
                "set in India’s 2015 NDC.",
                "determined through linear extrapolation using India’s 2017 emissions <br>and the NDC set in 2015, which set an emissions goal for 2030.",
            ),
        ],
        [
            (2030, 2050),
            (1, 0),
            (
                "set in Japan’s 2015 NDC.",
                "of net zero emissions, which was announced in Prime Minister Yoshihide <br>Suga's speech on October 26th, 2020.",
            ),
        ],
        (0, 0),
        (0, 0),
    ]

    ipcc = [
        [(2030, 2050), (24, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [(2030, 2050), (2.99, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [(2030, 2050), (0.69, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        [(2030, 2050), (2.39, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [(2030, 2050), (0.26, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [(2030, 2050), (1.02, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        [(2030, 2050), (12, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        [(2030, 2050), (1.75, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        [(2030, 2050), (0.55, 0), ("of 50% by 2030.", "of Net-zero by 2050.")],
        (0, 0),
        (0, 0),
    ]

    scenario = "pathway"

    for year in [2030, 2050]:
        for i in range(0, len(region_list)):
            em_mit_electricity = em_mitigated.loc[
                region_list[i], "Electricity", slice(None)
            ].sum()

            em_mit_transport = em_mitigated.loc[
                region_list[i], "Transport", slice(None)
            ].sum()

            em_mit_buildings = em_mitigated.loc[
                region_list[i], "Buildings", slice(None)
            ].sum()

            em_mit_industry = em_mitigated.loc[
                region_list[i], "Industry", slice(None)
            ].sum()

            em_mit_ra = em_mitigated.loc[
                region_list[i], "Agriculture", slice(None), slice(None)
            ].sum()

            em_mit_fw = em_mitigated.loc[
                region_list[i], "Forests & Wetlands", slice(None), slice(None)
            ].sum()

            if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:
                em_mit_cdr = (
                    pd.Series(
                        cdr.loc[region_list[i], "Carbon Dioxide Removal", scenario],
                        index=np.arange(data_start_year, long_proj_end_year + 1),
                    )
                ).rename(index="Unnamed 6")

                em_mit = pd.DataFrame(
                    [
                        em_mit_electricity,
                        em_mit_transport,
                        em_mit_buildings,
                        em_mit_industry,
                        em_mit_ra,
                        em_mit_fw,
                        em_mit_cdr,
                    ]
                ).rename(
                    index={
                        "Unnamed 0": "V1: Electricity",
                        "Unnamed 1": "V2: Transport",
                        "Unnamed 2": "V3: Buildings",
                        "Unnamed 3": "V4: Industry",
                        "Unnamed 4": "V5: Agriculture",
                        "Unnamed 5": "V6: Forests & Wetlands",
                        "Unnamed 6": "V7: CDR",
                    }
                )
                fig = (
                    ((em_mit) / 1000)
                    .reindex(
                        [
                            "V7: CDR",
                            "V6: Forests & Wetlands",
                            "V5: Agriculture",
                            "V4: Industry",
                            "V3: Buildings",
                            "V2: Transport",
                            "V1: Electricity",
                        ]
                    )
                    .round(decimals=4)
                    .clip(lower=0)
                )
                data = {
                    "V1: Electricity": [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V1: Electricity", year],
                        fig.loc["V1: Electricity", year],
                    ],
                    "V2: Transport": [
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V2: Transport", year],
                        0,
                        fig.loc["V2: Transport", year],
                    ],
                    "V3: Buildings": [
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V3: Buildings", year],
                        0,
                        0,
                        fig.loc["V3: Buildings", year],
                    ],
                    "V4: Industry": [
                        0,
                        0,
                        0,
                        fig.loc["V4: Industry", year],
                        0,
                        0,
                        0,
                        fig.loc["V4: Industry", year],
                    ],
                    "V5: Agriculture": [
                        0,
                        0,
                        fig.loc["V5: Agriculture", year],
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V5: Agriculture", year],
                    ],
                    "V6: Forests & Wetlands": [
                        0,
                        fig.loc["V6: Forests & Wetlands", year],
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V6: Forests & Wetlands", year],
                    ],
                    "V7: CDR": [
                        fig.loc["V7: CDR", year],
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V7: CDR", year],
                    ],
                    "Total": [
                        fig.loc["V7: CDR", year],
                        fig.loc["V6: Forests & Wetlands", year],
                        fig.loc["V5: Agriculture", year],
                        fig.loc["V4: Industry", year],
                        fig.loc["V3: Buildings", year],
                        fig.loc["V2: Transport", year],
                        fig.loc["V1: Electricity", year],
                        0,
                    ],
                    "labels": [
                        "V7: CDR",
                        "V6: Forests & Wetlands",
                        "V5: Agriculture",
                        "V4: Industry",
                        "V3: Buildings",
                        "V2: Transport",
                        "V1: Electricity",
                        "Total",
                    ],
                }
            else:
                em_mit = pd.DataFrame(
                    [
                        em_mit_electricity,
                        em_mit_transport,
                        em_mit_buildings,
                        em_mit_industry,
                        em_mit_ra,
                        em_mit_fw,
                    ]
                ).rename(
                    index={
                        0: "V1: Electricity",
                        1: "V2: Transport",
                        2: "V3: Buildings",
                        3: "V4: Industry",
                        4: "V5: Agriculture",
                        5: "V6: Forests & Wetlands",
                    }
                )
                fig = (
                    ((em_mit) / 1000)
                    .reindex(
                        [
                            "V6: Forests & Wetlands",
                            "V5: Agriculture",
                            "V4: Industry",
                            "V3: Buildings",
                            "V2: Transport",
                            "V1: Electricity",
                        ]
                    )
                    .round(decimals=4)
                    .clip(lower=0)
                )
                data = {
                    "V1: Electricity": [
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V1: Electricity", year],
                        fig.loc["V1: Electricity", year],
                    ],
                    "V2: Transport": [
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V2: Transport", year],
                        0,
                        fig.loc["V2: Transport", year],
                    ],
                    "V3: Buildings": [
                        0,
                        0,
                        0,
                        fig.loc["V3: Buildings", year],
                        0,
                        0,
                        fig.loc["V3: Buildings", year],
                    ],
                    "V4: Industry": [
                        0,
                        0,
                        fig.loc["V4: Industry", year],
                        0,
                        0,
                        0,
                        fig.loc["V4: Industry", year],
                    ],
                    "V5: Agriculture": [
                        0,
                        fig.loc["V5: Agriculture", year],
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V5: Agriculture", year],
                    ],
                    "V6: Forests & Wetlands": [
                        fig.loc["V6: Forests & Wetlands", year],
                        0,
                        0,
                        0,
                        0,
                        0,
                        fig.loc["V6: Forests & Wetlands", year],
                    ],
                    "Total": [
                        fig.loc["V6: Forests & Wetlands", year],
                        fig.loc["V5: Agriculture", year],
                        fig.loc["V4: Industry", year],
                        fig.loc["V3: Buildings", year],
                        fig.loc["V2: Transport", year],
                        fig.loc["V1: Electricity", year],
                        0,
                    ],
                    "labels": [
                        "V6: Forests & Wetlands",
                        "V5: Agriculture",
                        "V4: Industry",
                        "V3: Buildings",
                        "V2: Transport",
                        "V1: Electricity",
                        "Total",
                    ],
                }

            em_mit.loc[:, :2020] = 0
            opacity = 0.5

            if year == 2030:
                j = 0
            else:
                j = 1

            if region_list[i] in ["World ", "US ", "CHINA ", "EUR "]:

                figure = go.Figure(
                    data=[
                        go.Bar(
                            y=data["labels"],
                            x=data["V7: CDR"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#FF9DA6",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V6: Forests & Wetlands"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#54A24B",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V5: Agriculture"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#EECA3B",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V4: Industry"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#60738C",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V3: Buildings"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#F58518",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V2: Transport"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#7AA8B8",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V1: Electricity"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#B279A2",
                            opacity=opacity,
                        ),
                    ]
                )

                # IPCC target line
                figure.add_shape(
                    type="line",
                    x0=pd.Series(data["Total"]).sum(),
                    y0=-0.5,
                    x1=pd.Series(data["Total"]).sum(),
                    y1=7.5,
                    line=dict(color="LightSeaGreen", width=3, dash="dot"),
                    name="NDC",
                )

                figure.add_annotation(
                    text="The blue dotted line represents an emissions mitigation goal "
                    + ipcc[i][2][j],
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1.16,
                    showarrow=False,
                    font=dict(size=10, color="#2E3F5C"),
                    align="left",
                    borderpad=4,
                    bgcolor="#ffffff",
                    opacity=1,
                )

                # NDC target line
                if region_list[i] in ["US ", "CHINA "]:

                    figure.add_shape(
                        type="line",
                        x0=(
                            pd.Series(
                                em_baseline.groupby("region")
                                .sum()
                                .loc[region_list[i]][year]
                                / 1e3
                                - ndcs[i][1][j]
                            ).values[0]
                        ).clip(min=0),
                        y0=-0.5,
                        x1=(
                            pd.Series(
                                em_baseline.groupby("region")
                                .sum()
                                .loc[region_list[i]][year]
                                / 1e3
                                - ndcs[i][1][j]
                            ).values[0]
                        ).clip(min=0),
                        y1=7.5,
                        line=dict(color="green", width=3, dash="dot"),
                        name="NDC",
                    )

                    figure.add_annotation(
                        text="The blue dotted line represents an emissions mitigation goal "
                        + ipcc[i][2][j]
                        + "<br>The green dotted line represents an emissions mitigation goal "
                        + ndcs[i][2][j],
                        xref="paper",
                        yref="paper",
                        x=0,
                        y=1.2,
                        showarrow=False,
                        font=dict(size=10, color="#2E3F5C"),
                        align="left",
                        borderpad=4,
                        bgcolor="#ffffff",
                        opacity=1,
                    )

            else:
                figure = go.Figure(
                    data=[
                        go.Bar(
                            y=data["labels"],
                            x=data["V6: Forests & Wetlands"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#54A24B",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V5: Agriculture"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#EECA3B",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V4: Industry"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#60738C",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V3: Buildings"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#F58518",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V2: Transport"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#7AA8B8",
                            opacity=opacity,
                        ),
                        go.Bar(
                            y=data["labels"],
                            x=data["V1: Electricity"],
                            offsetgroup=0,
                            orientation="h",
                            marker_color="#B279A2",
                            opacity=opacity,
                        ),
                    ]
                )

            # IPCC & NDC target lines & (year == 2030)
            if region_list[i] in [
                "SAFR ",
                "RUS ",
                "JPN ",
                "BRAZIL ",
                "INDIA ",
            ]:
                figure.add_shape(
                    type="line",
                    x0=(
                        pd.Series(
                            em_baseline.groupby("region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ndcs[i][1][j]
                        ).values[0]
                    ).clip(min=0),
                    y0=-0.5,
                    x1=(
                        pd.Series(
                            em_baseline.groupby("region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ndcs[i][1][j]
                        ).values[0]
                    ).clip(min=0),
                    y1=6.5,
                    line=dict(color="green", width=3, dash="dot"),
                    name="NDC",
                )

                figure.add_annotation(
                    text="The green dotted line represents an emissions mitigation goal "
                    + ndcs[i][2][j]
                    + "<br>The blue dotted line represents an emissions mitigation goal of 50% emissions reduction by 2030",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=1.16,
                    showarrow=False,
                    font=dict(size=10, color="#2E3F5C"),
                    align="left",
                    borderpad=4,
                    bgcolor="#ffffff",
                    opacity=1,
                )

                figure.add_shape(
                    type="line",
                    x0=em_hist.loc[region_list[i], 2019].values[0] / 2000,
                    y0=-0.5,
                    x1=em_hist.loc[region_list[i], 2019].values[0] / 2000,
                    y1=6.5,
                    line=dict(color="LightSeaGreen", width=3, dash="dot"),
                    name="NDC",
                )

            # EI
            if region_list[i] in [
                "World ",
                "US ",
                "CHINA ",
                "EUR ",
                "SAFR ",
                "RUS ",
                "JPN ",
                "BRAZIL ",
                "INDIA ",
            ]:

                #  & (year == 2030)
                if region_list[i] in [
                    "US ",
                    "CHINA ",
                    "SAFR ",
                    "RUS ",
                    "JPN ",
                    "BRAZIL ",
                    "INDIA ",
                ]:
                    ei = (
                        em_mit.loc[
                            [
                                "V6: Forests & Wetlands",
                                "V5: Agriculture",
                                "V4: Industry",
                                "V3: Buildings",
                                "V2: Transport",
                                "V1: Electricity",
                            ],
                            year,
                        ].values.sum()
                        / 1e3
                    ) / (
                        em_baseline.groupby("region").sum().loc[region_list[i]][year]
                        / 1e3
                        - ndcs[i][1][j]
                    )

                    ndcan = (
                        "<br>EI (NDC Target) = "
                        + str(
                            (
                                em_mit.loc[
                                    [
                                        "V6: Forests & Wetlands",
                                        "V5: Agriculture",
                                        "V4: Industry",
                                        "V3: Buildings",
                                        "V2: Transport",
                                        "V1: Electricity",
                                    ],
                                    year,
                                ].values.sum()
                                / 1e3
                            ).round(decimals=2)
                        )
                        + " GtCO2e  /  "
                        + str(
                            (
                                em_baseline.groupby("region")
                                .sum()
                                .loc[region_list[i]][year]
                                / 1e3
                                - ndcs[i][1][j]
                            ).round(decimals=2)
                        )
                        + " GtCO2e = "
                        + str(ei.round(decimals=2))
                    )
                else:
                    ndcan = str("")

                ei = (
                    em_mit.loc[
                        [
                            "V6: Forests & Wetlands",
                            "V5: Agriculture",
                            "V4: Industry",
                            "V3: Buildings",
                            "V2: Transport",
                            "V1: Electricity",
                        ],
                        year,
                    ].values.sum()
                    / 1e3
                ) / (
                    em_baseline.groupby("region").sum().loc[region_list[i]][year] / 1e3
                    - ipcc[i][1][j]
                )

                figure.add_annotation(
                    text="Epic Index = PD Projected Mitigation Potential / Target Mitigation<br>EI (IPCC Target) = "
                    + str(
                        (
                            em_mit.loc[
                                [
                                    "V6: Forests & Wetlands",
                                    "V5: Agriculture",
                                    "V4: Industry",
                                    "V3: Buildings",
                                    "V2: Transport",
                                    "V1: Electricity",
                                ],
                                year,
                            ].values.sum()
                            / 1e3
                        ).round(decimals=2)
                    )
                    + " GtCO2e"
                    + "  /  "
                    + str(
                        (
                            em_baseline.groupby("region")
                            .sum()
                            .loc[region_list[i]][year]
                            / 1e3
                            - ipcc[i][1][j]
                        ).round(decimals=2)
                    )
                    + " GtCO2e = "
                    + str(ei.round(decimals=2))
                    + str(ndcan),
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=-0.4,
                    showarrow=False,
                    font=dict(size=10, color="#2E3F5C"),
                    align="left",
                    borderpad=4,
                    borderwidth=2,
                    bgcolor="#ffffff",
                    opacity=1,
                )

            figure.update_layout(
                title="Climate Mitigation Potential, "
                + str(year)
                + ", "
                + region_list[i],
                title_x=0.5,
                title_y=0.95,
                xaxis={"title": "GtCO2e mitigated in " + str(year)},
                barmode="stack",
                legend=dict(
                    x=0.7,
                    y=0,
                    bgcolor="rgba(255, 255, 255, 0)",
                    bordercolor="rgba(255, 255, 255, 0)",
                ),
                showlegend=False,
                margin_b=120,
            )

            if show_figs is True:
                figure.show()
            if save_figs is True:
                pio.write_html(
                    figure,
                    file=(
                        "./charts/em1-"
                        + "pathway"
                        + "-"
                        + str(year)
                        + "-"
                        + region_list[i]
                        + ".html"
                    ).replace(" ", ""),
                    auto_open=False,
                )

    # endregion

    #################
    # NDC ESTIMATES #
    #################

    # region

    bar_emissions_goal = [
        (
            "of 50% reduction in the year 2030.",
            "of net-zero emissions in the year 2050.",
        ),
        ("x",),
        (
            "determined through linear extrapolation using the U.S’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2025.",
            "of net zero emissions, which was set in President Biden’s climate plan.",
        ),
        ("x",),
        (
            "set in Brazil’s 2015 NDC.",
            "determined through linear extrapolation using Brazil’s 2025 and <br>2030 emissions goals set in their 2015 NDC.",
        ),
        (
            "of 50% reduction in the year 2030.",
            "of net-zero emissions in the year 2050.",
        ),
        ("x",),
        (
            "set in South Africa’s 2015 NDC.",
            "determined through linear extrapolation using South Africa’s 2005 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030. South Africa submitted a Low Emission <br>Development Scenario in 2020, but the scenario does not specify a 2050 emissions goal.",
        ),
        ("x",),
        (
            "set in Russia’s 2015 NDC.",
            "determined through linear extrapolation using Russia’s 1990 <br>emissions and the NDC set in 2015, which set an emissions goal for 2030.",
        ),
        ("x",),
        (
            "determined by China’s 2020 NDC update to peak emissions before <br>2030.",
            "of net zero emissions, which was announced by President Xi Jinping in <br>September 2020.",
        ),
        (
            "set in India’s 2015 NDC.",
            "determined through linear extrapolation using India’s 2017 emissions <br>and the NDC set in 2015, which set an emissions goal for 2030.",
        ),
        (
            "set in Japan’s 2015 NDC.",
            "of net zero emissions, which was announced in Prime Minister Yoshihide <br>Suga's speech on October 26th, 2020.",
        ),
        ("x",),
        ("x",),
    ]

    ndcs = [
        [(2030, 2050), (25, 0), ("50% by 2030", "Net-zero by 2050")],
        (3, 3),
        [(2030, 2050), (2.84, 0), ("NDC", "Net-zero by 2050")],
        (3, 3),
        (2030, 1.2),
        [(2030, 2050), (2.3, 0), ("50% by 2030", "Net-zero by 2050")],
        (3, 3),
        (2030, 0.398),
        (3, 3),
        (2030, 2.17),
        (3, 3),
        [(2030, 2050), (12.96, 0), ("NDC", "Net-zero by 2050")],
        (2030, 9.14),
        (2030, 1),
        (3, 3),
        (3, 3),
    ]

    scenario = "pathway"
    year = 2050

    data = []

    for i in range(0, len(region_list)):
        em_mit_electricity = em_mitigated.loc[
            region_list[i], "Electricity", slice(None)
        ].sum()

        em_mit_transport = em_mitigated.loc[
            region_list[i], "Transport", slice(None)
        ].sum()

        em_mit_buildings = em_mitigated.loc[
            region_list[i], "Buildings", slice(None)
        ].sum()

        em_mit_industry = em_mitigated.loc[
            region_list[i], "Industry", slice(None)
        ].sum()

        em_mit_ra = em_mitigated.loc[
            region_list[i], ["Agriculture"], slice(None), slice(None)
        ].sum()

        em_mit_fw = em_mitigated.loc[
            region_list[i], ["Forests & Wetlands"], slice(None), slice(None)
        ].sum()

        em_mit = pd.DataFrame(
            [
                em_mit_electricity,
                em_mit_transport,
                em_mit_buildings,
                em_mit_industry,
                em_mit_ra,
                em_mit_fw,
            ]
        ).rename(
            index={
                0: "V1: Electricity",
                1: "V2: Transport",
                2: "V3: Buildings",
                3: "V4: Industry",
                4: "V5: Agriculture",
                5: "V6: Forests & Wetlands",
            }
        )

        spacer = (
            pd.Series(
                em_baseline.groupby("region").sum().loc[region_list[i]]
                - em_mit.loc[
                    [
                        "V1: Electricity",
                        "V2: Transport",
                        "V3: Buildings",
                        "V4: Industry",
                    ],
                    :,
                ].sum()
            )
            .replace(nan, 0)
            .rename("")
            .T
        )

        fig = (
            ((em_mit) / 1000)
            .reindex(
                [
                    "V6: Forests & Wetlands",
                    "V5: Agriculture",
                    "V4: Industry",
                    "V3: Buildings",
                    "V2: Transport",
                    "V1: Electricity",
                ]
            )
            .round(decimals=4)
            .clip(lower=0)
        )

        data = pd.DataFrame(data).append(
            {
                "V5: Agriculture": fig.loc["V5: Agriculture", year],
                "V6: Forests & Wetlands": fig.loc["V6: Forests & Wetlands", year],
                "labels": region_list[i],
                "spacer": spacer[2050] / 1000,
            },
            ignore_index=True,
        )

    figure = go.Figure(
        data=[
            go.Bar(
                name="V6: Forests & Wetlands",
                x=data["labels"],
                y=data["V6: Forests & Wetlands"],
                offsetgroup=0,
                orientation="v",
                marker_color="#54A24B",
                opacity=0.5,
            ),
            go.Bar(
                name="V5: Agriculture",
                x=data["labels"],
                y=data["V5: Agriculture"],
                offsetgroup=0,
                orientation="v",
                marker_color="#EECA3B",
                opacity=0.5,
            ),
        ]
    )

    figure.add_trace(
        go.Scatter(
            mode="markers",
            name="Emissions gap, after energy sector mitigation",
            x=data["labels"],
            y=data["spacer"],
            fill="none",
        )
    )

    figure.add_trace(
        go.Scatter(
            mode="markers",
            opacity=0,
            name="Emissions gap, after energy sector mitigation",
            x=data["labels"],
            y=-data["spacer"],
            fill="none",
            showlegend=False,
        )
    )

    figure.update_layout(
        title="Opportunity for NCS Mitigation after Energy Markets, " + str(year),
        title_x=0.5,
        title_y=0.99,
        yaxis={"title": "GtCO2e"},
        barmode="stack",
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.2,
            y=1.25,
            bgcolor="rgba(255, 255, 255, 0)",
            bordercolor="rgba(255, 255, 255, 0)",
        ),
        xaxis={"categoryorder": "total descending"},
    )

    figure.update_yaxes(range=[0, 35])

    if show_figs is True:
        figure.show()
    if save_figs is True:
        pio.write_html(
            figure,
            file=(
                "./charts/ncsbar-"
                + "pathway"
                + "-"
                + str(year)
                + "-"
                + "World"
                + ".html"
            ).replace(" ", ""),
            auto_open=False,
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

    #############
    # CDR COSTS #
    #############

    # region

    # eCDR

    # region

    cdr_pathway = pd.read_csv("podi/data/cdr_curve.csv").set_index(
        ["region", "sector", "scenario"]
    )
    cdr_pathway.columns = cdr_pathway.columns.astype(int)

    costs = []

    for scen in ["pathway"]:
        cdr_i, cdr_cost_i, cdr_energy_i = cdr_mix(
            cdr_pathway.loc["World ", "Carbon Dioxide Removal", scen]
            .loc[2020:]
            .to_list(),
            grid_em_def,
            heat_em_def,
            transport_em_def,
            fuel_em_def,
            2020,
            2100,
        )

        costs = pd.DataFrame(costs).append(
            pd.DataFrame(cdr_cost_i).T.rename(index={0: scen})
        )

    costs.columns = np.arange(2020, 2101, 1)
    costs = (curve_smooth(-costs, "quadratic", 7)).clip(lower=0) / 1e6
    costs.rename(
        index={"pathway": "DAU21", "dauffi": "V4", "daupl": "PL"}, inplace=True
    )
    costs.index.name = "scenario"

    cdr_costs = costs

    # endregion

    # NCS

    # region
    costs_ra = pd.Series([0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55])
    costs_fw = pd.Series([22, 24, 22, 55, 0, 30, 55, 36])
    costs_fwra = pd.Series(
        [22, 24, 22, 55, 0, 30, 55, 36, 0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55]
    )
    costs_rafw = pd.Series(
        [0, 0, 0, 0, 0, 55, 55, 22, 30, 5, 30, 55, 55, 22, 24, 22, 55, 0, 30, 55, 36]
    )

    afolu_em_mit_dau21 = (
        (
            (
                afolu_em1.loc[
                    "World ",
                    ["Agriculture", "Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em1.loc[
                    "World ",
                    ["Agriculture", "Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            )
            .groupby(["region", "sector", "Metric"])
            .sum()
        )
        .multiply(costs_fwra.T.values, "index")
        .sum()
    )

    afolu_em_mit_v4 = (
        (
            (
                afolu_em1.loc[
                    "World ",
                    ["Agriculture", "Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em1.loc[
                    "World ",
                    ["Agriculture", "Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            )
            * 0
        )
        .groupby(["region", "sector", "Metric"])
        .sum()
        .sum()
    )

    afolu_em_mit_v5 = (
        (
            (
                afolu_em1.loc[
                    "World ",
                    ["Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em1.loc[
                    "World ",
                    ["Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            ).append(
                afolu_em.loc[
                    "World ",
                    ["Agriculture"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em.loc[
                    "World ",
                    ["Agriculture"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            )
        )
        .groupby(["region", "sector", "Metric"])
        .sum()
    ).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

    afolu_em_mit_v6 = (
        (
            (
                afolu_em.loc[
                    "World ",
                    ["Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em.loc[
                    "World ",
                    ["Forests & Wetlands"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            ).append(
                afolu_em1.loc[
                    "World ",
                    ["Agriculture"],
                    slice(None),
                    slice(None),
                    "baseline",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
                - afolu_em1.loc[
                    "World ",
                    ["Agriculture"],
                    slice(None),
                    slice(None),
                    "pathway",
                ]
                .loc[:, 2020:]
                .droplevel("scenario")
            )
        )
        .groupby(["region", "sector", "Metric"])
        .sum()
    ).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

    afolu_em_mit_v5v6 = (
        (
            afolu_em.loc[
                "World ",
                ["Forests & Wetlands", "Agriculture"],
                slice(None),
                slice(None),
                "baseline",
            ]
            .loc[:, 2020:]
            .droplevel("scenario")
            - afolu_em.loc[
                "World ",
                ["Forests & Wetlands", "Agriculture"],
                slice(None),
                slice(None),
                "pathway",
            ]
            .loc[:, 2020:]
            .droplevel("scenario")
        )
        .groupby(["region", "sector", "Metric"])
        .sum()
    ).multiply(costs_fwra.T.values, "index").sum() - afolu_em_mit_dau21

    """
    em_pathway = afolu_em1.loc[slice(None), slice(None),slice(None), slice(None),'pathway',:]
    em_baseline = afolu_em1.loc[slice(None), slice(None),slice(None), slice(None),'baseline',:]
    """
    # run section to get em_mitigated_alt for PL

    afolu_em_mit_pl = (em_mitigated_alt.loc[["World "]].loc[:, 2020:]).multiply(
        costs_fwra.T.values, "index"
    ).sum() - afolu_em_mit_dau21

    afolu_costs = (
        pd.DataFrame(
            [
                afolu_em_mit_dau21 * 0,
                afolu_em_mit_v4 * 0,
                afolu_em_mit_v5,
                afolu_em_mit_v6,
                afolu_em_mit_pl,
                afolu_em_mit_v5v6,
            ]
        ).rename(index={0: "DAU21", 1: "V4", 2: "V5", 3: "V6", 4: "PL", 5: "NCSmax"})
        / 1e6
    )

    afolu_costs.index.name = "scenario"

    # endregion

    costs = cdr_costs.append(afolu_costs).groupby("scenario").sum()

    cdr_costs = pd.DataFrame(pd.read_csv("cdr costs line28228.csv")).set_index(
        "scenario"
    )

    afolu_costs = pd.DataFrame(pd.read_csv("afolu costs line28228.csv")).set_index(
        "scenario"
    )

    costs = pd.DataFrame(pd.read_csv("costs line28228.csv")).set_index("scenario")

    costs.columns = costs.columns.astype(int)
    show_figs = True

    # Plot NCS annual

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = afolu_costs.clip(lower=0)

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "NCS Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot eCDR annual

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = cdr_costs.clip(lower=0)

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "eCDR Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot eCDR annual $/tCO2 cost

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = (
        cdr_costs.clip(lower=0)
        / cdr_pathway.loc["World ", "Carbon Dioxide Removal", scen].loc[2020:].to_list()
        * 1e6
    )

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "eCDR Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot Total annual

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = costs.clip(lower=0)

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot NCS cumulative

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = (afolu_costs.clip(lower=0)).cumsum(axis=1).loc[:, :2060]

    fig.loc["DAU21"] = fig.loc["DAU21"] + 0.06

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "NCS Cumulative Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cumulative Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot eCDR cumulative

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = cdr_costs.clip(lower=0).cumsum(axis=1).loc[:, :2060]

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "eCDR Cumulative Cost, World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cumulative Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # Plot Total cumulative

    # region

    scenario = scenario
    data_start_year = 2020
    i = 0

    colors = px.colors.qualitative.Vivid

    fig = costs.clip(lower=0).cumsum(axis=1).loc[:, :2060]

    fig = fig.T
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(fig, id_vars="year", var_name="scenario", value_name="Cost")

    fig = go.Figure()

    for x in fig2["scenario"].unique():
        fig.add_trace(
            go.Scatter(
                name=x,
                line=dict(
                    width=3,
                    color=colors[
                        pd.DataFrame(fig2["scenario"].unique())
                        .set_index(0)
                        .index.get_loc(x)
                    ],
                ),
                x=fig2["year"],
                y=fig2[fig2["scenario"] == x]["Cost"],
                fill="none",
                stackgroup=x,
                legendgroup=x,
            )
        )

    fig.update_layout(
        title={
            "text": "Total Cumulative Cost (NCS + eCDR), World ",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        # xaxis={"title": "year"},
        yaxis={"title": "Cumulative Cost [$T]"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, x=0.3, font=dict(size=10)
        ),
        margin_b=0,
        margin_t=70,
        margin_l=15,
        margin_r=15,
    )

    if show_figs is True:
        fig.show()

    # endregion

    # endregion

    #############################
    # HVPLOT EXPLORATORY CHARTS #
    #############################

    # region

    ############
    #  ENERGY  #
    ############

    # region

    def _energy_chart():
        df = energy_output.droplevel(
            ["model", "product_category", "product_short", "flow_short", "unit"]
        )
        df = pd.melt(
            df.reset_index(),
            id_vars=[
                "scenario",
                "region",
                "sector",
                "product_long",
                "flow_category",
                "flow_long",
            ],
            var_name="year",
            value_name="TFC",
        )

        df = df[(df.scenario == "pathway") & (df.year < 2021)]

        select_region = pn.widgets.Select(
            options=df.region.unique().tolist(), name="Region"
        )
        select_sector = pn.widgets.Select(
            options=df.sector.unique().tolist(), name="Sector"
        )

        @pn.depends(select_region, select_sector)
        def exp_plot(select_region, select_sector):
            return (
                df[(df.region == select_region) & (df.sector == select_sector)]
                .sort_values(by="year")
                .hvplot(x="year", y="TFC", by=["flow_long"])
            )

        return pn.Column(
            pn.Row(pn.pane.Markdown("##Energy Output")),
            select_region,
            select_sector,
            exp_plot,
        ).embed()

    app = _energy_chart()
    app.save("./charts/energy_chart.html", resources=CDN)

    # endregion

    ############
    #  AFOLU  #
    ############

    # region

    def _afolu_historical():
        df = afolu_historical.droplevel(["model", "scenario", "unit"])
        df = pd.melt(
            df.reset_index(),
            id_vars=["region", "variable"],
            var_name="year",
            value_name="Adoption",
        ).fillna(0)

        select_region = pn.widgets.Select(
            options=df.region.unique().tolist(), name="Region"
        )
        select_subvertical = pn.widgets.Select(
            options=df.variable.unique().tolist(), name="Subvertical"
        )

        @pn.depends(select_region, select_subvertical)
        def exp_plot(select_region, select_subvertical):
            return (
                df[(df.region == select_region) & (df.sector == select_subvertical)]
                .sort_values(by="year")
                .hvplot(x="year", y="Adoption", by=["variable"])
            )

        return pn.Column(select_region, select_subvertical, exp_plot).embed()

    app = _afolu_historical()
    app.save("./charts/afolu_historical.html", resources=CDN)

    # endregion

    #############
    # ANIMATION #
    #############

    # region

    url = "https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv"
    dataset = pd.read_csv(url)

    years = [
        "1952",
        "1962",
        "1967",
        "1972",
        "1977",
        "1982",
        "1987",
        "1992",
        "1997",
        "2002",
        "2007",
    ]

    # make list of continents
    continents = []
    for continent in dataset["continent"]:
        if continent not in continents:
            continents.append(continent)
    # make figure
    fig_dict = {"data": [], "layout": {}, "frames": []}

    # fill in most of layout
    fig_dict["layout"]["xaxis"] = {"range": [30, 85], "title": "Life Expectancy"}
    fig_dict["layout"]["yaxis"] = {"title": "GDP per Capita", "type": "log"}
    fig_dict["layout"]["hovermode"] = "closest"
    fig_dict["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [
                        None,
                        {
                            "frame": {"duration": 500, "redraw": False},
                            "fromcurrent": True,
                            "transition": {
                                "duration": 300,
                                "easing": "quadratic-in-out",
                            },
                        },
                    ],
                    "label": "Play",
                    "method": "animate",
                },
                {
                    "args": [
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": False},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                    "label": "Pause",
                    "method": "animate",
                },
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top",
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Year:",
            "visible": True,
            "xanchor": "right",
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": [],
    }

    # make data
    year = 1952
    for continent in continents:
        dataset_by_year = dataset[dataset["year"] == year]
        dataset_by_year_and_cont = dataset_by_year[
            dataset_by_year["continent"] == continent
        ]

        data_dict = {
            "x": list(dataset_by_year_and_cont["lifeExp"]),
            "y": list(dataset_by_year_and_cont["gdpPercap"]),
            "mode": "markers",
            "text": list(dataset_by_year_and_cont["country"]),
            "marker": {
                "sizemode": "area",
                "sizeref": 200000,
                "size": list(dataset_by_year_and_cont["pop"]),
            },
            "name": continent,
        }
        fig_dict["data"].append(data_dict)

    # make frames
    for year in years:
        frame = {"data": [], "name": str(year)}
        for continent in continents:
            dataset_by_year = dataset[dataset["year"] == int(year)]
            dataset_by_year_and_cont = dataset_by_year[
                dataset_by_year["continent"] == continent
            ]

            data_dict = {
                "x": list(dataset_by_year_and_cont["lifeExp"]),
                "y": list(dataset_by_year_and_cont["gdpPercap"]),
                "mode": "markers",
                "text": list(dataset_by_year_and_cont["country"]),
                "marker": {
                    "sizemode": "area",
                    "sizeref": 200000,
                    "size": list(dataset_by_year_and_cont["pop"]),
                },
                "name": continent,
            }
            frame["data"].append(data_dict)

        fig_dict["frames"].append(frame)
        slider_step = {
            "args": [
                [year],
                {
                    "frame": {"duration": 300, "redraw": False},
                    "mode": "immediate",
                    "transition": {"duration": 300},
                },
            ],
            "label": year,
            "method": "animate",
        }
        sliders_dict["steps"].append(slider_step)

    fig_dict["layout"]["sliders"] = [sliders_dict]

    fig = go.Figure(fig_dict)

    fig.show()

    # endregion

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
