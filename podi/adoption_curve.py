#!/usr/bin/env python
# coding: utf-8

import warnings
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit, differential_evolution


def func(x, a, b, c):
    return 1 / (1.0 + a * np.exp(-c * x)) ** (1 / b)


def adoption_curve(value):
    x_data = np.arange(len(value))
    y_data = value.to_numpy()[~np.isnan(value)]

    def sum_of_squared_error(parameters):
        warnings.filterwarnings("ignore")
        val = func(x_data, *parameters)
        return np.sum((y_data - val) ** 2.0)

    # By default, differential_evolution completes by calling curve_fit()
    # using parameter bounds.
    search_bounds = [[0.0, 5.0], [0.0, 5.0], [0.0, 5.0]]  # a  # b  # c
    # "seed" the numpy random number generator for repeatable results.
    genetic_parameters = differential_evolution(
        sum_of_squared_error, search_bounds, seed=3
    ).x

    # Now call curve_fit without passing bounds from the genetic algorithm,
    # just in case the best fit parameters are outside those bounds
    fitted_parameters, _ = curve_fit(
        func, x_data, y_data, genetic_parameters, maxfev=10000
    )

    # model_predictions = func(x_data, *fitted_parameters)

    # abs_error = model_predictions - y_data

    # sqaured_errors = np.square(abs_error)
    # mean_squared_errors = np.mean(sqaured_errors)
    # root_mean_squared_error = np.sqrt(mean_squared_errors)
    # r_squared = 1.0 - (np.var(abs_error) / np.var(y_data))

    x = np.arange(121)
    y = np.array(func(x, *fitted_parameters))
    years = np.linspace(1980, 2100, 121).astype(int)

    return pd.DataFrame(data=y, index=years)
