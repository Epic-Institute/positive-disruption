#!/usr/bin/env python
# coding: utf-8

import warnings
import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution


def func(x, a, b, c, d):
    return c / (1 + np.exp(-a * (x - b))) + d


def func2(x, a, b):
    return a * x + b


def adoption_curve_afolu(
    value, region, scenario, sector, data_start_year, data_end_year, proj_end_year
):

    # Load tech parameters
    parameters = pd.read_csv("podi/data/tech_parameters_afolu.csv").set_index(
        ["Region", "Technology", "Scenario", "Sector", "Metric"]
    )

    # Take 10 years prior data to fit logistic function
    x_data = np.arange(0, len(value.loc[data_end_year - 10 : proj_end_year]), 1)
    y_data = np.zeros((1, len(x_data)))
    y_data[:, :] = np.NaN
    y_data = y_data.squeeze().astype(float)
    y_data[:11] = value.loc[data_end_year - 10 : data_end_year]
    y_data[-1] = parameters.loc["saturation point"].Value.astype(float)

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
        x = np.arange(proj_end_year - pd.to_numeric(value.index[0]) + 1)
        # y = np.full((len(x), 1), y_data[-1])
        y = func2(
            x,
            min(0.0018, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
            (y_data[-1]),
        )
        genetic_parameters = [0, 0, 0, 0]

        if value.name == "Spanish Reforestation":
            y = func2(
                x,
                min(0.002, max(0.00001, ((y_data[-1] - y_data[0]) / len(y_data)))),
                (y_data[-1]),
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
        x = np.arange(proj_end_year - pd.to_numeric(value.index[0]) + 1)
        y = np.array(func(x, *genetic_parameters))

    years = np.linspace(
        pd.to_numeric(value.index[0]),
        proj_end_year,
        proj_end_year - pd.to_numeric(value.index[0]) + 1,
    ).astype(int)

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
