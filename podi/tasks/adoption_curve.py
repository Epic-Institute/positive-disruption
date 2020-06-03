#!/usr/bin/env python
# coding: utf-8

import warnings

import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, differential_evolution


def func(x, a, b, c, d):
    return a / (1.0 + numpy.exp(-c * (x - d))) + b


def model_and_scatter_plot(x_data, y_data, fitted_parameters, width, height):
    f = plt.figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    axes = f.add_subplot(111)

    # Plot the raw data as a scatter plot.
    axes.plot(x_data, y_data, "D")

    # Create data for the fitted equation plot.
    x_model = numpy.linspace(min(x_data), max(x_data))
    y_model = func(x_model, *fitted_parameters)

    # Plot the model as a line plot.
    axes.plot(x_model, y_model)

    axes.set_xlabel("X Data")
    axes.set_ylabel("Y Data")

    plt.show()
    plt.close("all")


def adoption_curve(x_data, y_data):
    def sum_of_squared_error(parameters):
        """Function for genetic algorithm to minimize (sum of squared error)."""
        # Do not print warnings by genetic algorithm.
        warnings.filterwarnings("ignore")
        val = func(x_data, *parameters)
        return numpy.sum((y_data - val) ** 2.0)

    # By default, differential_evolution completes by calling curve_fit()
    # using parameter bounds.
    search_bounds = [
        [0.0, 100.0],  # a
        [-10.0, 0.0],  # b
        [0.0, 10.0],  # c
        [0.0, 10.0],  # d
    ]
    # "seed" the numpy random number generator for repeatable results.
    genetic_parameters = differential_evolution(
        sum_of_squared_error, search_bounds, seed=3
    ).x

    # Now call curve_fit without passing bounds from the genetic algorithm,
    # just in case the best fit parameters are aoutside those bounds
    fitted_parameters, _ = curve_fit(func, x_data, y_data, genetic_parameters)
    print("Fitted parameters:", fitted_parameters)
    print()

    model_predictions = func(x_data, *fitted_parameters)

    abs_error = model_predictions - y_data

    sqaured_errors = numpy.square(abs_error)
    mean_squared_errors = numpy.mean(sqaured_errors)
    root_mean_squared_error = numpy.sqrt(mean_squared_errors)
    r_squared = 1.0 - (numpy.var(abs_error) / numpy.var(y_data))

    print()
    print("RMSE:", root_mean_squared_error)
    print("R-squared:", r_squared)
    print()

    model_and_scatter_plot(x_data, y_data, fitted_parameters, width=800, height=600)
