# region

import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution

# endregion


def linear(x, a, b, c, d):
    return a * x + d


def logistic(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def adoption_projection(
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
            y_data[10],
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

    return pd.Series(
        data=y[
            : len(np.arange(input_data.first_valid_index(), output_end_date + 1, 1))
        ],
        index=np.arange(input_data.first_valid_index(), output_end_date + 1, 1),
        name=input_data.name,
    )


def adoption_projection_demand(
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
        return np.sum((y_data - logistic(x_data, *parameters)) ** 2.0)

    # Generate genetic_parameters. For baseline scenarios, projections are linear
    if scenario == "baseline":
        y = linear(
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

    y = np.array(logistic(x_data, *genetic_parameters))

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
