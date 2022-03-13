#!/usr/bin/env python
# coding: utf-8

from os import sched_get_priority_max
import warnings
import pandas as pd
import numpy as np
import scipy
from scipy.optimize import differential_evolution
from scipy.sparse import data
from numpy import NaN
import os


def func(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def func2(x, a, b):
    return a * x + b


def adoption_curve(
    parameters,
    value,
    scenario,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    # Take 10 years prior data to fit logistic function
    x_data = np.arange(0, len(value[proj_end_year - data_end_year - 10 :]), 1)
    y_data = np.zeros((1, len(x_data)))
    y_data[:, :] = np.NaN
    y_data = y_data.squeeze().astype(float)
    y_data[:10] = value.loc[data_end_year - 10 : data_end_year - 1]
    y_data[-1] = parameters.loc["saturation point"].Value.astype(float)

    # Handle cases where saturation point is below current value, by making saturation point equidistant from current value but in positive direction
    if y_data[9] > y_data[-1]:
        y_data[-1] = y_data[9] + abs(y_data[-1] - y_data[9])
        neg = True
    else:
        neg = False

    y_data = np.array((pd.DataFrame(y_data).interpolate(method="linear")).squeeze())

    pd.DataFrame(y_data).T.to_csv(
        "podi/data/y_data.csv",
        mode="a",
        header=not os.path.exists("podi/data/y_data.csv"),
    )

    # Load search bounds for logistic function parameters
    search_bounds = [
        (
            pd.to_numeric(parameters.loc["parameter a min"].Value),
            pd.to_numeric(parameters.loc["parameter a max"].Value),
        ),
        (
            pd.to_numeric(parameters.loc["parameter b min"].Value),
            pd.to_numeric(parameters.loc["parameter b max"].Value),
        ),
        (
            pd.to_numeric(parameters.loc["saturation point"].Value),
            pd.to_numeric(parameters.loc["saturation point"].Value),
        ),
        (
            y_data[9],
            y_data[9],
        ),
    ]

    # Define sum of squared error function
    def sum_of_squared_error(parameters):
        return np.sum((y_data - func(x_data, *parameters)) ** 2.0)

    # Generate genetic_parameters. For baseline scenarios, projections are linear
    if scenario == "baseline":
        y = func2(
            x_data,
            min(0.0018, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
            (y_data[-1]),
        )
        genetic_parameters = [0, 0, 0, 0]
    else:
        genetic_parameters = differential_evolution(
            sum_of_squared_error,
            search_bounds,
            seed=3,
            polish=False,
            updating="immediate",
            mutation=(0, 1),
        ).x

    y = np.array(func(x_data, *genetic_parameters))

    """
    y = (
        pd.DataFrame(y)
        .pct_change()
        .multiply((y[-1]-value.loc[data_end_year-1])/(y[-1]-y[10]))
        .add(1)
        .fillna(y[10])
        .cumprod()[: (proj_end_year - data_end_year + 1)]
    )
    """

    # Rejoin with historical data at point where projection curve results in smooth growth
    y = np.concatenate(
        [
            value[: proj_end_year - data_end_year].values,
            y[y >= value[data_end_year - 1]].squeeze(),
        ]
    )[: (proj_end_year - data_start_year + 1)]

    years = np.linspace(
        data_start_year, proj_end_year, proj_end_year - data_start_year + 1
    ).astype(int)

    # Flip sign on cases where current value was greater than saturation point value
    """
    if neg == True:
        y[proj_end_year - data_end_year :] = -y[proj_end_year - data_end_year :]
    """
    pd.DataFrame(y).T.to_csv(
        "podi/data/y_data2.csv",
        mode="a",
        header=not os.path.exists("podi/data/y_data2.csv"),
    )

    # Save logistic function parameters to output file for inspection
    pd.DataFrame(
        (
            value.name[0],
            value.name[5],
            value.name[1],
            genetic_parameters[0],
            genetic_parameters[1],
            genetic_parameters[2],
            genetic_parameters[3],
        )
    ).T.to_csv(
        "podi/data/adoption_curve_parameters.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_curve_parameters.csv"),
    )

    return pd.Series(data=y, index=years, name=value.name)
