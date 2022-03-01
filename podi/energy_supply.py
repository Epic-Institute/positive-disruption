#!/usr/bin/env python

# region

import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
from podi.curve_smooth import curve_smooth

# endregion


def energy_supply(
    scenario, energy_demand, data_start_year, data_end_year, proj_end_year
):

    ###################################
    # ESTIMATE ELECTRIC ENERGY SUPPLY #
    ###################################

    # region

    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])

    # For each region, find the historical percent of total electricity consumption met by each product (might need to get flow categories Electricity output (GWh) and Heat output)
    energy_demand.loc[
        slice(None),
        region,
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        slice(None),
        [
            "Autoproducer electricity plants",
            "Main activity producer electricity plants",
        ],
    ]

    # Use the historical percent of total electricity consumption met by each product to estimate projected percent of total electricity consumption each meets
    def proj_per_elec_consump(region, hist_per_elec_consump):
        foo = hist_per_elec_consump.apply(
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

        perc = pd.DataFrame(perc.loc[:, data_end_year + 1 :]).set_index(foo.index)

        # harmonizing historical to projection
        def harmonize(perc, hist_per_elec_consump):
            """
            if (
                abs(
                    hist_per_elec_consump.loc[perc.name, data_end_year]
                    - perc.loc[data_end_year + 1]
                )
                > 0.003
            ):
                perc.loc[data_end_year + 1 :] = perc.loc[data_end_year + 1 :].subtract(
                    (
                        perc.loc[data_end_year + 1]
                        - hist_per_elec_consump.loc[perc.name, data_end_year]
                    )
                )
                return perc
            else:
                return perc
            """
            hf = (
                hist_per_elec_consump.loc[perc.name, data_end_year]
                + (
                    hist_per_elec_consump.loc[perc.name, data_end_year]
                    - hist_per_elec_consump.loc[perc.name, data_end_year - 2]
                )
                / 2
                - perc.loc[data_end_year + 1]
            )

            perc = perc + (hf)
            return perc

        perc = perc.apply(
            harmonize, hist_per_elec_consump=hist_per_elec_consump, axis=1
        ).clip(upper=1, lower=0)

        # set fossil fuel generation to fill balance

        perc.loc["Fossil fuels"] = (
            1
            - perc.loc[
                [
                    "Hydroelectricity",
                    "Tide and wave",
                    "Solar",
                    "Wind",
                    "Biomass and waste",
                    "Nuclear",
                    "Geothermal",
                ]
            ].sum()
        ).clip(lower=0)

        return perc.loc[:, data_end_year + 1 :]

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
        """
        if scenario == "baseline":
            proj_consump = curve_smooth(proj_consump, "quadratic", 4)
        else:
            proj_consump = curve_smooth(proj_consump, "quadratic", 4)
        """
        return proj_consump.clip(lower=0)

    # join timeseries of historical and projected electricity consumption met by a given technology
    def consump(region, hist_elec_consump, hist_per_elec_consump, proj_elec_consump):

        hist_elec_consump = hist_per_elec_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "TFC", "Electricity", scenario].loc[
                    str(data_start_year) : str(data_end_year)
                ]
            ),
            axis=1,
        )

        hist_elec_consump.drop(labels="Generation", inplace=True)
        return hist_elec_consump.join(proj_elec_consump)

    # join timeseries of historical and projected percent total electricity consumption met by a given technology
    def per_consump(hist_per_elec_consump, proj_per_elec_consump):

        hist_per_elec_consump.drop(labels="Generation", inplace=True)
        return hist_per_elec_consump.join(proj_per_elec_consump)

    # combine above functions to get electricity consumption met by a given technology
    def consump_total(region, scenario):
        consump_total = consump(
            region,
            hist_elec_consump(region, scenario),
            hist_per_elec_consump(
                region, scenario, hist_elec_consump(region, scenario)
            ),
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
            region,
            hist_elec_consump(region, scenario) * 0,
            hist_per_elec_consump(region, scenario, hist_elec_consump(region, scenario))
            * 0,
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

        consump_total.columns = consump_total.columns.astype(int)
        percent_adoption.columns = percent_adoption.columns.astype(int)
        consump_cdr.columns = consump_cdr.columns.astype(int)

        return (consump_total, percent_adoption, consump_cdr)

    # endregion

    ################################
    # ESTIMATE HEAT ENERGY SUPPLY #
    ################################

    # region

    # historical heat consumption
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
            .groupby(["Metric"])
            .sum()
            .mul(consump_gen_ratio)
        )

    # historical percent of total heat consumption met by a given technology (propotion)
    def hist_per_heat_consump(region, scenario, hist_heat_consump):
        return hist_heat_consump.div(hist_heat_consump.sum())

    # nearterm projected heat consumption
    def near_proj_heat_consump(region, scenario):
        # near_proj_start_year = data_end_year
        # near_proj_end_year = data_end_year
        # long_proj_start_year = near_proj_end_year + 1
        return hist_heat_consump(region, scenario)

    # nearterm projected percent of total heat consumption met by a given technology (proportion)
    def near_proj_per_heat_consump(
        region,
        scenario,
        hist_heat_consump,
        hist_per_heat_consump,
        near_proj_heat_consump,
    ):

        return near_proj_heat_consump.div(near_proj_heat_consump.sum())

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

        # harmonizing historical to projection
        def harmonize(perc, near_proj_per_heat_consump):
            """
            if (
                abs(
                    near_proj_per_heat_consump.loc[perc.name, data_end_year]
                    - perc.loc[data_end_year + 1]
                )
                > 0.003
            ):
                perc.loc[data_end_year + 1 :] = perc.loc[data_end_year + 1 :].subtract(
                    (
                        perc.loc[data_end_year + 1]
                        - near_proj_per_heat_consump.loc[perc.name, data_end_year]
                    )
                )
                return perc
            else:
                return perc
            """

            hf = (
                near_proj_per_heat_consump.loc[perc.name, data_end_year]
                + (
                    near_proj_per_heat_consump.loc[perc.name, data_end_year]
                    - near_proj_per_heat_consump.loc[perc.name, data_end_year - 2]
                )
                / 2
                - perc.loc[data_end_year + 1]
            )

            perc = perc + (hf)
            return perc

        perc = perc.apply(
            harmonize, near_proj_per_heat_consump=near_proj_per_heat_consump, axis=1
        ).clip(upper=1, lower=0)

        # set fossil fuel generation to fill balance

        perc.loc["Fossil fuels"] = (
            1
            - perc.loc[
                [
                    "Bioenergy",
                    "Waste",
                    "Geothermal",
                    "Solar thermal",
                    "Other sources",
                ]
            ].sum()
        ).clip(lower=0)

        return perc.loc[:, data_end_year + 1 :]

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
        """
        proj_consump.loc["Solar thermal"] = (
            proj_per_heat_consump.loc["Solar thermal"].values
            * energy_demand.loc[region, "Buildings", "Heat"].loc[
                :, str(near_proj_start_year) :
            ]
        ).values
            .add(
                proj_per_heat_consump.loc["Solar thermal"].values
                * energy_demand.loc[
                    region,
                    "Industry",
                    ["Heat"],
                ]
                .loc[:, str(near_proj_start_year) :]
                .sum()
            )
            ).values
        """
        """
        if scenario == "baseline":
            proj_consump = curve_smooth(proj_consump, "quadratic", 6)
        else:
            proj_consump = curve_smooth(proj_consump, "quadratic", 6)
        """
        return proj_consump.clip(lower=0)

    # join timeseries of historical and projected heat consumption met by a given technology
    def heat_consump(
        region, hist_heat_consump, hist_per_heat_consump, proj_heat_consump
    ):
        hist_per_heat_consump.loc["Fossil fuels"] = hist_per_heat_consump.loc[
            ["Coal", "Oil", "Natural gas", "Nuclear"]
        ].sum()

        hist_heat_consump = hist_per_heat_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "TFC", "Heat", scenario].loc[
                    str(data_start_year) : str(data_end_year)
                ]
            ),
            axis=1,
        )

        return hist_heat_consump.join(proj_heat_consump)

    # join timeseries of historical and projected percent total heat consumption met by a given technology
    def heat_per_consump(hist_per_heat_consump, proj_per_heat_consump):

        hist_per_heat_consump.loc["Fossil fuels"] = hist_per_heat_consump.loc[
            ["Coal", "Oil", "Natural gas", "Nuclear"]
        ].sum()

        return hist_per_heat_consump.join(proj_per_heat_consump)

    # combine above functions to get heat consumption met by a given technology
    def heat_consump_total(region, scenario):
        heat_consump_total = heat_consump(
            region,
            hist_heat_consump(region, scenario),
            hist_per_heat_consump(
                region, scenario, hist_heat_consump(region, scenario)
            ),
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
            region,
            hist_heat_consump(region, scenario) * 0,
            hist_per_heat_consump(region, scenario, hist_heat_consump(region, scenario))
            * 0,
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

    ################################################
    # ESTIMATE NONELECTRIC TRANSPORT ENERGY SUPPLY #
    ################################################

    # region

    # historical transport consumption
    def hist_transport_consump(region, scenario):
        return transport_data.iloc[
            transport_data.index.get_level_values(0).str.contains(region, na=False)
        ].loc[region, ["Oil", "Bioenergy", "Other fuels"], :]

    # historical percent of total transport consumption met by a given technology (propotion)
    def hist_per_transport_consump(region, scenario, hist_transport_consump):
        return hist_transport_consump.div(hist_transport_consump.sum()).droplevel(
            ["IEA Region"]
        )

    # nearterm projected transport consumption
    def near_proj_transport_consump(region, scenario):
        near_proj_start_year = data_end_year + 1
        near_proj_end_year = data_end_year + 1
        return hist_transport_consump(region, scenario).droplevel(["IEA Region"])

    # nearterm projected percent of total transport consumption met by a given technology (proportion)
    def near_proj_per_transport_consump(
        region,
        scenario,
        hist_transport_consump,
        hist_per_transport_consump,
        near_proj_transport_consump,
    ):
        foo = hist_per_transport_consump
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

        # harmonizing historical to projection
        def harmonize(perc, near_proj_per_transport_consump):
            hf = (
                near_proj_per_transport_consump.loc[perc.name, data_end_year]
                + (
                    near_proj_per_transport_consump.loc[perc.name, data_end_year]
                    - near_proj_per_transport_consump.loc[perc.name, data_end_year - 2]
                )
                / 2
                - perc.loc[data_end_year + 1]
            )

            perc = perc + (hf)

            """
            if (
                abs(
                    near_proj_per_transport_consump.loc[perc.name, data_end_year]
                    - perc.loc[data_end_year + 1]
                )
                > 0.003
            ):
                perc.loc[data_end_year + 1 :] = perc.loc[data_end_year + 1 :].subtract(
                    (
                        perc.loc[data_end_year + 1]
                        - near_proj_per_transport_consump.loc[perc.name, data_end_year]
                    )
                )
                return perc
            else:
                return perc
            """
            return perc

        perc = perc.apply(
            harmonize,
            near_proj_per_transport_consump=near_proj_per_transport_consump,
            axis=1,
        ).clip(upper=1, lower=0)

        # set fossil fuel generation to fill balance

        perc.loc["Fossil fuels"] = (
            1 - perc.loc[["Bioenergy", "Other fuels"]].sum()
        ).clip(lower=0)

        return perc.loc[:, data_end_year + 1 :]

    # project transport consumption met by a given technology
    def proj_transport_consump(region, scenario, proj_per_transport_consump):
        proj_consump = proj_per_transport_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[
                    region, "Transport", ["Oil", "Bioenergy", "Other fuels"], scenario
                ]
                .sum()
                .loc[str(near_proj_start_year) :]
                .values.T
            ),
            axis=1,
        )
        """
        if scenario == "baseline":
            proj_consump = curve_smooth(proj_consump, "quadratic", 4)
        else:
            proj_consump = curve_smooth(proj_consump, "quadratic", 4)
        """
        return proj_consump.clip(lower=0)

    # join timeseries of historical and projected transport consumption met by a given technology
    def transport_consump(
        region,
        hist_transport_consump,
        hist_per_transport_consump,
        proj_transport_consump,
    ):
        hist_per_transport_consump.loc["Fossil fuels"] = hist_per_transport_consump.loc[
            ["Oil"]
        ].sum()

        hist_transport_consump = hist_per_transport_consump.apply(
            lambda x: x
            * (
                energy_demand.loc[region, "Transport", "Transport", scenario].loc[
                    str(data_start_year) : str(data_end_year)
                ]
            ),
            axis=1,
        )

        return hist_transport_consump.join(proj_transport_consump)

    # join timeseries of historical and projected percent total transport consumption met by a given technology
    def transport_per_consump(hist_per_transport_consump, proj_per_transport_consump):
        hist_per_transport_consump.loc["Fossil fuels"] = hist_per_transport_consump.loc[
            ["Oil"]
        ].sum()

        return hist_per_transport_consump.join(proj_per_transport_consump)

    # combine above functions to get transport consumption met by a given technology
    def transport_consump_total(region, scenario):
        transport_consump_total = transport_consump(
            region,
            hist_transport_consump(region, scenario),
            hist_per_transport_consump(
                region, scenario, hist_transport_consump(region, scenario)
            ),
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
            hist_per_transport_consump(
                region, scenario, hist_transport_consump(region, scenario)
            )
            * 0,
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

        return (
            transport_consump_total,
            percent_adoption,
            consump_cdr,
        )

    # endregion

    #####################
    # COMBINE ESTIMATES #
    #####################

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

    for region in energy_demand.index.get_level_values(0).unique():
        elec_consump = pd.DataFrame(elec_consump).append(
            consump_total(region, scenario)[0]
        )
        heat_consump2 = pd.DataFrame(heat_consump2).append(
            heat_consump_total(region, scenario)[0]
        )
        transport_consump2 = pd.DataFrame(transport_consump2).append(
            transport_consump_total(region, scenario)[0]
        )
        elec_per_adoption = pd.DataFrame(elec_per_adoption).append(
            consump_total(region, scenario)[1]
        )
        heat_per_adoption = pd.DataFrame(heat_per_adoption).append(
            heat_consump_total(region, scenario)[1]
        )
        transport_per_adoption = pd.DataFrame(transport_per_adoption).append(
            transport_consump_total(region, scenario)[1]
        )

    elec_consump = pd.concat(
        [elec_consump], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])
    elec_per_adoption = pd.concat(
        [elec_per_adoption], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])
    heat_consump2 = pd.concat(
        [heat_consump2], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])
    heat_per_adoption = pd.concat(
        [heat_per_adoption], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])
    transport_consump2 = pd.concat(
        [transport_consump2], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])
    transport_per_adoption = pd.concat(
        [transport_per_adoption], keys=[scenario], names=["Scenario"]
    ).reorder_levels(["Region", "Metric", "Scenario"])

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
