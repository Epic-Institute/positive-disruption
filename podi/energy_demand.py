#!/usr/bin/env python

# region

import pandas as pd
from podi.adoption_curve import adoption_curve
import numpy as np
from podi.data.iea_weo_etl import iea_region_list
from scipy.interpolate import interp1d

# from cdr.cdr_main import cdr_energy_demand

# endregion


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

    # Load energy demand historical data (TWh) and projections (% change)
    energy_demand_historical = pd.read_csv(demand_historical)
    energy_demand_projection = pd.read_csv(demand_projection)

    # Define energy demand as timeseries consisting of historical data (TWh) and projections (% change)
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

    # Calculate projections as TWh by cumulative product
    energy_demand = energy_demand.loc[:, :"2039"].join(
        energy_demand.loc[:, "2040":].cumprod(axis=1).fillna(0).astype(int)
    )

    # Reallocate 'Other' energy demand from ag/non-energy use to industry
    energy_demand.loc[slice(None), "Industry", "Other renewables", scenario] = (
        energy_demand.loc[slice(None), "Industry", "Other renewables", scenario]
        .add(
            energy_demand.loc[
                slice(None),
                ["Other"],
                ["Other"],
                slice(None),
            ]
            .groupby("IEA Region")
            .sum()
            .reindex(
                energy_demand.loc[
                    slice(None), "Industry", "Other renewables", scenario
                ].index
            ),
            axis=1,
        )
        .values
    )

    # Reallocate heat demand within industry
    """
    energy_demand.loc[slice(None), "Industry", "Heat", scenario] = (
        energy_demand.loc[slice(None), "Industry", "Heat", scenario]
        .add(
            energy_demand.loc[
                slice(None),
                ["Industry"],
                ["Coal", "Oil", "Natural gas", "Bioenergy", "Other renewables"],
                slice(None),
            ]
            .groupby("IEA Region")
            .sum()
            .reindex(
                energy_demand.loc[
                    slice(None), "Industry", "Other renewables", scenario
                ].index
            ),
            axis=1,
        )
        .values
    )
    """

    # Reallocate heat demand within buildings
    """
    energy_demand.loc[slice(None), "Buildings", "Heat", scenario] = (
        energy_demand.loc[slice(None), "Buildings", "Heat", scenario]
        .add(
            energy_demand.loc[
                slice(None),
                ["Buildings"],
                ["Coal", "Oil", "Natural gas", "Bioenergy", "Other renewables"],
                slice(None),
            ]
            .groupby("IEA Region")
            .sum()
            .reindex(
                energy_demand.loc[
                    slice(None), "Industry", "Other renewables", scenario
                ].index
            ),
            axis=1,
        )
        .values
    )
    """

    # Reallocate international bunkers from Transport - Oil
    energy_demand.loc["World ", "Transport", "Oil"] = (
        energy_demand.loc["World ", "Transport", "Oil"] * 0.84
    ).values

    bunkers = pd.concat(
        [energy_demand.loc["World ", "Transport", "Oil"] * 0.16],
        keys=["International bunkers"],
        names=["Metric"],
    )
    bunkers["IEA Region"] = "World "
    bunkers["Sector"] = "Transport"
    bunkers.reset_index(inplace=True)
    bunkers.set_index(["IEA Region", "Sector", "Metric", "Scenario"], inplace=True)
    energy_demand = energy_demand.append(bunkers)

    # Apply percentage reduction attributed to energy efficiency measures
    energy_efficiency = (
        pd.read_csv(energy_efficiency)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    energy_efficiency = energy_efficiency.apply(lambda x: x + 1, axis=1)
    energy_efficiency = energy_efficiency.reindex(energy_demand.index)
    energy_demand_post_efficiency = energy_demand - (
        energy_demand * energy_efficiency.values
    )

    # Apply percentage reduction & shift to electrification attributed to heat pumps and electrification of industry
    heat_pumps = (
        pd.read_csv(heat_pumps)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)
    heat_pumps = heat_pumps.reindex(energy_demand.index)
    energy_demand_post_heat_pumps = energy_demand - (energy_demand * heat_pumps.values)

    # Apply percentage reduction & shift to electrification attributed to transportation improvements
    transport_efficiency = (
        pd.read_csv(transport_efficiency)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    transport_efficiency = transport_efficiency.apply(lambda x: x + 1, axis=1)
    transport_efficiency = transport_efficiency.reindex(energy_demand.index)
    energy_demand_post_transport = energy_demand - (
        energy_demand * transport_efficiency.values
    )

    # Apply percentage reduction attributed to solar thermal
    solar_thermal = (
        pd.read_csv(solar_thermal)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    solar_thermal = solar_thermal.apply(lambda x: x + 1, axis=1)
    solar_thermal = solar_thermal.reindex(energy_demand.index)
    energy_demand_post_solarthermal = energy_demand - (
        energy_demand * solar_thermal.values
    )

    # Apply shift attributed to biofuels
    biofuels = (
        pd.read_csv(biofuels)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    biofuels = biofuels.apply(lambda x: x + 1, axis=1)
    biofuels = biofuels.reindex(energy_demand.index)
    energy_demand_post_biofuels = energy_demand - (energy_demand * biofuels.values)

    # Estimate energy demand from CDR
    cdr_energy = pd.concat(
        [energy_demand.loc["World ", "Industry", "Electricity"] * 0.5],
        keys=["CDR"],
        names=["Metric"],
    )
    cdr_energy["IEA Region"] = "World "
    cdr_energy["Sector"] = "Industry"
    cdr_energy.reset_index(inplace=True)
    cdr_energy.set_index(["IEA Region", "Sector", "Metric", "Scenario"], inplace=True)
    energy_demand = energy_demand.append(cdr_energy)
    energy_demand.loc["OECD ", "Industry", "Electricity"] = (
        energy_demand.loc["OECD ", "Industry", "Electricity"].add(cdr_energy).values
    )

    # Add energy demand from international bunker
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
        - energy_demand_post_bunker
    )
    """
    # Smooth energy demand curves

    xnew = np.linspace(
        energy_demand.columns.values.astype(int).min(),
        energy_demand.columns.values.astype(int).max(),
        11,
    )
    energy_demand = energy_demand.apply(
        lambda x: interp1d(energy_demand.columns.values.astype(int), x, kind="cubic"),
        axis=1,
    )
    energy_demand = energy_demand.apply(lambda x: x(xnew))
    energy_demand = pd.DataFrame(energy_demand)

    # Apply adoption_curves to energy demand
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
    energy_demand.columns = energy_demand.columns.astype(int)
    energy_demand.clip(lower=0, inplace=True)

    return energy_demand
