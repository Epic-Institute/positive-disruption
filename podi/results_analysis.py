#!/usr/bin/env python

# region

import pandas as pd
from podi.energy_demand import data_start_year
from podi.energy_supply import long_proj_end_year
from podi.adoption_curve import adoption_curve

# endregion


def results_analysis(
    region,
    scenario,
    energy_demand,
    elec_consump,
    elec_per_adoption,
    heat_consump,
    heat_per_adoption,
    transport_consump,
    transport_per_adoption,
    afolu_per_adoption,
    cdr,
    em,
    em_mitigated,
):

    ###################
    # ADOPTION CURVES #
    ###################

    if region == "World ":
        #################################
        # ADOPTION CURVES SUM TO GLOBAL #
        #################################

        # region

        region = ["NAM ", "ASIAPAC ", "CSAM ", "EUR ", "AFRICA ", "ME "]

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
            elec_consump.loc[region, decarb, scenario, :]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump.columns = transport_consump.columns.astype(int)
        energy_demand.columns = energy_demand.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump.loc[
                        region, ["Fossil fuels", "Other fuels"], scenario, :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump.loc[
                        region,
                        ["Bioenergy", "Fossil fuels", "Other fuels"],
                        scenario,
                        :,
                    ]
                ).sum()
            )
        )

        transport_decarb = pd.DataFrame(transport_decarb.sum()).T - 5

        transport_decarb.index.name = ""
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
                    "Tide and wave",
                    "Wind",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )

        renewable_heat = (
            heat_consump.loc[
                region,
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(
                heat_consump.loc[
                    region,
                    [
                        "Bioenergy",
                        "Geothermal",
                        "Nuclear",
                        "Solar thermal",
                        "Waste",
                        "Other Sources",
                        "Fossil fuels",
                    ],
                    scenario,
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum())
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Industry", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Industry", ["Heat"], scenario].sum())
        )

        industry_decarb = pd.DataFrame(industry_decarb)

        industry_decarb = pd.DataFrame(industry_decarb).T
        industry_decarb.rename(index={0: "Industry"}, inplace=True)

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]

        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", "pathway", :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})

        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
    
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)

        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )
        """

        """
        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """

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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        region = "World "
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    elif region == " OECD ":
        ##################################
        # ADOPTION CURVES SUM TO OECD #
        ##################################

        # region

        region = ["NAM ", "EUR ", "JPN "]

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
            elec_consump.loc[region, decarb, scenario, :]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump.columns = transport_consump.columns.astype(int)
        energy_demand.columns = energy_demand.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump.loc[
                        region, ["Fossil fuels", "Other fuels"], scenario, :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump.loc[
                        region,
                        ["Bioenergy", "Fossil fuels", "Other fuels"],
                        scenario,
                        :,
                    ]
                ).sum()
            )
        )

        transport_decarb = pd.DataFrame(transport_decarb.sum()).T - 2

        transport_decarb.index.name = ""
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
                    "Tide and wave",
                    "Wind",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )

        renewable_heat = (
            heat_consump.loc[
                region,
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(
                heat_consump.loc[
                    region,
                    [
                        "Bioenergy",
                        "Geothermal",
                        "Nuclear",
                        "Solar thermal",
                        "Waste",
                        "Other Sources",
                        "Fossil fuels",
                    ],
                    scenario,
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum())
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Industry", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Industry", ["Heat"], scenario].sum())
        )

        industry_decarb = pd.DataFrame(industry_decarb)

        industry_decarb = pd.DataFrame(industry_decarb).T
        industry_decarb.rename(index={0: "Industry"}, inplace=True)

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """
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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        region = " OECD "
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    elif region == "NonOECD ":
        ##################################
        # ADOPTION CURVES SUM TO NonOECD #
        ##################################

        # region

        region = ["CSAM ", "AFRICA ", "ME ", "RUS ", "INDIA "]

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
            elec_consump.loc[region, decarb, scenario, :]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump.columns = transport_consump.columns.astype(int)
        energy_demand.columns = energy_demand.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump.loc[
                        region, ["Fossil fuels", "Other fuels"], scenario, :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump.loc[
                        region,
                        ["Bioenergy", "Fossil fuels", "Other fuels"],
                        scenario,
                        :,
                    ]
                ).sum()
            )
        )

        transport_decarb = pd.DataFrame(transport_decarb.sum()).T - 4

        transport_decarb.index.name = ""
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
                    "Tide and wave",
                    "Wind",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )

        renewable_heat = (
            heat_consump.loc[
                region,
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(
                heat_consump.loc[
                    region,
                    [
                        "Bioenergy",
                        "Geothermal",
                        "Nuclear",
                        "Solar thermal",
                        "Waste",
                        "Other Sources",
                        "Fossil fuels",
                    ],
                    scenario,
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum())
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Industry", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Industry", ["Heat"], scenario].sum())
        )

        industry_decarb = pd.DataFrame(industry_decarb)

        industry_decarb = pd.DataFrame(industry_decarb).T
        industry_decarb.rename(index={0: "Industry"}, inplace=True)

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """

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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        region = "NonOECD "
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    else:
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
            elec_consump.loc[region, decarb, scenario, :]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump.columns = transport_consump.columns.astype(int)
        energy_demand.columns = energy_demand.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump.loc[
                        region, ["Fossil fuels", "Other fuels"], scenario, :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump.loc[
                        region,
                        ["Bioenergy", "Fossil fuels", "Other fuels"],
                        scenario,
                        :,
                    ]
                ).sum()
            )
        )

        transport_decarb.index.name = ""
        transport_decarb.rename(index={region: "Transport"}, inplace=True)

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
                    "Tide and wave",
                    "Wind",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(elec_consump.loc[region, slice(None), scenario, :].sum())
        )

        renewable_heat = (
            heat_consump.loc[
                region,
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                scenario,
                :,
            ]
            .sum()
            .div(
                heat_consump.loc[
                    region,
                    [
                        "Bioenergy",
                        "Geothermal",
                        "Nuclear",
                        "Solar thermal",
                        "Waste",
                        "Other Sources",
                        "Fossil fuels",
                    ],
                    scenario,
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Buildings", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Buildings", ["Heat"], scenario].sum())
        )

        building_decarb = pd.DataFrame(building_decarb).T
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
                * renewable_elec
            ).add(
                energy_demand.loc[region, "Industry", ["Heat"], scenario].sum()
                * renewable_heat
            )
        ).div(
            (
                energy_demand.loc[region, "Industry", ["Electricity"], scenario].sum()
            ).add(energy_demand.loc[region, "Industry", ["Heat"], scenario].sum())
        )

        industry_decarb = pd.DataFrame(industry_decarb).T
        industry_decarb.rename(index={0: "Industry"}, inplace=True)

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """

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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    ######################
    # SUBADOPTION CURVES #
    ######################

    if region == "World ":
        #################################
        # ADOPTION CURVES SUM TO GLOBAL #
        #################################

        # region

        region = ["NAM ", "ASIAPAC ", "CSAM ", "EUR ", "AFRICA ", "ME "]

        # GRID DECARB

        # region

        sgrid_decarb = (
            elec_consump.loc[region, decarb, scenario, :]
            .groupby("Metric")
            .sum()
            .divide(
                elec_consump.loc[region, decarb, scenario, :]
                .groupby("Metric")
                .sum()
                .sum()
            )
        ).multiply(grid_decarb.values)

        """
        sgrid_decarb = sgrid_decarb.append(pd.DataFrame(sgrid_decarb.loc[['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave']].sum()).T.rename(index={0:'Other ren'})).drop(index=['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave'])
        """

        sgrid_decarb = pd.concat([sgrid_decarb], keys=["Electricity"], names=["Sector"])
        sgrid_decarb = pd.concat([sgrid_decarb], keys=["World "], names=["Region"])

        # endregion

        # TRANSPORTATION DECARB

        # region

        stransport_decarb = (
            (transport_decarb * 0.73)
            .rename(index={"Transport": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Transport": "Efficiency"})
        )

        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["Transport"], names=["Sector"]
        )
        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["World "], names=["Region"]
        )

        # endregion

        # BUILDINGS DECARB

        # region

        sbuildings_decarb = (
            (building_decarb * 0.73)
            .rename(index={"Buildings": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Buildings": "Efficiency"})
        )

        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["Buildings"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["World "], names=["Region"]
        )

        # endregion

        # INDUSTRY DECARB

        # region

        sindustry_decarb = (
            (industry_decarb * 0.73)
            .rename(index={'"Industry"': "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={'"Industry"': "Efficiency"})
        )

        sindustry_decarb = pd.concat(
            [sindustry_decarb], keys=["Industry"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sindustry_decarb], keys=["World "], names=["Region"]
        )

        # endregion

        # OTHER GASES DECARB

        # region

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        sra_decarb = ra_decarb

        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        sfw_decarb = fw_decarb

        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]

        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", "pathway", :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})

        # endregion

        sadoption_curves = pd.concat(
            [
                sgrid_decarb,
                stransport_decarb,
                sbuildings_decarb,
                sindustry_decarb,
                sra_decarb,
                sfw_decarb,
            ],
        ).loc[:, data_start_year:long_proj_end_year]

        sadoption_curves = sgrid_decarb.loc[
            :, data_start_year:long_proj_end_year
        ].append(stransport_decarb.loc[:, data_start_year:long_proj_end_year])
        sadoption_curves = adoption_curves.append(
            building_decarb.loc[:, data_start_year:long_proj_end_year]
        )
        sadoption_curves = adoption_curves.append(
            industry_decarb.loc[:, data_start_year:long_proj_end_year]
        )
        sadoption_curves = adoption_curves.append(
            ra_decarb.loc[:, data_start_year:long_proj_end_year]
        )
        sadoption_curves = adoption_curves.append(
            fw_decarb.loc[:, data_start_year:long_proj_end_year]
        )
        sadoption_curves = adoption_curves.append(
            cdr_decarb.loc[:, data_start_year:long_proj_end_year]
        )
        sadoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        sadoption_curves.index.name = "Sector"
        region = "World "
        sadoption_curves["Region"] = region
        sadoption_curves["Scenario"] = scenario
        sadoption_curves.reset_index(inplace=True)
        sadoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    elif region == " OECD ":
        ##################################
        # ADOPTION CURVES SUM TO OECD #
        ##################################

        # region

        region = ["NAM ", "EUR ", "JPN "]

        # GRID DECARB

        # region

        sgrid_decarb = (
            elec_consump.loc[region, decarb, scenario, :]
            .groupby("Metric")
            .sum()
            .divide(
                elec_consump.loc[region, decarb, scenario, :]
                .groupby("Metric")
                .sum()
                .sum()
            )
        ).multiply(grid_decarb.values)

        """
        sgrid_decarb = sgrid_decarb.append(pd.DataFrame(sgrid_decarb.loc[['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave']].sum()).T.rename(index={0:'Other ren'})).drop(index=['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave'])
        """

        sgrid_decarb = pd.concat([sgrid_decarb], keys=["Electricity"], names=["Sector"])
        sgrid_decarb = pd.concat([sgrid_decarb], keys=[" OECD "], names=["Region"])

        # endregion

        # TRANSPORTATION DECARB

        # region

        stransport_decarb = (
            (transport_decarb * 0.73)
            .rename(index={"Transport": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Transport": "Efficiency"})
        )

        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["Transport"], names=["Sector"]
        )
        stransport_decarb = pd.concat(
            [stransport_decarb], keys=[" OECD "], names=["Region"]
        )

        # endregion

        # BUILDINGS DECARB

        # region

        sbuildings_decarb = (
            (building_decarb * 0.73)
            .rename(index={"Buildings": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Buildings": "Efficiency"})
        )

        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["Buildings"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=[" OECD "], names=["Region"]
        )

        # endregion

        # INDUSTRY DECARB

        # region

        sindustry_decarb = (
            (industry_decarb * 0.73)
            .rename(index={"Industry": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={'"Industry"': "Efficiency"})
        )

        sindustry_decarb = pd.concat(
            [sindustry_decarb], keys=["Industry"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sindustry_decarb], keys=[" OECD "], names=["Region"]
        )

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """
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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        region = " OECD "
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    elif region == "NonOECD ":
        ##################################
        # ADOPTION CURVES SUM TO NonOECD #
        ##################################

        # region

        region = ["CSAM ", "AFRICA ", "ME ", "RUS ", "INDIA "]

        # GRID DECARB

        # region

        sgrid_decarb = (
            elec_consump.loc[region, decarb, scenario, :]
            .groupby("Metric")
            .sum()
            .divide(
                elec_consump.loc[region, decarb, scenario, :]
                .groupby("Metric")
                .sum()
                .sum()
            )
        ).multiply(grid_decarb.values)

        """
        sgrid_decarb = sgrid_decarb.append(pd.DataFrame(sgrid_decarb.loc[['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave']].sum()).T.rename(index={0:'Other ren'})).drop(index=['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave'])
        """

        sgrid_decarb = pd.concat([sgrid_decarb], keys=["Electricity"], names=["Sector"])
        sgrid_decarb = pd.concat([sgrid_decarb], keys=["NonOECD "], names=["Region"])

        # endregion

        # TRANSPORTATION DECARB

        # region

        stransport_decarb = (
            (transport_decarb * 0.73)
            .rename(index={"Transport": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Transport": "Efficiency"})
        )

        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["Transport"], names=["Sector"]
        )
        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["NonOECD "], names=["Region"]
        )

        # endregion

        # BUILDINGS DECARB

        # region

        sbuildings_decarb = (
            (building_decarb * 0.73)
            .rename(index={"Buildings": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Buildings": "Efficiency"})
        )

        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["Buildings"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["NonOECD "], names=["Region"]
        )

        # endregion

        # INDUSTRY DECARB

        # region

        sindustry_decarb = (
            (industry_decarb * 0.73)
            .rename(index={"Industry": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Industry": "Efficiency"})
        )

        sindustry_decarb = pd.concat(
            [sindustry_decarb], keys=["Industry"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sindustry_decarb], keys=["NonOECD "], names=["Region"]
        )

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """

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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        region = "NonOECD "
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    else:
        ######################
        # SUBADOPTION CURVES #
        ######################

        # region

        # GRID DECARB

        # region

        sgrid_decarb = (
            elec_consump.loc[region, decarb, scenario, :]
            .groupby("Metric")
            .sum()
            .divide(
                elec_consump.loc[region, decarb, scenario, :]
                .groupby("Metric")
                .sum()
                .sum()
            )
        ).multiply(grid_decarb.values)

        """
        sgrid_decarb = sgrid_decarb.append(pd.DataFrame(sgrid_decarb.loc[['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave']].sum()).T.rename(index={0:'Other ren'})).drop(index=['Biomass and waste', 'Geothermal', 'Hydroelectricity', 'Nuclear', 'Tide and wave'])
        """

        sgrid_decarb = pd.concat([sgrid_decarb], keys=["Electricity"], names=["Sector"])
        sgrid_decarb = pd.concat([sgrid_decarb], keys=[region], names=["Region"])

        # endregion

        # TRANSPORTATION DECARB

        # region

        stransport_decarb = (
            (transport_decarb * 0.73)
            .rename(index={"Transport": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Transport": "Efficiency"})
        )

        stransport_decarb = pd.concat(
            [stransport_decarb], keys=["Transport"], names=["Sector"]
        )
        stransport_decarb = pd.concat(
            [stransport_decarb], keys=[region], names=["Region"]
        )

        # endregion

        # BUILDINGS DECARB

        # region

        sbuildings_decarb = (
            (building_decarb * 0.73)
            .rename(index={"Buildings": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Buildings": "Efficiency"})
        )

        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=["Buildings"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sbuildings_decarb], keys=[region], names=["Region"]
        )

        # endregion

        # INDUSTRY DECARB

        # region

        sindustry_decarb = (
            (industry_decarb * 0.73)
            .rename(index={"Buildings": "Fuel Switching"})
            .append(transport_decarb * 0.27)
            .rename(index={"Buildings": "Efficiency"})
        )

        sindustry_decarb = pd.concat(
            [sindustry_decarb], keys=["Buildings"], names=["Sector"]
        )
        sbuildings_decarb = pd.concat(
            [sindustry_decarb], keys=[region], names=["Region"]
        )

        # endregion

        # OTHER GASES DECARB

        # region

        other_decarb = (
            industry_decarb.append(building_decarb).append(grid_decarb)
        ).mean()

        other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

        # endregion

        # REGENERATIVE AGRICULTURE DECARB

        # region
        ra_decarb_max = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            "pathway",
            :,
        ]

        ra_decarb = afolu_per_adoption.loc[
            region,
            "Regenerative Agriculture",
            [
                "Biochar",
                "Cropland Soil Health",
                "Improved Rice",
                "Nitrogen Fertilizer Management",
                "Trees in Croplands",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Regenerative Agriculture",
            ],
            scenario,
            :,
        ]
        ra_decarb = pd.DataFrame(ra_decarb.sum() / ra_decarb_max.sum().max()).T.rename(
            index={0: "Regenerative Agriculture"}
        )
        ra_decarb.columns = ra_decarb.columns.astype(int)

        # endregion

        # FORESTS & WETLANDS DECARB

        # region
        fw_decarb_max = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            "pathway",
            :,
        ]

        fw_decarb = afolu_per_adoption.loc[
            region,
            "Forests & Wetlands",
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
                "Forests & Wetlands",
            ],
            scenario,
            :,
        ]
        fw_decarb = pd.DataFrame(fw_decarb.sum() / fw_decarb_max.sum().max()).T.rename(
            index={0: "Forests & Wetlands"}
        )
        fw_decarb.columns = fw_decarb.columns.astype(int)
        fw_decarb.columns = ra_decarb.columns

        # endregion

        # CDR DECARB

        # region

        cdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", scenario, :].apply(
                lambda x: x
                / (
                    cdr.loc["World ", "Carbon Dioxide Removal", scenario, :]
                    .max(axis=1)
                    .values
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        """
        cdr_decarb.loc[:, cdr_decarb.idxmax(1).values[0] :] = cdr_decarb[
            cdr_decarb.idxmax(1).values[0]
        ]
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        cdr_decarb = pd.Series(
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", scenario, "All").T
        cdr_decarb.rename(index={0: "Carbon Dioxide Removal"}, inplace=True)
        """

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
        adoption_curves = adoption_curves.append(
            other_decarb.loc[:, data_start_year:long_proj_end_year]
        )

        adoption_curves.index.name = "Sector"
        adoption_curves["Region"] = region
        adoption_curves["Scenario"] = scenario
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector", "Scenario"], inplace=True)

        # endregion

    return adoption_curves
