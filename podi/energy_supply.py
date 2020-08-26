#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from podi.data.eia_etl import eia_etl
from podi.data.iea_weo_etl import iea_region_list

data_start_year = "2000"
data_end_year = "2017"
proj_start_year = "2018"
proj_end_year = "2100"

# set energy oversupply proportion, to estimate amount needed to meed CDR energy demand
energy_oversupply_prop = 0.10


def energy_supply(scenario, energy_demand):
    parameters = pd.read_csv("podi/parameters/tech_parameters.csv").set_index(
        ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
    )

    ###############
    # ELECTRICITY #
    ###############
    elec_gen_data = pd.DataFrame(
        eia_etl("podi/data/electricity.csv").loc[:, data_start_year:data_end_year]
    )

    # historical electricity consumption (TWh)
    def hist_elec_consump(region, scenario):
        consump_gen_ratio = pd.to_numeric(
            parameters.loc[
                region, "Grid", scenario, slice(None), "Consumption:Generation"
            ]["Value"].iat[0]
        )
        return (
            elec_gen_data.iloc[
                elec_gen_data.index.get_level_values(1).str.contains(region, na=False)
            ]
            .loc[(slice(None), slice(None), slice(None), scenario, slice(None)), :]
            .mul(consump_gen_ratio)
            .groupby(["Metric"])
            .sum()
        )

    # historical percent of total electricity consumption met by a given technology (propotion)
    def hist_per_elec_consump(region, scenario, hist_elec_consump):
        consump_gen_ratio = pd.to_numeric(
            parameters.loc[
                region, "Grid", scenario, slice(None), "Consumption:Generation"
            ]["Value"].iat[0]
        )
        return hist_elec_consump.div(hist_elec_consump.loc["Generation"]).mul(
            consump_gen_ratio
        )

    # project percent of total electricity consumption met by a given technology (proportion)
    def proj_per_elec_consump(percent_adoption):
        return (
            pd.DataFrame(percent_adoption.loc[proj_start_year:, :])
            .set_index(percent_adoption.loc[proj_start_year:, :].index)
            .T
        )

    # project electricity consumption met by a given technology
    def proj_elec_consump(region, scenario, proj_per_elec_consump):
        proj_elec_consump = pd.DataFrame(
            proj_per_elec_consump.values
            * energy_demand.loc[region, "TFC", "Electricity", scenario]
            .loc[proj_start_year:]
            .values.T
        )

        proj_elec_consump.columns = proj_per_elec_consump.columns

        return proj_elec_consump

    # join timeseries of historical and projected electricity consumption met by a given technology
    def consump(hist_elec_consump, proj_elec_consump):
        return hist_elec_consump.join(proj_elec_consump)

    # join timeseries of historical and projected percent total electricity consumption met by a given technology
    def per_consump(hist_per_elec_consump, proj_per_elec_consump):
        return hist_per_elec_consump.join(proj_per_elec_consump)

    # combine above functions to get electricity consumption met by a given technology
    def consump_total(region, technology, scenario):
        percent_adoption, yoy_adoption_growth = adoption_curve(
            hist_per_elec_consump(
                region, scenario, hist_elec_consump(region, scenario),
            ),
            region,
            technology,
            scenario,
        )

        consump_total = consump(
            hist_elec_consump(region, technology, scenario),
            proj_elec_consump(
                region, scenario, proj_per_elec_consump(percent_adoption),
            )
            * (1 + energy_oversupply_prop),
        )

        consump_cdr = consump(
            hist_elec_consump(region, technology, scenario) * 0,
            proj_elec_consump(
                region, scenario, proj_per_elec_consump(percent_adoption),
            )
            * (energy_oversupply_prop),
        )

        consump_total.index = [region]
        consump_cdr.index = [region]
        percent_adoption.columns = [region]
        yoy_adoption_growth.columns = [region]

        return consump_total, percent_adoption.T, yoy_adoption_growth.T, consump_cdr

    ##########
    #  HEAT  #
    ##########

    heat_generation_data = (
        pd.read_csv("podi/data/heat.csv")
        .fillna(0)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario", "Unit"])
    )

    def historical_heat_generation(region, sector, scenario, technology):
        return heat_generation_data.loc[
            region, sector, technology, scenario, slice(None)
        ]

    def historical_percent_heat_generation(
        region, sector, scenario, historical_heat_generation
    ):
        return historical_heat_generation.div(
            energy_demand.loc[region, sector, "Heat", scenario]
        ).dropna(axis="columns")

    def projected_percent_heat_generation(
        percent_adoption, region, technology, scenario, sector, metric
    ):
        return percent_adoption.loc[:, 2015:].mul(
            (
                pd.to_numeric(
                    parameters.loc[
                        region, technology, scenario, sector, "Saturation Point"
                    ].Value.iat[0]
                )
            )
        )

    def projected_heat_generation(
        region, sector, scenario, projected_percent_heat_generation
    ):
        return projected_percent_heat_generation.mul(
            energy_demand.loc[region, sector, "Heat", scenario].loc["2015"]
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
        heat_generation_total = energy_demand.loc[region, sector, "Heat", scenario]
        percent_adoption = adoption_curve(
            historical_percent_heat_generation(
                region,
                sector,
                historical_heat_generation(region, sector, scenario, technology),
            ),
        )[0].transpose(copy=True)

        heat_generation_total = heat_generation(
            historical_heat_generation(region, sector, scenario, technology),
            projected_heat_generation(
                region,
                sector,
                scenario,
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

    ###########################
    #  NONELECTRIC TRANSPORT  #
    ###########################

    ############
    #  OUTPUT  #
    ############

    solarpv_generation = []
    solarpv_percent_adoption = []
    solarpv_adoption_growth = []
    consump_cdr = []

    for i in range(0, len(iea_region_list)):
        solarpv_generation = pd.DataFrame(solarpv_generation).append(
            consump_total(
                iea_region_list[i], "Solar PV", scenario, "Saturation Point",
            )[0]
        )
        solarpv_percent_adoption = pd.DataFrame(solarpv_percent_adoption).append(
            consump_total(iea_region_list[i], "Solar PV", scenario)[1]
        )

        solarpv_adoption_growth = pd.DataFrame(solarpv_adoption_growth).append(
            consump_total(iea_region_list[i], "Solar PV", scenario)[2]
        )

        consump_cdr = pd.DataFrame(consump_cdr).append(
            consump_total(iea_region_list[i], "Solar PV", scenario)[3]
        )

    return (
        solarpv_generation,
        solarpv_percent_adoption,
        solarpv_adoption_growth,
        consump_cdr,
    )
