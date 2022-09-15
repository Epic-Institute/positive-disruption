# region

import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from numpy import NaN
import panel as pn

show_figs = True
save_figs = False

# endregion


def results_analysis(
    scenario,
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

    analog = analog[
        (analog.iso3c == "USA") & (analog.label.isin(labels))
    ].parallel_apply(percent_change, axis=1)

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
        .groupby(
            [
                "model",
                "scenario",
                "region",
                "sector",
                "product_long",
            ]
        )
        .sum()
        .parallel_apply(
            lambda x: x.divide(
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
                .groupby(["model", "scenario", "region"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2]]
            ),
            axis=1,
        )
    )

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Transportation"],
            slice(None),
            slice(None),
            ["ELECTR", "HYDROGEN"],
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
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Transportation"],
                    slice(None),
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
                .groupby(["model", "scenario", "region"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2]]
            ),
            axis=1,
        )
    )

    # Percent of buildings energy that is electric or nonelectric renewables
    buildings = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Commercial", "Residential"],
            slice(None),
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            slice(None),
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Commercial", "Residential"],
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
    )

    # Percent of industry energy that is electric or nonelectric renewables
    industry = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Industrial"],
            slice(None),
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
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Industrial"],
                    slice(None),
                    slice(None),
                    slice(None),
                    "Final consumption",
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
        .sort_values(by=[2050], axis=0)
    )

    industry_other = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Industrial"],
            slice(None),
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
        .groupby(["model", "scenario", "region", "sector"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Industrial"],
                    slice(None),
                    slice(None),
                    slice(None),
                    "Final consumption",
                    slice(None),
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
        .sort_values(by=[2050], axis=0)
    )

    industry_other = pd.concat(
        [industry_other], keys=["Other"], names=["flow_long"]
    ).reorder_levels(["model", "scenario", "region", "sector", "flow_long"])

    industry = pd.concat([industry, industry_other])

    # Percent of agriculture mitigation compared to max extent
    agriculture = (
        afolu_output.loc[slice(None), slice(None), slice(None), ["Agriculture"]]
        .groupby(["model", "scenario", "region", "sector", "product_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                afolu_output.loc[slice(None), slice(None), slice(None), ["Agriculture"]]
                .groupby(["model", "scenario", "region", "sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ).fillna(0),
            axis=1,
        )
    )

    # Percent of forests & wetlands mitigation compared to max extent
    forestswetlands = (
        afolu_output.loc[slice(None), slice(None), slice(None), ["Forests & Wetlands"]]
        .groupby(["model", "scenario", "region", "sector", "product_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                afolu_output.loc[
                    slice(None), slice(None), slice(None), ["Forests & Wetlands"]
                ]
                .groupby(["model", "scenario", "region", "sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ).fillna(0),
            axis=1,
        )
    )

    # Combine all verticals
    pdindex_output = pd.concat(
        [electricity, transport, buildings, industry, agriculture, forestswetlands]
    ).multiply(100)

    pdindex_output["unit"] = "% Adoption"
    pdindex_output.set_index("unit", append=True, inplace=True)

    # Plot pdindex_output
    # region

    #################
    # PD INDEX, [%] #
    #################

    # region

    region = "usa"

    fig = (
        pdindex_output.loc[slice(None), slice(None), region]
        .groupby(["scenario", "sector", "product_long"])
        .sum()
        .reindex(
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
        .T
    )

    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["scenario", "sector", "product_long"],
        value_name="% Adoption",
    )

    for scenario in fig2["scenario"].unique():

        fig = go.Figure()

        for sector in fig2["sector"].unique():

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
                            (fig2["scenario"] == scenario)
                            & (fig2["sector"] == sector)
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
                            & (fig2["product_long"] == product)
                            & (fig2["scenario"] == scenario)
                            & (fig2["sector"] == sector)
                        ]["% Adoption"],
                        stackgroup="one",
                        legendgroup=product,
                        showlegend=False,
                    )
                )

            fig.update_layout(
                title={
                    "text": "Percent of Total Adoption, Electric Power, "
                    + str(region)
                    + ", "
                    + str(sector)
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

    agriculture = (
        afolu_output.loc[slice(None), scenario, slice(None), ["Agriculture"]]
        .loc[:, data_start_year:proj_end_year]
        .groupby(["sector", "product_long"])
        .sum()
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
        .parallel_apply(
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
        .parallel_apply(
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
        .parallel_apply(
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
        .parallel_apply(
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
        .parallel_apply(
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
        .parallel_apply(
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
    app.save("./charts/energy_chart.html")

    # endregion

    ############
    #  AFOLU  #
    ############

    # region

    def _afolu_historical():
        df = afolu_output.loc[:, :data_end_year].droplevel(
            ["model", "scenario", "unit"]
        )
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
    app.save("./charts/afolu_historical.html")

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
