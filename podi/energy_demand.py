#!/usr/bin/env python

# region

import pandas as pd
from podi.curve_smooth import curve_smooth

# endregion


def energy_demand(
    scenario,
    demand_historical,
    demand_projection,
    energy_efficiency,
    heat_pumps,
    solar_thermal,
    trans_grid,
    cdr_demand,
):

    ##################################
    #  DEFINE AND REALLOCATE DEMAND  #
    ##################################

    # region

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

    energy_demand = energy_demand.append(
        pd.concat(
            [energy_demand.loc[slice(None), "Other", slice(None), slice(None)]],
            keys=["Industry"],
            names=["Sector"],
        ).reorder_levels(["IEA Region", "Sector", "Metric", "Scenario"])
    )

    energy_demand.drop(
        labels="Other",
        level=1,
        inplace=True,
    )

    """
    energy_demand.loc[slice(None), "Industry", "Other renewables", scenario] = (
        (
            (
                energy_demand.loc[
                    slice(None),
                    ["Industry", "Other"],
                    ["Other renewables", "Other"],
                    scenario,
                ].groupby("IEA Region")
            ).sum()
        )
        .reindex_like(
            energy_demand.loc[slice(None), "Industry", "Other renewables", scenario]
        )
        .values
    )
    """

    # Reallocate heat demand within industry
    energy_demand.loc[slice(None), "Industry", "Heat", scenario] = (
        (
            energy_demand.loc[
                slice(None),
                "Industry",
                [
                    "Coal",
                    "Oil",
                    "Natural gas",
                    "Bioenergy",
                    "Other renewables",
                    "Other",
                ],
                scenario,
            ].groupby("IEA Region")
        )
        .sum()
        .reindex_like(energy_demand.loc[slice(None), "Industry", "Heat", scenario])
        .values
    )

    # Reallocate heat demand within buildings
    energy_demand.loc[slice(None), "Buildings", "Heat", scenario] = (
        (
            energy_demand.loc[
                slice(None),
                "Buildings",
                ["Coal", "Oil", "Natural gas", "Bioenergy", "Other renewables"],
                scenario,
            ].groupby("IEA Region")
        )
        .sum()
        .reindex_like(energy_demand.loc[slice(None), "Buildings", "Heat", scenario])
        .values
    )

    """
    # Reallocate international bunkers from Transport - Oil
    energy_demand.loc["World ", "Transport", "Oil"] = (
        energy_demand.loc["World ", "Transport", "Oil"] * 0.9
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
    """

    # endregion

    #######################################
    #  ENERGY DEMAND REDUCTIONS & SHIFTS  #
    #######################################

    # region

    # Apply percentage reduction attributed to energy efficiency measures (in buildings, industry, and transport)
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

    # Apply percentage reduction & shift to electrification attributed to heat pumps
    heat_pumps = (
        pd.read_csv(heat_pumps)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    heat_pumps = heat_pumps.apply(lambda x: x + 1, axis=1)
    heat_pumps = heat_pumps.reindex(energy_demand.index)
    energy_demand_post_heat_pumps = energy_demand - (energy_demand * heat_pumps.values)

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

    # Apply percentage reduction attributed to transactive grids

    trans_grid = (
        pd.read_csv(trans_grid)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )
    trans_grid = trans_grid.apply(lambda x: x + 1, axis=1)
    trans_grid = trans_grid.reindex(energy_demand.index)
    energy_demand_post_trans_grid = energy_demand - (energy_demand * trans_grid.values)

    # Apply adoption_curves to energy demand

    """
    def proj_demand(region, hist_demand):
        foo = hist_demand.loc[region,slice(None),slice(None),slice(None)].droplevel(['Scenario']).apply(
            adoption_curve,
            axis=1,
            args=(
                [
                    region,
                    'Electricity',
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
    # endregion

    #########
    #  CDR  #
    #########

    # region

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

    # endregion

    #################################################
    #  COMBINE, RECALCULATE SECTOR & END-USE DEMAND #
    #################################################

    # region

    energy_demand = (
        energy_demand
        - energy_demand_post_efficiency
        - energy_demand_post_heat_pumps
        - energy_demand_post_solarthermal
        - energy_demand_post_trans_grid
    )

    energy_demand.loc[slice(None), "Industry", "Industry"] = (
        (
            energy_demand.loc[slice(None), "Industry", ["Electricity", "Heat"]].groupby(
                "IEA Region"
            )
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "Buildings", "Buildings"] = (
        (
            energy_demand.loc[
                slice(None), "Buildings", ["Electricity", "Heat"]
            ].groupby("IEA Region")
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "Transport", "Transport"] = (
        (
            energy_demand.loc[
                slice(None),
                "Transport",
                ["Electricity", "Oil", "Bioenergy", "Other fuels"],
            ].groupby("IEA Region")
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "TFC", "Electricity"] = (
        (
            energy_demand.loc[
                slice(None), ["Industry", "Buildings", "Transport"], ["Electricity"]
            ].groupby("IEA Region")
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "TFC", "Heat"] = (
        (
            energy_demand.loc[
                slice(None), ["Industry", "Buildings", "Transport"], ["Heat"]
            ].groupby("IEA Region")
        )
        .sum()
        .values
    )

    energy_demand.loc[slice(None), "TFC", "Total final consumption"] = (
        (
            energy_demand.loc[
                slice(None),
                ["Industry", "Buildings", "Transport"],
                ["Industry", "Buildings", "Transport"],
            ].groupby("IEA Region")
        )
        .sum()
        .values
    )

    energy_demand.columns = energy_demand.columns.astype(int)
    energy_demand.clip(lower=0, inplace=True)

    energy_demand_hist = energy_demand.loc[:, :data_end_year]
    energy_demand_proj = curve_smooth(energy_demand.loc[:, (data_end_year + 1) :], 5)

    energy_demand = energy_demand_hist.join(energy_demand_proj).clip(lower=0)

    # endregion

    return energy_demand
