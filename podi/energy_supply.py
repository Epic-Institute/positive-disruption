#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from podi.data.eia_etl import eia_etl
from podi.data.heat_etl import heat_etl
from podi.data.iea_weo_etl import region_list


def energy_supply(energy_demand):
    saturation_points = pd.read_excel("podi/parameters/techparameters.xlsx").set_index(
        ["R21 Region", "Technology", "Scenario", "Sector", "Metric"]
    )
    electricity_generation_data = eia_etl("podi/data/eia_electricity_generation.csv")
    heat_generation_data = heat_etl("podi/data/heat_generation.csv")

    def historical_electricity_generation(region, technology):
        electricity_generation = (
            electricity_generation_data.loc[
                electricity_generation_data["IEA Region"].str.contains(region, na=False)
            ][electricity_generation_data["Variable"] == technology]
            .set_index(["IEA Region", "Region", "Variable", "Unit"])
            .sum()
        )
        return electricity_generation

    def historical_percent_electricity_generation(
        region, historical_electricity_generation
    ):
        return historical_electricity_generation.div(
            electricity_generation_data.loc[
                electricity_generation_data["IEA Region"].str.contains(region, na=False)
            ][electricity_generation_data["Variable"] == "Generation"]
            .set_index(["IEA Region", "Region", "Variable", "Unit"])
            .sum()
        ).dropna()

    def projected_percent_generation(
        percent_adoption, region, technology, scenario, metric
    ):
        return percent_adoption.loc[:, 2018:].mul(
            (
                saturation_points.loc[
                    region, technology, scenario, slice(None), metric
                ].Value
            )
        )

    def projected_electricity_generation(region, projected_percent_generation):
        return projected_percent_generation.mul(
            energy_demand.loc[region, "TFC", "Total final consumption"].loc["2018"]
        )

    def generation(historical_electricity_generation, projected_generation):
        return pd.concat(
            [
                historical_electricity_generation.reset_index(drop=True),
                projected_generation.iloc[
                    :, len(historical_electricity_generation) :
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
            historical_percent_electricity_generation(
                region, historical_electricity_generation(region, technology)
            )
        ).transpose(copy=True)

        generation_total = generation(
            historical_electricity_generation(region, technology),
            projected_electricity_generation(
                region,
                projected_percent_generation(
                    percent_adoption, region, technology2, scenario, metric,
                ),
            ),
        )
        return generation_total

    #    def prepare_adoption_curve_data(historical_percent_generation):
    #        year = np.arange(len(historical_percent_generation.columns))
    #        percent_adoption = historical_percent_generation.to_numpy()[
    #            ~np.isnan(historical_percent_generation)
    #        ]
    #        return (year, percent_adoption)

    def historical_heat_generation(region, sector, technology):
        return heat_generation_data.loc[region, sector, technology, slice(None)]

    def historical_percent_heat_generation(region, sector, historical_heat_generation):
        return historical_heat_generation.div(
            energy_demand.loc[region, sector, "Heat"]
        ).dropna(axis="columns")

    def projected_percent_heat_generation(
        percent_adoption, region, technology, scenario, sector, metric
    ):
        return percent_adoption.loc[:, 2015:].mul(
            (
                saturation_points.loc[
                    region, technology, scenario, sector, "Saturation Point"
                ].Value
            )
        )

    def projected_heat_generation(region, sector, projected_percent_heat_generation):
        return projected_percent_heat_generation.mul(
            energy_demand.loc[region, sector, "Heat"].loc["2015"]
        )

    def heat_generation(historical_heat_generation, projected_heat_generation):
        return pd.concat(
            [
                historical_heat_generation.reset_index(drop=True),
                projected_heat_generation.iloc[
                    :, len(historical_heat_generation.columns) :
                ].reset_index(drop=True),
            ],
            axis=1,
        )

    def heat_generation_total(region, technology, scenario, sector):
        heat_generation_total = energy_demand.loc[region, sector, "Heat"]
        percent_adoption = adoption_curve(
            historical_percent_heat_generation(
                region, sector, historical_heat_generation(region, sector, technology)
            ),
        ).transpose(copy=True)

        heat_generation_total = heat_generation(
            historical_heat_generation(region, sector, technology),
            projected_heat_generation(
                region,
                sector,
                projected_percent_heat_generation(
                    percent_adoption,
                    region,
                    technology,
                    scenario,
                    sector,
                    "Saturation Point",
                ),
            ),
        )
        return heat_generation_total

    for i in range(0, len(region_list)):
        solarpv_generation = generation_total(
            region_list[i], "Solar", "Solar PV", "Pathway", "Saturation Point"
        ).rename(index={0: "Solar PV"})

        wind_generation = generation_total(
            region_list[i], "Wind", "Wind", "Pathway", "Saturation Point"
        ).rename(index={0: "Wind"})

        #    ff_generation = total electricity generation - sum(
        #        solarpv_generation, wind_generation
        #    )

        solar_thermal_generation = heat_generation_total(
            region_list[i], "Solar Thermal", "Pathway", "Industry",
        ).append(
            heat_generation_total(
                region_list[i], "Solar Thermal", "Pathway", "Buildings"
            )
        )

        #    biochar_generation = heat_generation_total(region_list[i], "Biochar")

        #    bioenergy_generation = heat_generation_total(region_list[i], "Bioenergy")

        #    ff_heat_generation = heat_generation_total(region_list[i], "")

        #    nonelectric_transport = nonelectric_transport(region_list[i])

        # energy_supply_output = pd.concat(
        #    [
        #        solarpv_generation,
        #        wind_generation,
        #            ff_generation,
        #        solar_thermal_generation
        #            biochar_generation,
        #            bioenergy_generation,
        #            ff_heat_generation,
        #            nonelectric_transport,
        #    ]
        # )

    return solarpv_generation, wind_generation, solar_thermal_generation
