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
        bnef_etl("podi/data/bnef.csv", "elec").loc[
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
            return hist_elec_consump(region, scenario)
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

        if scenario == "Baseline":
            foo = hist_per_elec_consump
            return foo
        else:
            foo = near_proj_elec_consump.div(
                near_proj_elec_consump.loc["Generation"]
            ).mul(consump_gen_ratio)

            # normalize to historical data
            foo = (
                foo.pct_change(axis=1)
                .replace(NaN, 0)
                .loc[:, str(near_proj_start_year) :]
                .apply(lambda x: x + 1, axis=1)
            )

            foo = hist_per_elec_consump.loc[:, : str(data_end_year - 1)].join(
                (
                    (
                        hist_per_elec_consump.loc[:, str(data_end_year) :].join(foo)
                    ).cumprod(axis=1)
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

    heat_gen_data = heat_etl("podi/data/heat.csv", scenario).loc[
        :, str(data_start_year) : str(data_end_year)
    ]
    heat_gen_data.columns = heat_gen_data.columns.astype(int)

    # historical heat consumption (TWh)
    def hist_heat_consump(region, scenario):
        consump_gen_ratio = pd.to_numeric(
            parameters.loc[
                region, "Heat", scenario, slice(None), "Consumption:Generation"
            ]["Value"].iat[0]
        )

        return (
            heat_gen_data.iloc[
                heat_gen_data.index.get_level_values(0).str.contains(region, na=False)
            ]
            .loc[(slice(None), slice(None), slice(None), scenario, slice(None)), :]
            .mul(consump_gen_ratio)
            .groupby(["Metric"])
            .sum()
        )

    # historical percent of total heat consumption met by a given technology (propotion)
    def hist_per_heat_consump(region, scenario, hist_heat_consump):
        return hist_heat_consump.div(hist_heat_consump.sum())

    # nearterm projected heat consumption
    def near_proj_heat_consump(region, scenario):
        near_proj_start_year = data_end_year
        long_proj_start_year = data_end_year + 1
        near_proj_end_year = data_end_year
        return hist_heat_consump(region, scenario)

    # nearterm projected percent of total heat consumption met by a given technology (proportion)
    def near_proj_per_heat_consump(
        region,
        scenario,
        hist_heat_consump,
        hist_per_heat_consump,
        near_proj_heat_consump,
    ):
        foo = hist_per_heat_consump
        return foo

    # longterm projected percent of total heat consumption met by a given technology (proportion)
    def proj_per_heat_consump(region, near_proj_per_heat_consump):
        foo = near_proj_per_heat_consump.apply(
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

        # set fossil fuel generation to fill balance
        perc.loc["Fossil fuels"] = perc.sum().apply(lambda x: (2 - x)).clip(lower=0)

        return perc

    # project heat consumption met by a given technology
    def proj_heat_consump(region, scenario, proj_per_heat_consump):
        proj_consump = proj_per_heat_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "TFC", "Heat", scenario]
                .loc[str(near_proj_start_year) :]
                .values.T
            ),
            axis=1,
        )
        return proj_consump

    # join timeseries of historical and projected heat consumption met by a given technology
    def heat_consump(hist_heat_consump, proj_heat_consump):
        return hist_heat_consump.join(proj_heat_consump)

    # join timeseries of historical and projected percent total heat consumption met by a given technology
    def heat_per_consump(hist_per_heat_consump, proj_per_heat_consump):
        return hist_per_heat_consump.join(proj_per_heat_consump)

    # combine above functions to get heat consumption met by a given technology
    def heat_consump_total(region, scenario):
        heat_consump_total = heat_consump(
            hist_heat_consump(region, scenario),
            proj_heat_consump(
                region,
                scenario,
                proj_per_heat_consump(
                    region,
                    near_proj_per_heat_consump(
                        region,
                        scenario,
                        hist_heat_consump(region, scenario),
                        hist_per_heat_consump(
                            region, scenario, hist_heat_consump(region, scenario)
                        ),
                        near_proj_heat_consump(region, scenario),
                    ),
                ),
            )
            * (1 + energy_oversupply_prop),
        )
        heat_consump_total = pd.concat(
            [heat_consump_total], keys=[region], names=["Region"]
        )

        percent_adoption = heat_per_consump(
            hist_per_heat_consump(
                region, scenario, hist_heat_consump(region, scenario)
            ),
            proj_per_heat_consump(
                region,
                near_proj_per_heat_consump(
                    region,
                    scenario,
                    hist_heat_consump(region, scenario),
                    hist_per_heat_consump(
                        region, scenario, hist_heat_consump(region, scenario)
                    ),
                    near_proj_heat_consump(region, scenario),
                ),
            ),
        )
        percent_adoption = pd.concat(
            [percent_adoption], keys=[region], names=["Region"]
        )

        consump_cdr = heat_consump(
            hist_heat_consump(region, scenario) * 0,
            proj_heat_consump(
                region,
                scenario,
                proj_per_heat_consump(
                    region,
                    near_proj_per_heat_consump(
                        region,
                        scenario,
                        hist_heat_consump(region, scenario),
                        hist_per_heat_consump(
                            region, scenario, hist_heat_consump(region, scenario)
                        ),
                        near_proj_heat_consump(region, scenario),
                    ),
                ),
            )
            * (energy_oversupply_prop),
        )
        consump_cdr = pd.concat([consump_cdr], keys=[region], names=["Region"])

        return (heat_consump_total, percent_adoption, consump_cdr)

    heat_consump2 = []
    heat_percent_adoption = []
    heat_consump_cdr = []

    for i in range(0, len(iea_region_list)):
        heat_consump2 = pd.DataFrame(heat_consump2).append(
            heat_consump_total(iea_region_list[i], scenario)[0]
        )

        heat_percent_adoption = pd.DataFrame(heat_percent_adoption).append(
            heat_consump_total(iea_region_list[i], scenario)[1]
        )

        heat_consump_cdr = pd.DataFrame(heat_consump_cdr).append(
            heat_consump_total(iea_region_list[i], scenario)[2]
        )

    ###########################
    #  NONELECTRIC TRANSPORT  #
    ###########################

    return (
        elec_consump,
        elec_per_adoption,
        elec_consump_cdr,
        heat_consump2,
        heat_per_adoption,
        heat_consump_cdr,
        transport_consump,
        transport_per_adoption,
        transport_consump_cdr,
    )
