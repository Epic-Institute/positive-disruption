import dash
import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html

dash.register_page(
    __name__,
    path="/EnergyBalances",
    title="Energy Balances",
    name="Energy Balances",
)

data_start_year = 1990
data_end_year = 2020

df = pd.read_csv("/home/n/positive-disruption/podi/data/energy_historical.csv")

df = pd.read_csv("/home/n/positive-disruption/podi/data/energy_historical.csv")

df.set_index(
    df.columns[
        (
            ~df.columns.isin(
                f"{i}" for i in range(data_start_year, data_end_year + 1)
            )
        )
    ].tolist(),
    inplace=True,
)

# Filter for region and year
energy_balance = (
    df.loc["PD22", "baseline", slice(None)]
    .groupby(
        [
            "sector",
            "product_category",
            "product_long",
            "flow_category",
            "flow_long",
        ]
    )
    .sum(numeric_only=True)
)

# Create energy balance table structure
energy_balance = (
    energy_balance.groupby(
        ["product_category", "product_long", "flow_category", "flow_long"]
    )
    .sum(numeric_only=True)
    .reset_index()
    .pivot(
        index=["flow_category", "flow_long"],
        columns=["product_category", "product_long"],
        values=str(data_end_year),
    )
    .fillna(0)
    .reindex(
        axis="index",
        level=0,
        labels=[
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
        energy_balance.groupby(
            "product_category", axis="columns", observed=True
        )
        .sum(numeric_only=True)[
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
            labels=[
                "Electricity",
                "Heat – High Temperature",
                "Heat – Low Temperature",
                "Nuclear",
                "Hydro",
            ],
            axis=1,
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
    energy_balance.loc["Final consumption", :]
    .loc[
        energy_balance.loc["Final consumption", :]
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

energy_balance.index.name = "sector"
energy_balance.reset_index(inplace=True)

layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Model", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            df.reset_index().model.unique().tolist(),
                            "PD22",
                            id="model",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Scenario", className="select-label"),
                html.Div(
                    [
                        dcc.RadioItems(
                            df.reset_index().scenario.unique().tolist(),
                            "baseline",
                            id="scenario",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.reset_index().region.unique().tolist(),
                            "usa",
                            id="region",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Year", className="select-label"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.columns[
                                df.columns.isin(
                                    f"{i}"
                                    for i in range(
                                        data_start_year, data_end_year + 1
                                    )
                                )
                            ].tolist(),
                            "2020",
                            id="year",
                            multi=False,
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        html.Div(
            className="select-label",
            children=[
                dash_table.DataTable(
                    energy_balance.to_dict("records"),
                    [{"name": i, "id": i} for i in energy_balance.columns],
                    id="table",
                )
            ],
        ),
        html.Br(),
    ]
)


@callback(
    Output("table", "data"),
    Input("model", "value"),
    Input("scenario", "value"),
    Input("region", "value"),
    Input("year", "value"),
)
def update_graph(
    model, scenario, region, year, data_start_year=1990, data_end_year=2020
):
    df = pd.read_csv(
        "/home/n/positive-disruption/podi/data/energy_historical.csv"
    )

    df.set_index(
        df.columns[
            (
                ~df.columns.isin(
                    f"{i}" for i in range(data_start_year, data_end_year + 1)
                )
            )
        ].tolist(),
        inplace=True,
    )

    # Filter for region and year
    energy_balance = (
        df.loc[model, scenario, region]
        .groupby(
            [
                "sector",
                "product_category",
                "product_long",
                "flow_category",
                "flow_long",
            ],
            observed=True,
        )
        .sum()
    )

    # Create energy balance table structure
    energy_balance = (
        energy_balance.groupby(
            ["product_category", "product_long", "flow_category", "flow_long"],
            observed=True,
        )
        .sum()
        .reset_index()
        .pivot(
            index=["flow_category", "flow_long"],
            columns=["product_category", "product_long"],
            values=year,
        )
        .fillna(0)
        .reindex(
            axis="index",
            level=0,
            labels=[
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
            energy_balance.groupby(
                "product_category", axis="columns", observed=True
            )
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
                labels=[
                    "Electricity",
                    "Heat – High Temperature",
                    "Heat – Low Temperature",
                    "Nuclear",
                    "Hydro",
                ],
                axis=1,
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
            pd.DataFrame(energy_balance.sum(axis=1)).rename(
                columns={0: "Total"}
            ),
        ],
        axis=1,
    )

    # Create Flow categories (rows)
    bunkers = (
        energy_balance.loc["Final consumption", :]
        .loc[
            energy_balance.loc["Final consumption", :]
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

    energy_balance.index.name = "sector"
    energy_balance.reset_index(inplace=True)

    return energy_balance.to_dict("records")
