#!/usr/bin/env python
# coding: utf-8

from os import sched_get_priority_max
import warnings
import pandas as pd
import numpy as np
import scipy
from scipy.optimize import differential_evolution
from scipy.sparse import data


def func(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def func2(x, a, b, c, d):
    return a * x + b


def adoption_curve_demand(
    value, region, scenario, sector, data_start_year, data_end_year, proj_end_year
):

    # Load tech parameters to get 2050 energy demand reduction values
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])

    # Create x array (year) and y array (linear scale from zero to saturation value)
    x_data = np.arange(data_end_year, 2051, 1)
    y_data = np.zeros((1, data_end_year - data_start_year + 1))
    y_data[:, :] = np.NaN
    y_data[:, 0] = parameters.loc[
        region, value.name[1], scenario, sector, "saturation point"
    ].Value
    y_data[:, -1] = parameters.loc[
        region, value.name[1], scenario, sector, "saturation point"
    ].Value
    y_data = np.array((pd.DataFrame(y_data).interpolate(axis=1)).squeeze())

    def sum_of_squared_error(parameters):
        warnings.filterwarnings("ignore")
        val = func(x_data, *parameters)
        return np.sum((y_data - val) ** 2.0)

    search_bounds = [
        (
            pd.to_numeric(
                parameters.loc[
                    region, value.name[1], scenario, sector, "parameter a min"
                ].Value
            ),
            pd.to_numeric(
                parameters.loc[
                    region, value.name[1], scenario, sector, "parameter a max"
                ].Value
            ),
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region, value.name[1], scenario, sector, "parameter b min"
                ].Value
            ),
            pd.to_numeric(
                parameters.loc[
                    region, value.name[1], scenario, sector, "parameter b max"
                ].Value
            ),
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name[1],
                    scenario,
                    sector,
                    "saturation point",
                ].Value
            ),
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name[1],
                    scenario,
                    sector,
                    "saturation point",
                ].Value
            ),
        ),
        (
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name[1],
                    scenario,
                    sector,
                    "floor",
                ].Value
            ),
            pd.to_numeric(
                parameters.loc[
                    region,
                    value.name[1],
                    scenario,
                    sector,
                    "floor",
                ].Value
            ),
        ),
    ]

    if scenario == "baseline":
        x = np.arange(proj_end_year - pd.to_numeric(value.index[0]) + 1)
        # y = np.full((len(x), 1), y_data[-1])
        y = func2(
            x,
            min(0.0018, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
            (y_data[-1]),
            0,
            0,
        )
        genetic_parameters = [0, 0, 0, 0]
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

    x = np.arange(proj_end_year - data_end_year + 1)
    y = np.array(func(x, *genetic_parameters))

    years = np.linspace(
        pd.to_numeric(data_end_year),
        proj_end_year,
        proj_end_year - pd.to_numeric(data_end_year) + 1,
    ).astype(int)

    """
    # set maximum annual growth rate
    max_growth = (
        pd.to_numeric(
            parameters.loc[
                region, value.name, scenario, sector, "Max annual growth"
            ].Value
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

    df = pd.DataFrame(data=y, index=years).T.reset_index().drop(columns="index")
    df["Region"] = value.name[0]
    df["Product"] = value.name[1]
    df["Scenario"] = value.name[2]
    df["Sector"] = value.name[3]

    return df
