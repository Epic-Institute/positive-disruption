#!/usr/bin/env python

import pandas as pd
from podi.energy_supply import data_start_year, long_proj_end_year


def results_analysis(
    region,
    energy_demand_baseline,
    energy_demand_pathway,
    elec_consump,
    heat_consump_pathway,
    transport_consump_pathway,
    afolu_per_adoption,
    cdr_needed_def,
):

    ###################
    # ADOPTION CURVES #
    ###################

    # region

    # GRID DECARB

    # region

    decarb = [
        "Biomass and waste",
        "Geothermal",
        "Hydroelectricity",
        "Solar",
        "Wind",
        "Tide and wave",
    ]

    grid_decarb = (
        elec_consump.loc[elec_consump.index.isin(decarb, level=1)]
        .sum()
        .div(elec_consump.drop("Nuclear", level=1).sum())
    )
    grid_decarb = pd.DataFrame(grid_decarb).T
    grid_decarb.columns = grid_decarb.columns.astype(int)
    grid_decarb.rename(index={0: "Grid"}, inplace=True)
    grid_decarb.loc[:, 2010:2018] = [
        0.25,
        0.258,
        0.275,
        0.289,
        0.303,
        0.325,
        0.355,
        0.373,
        0.385,
    ]

    # endregion

    # TRANSPORTATION DECARB

    # region

    transport_consump_pathway.columns = transport_consump_pathway.columns.astype(int)
    energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
    energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

    transport_decarb = (
        pd.DataFrame(transport_consump_pathway.loc[region, "Biofuels"])
        .T.droplevel(level=0)
        .append(energy_demand_pathway.loc[region, "Transport", "Electricity"])
        .sum()
        .div(
            max(
                energy_demand_pathway.loc[
                    region,
                    "Transport",
                    [
                        "Oil",
                        "Electricity",
                        "Biofuels",
                        "Other fuels",
                    ],
                ]
                .sum()
                .add(
                    energy_demand_pathway.loc[
                        "World ", "Transport", ["International bunkers"]
                    ]
                )
                .sum()
            )
        )
        / 0.9
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    [
                        "Oil",
                        "Electricity",
                        "Biofuels",
                        "Other fuels",
                    ],
                ]
                .sum()
                .add(
                    energy_demand_pathway.loc[
                        "World ", "Transport", ["International bunkers"]
                    ]
                )
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    [
                        "Oil",
                        "Electricity",
                        "Biofuels",
                        "Other fuels",
                    ],
                ]
                .sum()
                .add(
                    energy_demand_pathway.loc[
                        "World ", "Transport", ["International bunkers"]
                    ]
                )
                .sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    [
                        "Oil",
                        "Electricity",
                        "Biofuels",
                        "Other fuels",
                    ],
                ]
                .sum()
                .add(
                    energy_demand_pathway.loc[
                        "World ", "Transport", ["International bunkers"]
                    ]
                )
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    [
                        "Oil",
                        "Electricity",
                        "Biofuels",
                        "Other fuels",
                    ],
                ]
                .sum()
                .add(
                    energy_demand_pathway.loc[
                        "World ", "Transport", ["International bunkers"]
                    ]
                )
                .sum()
                .sum()
            )
        ).cumsum()
        / 1.05
    ) / 2

    transport_decarb = pd.DataFrame(transport_decarb).T
    transport_decarb.rename(index={0: "Transport"}, inplace=True)

    # endregion

    # BUILDINGS DECARB

    # region

    renewable_elec = (
        elec_consump_pathway.loc[
            region,
            [
                "Biomass and waste",
                "Geothermal",
                "Hydroelectricity",
                "Nuclear",
                "Solar",
                "Tide and wave",
                "Wind",
            ],
            :,
        ]
        .sum()
        .div(elec_consump_pathway.loc[region, slice(None), :].sum())
    )

    building_decarb = (
        (
            energy_demand_pathway.loc[region, "Buildings", ["Electricity", "Bioenergy"]]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
            .div(
                energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    ["Bioenergy", "Electricity"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .loc[2100]
            )
        )
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Buildings",
                    [
                        "Bioenergy",
                        "Coal",
                        "Electricity",
                        "Heat",
                        "Natural gas",
                        "Oil",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    [
                        "Bioenergy",
                        "Coal",
                        "Electricity",
                        "Heat",
                        "Natural gas",
                        "Oil",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Buildings",
                    [
                        "Bioenergy",
                        "Coal",
                        "Electricity",
                        "Heat",
                        "Natural gas",
                        "Oil",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    [
                        "Bioenergy",
                        "Coal",
                        "Electricity",
                        "Heat",
                        "Natural gas",
                        "Oil",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
            )
        ).cumsum()
    ) / 2

    building_decarb = pd.DataFrame(building_decarb).T
    building_decarb.rename(index={0: "Buildings"}, inplace=True)

    # endregion

    # INDUSTRY DECARB

    # region

    industry_decarb = (
        energy_demand_pathway.loc[
            region, "Industry", ["Electricity", "Bioenergy", "Other renewables"]
        ].append(
            heat_consump_pathway.loc[
                region,
                ["Bioenergy", "Geothermal", "Nuclear", "Solar thermal", "Waste"],
                :,
            ]
        )
    ).sum().div(
        max(
            energy_demand_pathway.loc[
                region,
                "Industry",
                [
                    "Electricity",
                    "Bioenergy",
                    "Oil",
                    "Natural gas",
                    "Other renewables",
                    "Heat",
                    "Coal",
                ],
            ]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
            .values
        )
    ) + (
        (
            energy_demand_baseline.loc[
                region,
                "Industry",
                [
                    "Electricity",
                    "Bioenergy",
                    "Coal",
                    "Oil",
                    "Other renewables",
                    "Heat",
                    "Coal",
                ],
            ]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
            - energy_demand_pathway.loc[
                region,
                "Industry",
                [
                    "Electricity",
                    "Bioenergy",
                    "Coal",
                    "Oil",
                    "Other renewables",
                    "Heat",
                    "Coal",
                ],
            ]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
        )
        / (
            energy_demand_baseline.loc[
                region,
                "Industry",
                [
                    "Electricity",
                    "Bioenergy",
                    "Coal",
                    "Oil",
                    "Other renewables",
                    "Heat",
                    "Coal",
                ],
            ]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
            .sum()
            - energy_demand_pathway.loc[
                region,
                "Industry",
                [
                    "Electricity",
                    "Bioenergy",
                    "Coal",
                    "Oil",
                    "Other renewables",
                    "Heat",
                    "Coal",
                ],
            ]
            .droplevel(["IEA Region", "Sector", "Scenario"])
            .sum()
            .sum()
        )
    ).cumsum() / 2

    industry_decarb = pd.DataFrame(industry_decarb).T
    industry_decarb.rename(index={0: "Industry"}, inplace=True)

    # endregion

    # REGENERATIVE AGRICULTURE DECARB

    # region

    ra_decarb = afolu_per_adoption.loc[
        "World ",
        slice(None),
        [
            " Biochar ",
            " Cropland Soil Health ",
            " Improved Rice ",
            " Nitrogen Fertilizer Management ",
            " Trees in Croplands ",
            " Animal Mgmt ",
            " Legumes ",
            " Optimal intensity ",
            " Silvopasture ",
        ],
        slice(None),
    ]
    ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb.sum().max()).T.rename(
        index={0: "Regenerative Agriculture"}
    )
    ra_decarb.columns = ra_decarb.columns.astype(int)

    # endregion

    # FORESTS & WETLANDS DECARB

    # region

    fw_decarb = afolu_per_adoption.loc[
        "World ",
        slice(None),
        [
            " Avoided Coastal Impacts ",
            " Avoided Forest Conversion ",
            " Avoided Peat Impacts ",
            " Coastal Restoration ",
            " Improved Forest Mgmt ",
            " Peat Restoration ",
            " Natural Regeneration ",
        ],
        slice(None),
    ]
    fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb.sum().max()).T.rename(
        index={0: "Forests & Wetlands"}
    )
    fw_decarb.columns = fw_decarb.columns.astype(int)
    fw_decarb.columns = ra_decarb.columns

    # endregion

    # CDR DECARB

    # region

    cdr_decarb = pd.DataFrame(
        pd.DataFrame(cdr_needed_def) / pd.DataFrame(cdr_needed_def).max()
    ).T
    cdr_decarb.columns = grid_decarb.columns
    cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)

    # endregion

    adoption_curves = grid_decarb.loc[:, data_start_year:long_proj_end_year].append(
        transport_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    adoption_curves = adoption_curves.append(
        building_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    adoption_curves = adoption_curves.append(
        industry_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    adoption_curves = adoption_curves.append(
        ra_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    adoption_curves = adoption_curves.append(
        fw_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    adoption_curves = adoption_curves.append(
        cdr_decarb.loc[:, data_start_year:long_proj_end_year]
    )

    # endregion

    return adoption_curves
