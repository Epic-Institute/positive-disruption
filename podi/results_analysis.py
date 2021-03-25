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

    if region == "World ":
        #################################
        # ADOPTION CURVES SUM TO GLOBAL #
        #################################

        # region

        # GRID DECARB

        # region

        region = ["NAM ", "ASIAPAC ", "CSAM ", "EUR ", "AFRICA ", "ME "]

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
            elec_consump_pathway.loc[region, decarb, :]
            .sum()
            .div(elec_consump_pathway.loc[region, slice(None), :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump_pathway.columns = transport_consump_pathway.columns.astype(
            int
        )
        energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
        energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        region, ["Fossil fuels", "Other fuels"], :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump_pathway.loc[
                        region, ["Bioenergy", "Fossil fuels", "Other fuels"], :
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
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                :,
            ]
            .sum()
            .div(
                heat_consump_pathway.loc[
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
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
            )
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
            )
        )

        industry_decarb = pd.DataFrame(industry_decarb)

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

        cdr_decarb = pd.DataFrame(cdr_pathway / cdr_pathway.max()).T.rename(
            index={0: "Carbon Dioxide Removal"}
        )
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
        cdr_decarb = adoption_curve(cdr_decarb, "World ", "pathway", "All").T
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

        adoption_curves["Region"] = "World "
        adoption_curves.index.set_names("Sector", inplace=True)
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector"], inplace=True)

        # endregion

    elif region == " OECD ":

        ##################################
        # ADOPTION CURVES SUM TO OECD #
        ##################################

        # region

        # GRID DECARB

        # region

        region = ["NAM ", "EUR ", "JPN "]

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
            elec_consump_pathway.loc[region, decarb, :]
            .sum()
            .div(elec_consump_pathway.loc[region, slice(None), :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump_pathway.columns = transport_consump_pathway.columns.astype(
            int
        )
        energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
        energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        region, ["Fossil fuels", "Other fuels"], :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump_pathway.loc[
                        region, ["Bioenergy", "Fossil fuels", "Other fuels"], :
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
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                :,
            ]
            .sum()
            .div(
                heat_consump_pathway.loc[
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
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
            )
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
            )
        )

        industry_decarb = pd.DataFrame(industry_decarb)

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
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", "pathway", "All").T
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

        adoption_curves["Region"] = " OECD "
        adoption_curves.index.set_names("Sector", inplace=True)
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector"], inplace=True)

        # endregion

    elif region == "NonOECD ":

        ##################################
        # ADOPTION CURVES SUM TO NonOECD #
        ##################################

        # region

        # GRID DECARB

        # region

        region = ["CSAM ", "AFRICA ", "ME ", "RUS ", "INDIA "]

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
            elec_consump_pathway.loc[region, decarb, :]
            .sum()
            .div(elec_consump_pathway.loc[region, slice(None), :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump_pathway.columns = transport_consump_pathway.columns.astype(
            int
        )
        energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
        energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        region, ["Fossil fuels", "Other fuels"], :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump_pathway.loc[
                        region, ["Bioenergy", "Fossil fuels", "Other fuels"], :
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
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                :,
            ]
            .sum()
            .div(
                heat_consump_pathway.loc[
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
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
            )
        )

        building_decarb = pd.DataFrame(building_decarb).T

        building_decarb = pd.DataFrame(building_decarb)
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
            )
        )

        industry_decarb = pd.DataFrame(industry_decarb)

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
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", "pathway", "All").T
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

        adoption_curves["Region"] = "NonOECD "
        adoption_curves.index.set_names("Sector", inplace=True)
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector"], inplace=True)

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
            elec_consump_pathway.loc[region, decarb, :]
            .sum()
            .div(elec_consump_pathway.loc[region, slice(None), :].sum())
        )
        grid_decarb = pd.DataFrame(grid_decarb).T
        grid_decarb.columns = grid_decarb.columns.astype(int)
        grid_decarb.rename(index={0: "Electricity"}, inplace=True)

        # endregion

        # TRANSPORTATION DECARB

        # region

        transport_consump_pathway.columns = transport_consump_pathway.columns.astype(
            int
        )
        energy_demand_pathway.columns = energy_demand_pathway.columns.astype(int)
        energy_demand_baseline.columns = energy_demand_baseline.columns.astype(int)

        transport_decarb = 1 - (
            (
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        region, ["Fossil fuels", "Other fuels"], :
                    ]
                )
                .groupby("Region")
                .sum()
            ).div(
                (
                    transport_consump_pathway.loc[
                        region, ["Bioenergy", "Fossil fuels", "Other fuels"], :
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
                [
                    "Bioenergy",
                    "Geothermal",
                    "Solar thermal",
                    "Waste",
                    "Other Sources",
                ],
                :,
            ]
            .sum()
            .div(
                heat_consump_pathway.loc[
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
                    :,
                ].sum()
            )
        )

        building_decarb = (
            (
                energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Buildings", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Buildings", ["Heat"]].sum()
            )
        )

        building_decarb = pd.DataFrame(building_decarb).T
        building_decarb.rename(index={0: "Buildings"}, inplace=True)

        # endregion

        # INDUSTRY DECARB

        # region

        industry_decarb = (
            (
                energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()
                * renewable_elec
            ).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
                * renewable_heat
            )
        ).div(
            (energy_demand_pathway.loc[region, "Industry", ["Electricity"]].sum()).add(
                energy_demand_pathway.loc[region, "Industry", ["Heat"]].sum()
            )
        )

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
            cdr_decarb.values[0],
            index=cdr_decarb.columns,
            name="Carbon Dioxide Removal",
        )

        cdr_decarb = adoption_curve(cdr_decarb, "World ", "pathway", "All").T
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

        adoption_curves["Region"] = region
        adoption_curves.index.set_names("Sector", inplace=True)
        adoption_curves.reset_index(inplace=True)
        adoption_curves.set_index(["Region", "Sector"], inplace=True)

        # endregion

    return adoption_curves
