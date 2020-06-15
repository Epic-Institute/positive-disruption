#!/usr/bin/env python

import pandas as pd

from podi import conf

###############

energy_demand_baseline = pd.read_csv("energy_demand_cps_baseline.csv").fillna(0)

energy_demand_baseline = energy_demand_baseline.pivot_table(
    values="Value", index=["Sector", "Metric"], columns="Year"
)

###############

energy_efficiency = (
    pd.read_csv("energy_efficiency.csv").set_index(["Sector", "Metric"]).fillna(0)
)

energy_efficiency = energy_efficiency.apply(lambda x: x + 1, axis=1)

energy_efficiency = energy_efficiency.reindex(energy_demand_baseline.index)

energy_demand_post_efficiency = energy_demand_baseline * energy_efficiency.values

###############

heat_pumps = pd.read_csv("heat_pumps.csv").set_index(["Sector", "Metric"]).fillna(0)

heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)

heat_pumps = heat_pumps.reindex(energy_demand_baseline.index)

energy_demand_post_efficiency_heat_pumps = (
    energy_demand_post_efficiency * heat_pumps.values
)

################

transport_efficiency = (
    pd.read_csv("transport_efficiency.csv").set_index(["Sector", "Metric"]).fillna(0)
)

transport_efficiency = transport_efficiency.apply(lambda x: x + 1, axis=1)

transport_efficiency = transport_efficiency.reindex(energy_demand_baseline.index)

energy_demand_post_efficiency_heat_pumps_transport = (
    energy_demand_baseline * transport_efficiency.values
)

################

energy_demand_post_efficiency_heat_pumps_transport = pd.melt(
    energy_demand_post_efficiency_heat_pumps_transport,
    ["Sector", "Metric"],
    var_name="Year",
    value_name="Value",
)

energy_demand_post_efficiency_heat_pumps_transport.to_csv("energy_demand_change.csv")
