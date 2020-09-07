#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from podi.data.eia_etl import eia_etl
from podi.data.bnef_etl import bnef_etl
from podi.data.iea_weo_etl import iea_region_list
from numpy import NaN

data_start_year = 2000
data_end_year = 2017
near_proj_start_year = data_end_year + 1
near_proj_end_year = 2025
long_proj_start_year = near_proj_end_year + 1
long_proj_end_year = 2100

# set energy oversupply proportion, to estimate CDR energy demand
energy_oversupply_prop = 0.0


def energy_supply(scenario, energy_demand):
    parameters = pd.read_csv("podi/parameters/tech_parameters.csv").set_index(
        ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
    )

    ###############
    # ELECTRICITY #
    ###############
    elec_gen_data = pd.DataFrame(
        eia_etl("podi/data/electricity.csv").loc[
            :, str(data_start_year) : str(data_end_year)
        ]
    )

    near_elec_proj_data = pd.DataFrame(
        bnef_etl("podi/data/bnef.csv").loc[
            :, str(near_proj_start_year - 1) : str(near_proj_end_year)
        ]
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
        return hist_elec_consump.div(hist_elec_consump.loc["Generation"])

    # nearterm projected electricity consumption
    def near_proj_elec_consump(region, scenario):
        consump_gen_ratio = pd.to_numeric(
            parameters.loc[
                region, "Grid", scenario, slice(None), "Consumption:Generation"
            ]["Value"].iat[0]
        )

        if scenario == "Baseline":
            near_proj_start_year = data_end_year
            long_proj_start_year = data_end_year + 1
            near_proj_end_year = data_end_year
            return near_proj_start_year, long_proj_start_year, near_proj_end_year
        else:
            return (
                near_elec_proj_data.iloc[
                    near_elec_proj_data.index.get_level_values(1).str.contains(
                        region, na=False
                    )
                ]
                .loc[(slice(None), slice(None), slice(None), scenario, slice(None)), :]
                .mul(consump_gen_ratio)
                .groupby(["Metric"])
                .sum()
            )

    # nearterm projected percent of total electricity consumption met by a given technology (proportion)
    def near_proj_per_elec_consump(
        region,
        scenario,
        hist_elec_consump,
        hist_per_elec_consump,
        near_proj_elec_consump,
    ):
        consump_gen_ratio = pd.to_numeric(
            parameters.loc[
                region, "Grid", scenario, slice(None), "Consumption:Generation"
            ]["Value"].iat[0]
        )
        foo = near_proj_elec_consump.div(near_proj_elec_consump.loc["Generation"]).mul(
            consump_gen_ratio
        )

        # normalize to historical data
        foo = (
            foo.pct_change(axis=1)
            .replace(NaN, 0)
            .loc[:, str(near_proj_start_year) :]
            .apply(lambda x: x + 1, axis=1)
        )

        foo = hist_per_elec_consump.loc[:, : str(data_end_year - 1)].join(
            (
                (hist_per_elec_consump.loc[:, str(data_end_year) :].join(foo)).cumprod(
                    axis=1
                )
            )
        )
        return foo

    # longterm projected percent of total electricity consumption met by a given technology (proportion)
    def proj_per_elec_consump(region, near_proj_per_elec_consump):
        foo = near_proj_per_elec_consump.apply(
            adoption_curve,
            axis=1,
            args=(
                [
                    region,
                    scenario,
                ]
            ),
        )
        perc = []
        for i in range(0, len(foo.index)):
            perc = pd.DataFrame(perc).append(foo[foo.index[i]][0].T)

        perc = pd.DataFrame(perc.loc[:, near_proj_start_year:]).set_index(foo.index)

        # set nuclear to be constant

        # set fossil fuel generation to fill balance
        perc.loc["Fossil fuels"] = perc.sum().apply(lambda x: (2 - x)).clip(lower=0)

        return perc

    # project electricity consumption met by a given technology
    def proj_elec_consump(region, scenario, proj_per_elec_consump):
        proj_consump = proj_per_elec_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "TFC", "Electricity", scenario]
                .loc[str(near_proj_start_year) :]
                .values.T
            ),
            axis=1,
        )
        return proj_consump

    # join timeseries of historical and projected electricity consumption met by a given technology
    def consump(hist_elec_consump, proj_elec_consump):
        return hist_elec_consump.join(proj_elec_consump)

    # join timeseries of historical and projected percent total electricity consumption met by a given technology
    def per_consump(hist_per_elec_consump, proj_per_elec_consump):
        return hist_per_elec_consump.join(proj_per_elec_consump)

    # combine above functions to get electricity consumption met by a given technology
    def consump_total(region, scenario):
        consump_total = consump(
            hist_elec_consump(region, scenario),
            proj_elec_consump(
                region,
                scenario,
                proj_per_elec_consump(
                    region,
                    near_proj_per_elec_consump(
                        region,
                        scenario,
                        hist_elec_consump(region, scenario),
                        hist_per_elec_consump(
                            region, scenario, hist_elec_consump(region, scenario)
                        ),
                        near_proj_elec_consump(region, scenario),
                    ),
                ),
            )
            * (1 + energy_oversupply_prop),
        )
        consump_total = pd.concat([consump_total], keys=[region], names=["Region"])

        percent_adoption = per_consump(
            hist_per_elec_consump(
                region, scenario, hist_elec_consump(region, scenario)
            ),
            proj_per_elec_consump(
                region,
                near_proj_per_elec_consump(
                    region,
                    scenario,
                    hist_elec_consump(region, scenario),
                    hist_per_elec_consump(
                        region, scenario, hist_elec_consump(region, scenario)
                    ),
                    near_proj_elec_consump(region, scenario),
                ),
            ),
        )
        percent_adoption = pd.concat(
            [percent_adoption], keys=[region], names=["Region"]
        )

        consump_cdr = consump(
            hist_elec_consump(region, scenario) * 0,
            proj_elec_consump(
                region,
                scenario,
                proj_per_elec_consump(
                    region,
                    near_proj_per_elec_consump(
                        region,
                        scenario,
                        hist_elec_consump(region, scenario),
                        hist_per_elec_consump(
                            region, scenario, hist_elec_consump(region, scenario)
                        ),
                        near_proj_elec_consump(region, scenario),
                    ),
                ),
            )
            * (energy_oversupply_prop),
        )
        consump_cdr = pd.concat([consump_cdr], keys=[region], names=["Region"])

        return (consump_total, percent_adoption, consump_cdr)

    elec_consump = []
    elec_percent_adoption = []
    elec_consump_cdr = []

    for i in range(0, len(iea_region_list)):
        elec_consump = pd.DataFrame(elec_consump).append(
            consump_total(iea_region_list[i], scenario)[0]
        )
        elec_percent_adoption = pd.DataFrame(elec_percent_adoption).append(
            consump_total(iea_region_list[i], scenario)[1]
        )

        elec_consump_cdr = pd.DataFrame(elec_consump_cdr).append(
            consump_total(iea_region_list[i], scenario)[2]
        )

    ##########
    #  HEAT  #
    ##########

    heat_gen_data = (
        pd.read_csv("podi/data/heat.csv")
        .fillna(0)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario", "Unit"])
    )

    elec_gen_data = pd.DataFrame(
        eia_etl("podi/data/electricity.csv").loc[
            :, str(data_start_year) : str(data_end_year)
        ]
    )

    def historical_heat_generation(region, sector, scenario, technology):
        return heat_gen_data.loc[region, sector, technology, scenario, slice(None)]

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
                scenario,
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

    return (
        elec_consump,
        elec_percent_adoption,
        elec_consump_cdr,
    )
