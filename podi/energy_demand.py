#!/usr/bin/env python

import pandas as pd


def energy_demand(
    demand_historical,
    demand_projection,
    energy_efficiency,
    heat_pumps,
    transport_efficiency,
    solar_thermal,
    biofuels,
):

    energy_demand_historical = pd.read_csv(demand_historical)
    energy_demand_projection = pd.read_csv(demand_projection)

    energy_demand = energy_demand_historical.merge(
        energy_demand_projection,
        right_on=["WEO Sector", "WEO Metric"],
        left_on=["Sector", "Metric"],
    ).drop(
        columns=["WEO Sector", "WEO Metric", "GCAM Value", "REGION", "VARIABLE", "UNIT"]
    )

    energy_demand = (
        energy_demand.loc[:, :"2039"]
        .join(energy_demand.loc[:, "2040":].cumprod(axis=1).fillna(0).astype(int))
        .set_index(["Sector", "Metric"])
    )

    energy_efficiency = (
        pd.read_csv(energy_efficiency).set_index(["Sector", "Metric"]).fillna(0)
    )

    energy_efficiency = energy_efficiency.apply(lambda x: x + 1, axis=1)
    energy_efficiency = energy_efficiency.reindex(energy_demand.index)
    energy_demand_post_efficiency = energy_demand * energy_efficiency.values

    heat_pumps = pd.read_csv(heat_pumps).set_index(["Sector", "Metric"]).fillna(0)

    heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)
    heat_pumps = heat_pumps.reindex(energy_demand.index)
    energy_demand_post_efficiency_heat_pumps = (
        energy_demand_post_efficiency * heat_pumps.values
    )

    transport_efficiency = (
        pd.read_csv(transport_efficiency).set_index(["Sector", "Metric"]).fillna(0)
    )
    transport_efficiency = transport_efficiency.apply(lambda x: x + 1, axis=1)
    transport_efficiency = transport_efficiency.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport = (
        energy_demand_post_efficiency_heat_pumps * transport_efficiency.values
    )

    solar_thermal = pd.read_csv(solar_thermal).set_index(["Sector", "Metric"]).fillna(0)
    solar_thermal = solar_thermal.apply(lambda x: x + 1, axis=1)
    solar_thermal = solar_thermal.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport_solarthermal = (
        energy_demand_post_efficiency_heatpumps_transport * solar_thermal.values
    )

    biofuels = pd.read_csv(biofuels).set_index(["Sector", "Metric"]).fillna(0)
    biofuels = biofuels.apply(lambda x: x + 1, axis=1)
    biofuels = biofuels.reindex(energy_demand.index)
    energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels = (
        energy_demand_post_efficiency_heatpumps_transport_solarthermal * biofuels.values
    )

    return energy_demand_post_efficiency_heatpumps_transport_solarthermal_biofuels
