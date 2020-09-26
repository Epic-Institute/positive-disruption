#!/usr/bin/env python

import pandas as pd
from podi.energy_supply import data_start_year, long_proj_end_year


def results_analysis(
    region,
    energy_demand_baseline,
    energy_demand_pathway,
    elec_consump,
    heat_consump2,
    transport_consump2,
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

    grid_decarb = energy_demand_pathway.loc[region,'TFC','Electricity'].sum()
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

    transport_consump2.columns = transport_consump2.columns.astype(int)
    energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
    energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

    transport_decarb = (
        pd.DataFrame(transport_consump2.loc[region, "Biofuels"])
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
                        "International bunkers",
                    ],
                ].sum()
            )
        )
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels"],
                ].sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels"],
                ].sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels"],
                ]
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels"],
                ]
                .sum()
                .sum()
            )
        ).cumsum()
    ) / 2

    transport_decarb = pd.DataFrame(transport_decarb).T
    transport_decarb.rename(index={0: "Transport"}, inplace=True)

    # endregion

    # BUILDINGS DECARB

    # region

    renewable_elec = (
        elec_consump.loc[
            region,
            [
                "Biomass and waste",
                "Geothermal",
                "Hydroelectricity",
                "Nuclear",
                "Solar",
                "Wind",
            ],
            :,
        ]
        .sum()
        .div(elec_consump.loc[region, slice(None), :].sum())
    )

    building_decarb = (
        energy_demand_pathway.loc[region, "Buildings", ["Electricity"]]
        .droplevel(["IEA Region", "Sector", "Scenario"])
        .multiply(renewable_elec)
        .div(
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .multiply(renewable_elec)
            )
            .max(axis=1)
            .values[0]
        )
        .values[0]
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
            heat_consump2.loc[
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
