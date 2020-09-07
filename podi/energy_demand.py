#!/usr/bin/env python

import pandas as pd

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
    energy_demand_post_efficiency = energy_demand * energy_efficiency.values

    # apply percentage reduction & shift to electrification attributed to heat pumps
    heat_pumps = (
        pd.read_csv(heat_pumps)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)
    heat_pumps = heat_pumps.reindex(energy_demand.index)
    energy_demand_post_efficiency_heat_pumps = (
        energy_demand_post_efficiency * heat_pumps.values
    )

    # apply percentage reduction & shift to electrification attributed to transportation improvements
    transport_efficiency = (
        pd.read_csv(transport_efficiency)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    transport_efficiency = transport_efficiency.apply(lambda x: x + 1, axis=1)
    transport_efficiency = transport_efficiency.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport = (
        energy_demand_post_efficiency_heat_pumps * transport_efficiency.values
    )

    # apply percentage reduction attributed to solar thermal
    solar_thermal = (
        pd.read_csv(solar_thermal)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    solar_thermal = solar_thermal.apply(lambda x: x + 1, axis=1)
    solar_thermal = solar_thermal.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport_solarthermal = (
        energy_demand_post_efficiency_heatpumps_transport * solar_thermal.values
    )

    # apply shift attributed to biofuels
    biofuels = (
        pd.read_csv(biofuels)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    biofuels = biofuels.apply(lambda x: x + 1, axis=1)
    biofuels = biofuels.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels = (
        energy_demand_post_efficiency_heatpumps_transport_solarthermal * biofuels.values
    )

    # add energy demand from CDR
    # energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels_cdr = energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels + cdr_energy_demand

    return energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels
