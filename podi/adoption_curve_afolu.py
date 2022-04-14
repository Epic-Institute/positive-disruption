#!/usr/bin/env python
# coding: utf-8

import warnings
import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution


def func(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def func2(x, a, b, c, d):
    return a * x + b


def adoption_curve_afolu(value, region, scenario, sector):
    parameters = pd.read_csv("podi/data/tech_parameters_afolu.csv").set_index(
        ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
    )

    # for technologies defined to remain constant/decrease, set saturation point to value of historical adoption level
    if (
        np.any(
            pd.Series(value.name).isin(
                [
                    "Nuclear",
                    "Fossil fuels",
                    "Biomass and waste",
                    "Bioenergy",
                    "Coal",
                    "Hydroelectric pumped storage",
                    "Natural gas",
                    "Oil",
                    "Other sources",
                ]
            )
        )
        is True
    ):
        from podi.energy_supply import (
            hist_elec_consump,
            hist_per_elec_consump,
            hist_heat_consump,
            hist_per_heat_consump,
            data_end_year,
        )

        if sector == "Electricity":
            parameters.loc[
                region, value.name, scenario, sector, "Saturation Point"
            ].Value[0] = hist_per_elec_consump(
                region, scenario, hist_elec_consump(region, scenario)
            ).loc[
                value.name, str(data_end_year)
            ]
        else:
            parameters.loc[
                region, value.name, scenario, sector, "Saturation Point"
            ].Value[0] = hist_per_heat_consump(
                region, scenario, hist_heat_consump(region, scenario)
            ).loc[
                value.name, str(data_end_year)
            ]

    x_data = np.arange(len(value.T))
    y_data = value.to_numpy()[~np.isnan(value)]

    def sum_of_squared_error(parameters):
        warnings.filterwarnings("ignore")
        val = func(x_data, *parameters)
        return np.sum((y_data - val) ** 2.0)

    search_bounds = [
        (
            pd.to_numeric(
                parameters.loc[
                    region, value.name, scenario, sector, "Parameter a, min"
                ].Value[0]
            ),
            pd.to_numeric(
                parameters.loc[
                    region, value.name, scenario, sector, "Parameter a, max"
                ].Value[0]
            ),
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region, value.name, scenario, sector, "Parameter b, min"
                ].Value[0]
            ),
            pd.to_numeric(
                parameters.loc[
                    region, value.name, scenario, sector, "Parameter b, max"
                ].Value[0]
            ),
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name,
                    scenario,
                    sector,
                    "Saturation Point",
                ].Value[0]
            )
            / 100,
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name,
                    scenario,
                    sector,
                    "Saturation Point",
                ].Value[0]
            )
            / 100,
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name,
                    scenario,
                    sector,
                    "Floor",
                ].Value[0]
            )
            / 100,
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name,
                    scenario,
                    sector,
                    "Floor",
                ].Value[0]
            )
            / 100,
        ),
    ]

    if scenario == "baseline":
        x = np.arange(2100 - pd.to_numeric(value.index[0]) + 1)
        # y = np.full((len(x), 1), y_data[-1])
        y = func2(
            x,
            min(0.0018, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
            (y_data[-1]),
            0,
            0,
        )
        genetic_parameters = [0, 0, 0, 0]

        if value.name == "Spanish Reforestation":
            y = func2(
                x,
                min(0.002, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
                (y_data[-1]),
                0,
                0,
            )
    else:
        # "seed" the numpy random number generator for repeatable results.
        genetic_parameters = differential_evolution(
            sum_of_squared_error,
            search_bounds,
            seed=3,
            polish=False,
            updating="immediate",
            mutation=(0, 1),
        ).x
        x = np.arange(2100 - pd.to_numeric(value.index[0]) + 1)
        y = np.array(func(x, *genetic_parameters))

    """
    # Now call curve_fit without passing bounds from the genetic algorithm, just in case the best fit parameters are outside those bounds
    fitted_parameters, _ = curve_fit(func, x_data, y_data, maxfev=10000)
    x = np.arange(2100 - pd.to_numeric(value.index[0]) + 1)
    y = np.array(func(x, *genetic_parameters))
    """

    """
    print("genetic_parameters = ", genetic_parameters)

    model_predictions = func(x_data, *genetic_parameters)
    print('model_predictions = ', model_predictions)
    abs_error = model_predictions - y_data
    print('abs_error = ', abs_error)

    squared_errors = np.square(abs_error)
    print('squared_errors = ', squared_errors)

    mean_squared_errors = np.mean(squared_errors)
    print('mean_squared_errors = ', mean_squared_errors)

    root_mean_squared_error = np.sqrt(mean_squared_errors)
    print("root_mean_squared_error = ", root_mean_squared_error)

    r_squared = 1.0 - (np.var(abs_error) / np.var(y_data))
    print("r_squared = ", r_squared)
    """

    years = np.linspace(
        pd.to_numeric(value.index[0]),
        2100,
        2100 - pd.to_numeric(value.index[0]) + 1,
    ).astype(int)

    """
    # set maximum annual growth rate
    max_growth = (
        pd.to_numeric(
            parameters.loc[
                region, value.name, scenario, sector, "Max annual growth"
            ].Value[0]
        )
        / 100
    )

    y_growth = pd.DataFrame(y).pct_change().replace(NaN, 0)
    for i in range(1, len(y_data)):
        y_growth = pd.DataFrame(y).pct_change().replace(NaN, 0)
        if y_growth[0][i].astype(float) <= 0:
            y_growth[0][i] = 0
            y_data[i] = y_data[i - 1]
            genetic_parameters = differential_evolution(
                sum_of_squared_error, search_bounds, seed=3
            ).x
            y = np.array(func(x, *genetic_parameters))
        elif y_growth[0][i].astype(float) > max_growth.astype(float):
            y_growth[0][i] = max_growth
            y_data[i] = y_data[i - 1] * (1 + max_growth)
            genetic_parameters = differential_evolution(
                sum_of_squared_error, search_bounds, seed=3
            ).x
            y = np.array(func(x, *genetic_parameters))

    y_growth = np.array(y_growth)
    """

    genetic_parameters = pd.DataFrame(genetic_parameters, ["a", "b", "c", "d"]).T.round(
        decimals=3
    )

    genetic_parameters["Region"] = region
    genetic_parameters["Sector"] = sector
    genetic_parameters["Technology"] = value.name
    genetic_parameters = genetic_parameters.reindex(
        columns=["Region", "Sector", "Technology", "a", "b", "c", "d"]
    )

    if scenario == "pathway":
        params = pd.read_csv("podi/data/params.csv")
        params = params.append(genetic_parameters)
        params.drop_duplicates(inplace=True)
        params.to_csv("podi/data/params.csv", index=False)

    return pd.DataFrame(data=y, index=years)
