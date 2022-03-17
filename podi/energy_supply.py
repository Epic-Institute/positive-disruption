#!/usr/bin/env python

# region

from operator import index
import re
import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
from podi.curve_smooth import curve_smooth
from pandarallel import pandarallel
import os

file = open("podi/data/y_data.csv", "w")
file.close()

file = open("podi/data/y_data2.csv", "w")
file.close()

pandarallel.initialize(nb_workers=8)

# endregion


def energy_supply(
    scenario, energy_demand, data_start_year, data_end_year, proj_end_year
):

    ###################################
    # ESTIMATE ELECTRIC ENERGY SUPPLY #
    ###################################

    # region

    # Add IRENA data for select electricity technologies

    # region
    irena = pd.read_csv(
        "podi/data/IRENA/electricity_supply_historical.csv", index_col="Region"
    )

    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "IRENA Region"],
            ).dropna(axis=0)
        )
        .set_index(["IRENA Region"])
        .rename_axis(index={"IRENA Region": "Region"})
    )

    irena = (
        irena.merge(regions, on=["Region"])
        .reset_index()
        .set_index(["WEB Region", "Region"])
        .droplevel("Region")
        .rename_axis(index={"WEB Region": "Region"})
    )
    irena.index = irena.index.str.lower()
    irena["Scenario"] = scenario
    irena = irena.reset_index().set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]
    )

    irena.columns = irena.columns.astype(int)
    irena = irena.loc[:, data_start_year:data_end_year]

    # Drop IEA WIND and SOLARPV to avoid duplication with IRENA ONSHORE/OFFSHORE/ROOFTOP/SOLARPV
    energy_demand.drop(labels="WIND", level=6, inplace=True)
    energy_demand.drop(labels="SOLARPV", level=6, inplace=True)

    energy_demand = pd.concat(
        [
            energy_demand,
            irena[
                irena.index.get_level_values(6).isin(
                    ["ONSHORE", "OFFSHORE", "ROOFTOP", "SOLARPV"]
                )
            ],
        ]
    )

    # endregion

    # For each region, find the percent of total electricity consumption met by each product. For future years, the percentage for renewables will not yet be updated to reflect logistic-style growth that covers the electrified demand (ELECTR) estimated in energy_demand.py.
    elec_supply = (
        energy_demand.loc[
            scenario,
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            [
                "Electricity output",
            ],
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            "N",
            :,
        ]
        .groupby(
            [
                "Region",
                "Sector",
                "Subsector",
                "Product_category",
                "Product_long",
                "Product",
            ]
        )
        .sum()
    )

    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total electricity consumption met by each renewable product to estimate projected percent of total electricity consumption each meets
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
    parameters = parameters.sort_index()

    renewables = [
        "GEOTHERM",
        "HYDRO",
        "ROOFTOP",
        "SOLARPV",
        "SOLARTH",
        "OFFSHORE",
        "ONSHORE",
        "TIDE",
    ]

    per_elec_supply[per_elec_supply.index.get_level_values(5).isin(renewables)] = (
        per_elec_supply[per_elec_supply.index.get_level_values(5).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[0], x.name[5], scenario, x.name[1]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Set renewables generation to meet ELECTR (which represents electrified demand that replaces fossil fuels, calculated in energy_demand.py)
    elec_supply[
        elec_supply.index.get_level_values(5).isin(renewables)
    ] = per_elec_supply[
        per_elec_supply.index.get_level_values(5).isin(renewables)
    ].parallel_apply(
        lambda x: x.multiply(
            elec_supply[
                elec_supply.index.get_level_values(5).isin(
                    pd.concat([pd.DataFrame(renewables), pd.DataFrame(["ELECTR"])])
                    .squeeze()
                    .values
                )
            ]
            .groupby("Region")
            .sum(0)
            .loc[x.name[0]]
        ),
        axis=1,
    )

    # Drop ELECTR now that it has been reallocated to the specific set of renewables
    per_elec_supply.drop(labels="ELECTR", level=5, inplace=True)
    elec_supply.drop(labels="ELECTR", level=5, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_elec_supply = elec_supply.parallel_apply(
        lambda x: x.divide(elec_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # endregion

    ################################
    # ESTIMATE HEAT ENERGY SUPPLY #
    ################################

    # region

    # Add IRENA data for select heat technologies
    """    
    # region
    irena = pd.read_csv(
        "podi/data/IRENA/heat_supply_historical.csv", index_col="Region"
    )

    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "IRENA Region"],
            ).dropna(axis=0)
        )
        .set_index(["IRENA Region"])
        .rename_axis(index={"IRENA Region": "Region"})
    )

    irena = (
        irena.merge(regions, on=["Region"])
        .reset_index()
        .set_index(["WEB Region", "Region"])
        .droplevel("Region")
        .rename_axis(index={"WEB Region": "Region"})
    )
    irena.index = irena.index.str.lower()
    irena["Scenario"] = scenario
    irena = irena.reset_index().set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]
    )

    irena.columns = irena.columns.astype(int)
    irena = irena.loc[:, data_start_year:data_end_year]

    energy_demand = pd.concat(
        [energy_demand, irena[irena.index.get_level_values(6).isin(["SOLARTH"])]]
    )

    # endregion
    """

    # For each region, find the percent of total heat consumption met by each product. For future years, the percentage for renewables will not yet be updated to reflect logistic-style growth that covers the electrified/renewables heat demand estimated in energy_demand.py.

    heat_supply = (
        energy_demand.loc[
            scenario,
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            [
                "Heat output",
            ],
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            "N",
            :,
        ]
        .groupby(
            [
                "Region",
                "Sector",
                "Subsector",
                "Product_category",
                "Product_long",
                "Product",
            ]
        )
        .sum()
    )

    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total heat consumption met by each renewable product to estimate projected percent of total heat consumption each meets
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
    parameters = parameters.sort_index()

    renewables = [
        "ELECTR",
        "HEAT",
        "BIOGASES",
        "MUNWASTER",
        "OBIOLIQ",
        "PRIMSBIO",
        "GEOTHERM",
        "BIODIESEL",
    ]

    per_heat_supply[per_heat_supply.index.get_level_values(5).isin(renewables)] = (
        per_heat_supply[per_heat_supply.index.get_level_values(5).isin(renewables)]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[0], x.name[5], scenario, x.name[1]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Set renewables heat generation to meet RHEAT (which represents heat demand previously met by fossil fuel heat but replaced by renewables heat, calculated in energy_demand.py)
    heat_supply[
        heat_supply.index.get_level_values(5).isin(renewables)
    ] = per_heat_supply[
        per_heat_supply.index.get_level_values(5).isin(renewables)
    ].parallel_apply(
        lambda x: x.multiply(
            heat_supply[
                heat_supply.index.get_level_values(5).isin(
                    pd.concat([pd.DataFrame(renewables), pd.DataFrame(["RHEAT"])])
                    .squeeze()
                    .values
                )
            ]
            .groupby("Region")
            .sum(0)
            .loc[x.name[0]]
        ),
        axis=1,
    )

    # Drop RHEAT now that it has been reallocated to the specific set of renewables
    per_heat_supply.drop(labels="RHEAT", level=5, inplace=True)
    heat_supply.drop(labels="RHEAT", level=5, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_heat_supply = heat_supply.parallel_apply(
        lambda x: x.divide(heat_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # endregion

    ################################################
    # ESTIMATE NONELECTRIC TRANSPORT ENERGY SUPPLY #
    ################################################

    # region

    # Add IRENA data for select transport technologies
    """    
    # region
    irena = pd.read_csv(
        "podi/data/IRENA/transport_supply_historical.csv", index_col="Region"
    )

    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "IRENA Region"],
            ).dropna(axis=0)
        )
        .set_index(["IRENA Region"])
        .rename_axis(index={"IRENA Region": "Region"})
    )

    irena = (
        irena.merge(regions, on=["Region"])
        .reset_index()
        .set_index(["WEB Region", "Region"])
        .droplevel("Region")
        .rename_axis(index={"WEB Region": "Region"})
    )
    irena.index = irena.index.str.lower()
    irena["Scenario"] = scenario
    irena = irena.reset_index().set_index(
        [
            "Scenario",
            "Region",
            "Sector",
            "Subsector",
            "Product_category",
            "Product_long",
            "Product",
            "Flow_category",
            "Flow_long",
            "Flow",
            "Hydrogen",
            "Flexible",
            "Non-Energy Use",
        ]
    )

    irena.columns = irena.columns.astype(int)
    irena = irena.loc[:, data_start_year:data_end_year]

    energy_demand = pd.concat(
        [energy_demand, irena[irena.index.get_level_values(6).isin(["EVS"])]]
    )

    # endregion
    """

    # For each region, find the percent of total transport consumption met by each product. For future years, the percentage for renewables will not yet be updated to reflect logistic-style growth that covers the electrified/renewables transport demand estimated in energy_demand.py.

    transport_supply = (
        energy_demand.loc[
            scenario,
            slice(None),
            ["Transportation"],
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            slice(None),
            "N",
            :,
        ]
        .groupby(
            [
                "Region",
                "Sector",
                "Subsector",
                "Product_category",
                "Product_long",
                "Product",
                "Flow_category",
                "Flow_long",
            ]
        )
        .sum()
    )

    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # Use the historical percent of total transport consumption met by each renewable product to estimate projected percent of total transport consumption each meets
    parameters = pd.read_csv(
        "podi/data/tech_parameters.csv",
        usecols=["Region", "Product", "Scenario", "Sector", "Metric", "Value"],
    ).set_index(["Region", "Product", "Scenario", "Sector", "Metric"])
    parameters = parameters.sort_index()

    renewables = [
        "BIODIESEL",
        "ELECTR",
        "HYDROGEN",
        "BIOGASOL",
        "BIOGASES",
        "PRIMSBIO",
        "OBIOLIQ",
    ]

    per_transport_supply[
        per_transport_supply.index.get_level_values(5).isin(renewables)
    ] = (
        per_transport_supply[
            per_transport_supply.index.get_level_values(5).isin(renewables)
        ]
        .parallel_apply(
            lambda x: adoption_curve(
                parameters.loc[x.name[0], x.name[5], scenario, x.name[1]],
                x,
                scenario,
                data_start_year,
                data_end_year,
                proj_end_year,
            ),
            axis=1,
        )
        .clip(upper=1)
    )

    # Set renewables transport generation to meet RTRANS (which represents transport demand previously met by fossil fuel transport but replaces by renewables transport, calculated in energy_demand.py)
    transport_supply[
        transport_supply.index.get_level_values(5).isin(renewables)
    ] = per_elec_supply[
        per_elec_supply.index.get_level_values(5).isin(renewables)
    ].parallel_apply(
        lambda x: x.multiply(
            transport_supply[
                transport_supply.index.get_level_values(5).isin(
                    pd.concat([pd.DataFrame(renewables), pd.DataFrame(["RTRANS"])])
                    .squeeze()
                    .values
                )
            ]
            .groupby("Region")
            .sum(0)
            .loc[x.name[0]]
        ),
        axis=1,
    )

    # Drop RTRANS now that it has been reallocated to the specific set of renewables
    per_transport_supply.drop(labels="RTRANS", level=5, inplace=True)
    transport_supply.drop(labels="RTRANS", level=5, inplace=True)

    # Recalculate percent of total consumption each technology meets
    per_transport_supply = transport_supply.parallel_apply(
        lambda x: x.divide(transport_supply.groupby(["Region"]).sum(0).loc[x.name[0]]),
        axis=1,
    ).fillna(0)

    # endregion

    ##############################
    #  SAVE OUTPUT TO CSV FILES  #
    ##############################

    # region
    pd.concat([per_elec_supply, per_heat_supply, per_transport_supply]).to_csv(
        "podi/data/per_energy_supply_" + str(scenario) + ".csv"
    )

    pd.concat([elec_supply, heat_supply, transport_supply]).to_csv(
        "podi/data/energy_supply_" + str(scenario) + ".csv"
    )

    # endregion

    return (
        pd.concat([per_elec_supply, per_heat_supply, per_transport_supply]),
        pd.concat([elec_supply, heat_supply, transport_supply]),
    )
