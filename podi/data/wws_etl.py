#!/usr/bin/env python

import pandas as pd
from numpy import NaN
from energy_demand import iea_region_list


def wws_etl(data_source):
    elec_gen = pd.read_csv("podi/data/wws.csv").dropna()
    region_categories = pd.read_csv(
        "podi/data/region_categories.csv", usecols=["WWS Region", "IEA Region"]
    )

    elec_gen = elec_gen.merge(
        region_categories, right_on=["WWS Region"], left_on=["Region"]
    )

    # collect rows into IEA regions
    elec_gen = elec_gen.groupby("IEA Region").mean() * 100

    # split into various levels of IEA regional grouping
    elec_gen["IEA Region 1"] = elec_gen.apply(lambda x: x.name.split()[0] + " ", axis=1)
    elec_gen["IEA Region 2"] = elec_gen.apply(lambda x: x.name.split()[2] + " ", axis=1)
    elec_gen["IEA Region 3"] = elec_gen.apply(
        lambda x: x.name.split()[-1] + " ", axis=1
    )
    elec_gen.set_index(["IEA Region 1", "IEA Region 2", "IEA Region 3"], inplace=True)

    # make new row for world level data
    elec_gen_world = pd.DataFrame(elec_gen.mean()).T.rename(index={0: "World "})

    # make new rows for advanced/developing economies
    elec_gen_eco = pd.DataFrame(elec_gen.groupby("IEA Region 1").mean())

    # make new rows for OECD/NonOECD regions
    elec_gen_oecd = pd.DataFrame(elec_gen.groupby("IEA Region 2").mean()).rename(
        index={"OECD ": " OECD "}
    )

    # make new rows for IEA regions
    elec_gen_regions = pd.DataFrame(elec_gen.groupby("IEA Region 3").mean())

    # combine all
    elec_gen = elec_gen_world.append([elec_gen_eco, elec_gen_oecd, elec_gen_regions])
    elec_gen.index.name = "IEA Region"

    # combine columns to match tech_list
    mapping = {
        "Onshore wind": "Wind",
        "Offshore wind": "Wind",
        "Wave device": "Tide and wave",
        "Geothermal electric plant": "Geothermal",
        "Hydroelectric plant": "Hydroelectricity",
        "Tidal turbine": "Tide and wave",
        "Res. roof PV system": "Solar",
        "Com/gov/Indus roof PV system": "Solar",
        "Solar PV plant": "Solar",
        "CSP plant": "Solar",
    }
    elec_gen = elec_gen.groupby(mapping, axis=1).sum().round()

    # melt
    elec_gen = pd.melt(
        elec_gen, var_name="Technology", value_name="Value", ignore_index=False
    )
    elec_gen["Metric"] = "Saturation Point"
    elec_gen["Sector"] = "Electricity"
    elec_gen["Scenario"] = "pathway"
    elec_gen.reset_index(inplace=True)

    elec_gen = pd.DataFrame(elec_gen).set_index(
        ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
    )

    params = []
    for i in range(0, len(iea_region_list)):
        params = pd.DataFrame(params).append(
            pd.concat(
                [
                    elec_gen.loc[iea_region_list[i]].div(
                        elec_gen.loc[iea_region_list[i]].sum()
                    )
                    * 100
                ],
                keys=[iea_region_list[i]],
                names=["IEA Region"],
            ).round(decimals=1)
        )

    """
    params.reset_index(inplace=True)
    params = (
        pd.DataFrame(params).set_index(
            ["IEA Region", "Technology", "Scenario", "Sector", "Metric"]
        )
    )
    """

    # add to tech_parameters
    tech_parameters = pd.read_csv("podi/data/tech_parameters.csv")
    tech_parameters = tech_parameters.append(params.reset_index())
    tech_parameters.to_csv("podi/data/tech_parameters.csv", index=False)

    return
