#!/usr/bin/env python

import pandas as pd


def results_analysis(
    energy_demand_baseline,
    energy_supply_baseline,
    afolu_baseline,
    emissions_baseline,
    cdr_baseline,
    climate_baseline,
    energy_demand_pathway,
    energy_supply_pathway,
    afolu_pathway,
    emissions_pathway,
    cdr_pathway,
    climate_pathway,
):

    ###################
    # ADOPTION CURVES #
    ###################

    # region

    acurve_start = 2020
    acurve_end = 2100

    # GRID DECARB

    # region

    decarb = [
        "Biomass and waste",
        "Geothermal",
        "Hydroelectricity",
        "Nuclear",
        "Solar",
        "Wind",
    ]

    grid_decarb = (
        elec_consump.loc[elec_consump.index.isin(decarb, level=1)]
        .sum()
        .div(elec_consump.groupby("Region", axis=0, level=1).sum())
    )
    grid_decarb.columns = grid_decarb.columns.astype(int)
    grid_decarb = grid_decarb.loc[:, acurve_start:acurve_end]
    grid_decarb.rename(index={"World ": "Grid"}, inplace=True)

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
                pd.DataFrame(transport_consump2.loc[region, "Biofuels"])
                .T.droplevel(level=0)
                .append(energy_demand_pathway.loc[region, "Transport", "Electricity"])
                .sum()
                .values
            )
        )
        / 1.8
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels", "Other fuels"],
                ].sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels", "Other fuels"],
                ].sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels", "Other fuels"],
                ]
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Transport",
                    ["Oil", "Electricity", "Biofuels", "Other fuels"],
                ]
                .sum()
                .sum()
            )
        ).cumsum()
        / 2.5
    )

    transport_decarb = pd.DataFrame(transport_decarb).T.loc[:, acurve_start:acurve_end]
    transport_decarb.rename(index={0: "Transport"}, inplace=True)

    # endregion

    # BUILDINGS DECARB

    # region

    heat_consump2 = heat_consump2.loc[:, acurve_start:acurve_end]

    building_decarb = (
        energy_demand_pathway.loc[
            region, "Buildings", ["Electricity", "Bioenergy", "Other renewables"]
        ]
        .droplevel(["IEA Region", "Sector", "Scenario"])
        .append(
            heat_consump2.loc[
                region,
                ["Bioenergy", "Geothermal", "Nuclear", "Solar thermal", "Waste"],
                :,
            ]
        )
        .sum()
        .div(
            max(
                energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    [
                        "Electricity",
                        "Bioenergy",
                        "Coal",
                        "Oil",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .values
            )
        )
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Buildings",
                    [
                        "Electricity",
                        "Bioenergy",
                        "Coal",
                        "Oil",
                        "Natural gas",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    [
                        "Electricity",
                        "Bioenergy",
                        "Coal",
                        "Oil",
                        "Natural gas",
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
                        "Electricity",
                        "Bioenergy",
                        "Coal",
                        "Oil",
                        "Natural gas",
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
                        "Electricity",
                        "Bioenergy",
                        "Coal",
                        "Oil",
                        "Natural gas",
                        "Other renewables",
                    ],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
            )
        ).cumsum()
    ) / 2

    building_decarb = pd.DataFrame(building_decarb).T.loc[:, acurve_start:acurve_end]
    building_decarb.rename(index={0: "Buildings"}, inplace=True)

    # endregion

    # INDUSTRY DECARB

    # region

    heat_consump2 = heat_consump2.loc[:, acurve_start:acurve_end]

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
    ) / 1.8 + (
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
    ).cumsum() / 1.45

    industry_decarb = pd.DataFrame(industry_decarb).T.loc[:, acurve_start:acurve_end]
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
    ra_decarb = ra_decarb.loc[:, acurve_start:acurve_end]

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
    fw_decarb = fw_decarb.loc[:, acurve_start:acurve_end]
    fw_decarb.columns = ra_decarb.columns

    # endregion

    # CDR DECARB

    # region

    cdr_decarb = pd.DataFrame(
        pd.DataFrame(CDR_NEEDED_DEF) / pd.DataFrame(CDR_NEEDED_DEF).max()
    ).T
    cdr_decarb.columns = np.arange(acurve_start, acurve_end + 1)
    cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)

    # endregion

    adoption_curves = grid_decarb.append(transport_decarb)
    adoption_curves = adoption_curves.append(building_decarb)
    adoption_curves = adoption_curves.append(industry_decarb)
    adoption_curves = adoption_curves.append(ra_decarb)
    adoption_curves = adoption_curves.append(fw_decarb)
    adoption_curves = adoption_curves.append(cdr_decarb)

    # endregion

    return results_analysis
