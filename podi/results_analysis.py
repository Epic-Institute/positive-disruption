#!/usr/bin/env python

import pandas as pd
from podi.energy_supply import data_start_year, long_proj_end_year
from podi.adoption_curve import adoption_curve
from podi.energy_supply import near_proj_start_year


def results_analysis(
    region,
    scenario,
    energy_demand_baseline,
    energy_demand_pathway,
    elec_consump_pathway,
    heat_consump_pathway,
    transport_consump_pathway,
    afolu_per_adoption,
    cdr_pathway,
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
        "Nuclear",
        "Solar",
        "Wind",
        "Tide and wave",
    ]

    grid_decarb = (
        elec_consump_pathway.loc[elec_consump_pathway.index.isin(decarb, level=1)]
        .sum()
        .div(elec_consump_pathway.sum())
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
        pd.DataFrame(transport_consump_pathway.loc[region, "Biofuels", :])
        .droplevel(level=0)
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

    renewable_heat = (
        heat_consump_pathway.loc[
            region,
            ["Bioenergy" "Geothermal", "Nuclear", "Solar thermal", "Waste"],
            :,
        ]
        .sum()
        .div(heat_consump_pathway.loc[region, slice(None), :].sum())
    )

    building_decarb = (
        (
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()
                * renewable_elec
            )
            .add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                * renewable_heat
            )
            .div(
                max(
                    (
                        energy_demand_pathway.loc[
                            region, "Buildings", ["Electricity"]
                        ].sum()
                        * renewable_elec
                    ).add(
                        energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                        * renewable_heat
                    )
                )
            )
        )
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Buildings",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Buildings",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Buildings",
                    ["Electricity", "Heat"],
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
        (
            (
                energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()
                * renewable_elec
            )
            .add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                * renewable_heat
            )
            .div(
                max(
                    (
                        energy_demand_pathway.loc[
                            region, "Industry", ["Electricity"]
                        ].sum()
                        * renewable_elec
                    ).add(
                        energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                        * renewable_heat
                    )
                )
            )
        )
        + (
            (
                energy_demand_baseline.loc[
                    region,
                    "Industry",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Industry",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
            )
            / (
                energy_demand_baseline.loc[
                    region,
                    "Industry",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
                - energy_demand_pathway.loc[
                    region,
                    "Industry",
                    ["Electricity", "Heat"],
                ]
                .droplevel(["IEA Region", "Sector", "Scenario"])
                .sum()
                .sum()
            )
        ).cumsum()
    ) / 2

    industry_decarb = pd.DataFrame(industry_decarb).T
    industry_decarb.rename(index={0: "Industry"}, inplace=True)

    # endregion

    # REGENERATIVE AGRICULTURE DECARB

    # region

    ra_decarb = afolu_per_adoption.loc[
        region,
        [
            "Biochar",
            "Cropland Soil Health",
            "Improved Rice",
            "Nitrogen Fertilizer Management",
            "Trees in Croplands",
            "Animal Mgmt",
            "Legumes",
            "Optimal Intensity",
            "Silvopasture",
        ],
        :,
    ]
    ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb.sum().max()).T.rename(
        index={0: "Regenerative Agriculture"}
    )
    ra_decarb.columns = ra_decarb.columns.astype(int)

    # endregion

    # FORESTS & WETLANDS DECARB

    # region

    fw_decarb = afolu_per_adoption.loc[
        region,
        [
            "Avoided Coastal Impacts",
            "Avoided Forest Conversion",
            "Avoided Peat Impacts",
            "Coastal Restoration",
            "Improved Forest Mgmt",
            "Peat Restoration",
            "Natural Regeneration",
        ],
        :,
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
        pd.DataFrame(cdr_pathway).sum() / pd.DataFrame(cdr_pathway).sum().max()
    ).T
    cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
        cdr_decarb.idxmax(1).values[0]
    ]
    cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
    cdr_decarb = pd.Series(
        cdr_decarb.values[0], index=cdr_decarb.columns, name="Carbon Dioxide Removal"
    )

    cdr_decarb = adoption_curve(cdr_decarb, "World ", "Pathway", "All").T
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

    """

    adoption_curves = adoption_curves.apply(
        adoption_curve, axis=1, args=["World ", scenario], sector="All"
    )

    perc = []
    for i in range(0, len(adoption_curves.index)):
        perc = pd.DataFrame(perc).append(adoption_curves[adoption_curves.index[i]][0].T)

    adoption_curves = pd.DataFrame(perc.loc[:, near_proj_start_year:]).set_index(
        adoption_curves.index
    )
    """

    return adoption_curves
