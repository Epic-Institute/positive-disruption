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


def adoption_curve_demand(
    parameters,
    value,
    scenario,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    # Create x array (year) and y array (linear scale from zero to saturation value)
    x_data = np.arange(0, proj_end_year - data_end_year + 1, 1)
    y_data = np.zeros((1, len(x_data)))
    y_data[:] = np.NaN
    y_data = y_data.squeeze().astype(float)
    y_data[0] = 0
    y_data[-1] = parameters.loc["saturation point"].value.astype(float)

    y_data = np.array((pd.DataFrame(y_data).interpolate()).squeeze())

    # Load search bounds for logistic function parameters
    search_bounds = [
        (
            pd.to_numeric(parameters.loc["parameter a min"].value),
            pd.to_numeric(parameters.loc["parameter a max"].value),
        ),
        (
            pd.to_numeric(parameters.loc["parameter b min"].value),
            pd.to_numeric(parameters.loc["parameter b max"].value),
        ),
        (
            pd.to_numeric(parameters.loc["saturation point"].value),
            pd.to_numeric(parameters.loc["saturation point"].value),
        ),
        (
            0,
            0,
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

    pd.concat(
        [
            pd.DataFrame(
                np.array([value.name[0], value.name[1], value.name[2], value.name[3]])
            ).T,
            pd.DataFrame(y).T,
        ],
        axis=1,
    ).to_csv(
        "podi/data/energy_adoption_curves.csv",
        mode="a",
        header=None,
        index=False,
    )

    return
