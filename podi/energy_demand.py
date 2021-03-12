#!/usr/bin/env python

# region

import pandas as pd
from podi.curve_smooth import curve_smooth
import numpy as np
from numpy import NaN

data_start_year = 1990
data_end_year = 2019

iea_region_list = (
    "World ",
    "NAM ",
    "US ",
    "CSAM ",
    "BRAZIL ",
    "EUR ",
    "AFRICA ",
    "SAFR ",
    "ME ",
    "RUS ",
    "ASIAPAC ",
    "CHINA ",
    "INDIA ",
    "JPN ",
    " OECD ",
    "NonOECD ",
)

gcam_region_list = (
    "World ",
    "OECD90 ",
    "OECD90 ",
    "LAM ",
    "LAM ",
    "OECD90 ",
    "MAF ",
    "MAF ",
    "MAF ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "ASIA ",
    "OECD90 ",
    "World ",
)

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

    ############################
    #  LOAD DEMAND INPUT DATA  #
    ############################

    # region

    # Load energy demand historical data (TWh) and projections (% change)
    energy_demand_historical = pd.read_csv(demand_historical)
    energy_demand_projection = pd.read_csv(demand_projection)

    # endregion

    ##################################
    #  DEFINE AND REALLOCATE DEMAND  #
    ##################################

    # region

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

    # Reallocate 'Other' energy demand from ag/non-energy use to industry heat

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
                    "Heat",
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
                [
                    "Coal",
                    "Oil",
                    "Natural gas",
                    "Heat",
                    "Bioenergy",
                    "Other renewables",
                ],
                scenario,
            ].groupby("IEA Region")
        )
        .sum()
        .reindex_like(energy_demand.loc[slice(None), "Buildings", "Heat", scenario])
        .values
    )

    energy_demand_hist = energy_demand.loc[:, : str(data_end_year)]
    energy_demand_proj = curve_smooth(
        energy_demand.loc[:, (str(data_end_year + 1)) :], "quadratic", 4
    )

    energy_demand = energy_demand_hist.join(energy_demand_proj).clip(lower=0)

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

    energy_efficiency = energy_efficiency.loc[:, : str(data_end_year + 1)].join(
        curve_smooth(energy_efficiency.loc[:, str(data_end_year + 1) :], "quadratic", 4)
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

    heat_pumps = heat_pumps.loc[:, : str(data_end_year + 1)].join(
        curve_smooth(heat_pumps.loc[:, str(data_end_year + 1) :], "quadratic", 4)
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

    solar_thermal = solar_thermal.loc[:, : str(data_end_year + 1)].join(
        curve_smooth(solar_thermal.loc[:, str(data_end_year + 1) :], "quadratic", 4)
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

    trans_grid = trans_grid.loc[:, : str(data_end_year + 1)].join(
        curve_smooth(trans_grid.loc[:, str(data_end_year + 1) :], "quadratic", 4)
    )

    # Apply transport mode design improvements

    # LDV (including two/three-wheelers)
    """
    ldv = (
        pd.read_csv(ldv)
        .set_index(["IEA Region", "Sector", "Metric", "Scenario"])
        .fillna(0)
    )

    ldv = ldv.apply(lambda x: x + 1, axis=1)
    ldv = ldv.reindex(energy_demand.index)
    energy_demand_post_ldv = energy_demand - (
        energy_demand * ldv.values
    )
    """
    # Shortrange Trucking

    # Longrange Trucking

    # Aviation (World Aviation Bunker, Domestic Aviation)

    # Remaining (Rail, Pipeline Transport, World Marine Bunker, Domestic Navigation, Non-specified Transport)

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

    # Add international bunker for World region
    energy_demand.loc["World ", "Transport", "Transport"] = (
        (
            energy_demand.loc[
                "World ",
                "Transport",
                [
                    "Electricity",
                    "Oil",
                    "Bioenergy",
                    "International bunkers",
                    "Other fuels",
                ],
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
    energy_demand_proj = curve_smooth(
        energy_demand.loc[:, (data_end_year + 1) :], "quadratic", 3
    )

    energy_demand = energy_demand_hist.join(energy_demand_proj).clip(lower=0)

    # endregion

    return energy_demand.round(decimals=0).replace(NaN, 0)
