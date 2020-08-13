#!/usr/bin/env python
# coding: utf-8

import warnings
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit, differential_evolution


def func(x, a, b, c):
    # return 1 / (1.0 + a * np.exp(-c * x)) ** (1 / b)
    # return np.exp(a + b * x) / (1.0 + np.exp(a + b * x))
    return c / (1 + np.exp(-a * (x - b)))


def adoption_curve(value, c):
    x_data = np.arange(len(value.T))
    y_data = value.to_numpy()[~np.isnan(value)]

    def sum_of_squared_error(parameters):
        warnings.filterwarnings("ignore")
        val = func(x_data, *parameters)
        return np.sum((y_data - val) ** 2.0)

    # By default, differential_evolution completes by calling curve_fit()
    # using parameter bounds.
    search_bounds = [
        [0.0, 5.0],
        [0.0, 100],
        [c.astype(float), c.astype(float)],
    ]  # a  # b  # c
    # "seed" the numpy random number generator for repeatable results.
    genetic_parameters = differential_evolution(
        sum_of_squared_error, search_bounds, seed=3
    ).x

    # Now call curve_fit without passing bounds from the genetic algorithm,
    # just in case the best fit parameters are outside those bounds
    # fitted_parameters, _ = curve_fit(
    #    func, x_data, y_data, genetic_parameters, maxfev=100000
    # )

    # print("genetic_parameters = ", genetic_parameters)

    # model_predictions = func(x_data, *fitted_parameters)
    # print('model_predictions = ', model_predictions)

    # abs_error = model_predictions - y_data
    # print('abs_error = ', abs_error)

    # squared_errors = np.square(abs_error)
    # print('squared_errors = ', squared_errors)

    # mean_squared_errors = np.mean(squared_errors)
    # print('mean_squared_errors = ', mean_squared_errors)

    # root_mean_squared_error = np.sqrt(mean_squared_errors)
    # print("root_mean_squared_error = ", root_mean_squared_error)

    # r_squared = 1.0 - (np.var(abs_error) / np.var(y_data))
    # print("r_squared = ", r_squared)

    x = np.arange(2100 - value.columns.astype(int).values[0] + 1)
    y = np.array(func(x, *genetic_parameters))
    years = np.linspace(
        value.columns.astype(int).values[0],
        2100,
        2100 - value.columns.astype(int).values[0] + 1,
    ).astype(int)

    return pd.DataFrame(data=y, index=years)
