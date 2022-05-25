# region

import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution
import os

# endregion


def linear(x, a, b, c):
    return a * x + b


def logistic(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def adoption_curve(
    input_data, output_start_date, output_end_date, change_model, change_parameters
):
    """Given input data of arbitrary start/end date, and desired output start/end date, and model to fit to this data (linear/logistic/generalized logistic), this function provides output that combines input data with projected change in that data"""

    # Take 10 years prior data to fit logistic function
    x_data = np.arange(0, output_end_date - input_data.last_valid_index() + 11, 1)
    y_data = np.zeros((1, len(x_data)))
    y_data[:, :] = np.NaN
    y_data = y_data.squeeze().astype(float)
    y_data[:11] = input_data.loc[
        input_data.last_valid_index() - 10 : input_data.last_valid_index()
    ]
    y_data[-1] = change_parameters.loc["saturation point"].value.astype(float)

    # Handle cases where saturation point is below current value, by making saturation point equidistant from current value but in positive direction
    if y_data[10] > y_data[-1]:
        y_data[-1] = y_data[10] + abs(y_data[-1] - y_data[10])
        neg = True
    else:
        neg = False

    y_data = np.array((pd.DataFrame(y_data).interpolate(method="linear")).squeeze())

    # Save intermediate projections to logfile
    pd.DataFrame(y_data).T.to_csv(
        "podi/data/adoption_projection_logfile1.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_projection_logfile1.csv"),
    )

    # Load search bounds for logistic function parameters
    search_bounds = [
        (
            pd.to_numeric(change_parameters.loc["parameter a min"].value),
            pd.to_numeric(change_parameters.loc["parameter a max"].value),
        ),
        (
            pd.to_numeric(change_parameters.loc["parameter b min"].value),
            pd.to_numeric(change_parameters.loc["parameter b max"].value),
        ),
        (
            pd.to_numeric(change_parameters.loc["saturation point"].value),
            pd.to_numeric(change_parameters.loc["saturation point"].value),
        ),
        (
            y_data[10],
            y_data[10],
        ),
    ]

    # Define sum of squared error function
    def sum_of_squared_error(change_parameters):
        return np.sum((y_data - logistic(x_data, *change_parameters)) ** 2.0)

    # Generate genetic_parameters. For baseline scenarios, projections are linear
    if change_model == "linear":
        y = linear(
            x_data,
            min(0.04, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
            0,
            0,
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

        y = np.array(logistic(x_data, *genetic_parameters))

    # Rejoin with input data at point where projection curve results in smooth growth
    y = np.concatenate(
        [
            input_data.loc[: input_data.last_valid_index()].values,
            y[y >= input_data.loc[input_data.last_valid_index()]].squeeze(),
        ]
    )[: (output_end_date - input_data.first_valid_index() + 1)]

    # Save projections to logfile
    pd.DataFrame(y).to_csv(
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
            genetic_parameters[3],
        )
    ).T.to_csv(
        "podi/data/adoption_curve_parameters.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_curve_parameters.csv"),
    )

    # Save model to output file
    pd.Series(
        data=y[
            : len(np.arange(input_data.first_valid_index(), output_end_date + 1, 1))
        ],
        index=np.arange(input_data.first_valid_index(), output_end_date + 1, 1),
        name=input_data.name,
    ).T.to_csv(
        "podi/data/adoption_curve_models.csv",
        mode="a",
        header=not os.path.exists("podi/data/adoption_curve_models.csv"),
    )

    return pd.Series(
        data=y[
            : len(np.arange(input_data.first_valid_index(), output_end_date + 1, 1))
        ],
        index=np.arange(input_data.first_valid_index(), output_end_date + 1, 1),
        name=input_data.name,
    )
