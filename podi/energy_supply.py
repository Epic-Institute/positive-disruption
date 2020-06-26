#!/usr/bin/env python

import pandas as pd
import numpy as np
from podi.adoption_curve import adoption_curve
from podi.data.eia_etl import eia_etl

"TODO: parameterize start year and units"


def energy_supply(energy_demand):
    saturation_points = pd.read_excel("podi/parameters/techparameters.xlsx")
    electricity_generation, electricity_generation_total = eia_etl(
        "podi/data/eia_electricity_generation.csv"
    )

    def historical_generation(region, technology):
        return (
            electricity_generation[
                (electricity_generation["API"].str.contains(region))
                & (electricity_generation["World"].str.contains(technology))
            ]
            .set_index(["API", "World"])
            .astype(float)
        )

    def historical_percent_generation(historical_generation):
        return historical_generation.div(electricity_generation_total.sum()).dropna(
            axis="columns"
        )

    def prepare_adoption_curve_data(historical_percent_generation):
        year = np.arange(len(historical_percent_generation.columns))
        percent_adoption = historical_percent_generation.to_numpy()[
            ~np.isnan(historical_percent_generation)
        ]
        return (year, percent_adoption)

    def projected_percent_generation(percent_adoption, technology, scenario, metric):
        return percent_adoption.loc[:, 2018:].mul(
            (
                saturation_points[
                    (saturation_points.Technology == technology)
                    & (saturation_points.Scenario == scenario)
                    & (saturation_points.Metric == metric)
                ]
            ).Value.iat[0]
        )

    def projected_generation(projected_percent_generation):
        return projected_percent_generation.mul(
            energy_demand.loc["TFC"].loc["Total final consumption"].loc["2018"]
        )

    def generation(historical_generation, projected_generation):
        return pd.concat(
            [
                historical_generation.reset_index(drop=True),
                projected_generation.iloc[
                    :, len(historical_generation.columns) :
                ].reset_index(drop=True),
            ],
            axis=1,
        )

    def percent_generation(historical_percent_generation, projected_percent_generation):
        return pd.concat(
            [
                historical_percent_generation.reset_index(drop=True),
                projected_percent_generation.loc[:, 2018:].reset_index(drop=True),
            ],
            axis=1,
        )

    def generation_total(region, technology, technology2, scenario, metric):
        percent_adoption = adoption_curve(
            historical_percent_generation(historical_generation(region, technology))
        ).transpose(copy=True)

        generation_total = generation(
            historical_generation(region, technology),
            projected_generation(
                projected_percent_generation(
                    percent_adoption, technology2, scenario, metric,
                )
            ),
        )
        return generation_total

    solarpv_generation = generation_total(
        "WORL", "Solar ", "Solar PV", "positive disruption", "Saturation Point, M"
    ).rename(index={0: "Solar PV"})

    wind_generation = generation_total(
        "WORL", "Wind", "Wind", "positive disruption", "Saturation Point, M"
    ).rename(index={0: "Wind"})

    energy_supply = pd.concat([solarpv_generation, wind_generation])

    return energy_supply
