#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
import numpy as np
from podi.data.iea_weo_etl import iea_region_list

# from cdr.cdr_main import cdr_energy_demand


def energy_demand(
    scenario,
    demand_historical,
    demand_projection,
    energy_efficiency,
    heat_pumps,
    transport_efficiency,
    solar_thermal,
    biofuels,
    cdr,
    bunker,
):

    # load energy demand historical data (TWh) and projections (% change)
    energy_demand_historical = pd.read_csv(demand_historical)
    energy_demand_projection = pd.read_csv(demand_projection)

    # define energy demand as timeseries consisting of historical data (TWh) and projections (% change)
    energy_demand = energy_demand_historical.merge(
        energy_demand_projection,
        right_on=["IEA Sector", "IEA Metric", "Region"],
        left_on=["Sector", "Metric", "GCAM Region"],
    ).drop(
        columns=[
            "IEA Sector",
            "IEA Metric",
            "GCAM Metric",
            "Variable",
            "Unit",
            "GCAM Region",
            "Region",
            "EIA Metric",
            "BNEF Metric",
            "WWS Metric",
        ]
    )
    energy_demand["Scenario"] = scenario
    energy_demand.set_index(
        ["IEA Region", "Sector", "Metric", "Scenario"], inplace=True
    )

    # calculate projections as TWh by cumulative product
    energy_demand = energy_demand.loc[:, :"2039"].join(
        energy_demand.loc[:, "2040":].cumprod(axis=1).fillna(0).astype(int)
    )

    # apply percentage reduction attributed to energy efficiency measures
    energy_efficiency = (
        pd.read_csv(energy_efficiency)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    energy_efficiency = energy_efficiency.apply(lambda x: x + 1, axis=1)
    energy_efficiency = energy_efficiency.reindex(energy_demand.index)
    # energy_demand_post_efficiency = energy_demand * energy_efficiency.values
    energy_demand_post_efficiency = energy_demand - (
        energy_demand * energy_efficiency.values
    )

    # apply percentage reduction & shift to electrification attributed to heat pumps
    heat_pumps = (
        pd.read_csv(heat_pumps)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)
    heat_pumps = heat_pumps.reindex(energy_demand.index)
    """
    energy_demand_post_efficiency_heat_pumps = (
        energy_demand_post_efficiency * heat_pumps.values
    )
    """
    energy_demand_post_heat_pumps = energy_demand - (energy_demand * heat_pumps.values)

    # apply percentage reduction & shift to electrification attributed to transportation improvements
    transport_efficiency = (
        pd.read_csv(transport_efficiency)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    transport_efficiency = transport_efficiency.apply(lambda x: x + 1, axis=1)
    transport_efficiency = transport_efficiency.reindex(energy_demand.index)
    """
    energy_demand_post_efficiency_heatpumps_transport = (
        energy_demand_post_efficiency_heat_pumps * transport_efficiency.values
    )
    """
    energy_demand_post_transport = energy_demand - (
        energy_demand * transport_efficiency.values
    )

    # apply percentage reduction attributed to solar thermal
    solar_thermal = (
        pd.read_csv(solar_thermal)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    solar_thermal = solar_thermal.apply(lambda x: x + 1, axis=1)
    solar_thermal = solar_thermal.reindex(energy_demand.index)
    """
    energy_demand_post_efficiency_heatpumps_transport_solarthermal = (
        energy_demand_post_efficiency_heatpumps_transport * solar_thermal.values
    )
    """
    energy_demand_post_solarthermal = energy_demand - (
        energy_demand * solar_thermal.values
    )

    # apply shift attributed to biofuels
    biofuels = (
        pd.read_csv(biofuels)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    biofuels = biofuels.apply(lambda x: x + 1, axis=1)
    biofuels = biofuels.reindex(energy_demand.index)
    """
    energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels = (
        energy_demand_post_efficiency_heatpumps_transport_solarthermal * biofuels.values
    )
    """
    energy_demand_post_biofuels = energy_demand - (energy_demand * biofuels.values)

    # add energy demand from CDR
    cdr = (
        pd.read_csv(cdr)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    cdr = cdr.reindex(energy_demand.index)
    cdr = cdr.apply(lambda x: x + 1, axis=1)
    energy_demand_post_cdr = energy_demand - (energy_demand * cdr.values)

    # add energy demand from international bunker
    bunker = (
        pd.read_csv(bunker)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    bunker = bunker.reindex(energy_demand.index)
    bunker = bunker.apply(lambda x: x + 1, axis=1)
    energy_demand_post_bunker = energy_demand - (energy_demand * bunker.values)

    energy_demand = (
        energy_demand
        - energy_demand_post_efficiency
        - energy_demand_post_heat_pumps
        - energy_demand_post_transport
        - energy_demand_post_solarthermal
        - energy_demand_post_biofuels
        - energy_demand_post_cdr
        - energy_demand_post_bunker
    )

    """
    xnew = np.linspace(
        energy_demand.columns.values.astype(int).min(),
        energy_demand.columns.values.astype(int).max(),
        11,
    )
    energy_demand = energy_demand.apply(
        lambda x: proj_demand(energy_demand.columns.values.astype(int), x),
        axis=1,
    )
    energy_demand = energy_demand.apply(lambda x: x(xnew))
    energy_demand = pd.DataFrame(energy_demand)
    """
    """
    def proj_demand(region, hist_demand):
        foo = hist_demand.loc[region,slice(None),slice(None),slice(None)].droplevel(['Scenario']).apply(
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

        perc = pd.DataFrame(perc).set_index(foo.index)
        return perc

    en_demand = []

    for i in range(0, len(iea_region_list)):
        en_demand = pd.DataFrame(en_demand).append(
            proj_demand(iea_region_list[i], energy_demand)
        )
    """

    return energy_demand
