import dash
from dash import dcc, html, callback, Input, Output
import pandas as pd

dash.register_page(
    __name__, path="/EnergyBalances", title="Energy Balances", name="Energy Balances"
)

df = pd.read_csv("/home/n/positive-disruption/podi/data/energy_historical.csv")

layout = html.Div(
    [
        html.Div(
            children=[
                html.Label("Model"),
                html.Div(
                    [
                        dcc.RadioItems(
                            df.model.unique().tolist(),
                            "PD22",
                            id="model",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Scenario"),
                html.Div(
                    [
                        dcc.RadioItems(
                            df.scenario.unique().tolist(),
                            "baseline",
                            id="scenario",
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Region"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.region.unique().tolist(),
                            df.region.unique().tolist(),
                            id="region",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Sector"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.sector.unique().tolist(),
                            df.sector.unique().tolist(),
                            id="sector",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product Category"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_category.unique().tolist(),
                            df.product_category.unique().tolist(),
                            id="product_category",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_long.unique().tolist(),
                            df.product_long.unique().tolist(),
                            id="product_long",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Product Short"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.product_short.unique().tolist(),
                            df.product_short.unique().tolist(),
                            id="product_short",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow Category"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_category.unique().tolist(),
                            df.flow_category.unique().tolist(),
                            id="flow_category",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_long.unique().tolist(),
                            df.flow_long.unique().tolist(),
                            id="flow_long",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flow Short"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flow_short.unique().tolist(),
                            df.flow_short.unique().tolist(),
                            id="flow_short",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Hydrogen"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.hydrogen.unique().tolist(),
                            df.hydrogen.unique().tolist(),
                            id="hydrogen",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Flexible"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.flexible.unique().tolist(),
                            df.flexible.unique().tolist(),
                            id="flexible",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Nonenergy"),
                html.Div(
                    [
                        dcc.Dropdown(
                            df.nonenergy.unique().tolist(),
                            df.nonenergy.unique().tolist(),
                            id="nonenergy",
                            multi=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Unit"),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["TJ", "TWh"],
                            "TJ",
                            id="yaxis_unit",
                        ),
                    ],
                ),
                html.Div(
                    [
                        dcc.RadioItems(
                            ["Linear", "Log"],
                            "Linear",
                            id="yaxis_type",
                            inline=True,
                        ),
                    ],
                ),
                html.Br(),
                html.Label("Group by"),
                html.Div(
                    [
                        dcc.RadioItems(
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
                            "flow_short",
                            id="groupby",
                        ),
                    ],
                ),
            ]
        ),
        html.Br(),
        dcc.Graph(id="graphic-tables"),
    ]
)


@callback(
    Output("graphic-tables", "figure"),
    Input("model", "value"),
    Input("scenario", "value"),
    Input("region", "value"),
    Input("sector", "value"),
    Input("product_category", "value"),
    Input("product_long", "value"),
    Input("product_short", "value"),
    Input("flow_category", "value"),
    Input("flow_long", "value"),
    Input("flow_short", "value"),
    Input("hydrogen", "value"),
    Input("flexible", "value"),
    Input("nonenergy", "value"),
    Input("yaxis_unit", "value"),
    Input("yaxis_type", "value"),
    Input("groupby", "value"),
)
def update_graph(
    model,
    scenario,
    region,
    sector,
    product_category,
    product_long,
    product_short,
    flow_category,
    flow_long,
    flow_short,
    hydrogen,
    flexible,
    nonenergy,
    yaxis_unit,
    yaxis_type,
    groupby,
    year,
):

    # Filter for region and year
    energy_balance = (
        df.loc[slice(None), slice(None), region]
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
            values=year,
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

    return energy_balance.astype(int)
