#!/usr/bin/env python

import pandas as pd
from podi.data.eia_etl import metric_list


def bnef_etl(data_source, metric):
    if metric == "elec":
        # load electricity generation projections
        elec_gen = pd.read_csv(data_source).fillna(0)
        elec_gen = elec_gen.loc[
            (elec_gen["Metric"] == "Generation")
            | (elec_gen["Metric"] == "Total generation")
        ]

        # load region categories
        region_categories = pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["IEA Region", "BNEF Region"],
        ).drop_duplicates(ignore_index=True)

        # load metric categories
        metric_categories = pd.read_csv(
            "podi/data/metric_categories.csv", usecols=["EIA Metric", "BNEF Metric"]
        ).dropna()

        # add IEA region categories to electricity generation projections
        elec_gen = elec_gen.merge(
            region_categories, how="inner", right_on=["BNEF Region"], left_on=["Region"]
        )

        # drop unused columns
        elec_gen = elec_gen.drop(columns=["Metric", "Unit", "BNEF Region"])

        # add EIA metric categories to electricity generation projections
        elec_gen = (
            elec_gen.merge(
                metric_categories,
                how="left",
                right_on=["BNEF Metric"],
                left_on=["Sector"],
            )
            .drop(columns=["Sector", "BNEF Metric"])
            .dropna()
        )

        # change index naming and convert to TWh
        elec_gen["Unit"] = "TWh"
        elec_gen = elec_gen.set_index(
            ["Region", "IEA Region", "EIA Metric", "Scenario", "Unit"]
        )
        elec_gen.index = elec_gen.index.rename(
            ["Region", "IEA Region", "Metric", "Scenario", "Unit"]
        )
        elec_gen = elec_gen / 1000

        # combine like EIA metric categories
        elec_gen = elec_gen.groupby(
            by=["Region", "IEA Region", "Metric", "Scenario", "Unit"]
        ).sum()

        # create 'World' region
        elec_gen_world = elec_gen.groupby(by=["Metric"]).sum()
        elec_gen_world = elec_gen_world.assign(
            Region="World ", IEA_Region="World ", Scenario="pathway", Unit="TWh"
        ).set_index(["Region", "IEA_Region", "Scenario", "Unit"], append=True)
        elec_gen_world.index = elec_gen_world.index.rename(
            ["Metric", "Region", "IEA Region", "Scenario", "Unit"]
        ).reorder_levels(["Region", "IEA Region", "Metric", "Scenario", "Unit"])

        elec_gen = elec_gen.append(elec_gen_world)

        elec_gen = elec_gen[elec_gen.index.isin(metric_list, level=2)]

        return elec_gen
    elif metric == "heat":
        # load heat generation projections
        heat_gen = pd.read_csv(data_source).fillna(0)
        heat_gen = heat_gen.loc[
            (heat_gen["Metric"] == "Generation")
            | (heat_gen["Metric"] == "Total generation")
        ]

        # load region categories
        region_categories = pd.read_csv(
            "podi/data/region_categories.csv",
            usecols=["IEA Region", "BNEF Region"],
        ).drop_duplicates(ignore_index=True)

        # load metric categories
        metric_categories = pd.read_csv(
            "podi/data/metric_categories.csv", usecols=["EIA Metric", "BNEF Metric"]
        ).dropna()

        # add IEA region categories to heat generation projections
        heat_gen = heat_gen.merge(
            region_categories, how="inner", right_on=["BNEF Region"], left_on=["Region"]
        )

        # drop unused columns
        heat_gen = heat_gen.drop(columns=["Metric", "Unit", "BNEF Region"])

        # add EIA metric categories to heat generation projections
        heat_gen = (
            heat_gen.merge(
                metric_categories,
                how="left",
                right_on=["BNEF Metric"],
                left_on=["Sector"],
            )
            .drop(columns=["Sector", "BNEF Metric"])
            .dropna()
        )

        # change index naming and convert to TWh
        heat_gen["Unit"] = "TWh"
        heat_gen = heat_gen.set_index(
            ["Region", "IEA Region", "EIA Metric", "Scenario", "Unit"]
        )
        heat_gen.index = heat_gen.index.rename(
            ["Region", "IEA Region", "Metric", "Scenario", "Unit"]
        )
        heat_gen = heat_gen / 1000

        # combine like EIA metric categories
        heat_gen = heat_gen.groupby(
            by=["Region", "IEA Region", "Metric", "Scenario", "Unit"]
        ).sum()

        # create 'World' region
        heat_gen_world = heat_gen.groupby(by=["Metric"]).sum()
        heat_gen_world = heat_gen_world.assign(
            Region="World ", IEA_Region="World ", Scenario="pathway", Unit="TWh"
        ).set_index(["Region", "IEA_Region", "Scenario", "Unit"], append=True)
        heat_gen_world.index = heat_gen_world.index.rename(
            ["Metric", "Region", "IEA Region", "Scenario", "Unit"]
        ).reorder_levels(["Region", "IEA Region", "Metric", "Scenario", "Unit"])

        heat_gen = heat_gen.append(heat_gen_world)

        heat_gen = heat_gen[heat_gen.index.isin(metric_list, level=2)]

        return heat_gen