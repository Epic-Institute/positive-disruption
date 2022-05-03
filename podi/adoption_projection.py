# region

import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution
from numpy import NaN
import os

# endregion


def linear(x, a, b, c):
    return a * x + b


def logistic(x, a, b, c):
    return c / (1 + np.exp(-a * (x - b)))


def adoption_projection(
    input_data, output_start_date, output_end_date, change_model, change_parameters
):
    """Given input data of arbitrary start/end date, and desired output start/end date, and model to fit to this data (linear/logistic/generalized logistic), this function provides output that combines input data with projected change in that data"""

    y = pd.DataFrame(input_data).T

    # Handle cases where saturation point is below current value, by making saturation point equidistant from current value but in positive direction
    if (
        y.loc[:, input_data.last_valid_index()].values
        > y.loc[:, output_end_date].values
    ):
        y.loc[:, output_end_date] = y.loc[:, input_data.last_valid_index()] + abs(
            y.loc[:, output_end_date] - y.loc[:, input_data.last_valid_index()]
        )
        neg = True
    else:
        neg = False

    y = np.array(
        y.interpolate(method="linear", limit_area="inside", axis=1).dropna(axis=1)
    )

    # Save intermediate projections to logfile
    pd.DataFrame(input_data.name).to_csv(
        "podi/data/adoption_projection_logfile1.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_projection_logfile1.csv"),
    )

    # Load search bounds function parameters
    search_bounds = [
        (
            change_parameters.loc["parameter a min"].Value,
            change_parameters.loc["parameter a max"].Value,
        ),
        (
            change_parameters.loc["parameter b min"].Value,
            change_parameters.loc["parameter b max"].Value,
        ),
        (
            change_parameters.loc["saturation point"].Value,
            change_parameters.loc["saturation point"].Value,
        ),
    ]

    # Define sum of squared error function and use differential_evolution() to compute genetic parameters
    if change_model == "linear":

        def sum_of_squared_error(change_parameters):
            return np.sum(
                (
                    y[0]
                    - linear(
                        np.arange(0, len(y[0] + 1), 1),
                        *change_parameters,
                    )
                )
                ** 2.0
            )

        genetic_parameters = differential_evolution(
            sum_of_squared_error,
            search_bounds,
            seed=3,
            polish=False,
            mutation=(0, 1.99),
        ).x

        y = np.array(linear(np.arange(0, 200, 1), *genetic_parameters))

    else:

        def sum_of_squared_error(change_parameters):
            return np.sum(
                (
                    y[0]
                    - logistic(
                        np.arange(0, len(y[0] + 1), 1),
                        *change_parameters,
                    )
                )
                ** 2.0
            )

        genetic_parameters = differential_evolution(
            sum_of_squared_error,
            search_bounds,
            seed=3,
            polish=False,
            mutation=(0, 1.99),
        ).x

        y = np.array(logistic(np.arange(0, 200, 1), *genetic_parameters))

    # Rejoin with input data at point where projection results in smooth growth
    y2 = np.concatenate(
        [
            input_data.loc[: input_data.last_valid_index()].values,
            y[y >= input_data.loc[input_data.last_valid_index()]],
        ]
    )

    # Compare modeled to actual
    # pd.DataFrame([y, y2]).T.plot()

    # Save projections to logfile
    pd.DataFrame(input_data.name).to_csv(
        "podi/data/adoption_projection_logfile2.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_projection_logfile2.csv"),
    )

    # Save logistic function parameters to output file for inspection
    pd.DataFrame(
        (
            input_data.name[0],
            genetic_parameters[0],
            genetic_parameters[1],
            genetic_parameters[2],
        )
    ).T.to_csv(
        "podi/data/adoption_curve_parameters.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_curve_parameters.csv"),
    )

    # Save model to output file
    pd.Series(
        data=y[: len(input_data.index)],
        index=input_data.index,
        name=input_data.name,
    ).T.to_csv(
        "podi/data/adoption_curve_models.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_curve_models.csv"),
    )

    return pd.Series(
        data=y2[: len(input_data.index)],
        index=input_data.index,
        name=input_data.name,
    )
