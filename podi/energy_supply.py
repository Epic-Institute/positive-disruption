#!/usr/bin/env python

# region

import pandas as pd
from podi.adoption_curve import adoption_curve
from podi.data.eia_etl import eia_etl
from podi.data.bnef_etl import bnef_etl
from podi.data.heat_etl import heat_etl
from podi.data.iea_weo_etl import iea_region_list
from numpy import NaN

# endregion

data_start_year = 2010
data_end_year = 2017
near_proj_start_year = data_end_year + 1
near_proj_end_year = 2025
long_proj_start_year = near_proj_end_year + 1
long_proj_end_year = 2100
energy_oversupply_prop = 0.0


def energy_supply(scenario, energy_demand):
    # region

    parameters = pd.read_csv("podi/data/tech_parameters.csv").set_index(
        ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
    )

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
    heat_gen_data = heat_etl("podi/data/heat.csv", scenario).loc[
        :, str(data_start_year) : str(data_end_year)
    ]
    heat_gen_data.columns = heat_gen_data.columns.astype(int)

    heat_gen_data.loc[slice(None), slice(None), "Bioenergy", scenario] = (
        energy_demand.loc[[" OECD ", "NonOECD "], "Buildings", "Bioenergy", slice(None)]
        .loc[:, data_start_year:data_end_year]
        .values
    )

    transport_data = (
        energy_demand.loc[
            slice(None),
            "Transport",
            ["Oil", "Biofuels", "Other fuels", "International bunkers"],
            scenario,
        ]
        .loc[:, str(data_start_year) : str(data_end_year)]
        .droplevel(["Sector", "Scenario"])
    )
    transport_data.columns = transport_data.columns.astype(int)

    # endregion

    ###############
    # ELECTRICITY #
    ###############

    # region

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
            foo.drop(labels="Generation", inplace=True)
            hist_elec_consump.drop(labels="Generation", inplace=True)

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
            sector="Electricity",
        )

        perc = []
        for i in range(0, len(foo.index)):
            perc = pd.DataFrame(perc).append(foo[foo.index[i]][0].T)

        perc = pd.DataFrame(perc.loc[:, near_proj_start_year:]).set_index(foo.index)

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
        hist_elec_consump.drop(labels="Generation", inplace=True)
        return hist_elec_consump.join(proj_elec_consump)

    # join timeseries of historical and projected percent total electricity consumption met by a given technology
    def per_consump(hist_per_elec_consump, proj_per_elec_consump):
        hist_per_elec_consump.drop(labels="Generation", inplace=True)
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
        # consump_total.drop(labels="Generation", level=1, inplace=True)

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
        # percent_adoption.drop(labels="Generation", level=1, inplace=True)

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
        # consump_cdr.drop(labels="Generation", level=1, inplace=True)

        consump_total.columns = consump_total.columns.astype(int)
        percent_adoption.columns = percent_adoption.columns.astype(int)
        consump_cdr.columns = consump_cdr.columns.astype(int)

        return (consump_total, percent_adoption, consump_cdr)

    # endregion

    ##########
    #  HEAT  #
    ##########

    # region

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
            sector="Heat",
        )

        perc = []
        for i in range(0, len(foo.index)):
            perc = pd.DataFrame(perc).append(foo[foo.index[i]][0].T)

        perc = pd.DataFrame(perc.loc[:, near_proj_start_year:]).set_index(foo.index)

        return perc

    # project heat consumption met by a given technology
    def proj_heat_consump(region, scenario, proj_per_heat_consump):
        proj_consump = proj_per_heat_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "TFC", "Heat", scenario]
                .add(
                    energy_demand.loc[
                        region,
                        "Industry",
                        ["Other renewables", "Coal", "Oil", "Natural gas", "Bioenergy"],
                        scenario,
                    ].sum()
                )
                .loc[str(near_proj_start_year) :]
                .values.T
            ),
            axis=1,
        )

        proj_consump.loc["Solar thermal"] = (
            (
                proj_per_heat_consump.loc["Solar thermal"].values
                * energy_demand.loc[region, "Buildings", "Heat"].loc[
                    :, str(near_proj_start_year) :
                ]
            ).add(
                proj_per_heat_consump.loc["Solar thermal"].values
                * energy_demand.loc[
                    region,
                    "Industry",
                    ["Heat"],
                ]
                .loc[:, str(near_proj_start_year) :]
                .sum()
                * 0.2
            )
        ).values

        return proj_consump

    # join timeseries of historical and projected heat consumption met by a given technology
    def heat_consump(hist_heat_consump, proj_heat_consump):
        hist_heat_consump.loc["Fossil fuels"] = hist_heat_consump.loc[
            ["Coal", "Oil", "Natural gas"]
        ].sum()
        return hist_heat_consump.join(proj_heat_consump)

    # join timeseries of historical and projected percent total heat consumption met by a given technology
    def heat_per_consump(hist_per_heat_consump, proj_per_heat_consump):
        hist_per_heat_consump.loc["Fossil fuels"] = hist_per_heat_consump.loc[
            ["Coal", "Oil", "Natural gas"]
        ].sum()
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

        heat_consump_total.columns = heat_consump_total.columns.astype(int)
        percent_adoption.columns = percent_adoption.columns.astype(int)
        consump_cdr.columns = consump_cdr.columns.astype(int)

        return (heat_consump_total, percent_adoption, consump_cdr)

    # endregion

    ###########################
    #  NONELECTRIC TRANSPORT  #
    ###########################

    # region

    # historical transport consumption (TWh)
    def hist_transport_consump(region, scenario):
        return transport_data.iloc[
            transport_data.index.get_level_values(0).str.contains(region, na=False)
        ].loc[region, ["Oil", "Biofuels", "Other fuels"], :]

    # historical percent of total transport consumption met by a given technology (propotion)
    def hist_per_transport_consump(region, scenario, hist_transport_consump):
        return hist_transport_consump.div(hist_transport_consump.sum())

    # nearterm projected transport consumption
    def near_proj_transport_consump(region, scenario):
        near_proj_start_year = data_end_year
        long_proj_start_year = data_end_year + 1
        near_proj_end_year = data_end_year
        return hist_transport_consump(region, scenario)

    # nearterm projected percent of total transport consumption met by a given technology (proportion)
    def near_proj_per_transport_consump(
        region,
        scenario,
        hist_transport_consump,
        hist_per_transport_consump,
        near_proj_transport_consump,
    ):
        foo = hist_per_transport_consump.droplevel(["IEA Region"])
        return foo

    # longterm projected percent of total transport consumption met by a given technology (proportion)
    def proj_per_transport_consump(region, near_proj_per_transport_consump):
        foo = near_proj_per_transport_consump.apply(
            adoption_curve,
            axis=1,
            args=(
                [
                    region,
                    scenario,
                ]
            ),
            sector="Transport",
        )

        perc = []
        for i in range(0, len(foo.index)):
            perc = pd.DataFrame(perc).append(foo[foo.index[i]][0].T)

        perc = pd.DataFrame(perc.loc[:, near_proj_start_year:]).set_index(foo.index)

        # set fossil fuel generation to fill balance
        perc.loc["Fossil fuels"] = perc.loc[["Oil", "Other fuels"]].sum()

        return perc

    # project transport consumption met by a given technology
    def proj_transport_consump(region, scenario, proj_per_transport_consump):
        proj_consump = proj_per_transport_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[
                    region, "Transport", ["Oil", "Biofuels", "Other fuels"], scenario
                ]
                .sum()
                .loc[str(near_proj_start_year) :]
                .values.T
            ),
            axis=1,
        )
        return proj_consump

    # join timeseries of historical and projected transport consumption met by a given technology
    def transport_consump(region, hist_transport_consump, proj_transport_consump):
        hist_transport_consump = hist_transport_consump.droplevel(["IEA Region"])
        hist_transport_consump.loc["Fossil fuels"] = hist_transport_consump.loc["Oil"]

        if scenario == "Pathway":
            transport_consump = (
                hist_transport_consump.join(proj_transport_consump) * 1.7
            )
        else:
            transport_consump = hist_transport_consump.join(proj_transport_consump)

        return transport_consump

    # join timeseries of historical and projected percent total transport consumption met by a given technology
    def transport_per_consump(hist_per_transport_consump, proj_per_transport_consump):
        return hist_per_transport_consump.join(proj_per_transport_consump)

    # combine above functions to get transport consumption met by a given technology
    def transport_consump_total(region, scenario):
        transport_consump_total = transport_consump(
            region,
            hist_transport_consump(region, scenario),
            proj_transport_consump(
                region,
                scenario,
                proj_per_transport_consump(
                    region,
                    near_proj_per_transport_consump(
                        region,
                        scenario,
                        hist_transport_consump(region, scenario),
                        hist_per_transport_consump(
                            region, scenario, hist_transport_consump(region, scenario)
                        ),
                        near_proj_transport_consump(region, scenario),
                    ),
                ),
            )
            * (1 + energy_oversupply_prop),
        )
        transport_consump_total = pd.concat(
            [transport_consump_total], keys=[region], names=["Region"]
        )

        percent_adoption = transport_per_consump(
            hist_per_transport_consump(
                region, scenario, hist_transport_consump(region, scenario)
            ),
            proj_per_transport_consump(
                region,
                near_proj_per_transport_consump(
                    region,
                    scenario,
                    hist_transport_consump(region, scenario),
                    hist_per_transport_consump(
                        region, scenario, hist_transport_consump(region, scenario)
                    ),
                    near_proj_transport_consump(region, scenario),
                ),
            ),
        )
        percent_adoption = pd.concat(
            [percent_adoption], keys=[region], names=["Region"]
        )

        consump_cdr = transport_consump(
            region,
            hist_transport_consump(region, scenario) * 0,
            proj_transport_consump(
                region,
                scenario,
                proj_per_transport_consump(
                    region,
                    near_proj_per_transport_consump(
                        region,
                        scenario,
                        hist_transport_consump(region, scenario),
                        hist_per_transport_consump(
                            region, scenario, hist_transport_consump(region, scenario)
                        ),
                        near_proj_transport_consump(region, scenario),
                    ),
                ),
            )
            * (energy_oversupply_prop),
        )
        consump_cdr = pd.concat([consump_cdr], keys=[region], names=["Region"])

        transport_consump_total.columns = transport_consump_total.columns.astype(int)
        percent_adoption.columns = percent_adoption.columns.astype(int)
        consump_cdr.columns = consump_cdr.columns.astype(int)

        return (transport_consump_total, percent_adoption, consump_cdr)

    # endregion

    # region
    elec_consump = []
    elec_per_adoption = []
    elec_consump_cdr = []
    heat_consump2 = []
    heat_per_adoption = []
    heat_consump_cdr = []
    transport_consump2 = []
    transport_per_adoption = []
    transport_consump_cdr = []

    for i in range(17, 19):
        elec_consump = pd.DataFrame(elec_consump).append(
            consump_total(iea_region_list[i], scenario)[0]
        )
        heat_consump2 = pd.DataFrame(heat_consump2).append(
            heat_consump_total(iea_region_list[i], scenario)[0]
        )
        transport_consump2 = pd.DataFrame(transport_consump2).append(
            transport_consump_total(iea_region_list[i], scenario)[0]
        )
        elec_per_adoption = pd.DataFrame(elec_per_adoption).append(
            consump_total(iea_region_list[i], scenario)[1]
        )
        heat_per_adoption = pd.DataFrame(heat_per_adoption).append(
            heat_consump_total(iea_region_list[i], scenario)[1]
        )
        transport_per_adoption = pd.DataFrame(transport_per_adoption).append(
            transport_consump_total(iea_region_list[i], scenario)[1]
        )

    # endregion

    return (
        elec_consump,
        elec_per_adoption,
        elec_consump_cdr,
        heat_consump2,
        heat_per_adoption,
        heat_consump_cdr,
        transport_consump2,
        transport_per_adoption,
        transport_consump_cdr,
    )
