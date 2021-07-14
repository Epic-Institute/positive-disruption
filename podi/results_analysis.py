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

    rgroup = {
        "World ": ["NAM ", "ASIAPAC ", "CSAM ", "EUR ", "AFRICA ", "ME "],
        " OECD ": ["NAM ", "EUR ", "JPN "],
        "NonOECD ": ["CSAM ", "AFRICA ", "ME ", "RUS ", "INDIA "],
        "NAM ": "NAM ",
        "US ": "US ",
        "CSAM ": "CSAM ",
        "BRAZIL ": "BRAZIL ",
        "EUR ": "EUR ",
        "AFRICA ": "AFRICA ",
        "SAFR ": "SAFR ",
        "ME ": "ME ",
        "RUS ": "RUS ",
        "ASIAPAC ": "ASIAPAC ",
        "CHINA ": "CHINA ",
        "INDIA ": "INDIA ",
        "JPN ": "JPN ",
    }

    region2 = rgroup[region]

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
        elec_consump.loc[region2, decarb, scenario, :]
        .sum()
        .div(elec_consump.loc[region2, slice(None), scenario, :].sum())
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
                    region2, ["Fossil fuels", "Other fuels"], scenario, :
                ]
            )
            .groupby("Region")
            .sum()
            .sum()
        ).div(
            (
                transport_consump.loc[
                    region2,
                    ["Bioenergy", "Fossil fuels", "Other fuels"],
                    scenario,
                    :,
                ]
            ).sum()
        )
    )

    # transport_decarb.index.name = ""
    transport_decarb = pd.DataFrame(transport_decarb).T
    transport_decarb.columns = transport_decarb.columns.astype(int)
    transport_decarb.rename(index={0: "Transport"}, inplace=True)

    # endregion

    # BUILDINGS DECARB

    # region

    renewable_elec = (
        elec_consump.loc[
            region2,
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
        .div(elec_consump.loc[region2, slice(None), scenario, :].sum())
    )

    renewable_heat = (
        heat_consump.loc[
            region2,
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
                region2,
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
            energy_demand.loc[region2, "Buildings", ["Electricity"], scenario].sum()
            * renewable_elec
        ).add(
            energy_demand.loc[region2, "Buildings", ["Heat"], scenario].sum()
            * renewable_heat
        )
    ).div(
        (energy_demand.loc[region2, "Buildings", ["Electricity"], scenario].sum()).add(
            energy_demand.loc[region2, "Buildings", ["Heat"], scenario].sum()
        )
    )

    building_decarb = pd.DataFrame(building_decarb).T
    building_decarb.rename(index={0: "Buildings"}, inplace=True)

    # endregion

    # INDUSTRY DECARB

    # region

    industry_decarb = (
        (
            energy_demand.loc[region2, "Industry", ["Electricity"], scenario].sum()
            * renewable_elec
        ).add(
            energy_demand.loc[region2, "Industry", ["Heat"], scenario].sum()
            * renewable_heat
        )
    ).div(
        (energy_demand.loc[region2, "Industry", ["Electricity"], scenario].sum()).add(
            energy_demand.loc[region2, "Industry", ["Heat"], scenario].sum()
        )
    )

    industry_decarb = pd.DataFrame(industry_decarb).T
    industry_decarb.rename(index={0: "Industry"}, inplace=True)

    # endregion

    # OTHER GASES DECARB

    # region

    other_decarb = (industry_decarb.append(building_decarb).append(grid_decarb)).mean()

    other_decarb = pd.DataFrame(other_decarb).T.rename(index={0: "Other Gases"})

    # endregion

    # REGENERATIVE AGRICULTURE DECARB

    # region
    ra_decarb_max = afolu_per_adoption.loc[
        region2,
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
        region2,
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
        region2,
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
        region2,
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

    # MARICULTURE DECARB

    # region
    """
    mar_decarb_max = afolu_per_adoption.loc[
        region2,
        "Forests & Wetlands",
        [
            "Coastal Restoration",
        ],
        "pathway",
        :,
    ]

    mar_decarb = afolu_per_adoption.loc[
        region2,
        "Forests & Wetlands",
        [
            "Coastal Restoration",
        ],
        scenario,
        :,
    ]
    mar_decarb = pd.DataFrame(mar_decarb.sum() / mar_decarb_max.sum().max()).T.rename(
        index={0: "Mariculture"}
    )
    mar_decarb.columns = mar_decarb.columns.astype(int)
    mar_decarb.columns = ra_decarb.columns
    """
    # endregion

    # CDR DECARB

    # region

    if region in ["World ", "US ", "CHINA ", "EUR "]:
        cdr_decarb = pd.DataFrame(
            pd.DataFrame(
                cdr.loc[
                    "World ", "Carbon Dioxide Removal", slice(None), scenario, :
                ].sum()
            ).T.apply(
                lambda x: x
                / (
                    cdr.loc[
                        "World ", "Carbon Dioxide Removal", slice(None), scenario, :
                    ]
                    .sum()
                    .max()
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        cdr_decarb.index.name = ""
        cdr_decarb.columns = cdr_decarb.columns.astype(int)
    else:
        cdr_decarb = pd.DataFrame(
            pd.DataFrame(
                cdr.loc[
                    "World ", "Carbon Dioxide Removal", slice(None), scenario, :
                ].sum()
            ).T.apply(
                lambda x: x
                / (
                    cdr.loc[
                        "World ", "Carbon Dioxide Removal", slice(None), scenario, :
                    ]
                    .sum()
                    .max()
                ),
                axis=1,
            )
        ).rename(index={0: "Carbon Dioxide Removal"})
        cdr_decarb.index.name = ""
        cdr_decarb.columns = cdr_decarb.columns.astype(int)

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

    # region

    # GRID DECARB

    # region

    sgrid_decarb = (
        elec_consump.loc[region2, decarb, scenario, :]
        .groupby("Metric")
        .sum()
        .divide(
            elec_consump.loc[region2, decarb, scenario, :].groupby("Metric").sum().sum()
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
    """
    stransport_decarb = (
        (transport_decarb * 0.73)
        .rename(index={"Transport": "Electrification"})
        .append(transport_decarb * 0.27)
        .rename(index={"Transport": "Efficiency"})
    )
    """

    stransport_decarb = (
        (
            (transport_decarb * 0.365).rename(
                index={"Transport": "Electrification (LDV)"}
            )
        )
        .append(
            (transport_decarb * 0.064).rename(
                index={"Transport": "Electrification (HDV)"}
            )
        )
        .append(
            (transport_decarb * 0.008).rename(
                index={"Transport": "Electrification (Shipping)"}
            )
        )
        .append(
            (transport_decarb * 0.016).rename(
                index={"Transport": "Electrification (Aviation)"}
            )
        )
        .append(
            (transport_decarb * 0.069).rename(
                index={"Transport": "Electrification (Rail)"}
            )
        )
        .append((transport_decarb * 0.02).rename(index={"Transport": "H2 (LDV)"}))
        .append((transport_decarb * 0.016).rename(index={"Transport": "H2 (HDV)"}))
        .append(
            (transport_decarb * 0.064).rename(
                index={"Transport": "H2/Ammonia (Shipping)"}
            )
        )
        .append(
            (transport_decarb * 0.097).rename(
                index={"Transport": "H2/Synfuels (Aviation)"}
            )
        )
        .append((transport_decarb * 0.008).rename(index={"Transport": "H2 (Rail)"}))
        .append((transport_decarb * 0.27).rename(index={"Transport": "Efficiency"}))
    )

    stransport_decarb.index.name = "Metric"

    stransport_decarb = pd.concat(
        [stransport_decarb], keys=["Transport"], names=["Sector"]
    )
    stransport_decarb = pd.concat([stransport_decarb], keys=[region], names=["Region"])

    # endregion

    # BUILDINGS DECARB

    # region
    """
    sbuilding_decarb = (
        (building_decarb * 0.35)
        .rename(index={"Buildings": "Electrification"})
        .append(building_decarb * 0.65)
        .rename(index={"Buildings": "Efficiency"})
    )
    """

    sbuilding_decarb = (
        (
            (building_decarb * 0.277).rename(
                index={"Buildings": "Electrification (Heating)"}
            )
        )
        .append((building_decarb * 0.035).rename(index={"Buildings": "H2 (Heating)"}))
        .append(
            (building_decarb * 0.038).rename(
                index={"Buildings": "Electrification (Other)"}
            )
        )
        .append((building_decarb * 0.65).rename(index={"Buildings": "Efficiency"}))
    )

    sbuilding_decarb.index.name = "Metric"

    sbuilding_decarb = pd.concat(
        [sbuilding_decarb], keys=["Buildings"], names=["Sector"]
    )
    sbuilding_decarb = pd.concat([sbuilding_decarb], keys=[region], names=["Region"])

    # endregion

    # INDUSTRY DECARB

    # region
    """
    sindustry_decarb = (
        (industry_decarb * 0.34)
        .rename(index={"Industry": "Electrification"})
        .append(industry_decarb * 0.31)
        .rename(index={"Industry": "Hydrogen"})
        .append(industry_decarb * 0.35)
        .rename(index={"Industry": "Efficiency"})
    )
    """

    sindustry_decarb = (
        (
            (industry_decarb * 0.036).rename(
                index={"Industry": "Electrification (Cement)"}
            )
        )
        .append((industry_decarb * 0.053).rename(index={"Industry": "H2 (Cement)"}))
        .append(
            (industry_decarb * 0.157).rename(
                index={"Industry": "Electrification (Steel)"}
            )
        )
        .append((industry_decarb * 0.224).rename(index={"Industry": "H2 (Steel)"}))
        .append(
            (industry_decarb * 0.045).rename(
                index={"Industry": "Electrification (Chemicals)"}
            )
        )
        .append((industry_decarb * 0.045).rename(index={"Industry": "H2 (Chemicals)"}))
        .append(
            (industry_decarb * 0.085).rename(
                index={"Industry": "Electrification (Other)"}
            )
        )
        .append((industry_decarb * 0.0045).rename(index={"Industry": "H2 (Other)"}))
        .append((industry_decarb * 0.35).rename(index={"Industry": "Efficiency"}))
    )

    sindustry_decarb.index.name = "Metric"

    sindustry_decarb = pd.concat(
        [sindustry_decarb], keys=["Industry"], names=["Sector"]
    )
    sindustry_decarb = pd.concat([sindustry_decarb], keys=[region], names=["Region"])

    # endregion

    # OTHER GASES DECARB

    # region

    sother_decarb = (
        (other_decarb * 0.7).rename(index={"Other Gases": "Other Unspecified"})
    ).append((other_decarb * 0.3).rename(index={"Other Gases": "Indirect Non-ag N20"}))

    sother_decarb.index.name = "Metric"
    sother_decarb = pd.concat([sother_decarb], keys=["Other Gases"], names=["Sector"])
    sother_decarb = pd.concat([sother_decarb], keys=[region], names=["Region"])

    # endregion

    # REGENERATIVE AGRICULTURE DECARB

    # region

    sra_decarb = (
        (
            afolu_per_adoption.loc[
                region2,
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
            .groupby("Metric")
            .mean()
        )
        / (
            afolu_per_adoption.loc[
                region2,
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
            .groupby("Metric")
            .mean()
        ).sum()
    ).apply(lambda x: x * ra_decarb.squeeze(), axis=1)

    """
    sra_decarb_max = sra_decarb.sum()
    sra_decarb = sra_decarb.apply(lambda x: x.divide(sra_decarb_max), axis=1)
    """

    sra_decarb.columns = sra_decarb.columns.astype(int)
    sra_decarb.index.name = "Metric"
    sra_decarb = pd.concat(
        [sra_decarb], keys=["Regenerative Agriculture"], names=["Sector"]
    )
    sra_decarb = pd.concat([sra_decarb], keys=[region], names=["Region"])

    # endregion

    # FORESTS & WETLANDS DECARB

    # region

    sfw_decarb = (
        (
            afolu_per_adoption.loc[
                region2,
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
            .groupby("Metric")
            .mean()
        )
        / (
            afolu_per_adoption.loc[
                region2,
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
            .groupby("Metric")
            .mean()
            .sum()
        )
    ).apply(lambda x: x * fw_decarb.squeeze(), axis=1)

    """
    sfw_decarb_max = sfw_decarb.sum()
    sfw_decarb = sfw_decarb.apply(lambda x: x.divide(sfw_decarb_max), axis=1)
    """

    sfw_decarb.columns = sfw_decarb.columns.astype(int)
    sfw_decarb.index.name = "Metric"
    sfw_decarb = pd.concat([sfw_decarb], keys=["Forests & Wetlands"], names=["Sector"])
    sfw_decarb = pd.concat([sfw_decarb], keys=[region], names=["Region"])

    # endregion

    # CDR DECARB

    # region

    if region in ["World "]:
        scdr_decarb = pd.DataFrame(
            cdr.loc[region, "Carbon Dioxide Removal", slice(None), scenario, :].apply(
                lambda x: x / (x.max()),
                axis=1,
            )
        )
        scdr_decarb["Region"] = region
        scdr_decarb["Sector"] = "Carbon Dioxide Removal"
        scdr_decarb = scdr_decarb.reset_index().set_index(
            ["Region", "Sector", "Metric"]
        )

    else:
        scdr_decarb = pd.DataFrame(
            cdr.loc["World ", "Carbon Dioxide Removal", slice(None), scenario, :].apply(
                lambda x: x / (x.max()),
                axis=1,
            )
        )
        scdr_decarb["Region"] = region
        scdr_decarb["Sector"] = "Carbon Dioxide Removal"
        scdr_decarb = scdr_decarb.reset_index().set_index(
            ["Region", "Sector", "Metric"]
        )

    # endregion

    sadoption_curves = pd.concat(
        [
            sgrid_decarb,
            stransport_decarb,
            sbuilding_decarb,
            sindustry_decarb,
            sra_decarb,
            sfw_decarb,
            sother_decarb,
            scdr_decarb,
        ],
    ).loc[:, data_start_year:long_proj_end_year]

    """
    sadoption_curves = sgrid_decarb.loc[:, data_start_year:long_proj_end_year].append(
        stransport_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        sbuilding_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        sindustry_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        sra_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        sfw_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        scdr_decarb.loc[:, data_start_year:long_proj_end_year]
    )
    sadoption_curves = sadoption_curves.append(
        sother_decarb.loc[:, data_start_year:long_proj_end_year]
    )

    sadoption_curves.index.name = "Sector"
    sadoption_curves["Region"] = region
    """
    sadoption_curves["Scenario"] = scenario
    sadoption_curves.reset_index(inplace=True)
    sadoption_curves.set_index(["Region", "Sector", "Metric", "Scenario"], inplace=True)

    # endregion

    return adoption_curves, sadoption_curves
