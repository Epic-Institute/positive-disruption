# region

import numpy as np
import pandas as pd
import fair
from fair.forward import fair_scm
from fair.RCPs import rcp26, rcp45, rcp60, rcp85, rcp3pd
from fair.SSPs import ssp119
from fair.constants import radeff
from scipy.stats import gamma
import pyam
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

show_figs = True
save_figs = True

# endregion


def climate(
    scenario,
    emissions_output,
    emissions_output_co2e,
    cdr_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ########################
    # LOAD HISTORICAL DATA #
    ########################

    # region

    # Load GHG concentration data from external source
    climate_historical_concentration = pd.DataFrame(
        pd.read_csv(
            "podi/data/external/climate-change.csv",
            usecols=[
                "Entity",
                "Year",
                "CO2 concentrations",
                "CH4 concentrations",
                "N2O concentrations",
            ],
        )
    )

    # Select World-level data
    climate_historical_concentration = climate_historical_concentration[
        (climate_historical_concentration["Entity"] == "World").values
    ].drop(columns="Entity")

    # Update column names
    climate_historical_concentration = climate_historical_concentration.rename(
        {
            "CO2 concentrations": "CO2",
            "CH4 concentrations": "CH4",
            "N2O concentrations": "N2O",
        },
        axis="columns",
    )

    climate_historical_concentration = (
        climate_historical_concentration[
            (climate_historical_concentration["Year"] >= data_start_year).values
        ]
        .rename(columns={"Year": "year"})
        .set_index("year")
    )

    # Load radiative forcing data from external source
    climate_historical_forcing = pd.DataFrame(
        pd.read_csv("podi/data/external/radiative_forcing_historical.csv")
    )
    climate_historical_forcing.columns = climate_historical_forcing.columns.astype(int)
    climate_historical_forcing = climate_historical_forcing.loc[
        :, data_start_year:data_end_year
    ].T

    # Load temperature change data from external source
    climate_historical_temperature = pd.DataFrame(
        pd.read_csv("podi/data/external/temperature_change_historical.csv")
    )
    climate_historical_temperature.columns = (
        climate_historical_temperature.columns.astype(int)
    )
    climate_historical_temperature = climate_historical_temperature.loc[
        :, data_start_year:data_end_year
    ].T

    # endregion

    ############################################
    # PREPARE EMISSIONS DATA FOR CLIMATE MODEL #
    ############################################

    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output = emissions_output[
        ~(
            emissions_output.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    # Rename emissions_output gases to match required inputs for FAIR

    # SO2 to SOx
    emissions_output.rename(index={"SO2": "SOx"}, inplace=True)

    # Drop dashes
    for gas in [
        "HFC-23",
        "HFC-32",
        "HFC-125",
        "HFC-134a",
        "HFC-143a",
        "HFC-227ea",
        "HFC-245fa",
        "HCFC-141b",
        "HCFC-142b",
    ]:
        emissions_output.rename(index={gas: gas.replace("-", "")}, inplace=True)

    #'HFC-43-10-mee' to 'HFC43-10'
    emissions_output.rename(index={"HFC-43-10-mee": "HFC43-10"}, inplace=True)

    # Update emissions that don't list gas in flow_long (these are all CO2)
    emissions_output.reset_index(inplace=True)

    # Select CO2 emissions
    emissions_output_co2 = emissions_output[
        ~(
            emissions_output.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "SOx",
                    "CO",
                    "NMVOC",
                    "NOx",
                    "BC",
                    "OC",
                    "NH3",
                    "CF4",
                    "C2F6",
                    "C6F14",
                    "HFC23",
                    "HFC32",
                    "HFC43-10",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC227ea",
                    "HFC245fa",
                    "SF6",
                    "CFC11",
                    "CFC12",
                    "CFC113",
                    "CFC114",
                    "CFC115",
                    "CCl4",
                    "Methyl chloroform",
                    "HCFC22",
                    "HCFC141b",
                    "HCFC142b",
                    "Halon 1211",
                    "Halon 1202",
                    "Halon 1301",
                    "Halon 2401",
                    "CH3Br",
                    "CH3Cl",
                    "HFC-365mfc",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "c-C4F8",
                    "HFC-134",
                    "HFC-143",
                    "HFC-152a",
                    "HFC-236fa",
                    "HFC-41",
                    "C5F12",
                ]
            )
        ).values
    ]

    # Remove CO2 emissions from full emissions list
    emissions_output = emissions_output[
        (
            emissions_output.flow_long.isin(
                [
                    "CH4",
                    "N2O",
                    "SOx",
                    "CO",
                    "NMVOC",
                    "NOx",
                    "BC",
                    "OC",
                    "NH3",
                    "CF4",
                    "C2F6",
                    "C6F14",
                    "HFC23",
                    "HFC32",
                    "HFC43-10",
                    "HFC125",
                    "HFC134a",
                    "HFC143a",
                    "HFC227ea",
                    "HFC245fa",
                    "SF6",
                    "CFC11",
                    "CFC12",
                    "CFC113",
                    "CFC114",
                    "CFC115",
                    "CCl4",
                    "Methyl chloroform",
                    "HCFC22",
                    "HCFC141b",
                    "HCFC142b",
                    "Halon 1211",
                    "Halon 1202",
                    "Halon 1301",
                    "Halon 2401",
                    "CH3Br",
                    "CH3Cl",
                    "HFC-365mfc",
                    "C3F8",
                    "C4F10",
                    "NF3",
                    "c-C4F8",
                    "HFC-134",
                    "HFC-143",
                    "HFC-152a",
                    "HFC-236fa",
                    "HFC-41",
                    "C5F12",
                ]
            )
        ).values
    ]

    # Replace 'flow_long' value with 'CO2'
    emissions_output_co2.drop(columns="flow_long", inplace=True)
    emissions_output_co2["flow_long"] = "CO2"

    # Replace 'CO2' with 'CO2-fossil' for subset
    emissions_output_fossil = emissions_output_co2[
        (
            (emissions_output_co2.flow_long == "CO2")
            & (
                emissions_output_co2.sector.isin(
                    [
                        "Electric Power",
                        "Transportation",
                        "Residential",
                        "Commercial",
                        "Industrial",
                    ]
                )
            )
        ).values
    ].drop(columns="flow_long")

    emissions_output_fossil["flow_long"] = "CO2-fossil"

    # Replace 'CO2' with 'CO-landuse' for subset
    emissions_output_landuse = emissions_output_co2[
        (
            (emissions_output_co2.flow_long == "CO2")
            & (emissions_output_co2.sector.isin(["Agriculture", "Forests & Wetlands"]))
        ).values
    ].drop(columns="flow_long")

    emissions_output_landuse["flow_long"] = "CO2-landuse"

    # Recombine
    emissions_output_co2 = pd.concat(
        [emissions_output_fossil, emissions_output_landuse]
    )

    # Add the updated subset back into the original df
    emissions_output = pd.concat([emissions_output, emissions_output_co2])

    emissions_output = emissions_output.set_index(
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

    # List gases that FAIR climate model takes as input, with associated units
    fair_input_gases = {
        "CO2-fossil": "GtC/yr",
        "CO2-landuse": "GtC/yr",
        "CH4": "Mt/yr",
        "N2O": "MtN2/yr",
        "SOx": "MtS/yr",
        "CO": "Mt/yr",
        "NMVOC": "Mt/yr",
        "NOx": "MtN/yr",
        "BC": "Mt/yr",
        "OC": "Mt/yr",
        "NH3": "Mt/yr",
        "CF4": "kt/yr",
        "C2F6": "kt/yr",
        "C6F14": "kt/yr",
        "HFC23": "kt/yr",
        "HFC32": "kt/yr",
        "HFC43-10": "kt/yr",
        "HFC125": "kt/yr",
        "HFC134a": "kt/yr",
        "HFC143a": "kt/yr",
        "HFC227ea": "kt/yr",
        "HFC245fa": "kt/yr",
        "SF6": "kt/yr",
        "CFC11": "kt/yr",
        "CFC12": "kt/yr",
        "CFC113": "kt/yr",
        "CFC114": "kt/yr",
        "CFC115": "kt/yr",
        "CCl4": "kt/yr",
        "Methyl chloroform": "kt/yr",
        "HCFC22": "kt/yr",
        "HCFC141b": "kt/yr",
        "HCFC142b": "kt/yr",
        "Halon 1211": "kt/yr",
        "Halon 1202": "kt/yr",
        "Halon 1301": "kt/yr",
        "Halon 2401": "kt/yr",
        "CH3Br": "kt/yr",
        "CH3Cl": "kt/yr",
    }

    # Filter emissions_output to contain only inputs for fair_input_gases
    emissions_output = emissions_output[
        (emissions_output.reset_index().flow_long.isin(fair_input_gases.keys())).values
    ].sort_index()

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output = emissions_output.apply(
        lambda x: x.multiply(
            pd.read_csv(
                "podi/data/climate_unit_conversions.csv", usecols=["value", "gas"]
            )
            .set_index("gas")
            .loc[x.name[8]]
            .values[0]
        ),
        axis=1,
    )

    # Plot emissions
    # region

    #####################
    # EMISSIONS, BY GAS #
    #####################

    # region

    for gas in fair_input_gases.keys():  # emissions_output.index.levels[8]

        fig = go.Figure()

        for scenario in emissions_output.index.levels[1]:
            fig.add_trace(
                go.Scatter(
                    name=scenario + ", " + gas,
                    line=dict(width=3),
                    x=emissions_output.columns[
                        emissions_output.columns >= data_end_year
                    ],
                    y=emissions_output[
                        (emissions_output.index.get_level_values(1) == scenario)
                        & (emissions_output.index.get_level_values(8) == gas)
                    ]
                    .loc[:, (emissions_output.columns >= data_end_year)]
                    .sum()
                    .squeeze(),
                    fill="none",
                )
            )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=3, color="black"),
                x=emissions_output.columns[emissions_output.columns <= data_end_year],
                y=emissions_output[
                    (emissions_output.index.get_level_values(1) == scenario)
                    & (emissions_output.index.get_level_values(8) == gas)
                ]
                .loc[:, (emissions_output.columns <= data_end_year)]
                .sum()
                .squeeze(),
                fill="none",
            )
        )

        fig.update_layout(
            title={
                "text": "Emissions, " + scenario + ", " + gas,
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": fair_input_gases[gas] + " " + gas},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)
            ),
            margin_b=0,
            margin_t=60,
            margin_l=15,
            margin_r=15,
        )

        fig.show()

    # endregion

    # endregion

    # endregion

    ################################################
    # ESTIMATE CONCENTRATION, FORCING, TEMPERATURE #
    ################################################

    # region

    # Run the climate model for each scenario. Note that natural emissions of CH4 and N2O is set to zero, and volcanic and solar forcing are provided externally and estimated here

    climate_output_concentration = pd.DataFrame()
    climate_output_forcing = pd.DataFrame()
    climate_output_temperature = pd.DataFrame()

    for scenario in emissions_output.reset_index().scenario.unique():

        # Add in remaining gases needed for fair_input_gases and format for input into FAIR
        emissions_output_fair = (
            pd.concat(
                [
                    emissions_output.loc[slice(None), scenario, :]
                    .groupby(["flow_long"])
                    .sum()
                    .T,
                    pd.DataFrame(
                        index=emissions_output.columns,
                        columns=[
                            "CFC11",
                            "CFC12",
                            "CFC113",
                            "CFC114",
                            "CFC115",
                            "CCl4",
                            "Methyl chloroform",
                            "HCFC22",
                            "Halon 1211",
                            "Halon 1202",
                            "Halon 1301",
                            "Halon 2401",
                            "CH3Br",
                            "CH3Cl",
                        ],
                    ),
                ],
                axis=1,
            )
            .fillna(0)
            .reset_index()
        )

        emissions_output_fair = np.array(
            emissions_output_fair[list(["index"]) + list(fair_input_gases.keys())]
        )

        C_temp, F_temp, T_temp = fair.forward.fair_scm(
            emissions=emissions_output_fair,
            natural=np.zeros((len(emissions_output_fair), 2)),
            F_solar=1e-3
            * np.sin(2 * np.pi * np.arange(len(emissions_output_fair)) / 11.5),
            F_volcanic=-gamma.rvs(
                1e-6, size=len(emissions_output_fair), random_state=100
            ),
        )

        # Gases that FAIR provides as output, with associated units
        fair_output_gases = {
            "CO2": "ppm",
            "CH4": "ppb",
            "N2O": "ppb",
            "CF4": "ppt",
            "C2F6": "ppt",
            "C6F14": "ppt",
            "HFC23": "ppt",
            "HFC32": "ppt",
            "HFC43-10": "ppt",
            "HFC125": "ppt",
            "HFC134a": "ppt",
            "HFC143a": "ppt",
            "HFC227ea": "ppt",
            "HFC245fa": "ppt",
            "SF6": "ppt",
            "CFC11": "ppt",
            "CFC12": "ppt",
            "CFC113": "ppt",
            "CFC114": "ppt",
            "CFC115": "ppt",
            "CCl4": "ppt",
            "Methyl chloroform": "ppt",
            "HCFC22": "ppt",
            "HCFC141b": "ppt",
            "HCFC142b": "ppt",
            "Halon 1211": "ppt",
            "Halon 1202": "ppt",
            "Halon 1301": "ppt",
            "Halon 2401": "ppt",
            "CH3Br": "ppt",
            "CH3Cl": "ppt",
        }

        # Forcing that FAIR provides as output
        fair_output_forcing = [
            "CO2",
            "CH4",
            "N2O",
            "All other well-mixed GHGs",
            "Tropospheric O3",
            "Stratospheric O3",
            "Stratospheric water vapour from CH4 oxidation",
            "Contrails",
            "Aerosols",
            "Black carbon on snow",
            "Land use change",
            "Volcanic",
            "Solar",
        ]

        climate_output_concentration_temp = pd.DataFrame(
            data=C_temp.T,
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            index=pd.MultiIndex.from_frame(
                pd.concat(
                    [
                        pd.Series(
                            np.full(len(list(fair_output_gases.keys())), scenario)
                        ),
                        pd.Series(fair_output_gases.keys()),
                    ],
                    axis=1,
                )
            ),
        )
        climate_output_concentration_temp.index.set_names(
            ["scenario", "product_long"], inplace=True
        )

        climate_output_forcing_temp = pd.DataFrame(
            data=F_temp.T,
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            index=pd.MultiIndex.from_frame(
                pd.concat(
                    [
                        pd.Series(np.full(len(list(fair_output_forcing)), scenario)),
                        pd.Series(fair_output_forcing),
                    ],
                    axis=1,
                )
            ),
        )
        climate_output_forcing_temp.index.set_names(
            ["scenario", "product_long"], inplace=True
        )

        climate_output_temperature_temp = pd.DataFrame(
            data=[T_temp],
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            index=pd.MultiIndex.from_frame(
                pd.concat(
                    [pd.Series(scenario), pd.Series("Temperature change")], axis=1
                )
            ),
        )
        climate_output_temperature_temp.index.set_names(
            ["scenario", "product_long"], inplace=True
        )

        climate_output_concentration = pd.concat(
            [climate_output_concentration_temp, climate_output_concentration]
        )
        climate_output_forcing = pd.concat(
            [climate_output_forcing_temp, climate_output_forcing]
        )
        climate_output_temperature = pd.concat(
            [climate_output_temperature_temp, climate_output_temperature]
        )

    # Create version of climate_output_concentration with units CO2e
    # region

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output_co2e = emissions_output_co2e[
        ~(
            emissions_output_co2e.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ].sort_index()

    emissions_output_co2e.reset_index(inplace=True)
    emissions_output_co2e["flow_long"] = "CO2"
    emissions_output_co2e.set_index(emissions_output.index.names, inplace=True)

    # Convert units from emissions_output_co2e to assumed units for FAIR model input
    emissions_output_co2e = emissions_output_co2e.apply(
        lambda x: x.multiply(
            pd.read_csv(
                "podi/data/climate_unit_conversions.csv", usecols=["value", "gas"]
            )
            .set_index("gas")
            .loc[x.name[8]]
            .values[0]
        ),
        axis=1,
    )

    # Convert units from emissions_output to assumed units for FAIR model input
    emissions_output_co2e = emissions_output_co2e.groupby(
        ["scenario", "flow_long"]
    ).sum()

    climate_output_concentration_co2e = pd.DataFrame()
    climate_output_forcing_co2e = pd.DataFrame()

    for scenario in emissions_output_co2e.reset_index().scenario.unique():

        emissions_output_co2e_fair = (
            emissions_output_co2e.loc[scenario, :]
            .groupby(["flow_long"])
            .sum()
            .values[0]
        )

        C_co2e_temp, F_co2e_temp, T_co2e_temp = fair.forward.fair_scm(
            emissions=emissions_output_co2e_fair,
            natural=np.zeros((len(emissions_output_co2e), 2)),
            F_solar=1e-3
            * np.sin(2 * np.pi * np.arange(len(emissions_output_co2e)) / 11.5),
            F_volcanic=-gamma.rvs(
                1e-3, size=len(emissions_output_co2e), random_state=100
            ),
            useMultigas=False,
        )

        climate_output_concentration_co2e_temp = pd.DataFrame(
            data=[C_co2e_temp],
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            index=pd.MultiIndex.from_frame(
                pd.concat([pd.Series(scenario), pd.Series("CO2e")], axis=1)
            ),
        )
        climate_output_concentration_co2e_temp.index.set_names(
            ["scenario", "product_long"], inplace=True
        )

        climate_output_concentration_co2e = pd.concat(
            [climate_output_concentration_co2e_temp, climate_output_concentration_co2e]
        )

        climate_output_forcing_co2e_temp = pd.DataFrame(
            data=[F_co2e_temp],
            columns=np.arange(data_start_year, proj_end_year + 1, 1),
            index=pd.MultiIndex.from_frame(
                pd.concat([pd.Series(scenario), pd.Series("CO2e")], axis=1)
            ),
        )
        climate_output_forcing_co2e_temp.index.set_names(
            ["scenario", "product_long"], inplace=True
        )

        climate_output_forcing_co2e = pd.concat(
            [climate_output_forcing_co2e_temp, climate_output_forcing_co2e]
        )

    # endregion

    # Plot concentration, forcing, temperature
    # region

    ###################################
    # ATMOSPHERIC CONCENTRATION, CO2e #
    ###################################

    # region

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=climate_output_concentration_co2e.columns[
                climate_output_concentration_co2e.columns <= data_end_year
            ],
            y=climate_output_concentration_co2e.loc[scenario].squeeze(),
            fill="none",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=3, color="red", dash="dot"),
            x=climate_output_concentration_co2e.columns[
                climate_output_concentration_co2e.columns >= data_end_year
            ],
            y=climate_output_concentration_co2e.loc["baseline"]
            .loc[:, (climate_output_concentration_co2e.columns >= data_end_year)]
            .squeeze(),
            fill="none",
            stackgroup="baseline",
            legendgroup="baseline",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="PD22",
            line=dict(width=3, color="purple", dash="dashdot"),
            x=climate_output_concentration_co2e.columns[
                climate_output_concentration_co2e.columns >= data_end_year
            ],
            y=climate_output_concentration_co2e.loc["pathway"]
            .loc[:, (climate_output_concentration_co2e.columns >= data_end_year)]
            .squeeze(),
            fill="none",
            stackgroup="pd22",
            legendgroup="pd22",
        )
    )

    fig.update_layout(
        title={
            "text": "Atmospheric GHG Concentration",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "ppm CO2e"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin_b=0,
        margin_t=60,
        margin_l=15,
        margin_r=15,
    )

    fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=("./charts/climate-ghg-concentration.html").replace(" ", ""),
            auto_open=False,
        )

    # endregion

    #####################################
    # ATMOSPHERIC CONCENTRATION, BY GAS #
    #####################################

    # region

    for gas in climate_output_concentration.index.levels[1]:

        fig = go.Figure()

        for scenario in climate_output_concentration.index.levels[0]:
            fig.add_trace(
                go.Scatter(
                    name=scenario + ", " + gas,
                    line=dict(width=3),
                    x=climate_output_concentration.columns[
                        climate_output_concentration.columns >= data_end_year
                    ],
                    y=climate_output_concentration.loc[scenario, gas]
                    .loc[data_end_year:]
                    .squeeze(),
                    fill="none",
                )
            )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=3, color="black"),
                x=climate_output_concentration.columns[
                    climate_output_concentration.columns <= data_end_year
                ],
                y=climate_output_concentration.loc[scenario, gas].squeeze(),
                fill="none",
            )
        )

        fig.update_layout(
            title={
                "text": "Atmospheric Concentration, " + scenario + ", " + gas,
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": fair_output_gases[gas] + " " + gas},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)
            ),
            margin_b=0,
            margin_t=60,
            margin_l=15,
            margin_r=15,
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=(
                    "./charts/climate-" + gas.lower() + "-concentration.html"
                ).replace(" ", ""),
                auto_open=False,
            )

    # endregion

    ###########################
    # RADIATIVE FORCING, CO2e #
    ###########################

    # region

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=3, color="red", dash="dot"),
            x=climate_output_forcing_co2e.columns[
                climate_output_forcing_co2e.columns >= data_end_year
            ],
            y=climate_output_forcing_co2e.loc["baseline"]
            .loc[:, data_end_year:]
            .squeeze(),
            fill="none",
            legendgroup="baseline",
        )
    )

    fig.add_trace(
        go.Scatter(
            name=scenario.capitalize(),
            line=dict(width=3, color="purple", dash="dashdot"),
            x=climate_output_forcing_co2e.columns[
                climate_output_forcing_co2e.columns >= data_end_year
            ],
            y=climate_output_forcing_co2e.loc[scenario]
            .loc[:, data_end_year:]
            .squeeze(),
            fill="none",
            legendgroup=scenario,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=climate_output_forcing_co2e.columns[
                climate_output_forcing_co2e.columns <= data_end_year
            ],
            y=climate_output_forcing_co2e.loc[scenario]
            .loc[:, :data_end_year]
            .squeeze(),
            fill="none",
        )
    )

    fig.update_layout(
        title={
            "text": "Radiative Forcing, CO2e, " + scenario.capitalize(),
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "W/m2"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin_b=0,
        margin_t=60,
        margin_l=15,
        margin_r=15,
    )

    fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=("./charts/climate-radiativeforcing.html").replace(" ", ""),
            auto_open=False,
        )

    # endregion

    #############################
    # RADIATIVE FORCING, BY GAS #
    #############################

    # region

    for gas in climate_output_forcing.index.levels[1]:

        fig = go.Figure()

        for scenario in climate_output_forcing.index.levels[0]:
            fig.add_trace(
                go.Scatter(
                    name=scenario.capitalize(),
                    line=dict(width=3),
                    x=climate_output_forcing.columns[
                        climate_output_forcing.columns >= data_end_year
                    ],
                    y=climate_output_forcing.loc[scenario, gas]
                    .loc[data_end_year:]
                    .squeeze(),
                    fill="none",
                )
            )

        fig.add_trace(
            go.Scatter(
                name="Historical",
                line=dict(width=3, color="black"),
                x=climate_output_forcing.columns[
                    climate_output_forcing.columns <= data_end_year
                ],
                y=climate_output_forcing.loc[scenario, gas].squeeze(),
                fill="none",
            )
        )

        fig.update_layout(
            title={
                "text": "Radiative Forcing, " + scenario.capitalize() + ", " + gas,
                "xanchor": "center",
                "x": 0.5,
                "y": 0.99,
            },
            yaxis={"title": "W/m2"},
        )

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01, x=0.12, font=dict(size=10)
            ),
            margin_b=0,
            margin_t=60,
            margin_l=15,
            margin_r=15,
        )

        fig.show()

        if save_figs is True:
            pio.write_html(
                fig,
                file=("./charts/radiativeforcing-" + "World " + ".html").replace(
                    " ", ""
                ),
                auto_open=False,
            )

    # endregion

    ######################
    # TEMPERATURE CHANGE #
    ######################

    # region

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=climate_historical_temperature.loc[
                data_start_year:data_end_year
            ].squeeze(),
            fill="none",
            legendgroup="hist",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Historical",
            line=dict(width=3, color="black"),
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=climate_historical_temperature.loc[
                data_start_year:data_end_year
            ].squeeze(),
            fill="none",
            legendgroup="hist",
            showlegend=False,
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=3, color="red", dash="dot"),
            x=np.arange(data_end_year, proj_end_year + 1, 1),
            y=(
                climate_output_temperature.loc["baseline"].loc[:, data_end_year:]
                + (
                    climate_historical_temperature.loc[data_end_year].values[0]
                    - climate_output_temperature.loc["baseline"]
                    .loc[:, data_end_year]
                    .values[0]
                )
            ).squeeze(),
            fill="none",
            legendgroup="baseline",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            name="Baseline",
            line=dict(width=3, color="red", dash="dot"),
            x=np.arange(data_end_year, proj_end_year + 1, 1),
            y=(
                climate_output_temperature.loc["baseline"].loc[:, data_end_year:]
                + (
                    climate_historical_temperature.loc[data_end_year].values[0]
                    - climate_output_temperature.loc["baseline"]
                    .loc[:, data_end_year]
                    .values[0]
                )
            ).squeeze(),
            fill="none",
            legendgroup="baseline",
            showlegend=True,
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            name=scenario.capitalize(),
            line=dict(width=3, color="purple", dash="dashdot"),
            x=np.arange(data_end_year, proj_end_year + 1, 1),
            y=(
                climate_output_temperature.loc[scenario].loc[:, data_end_year:]
                + (
                    climate_historical_temperature.loc[data_end_year].values[0]
                    - climate_output_temperature.loc[scenario]
                    .loc[:, data_end_year]
                    .values[0]
                )
            ).squeeze(),
            fill="none",
            legendgroup="pd22",
        )
    )

    # Show temperature uncertainty range

    # region
    range = "other"
    # Historical
    # region

    temp_range = pd.read_csv("podi/data/temperature_change_range.csv").set_index(
        "Range"
    )
    temp_range.columns = temp_range.columns.astype(int)

    fig.add_trace(
        go.Scatter(
            name="Historical_upper",
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=temp_range.loc["83p", data_start_year:data_end_year].squeeze(),
            mode="lines",
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False,
        ),
    )

    fig.add_trace(
        go.Scatter(
            name="Historical_upper",
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=temp_range.loc["83p", data_start_year:data_end_year].squeeze(),
            mode="lines",
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False,
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            name="Est. range",
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=temp_range.loc["17p", data_start_year:data_end_year].squeeze(),
            marker=dict(color="#444"),
            line=dict(width=0),
            mode="lines",
            fillcolor="rgba(255,155,5,0.15)",
            fill="tonexty",
            showlegend=False,
        ),
    )

    fig.add_trace(
        go.Scatter(
            name="Historical_lower",
            x=np.arange(data_start_year, data_end_year + 1, 1),
            y=temp_range.loc["17p", data_start_year:data_end_year].squeeze(),
            marker=dict(color="#444"),
            line=dict(width=0),
            mode="lines",
            fillcolor="rgba(255,155,5,0.15)",
            fill="tonexty",
            showlegend=False,
        ),
        secondary_y=True,
    )
    # endregion

    # PD22 regular or expanding
    if range == "pd22":
        # PD22 regular
        # region
        fig.add_trace(
            go.Scatter(
                name="dau21_upper",
                x=np.arange(data_end_year, proj_end_year + 1, 1),
                y=(
                    (climate_output_temperature.loc[scenario].loc[:, data_end_year:])
                    + (
                        climate_historical_temperature.loc[data_end_year].values[0]
                        - climate_output_temperature.loc[scenario]
                        .loc[:, data_end_year]
                        .values[0]
                    )
                )
                .multiply(1.2)
                .squeeze(),
                mode="lines",
                marker=dict(color="#444"),
                line=dict(width=0),
                showlegend=False,
            ),
        )

        fig.add_trace(
            go.Scatter(
                name="dau21_lower",
                x=np.arange(data_end_year, proj_end_year + 1, 1),
                y=(
                    (climate_output_temperature.loc[scenario].loc[:, data_end_year:])
                    + (
                        climate_historical_temperature.loc[data_end_year].values[0]
                        - climate_output_temperature.loc[scenario]
                        .loc[:, data_end_year]
                        .values[0]
                    )
                )
                .multiply(0.8)
                .squeeze(),
                marker=dict(color="#444"),
                line=dict(width=0),
                mode="lines",
                fillcolor="rgba(153,0,153,0.15)",
                fill="tonexty",
                showlegend=False,
            ),
        )

        # endregion
    else:
        # PD22 expanding
        # region

        tproj_err = pd.read_csv("podi/data/temperature_change_range.csv").set_index(
            "Range"
        )
        tproj_err.columns = temp_range.columns.astype(int)

        fig.add_trace(
            go.Scatter(
                name="dau21_upper",
                x=np.arange(data_end_year, proj_end_year + 1, 1),
                y=(
                    (
                        climate_output_temperature.loc[scenario].loc[:, data_end_year:]
                        + temp_range.loc["dau21_upper", data_end_year:proj_end_year]
                    )
                    + (
                        climate_historical_temperature.loc[data_end_year].values[0]
                        - climate_output_temperature.loc[scenario]
                        .loc[:, data_end_year]
                        .values[0]
                    )
                )
                .multiply(1.2)
                .squeeze(),
                mode="lines",
                marker=dict(color="#444"),
                line=dict(width=0),
                showlegend=False,
            ),
        )

        fig.add_trace(
            go.Scatter(
                name="dau21_lower",
                x=np.arange(data_end_year, proj_end_year + 1, 1),
                y=(
                    (
                        climate_output_temperature.loc[scenario].loc[:, data_end_year:]
                        + temp_range.loc["dau21_lower", data_end_year:proj_end_year]
                    )
                    + (
                        climate_historical_temperature.loc[data_end_year].values[0]
                        - climate_output_temperature.loc[scenario]
                        .loc[:, data_end_year]
                        .values[0]
                    )
                )
                .multiply(0.8)
                .squeeze(),
                marker=dict(color="#444"),
                line=dict(width=0),
                mode="lines",
                fillcolor="rgba(153,0,153,0.15)",
                fill="tonexty",
                showlegend=False,
            ),
        )

        # endregion

    # endregion

    fig.update_layout(
        title={
            "text": "Global Mean Temperature",
            "xanchor": "center",
            "x": 0.5,
            "y": 0.99,
        },
        yaxis={"title": "Deg. C over pre-industrial (1850-1900 mean)"},
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        margin_b=0,
        margin_t=60,
        margin_l=15,
        margin_r=15,
        yaxis=dict(tickmode="linear", tick0=0.5, dtick=0.25),
        yaxis2=dict(tickmode="linear", tick0=0.5, dtick=0.25),
    )

    fig.show()

    if save_figs is True:
        pio.write_html(
            fig,
            file=("./charts/temperature.html").replace(" ", ""),
            auto_open=False,
        )

    # endregion

    # endregion

    # endregion

    ##############################
    # COMPARE TO MODELED RESULTS #
    ##############################

    # region

    # Calculate error between modeled and observed
    climate_error_concentration = (
        abs(
            (
                climate_historical_concentration
                - climate_output_concentration.loc[
                    scenario, climate_historical_concentration.columns.values, :
                ]
                .droplevel("scenario")
                .T
            ).dropna()
            / climate_historical_concentration
        )
        * 100
    )

    climate_error_forcing = (
        abs(
            (
                climate_historical_forcing
                - pd.DataFrame(
                    climate_output_forcing.sum(axis=0)[climate_historical_forcing.index]
                )
            ).dropna()
            / climate_historical_forcing
        )
        * 100
    )

    climate_error_temperature = (
        abs(
            (
                climate_historical_temperature
                - pd.DataFrame(
                    climate_output_temperature.sum(axis=0)[
                        climate_historical_temperature.index
                    ]
                )
            ).dropna()
            / climate_historical_temperature
        )
        * 100
    )

    # Plot error
    climate_error_concentration.plot(
        legend=True, title="Error between PD22 and NOAA GHG Concentrations", ylabel="%"
    )

    climate_error_forcing.plot(
        legend=False, title="Error between PD22 and NOAA Radiative Forcing", ylabel="%"
    )

    climate_error_temperature.plot(
        legend=False, title="Error between PD22 and NOAA Temperature Change", ylabel="%"
    )

    # endregion

    ##############
    #  REFORMAT  #
    ##############

    # region

    climate_historical_concentration = climate_historical_concentration.T
    climate_historical_concentration["model"] = "PD22"
    climate_historical_concentration["scenario"] = "historical"
    climate_historical_concentration["region"] = "world"
    climate_historical_concentration["variable"] = (
        "Concentration|" + climate_historical_concentration.index
    )
    climate_historical_concentration["unit"] = "PPM"
    climate_historical_concentration.set_index(pyam.IAMC_IDX, inplace=True)

    climate_historical_forcing = climate_historical_forcing.T
    climate_historical_forcing["model"] = "PD22"
    climate_historical_forcing["scenario"] = "historical"
    climate_historical_forcing["region"] = "world"
    climate_historical_forcing["variable"] = "Radiative forcing"
    climate_historical_forcing["unit"] = "W/m2"
    climate_historical_forcing.set_index(pyam.IAMC_IDX, inplace=True)

    climate_historical_temperature = climate_historical_temperature.T
    climate_historical_temperature["model"] = "PD22"
    climate_historical_temperature["scenario"] = "historical"
    climate_historical_temperature["region"] = "world"
    climate_historical_temperature["variable"] = "Temperature change"
    climate_historical_temperature["unit"] = "F"
    climate_historical_temperature.set_index(pyam.IAMC_IDX, inplace=True)

    climate_output_concentration["model"] = "PD22"
    climate_output_concentration["region"] = "world"
    climate_output_concentration["variable"] = (
        "Concentration|" + climate_output_concentration.reset_index().product_long
    ).values
    climate_output_concentration["unit"] = "PPM"
    climate_output_concentration = (
        climate_output_concentration.droplevel("product_long")
        .reset_index()
        .set_index(pyam.IAMC_IDX)
    )

    climate_output_forcing["model"] = "PD22"
    climate_output_forcing["region"] = "world"
    climate_output_forcing["variable"] = (
        "Radiative forcing|" + climate_output_forcing.reset_index().product_long
    ).values
    climate_output_forcing["unit"] = "W/m2"
    climate_output_forcing = (
        climate_output_forcing.droplevel("product_long")
        .reset_index()
        .set_index(pyam.IAMC_IDX)
    )

    climate_output_temperature["model"] = "PD22"
    climate_output_temperature["region"] = "world"
    climate_output_temperature["variable"] = (
        "Temperature change|" + climate_output_temperature.reset_index().product_long
    ).values
    climate_output_temperature["unit"] = "F"
    climate_output_temperature = (
        climate_output_temperature.droplevel("product_long")
        .reset_index()
        .set_index(pyam.IAMC_IDX)
    )

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    pd.concat(
        [
            climate_historical_concentration,
            climate_historical_forcing,
            climate_historical_temperature,
            climate_output_concentration,
            climate_output_forcing,
            climate_output_temperature,
        ]
    ).to_csv("podi/data/output/climate/climate_output.csv")

    # endregion

    return
