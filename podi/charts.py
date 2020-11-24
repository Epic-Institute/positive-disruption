#!/usr/bin/env python

# region

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
from scipy.interpolate import interp1d
import pyhector
from pyhector import rcp19, rcp26, rcp45, rcp60, rcp85
from podi.data.iea_weo_etl import iea_region_list
from podi.energy_supply import (
    data_end_year,
    data_start_year,
    long_proj_end_year,
    long_proj_start_year,
)
from pymagicc import scenarios
from pandas_datapackage_reader import read_datapackage
from shortcountrynames import to_name

# endregion


def charts(energy_demand_baseline, energy_demand_pathway):

    #####################################
    # PROJECTED MARKET DIFFUSION CURVES #
    #####################################

    # region
    xnew = np.linspace(adoption_curves.columns.min(), adoption_curves.columns.max(), 19)

    color = pd.DataFrame(
        {
            "Grid": [(0.120, 0.107, 0.155)],
            "Transport": [(0.93, 0.129, 0.180)],
            "Buildings": [(0.225, 0.156, 0.98)],
            "Industry": [(0.44, 0.74, 0.114)],
            "Regenerative Agriculture": [(0.130, 0.143, 0.81)],
            "Forests & Wetlands": [(0.138, 0.188, 0.175)],
            "Carbon Dioxide Removal": [(0.200, 0.156, 0.152)],
        }
    ).T

    for i in range(0, 1):
        fig = adoption_curves.apply(
            lambda x: interp1d(adoption_curves.columns.values, x, kind="cubic"), axis=1
        )
        plt.figure(i)
        fig.apply(lambda x: plt.plot(xnew, x(xnew) * 100, linestyle="--"))
        fig.apply(
            lambda x: plt.plot(
                xnew[0 : (data_end_year - data_start_year) + 1],
                x(xnew)[0 : (data_end_year - data_start_year) + 1] * 100,
                linestyle="-",
                color=(0, 0, 0),
            )
        )
        plt.ylabel("% Adoption")
        plt.xlim([adoption_curves.columns.min(), adoption_curves.columns.max()])
        plt.title("Percent of Total PD Adoption, " + iea_region_list[i])
        plt.legend(
            adoption_curves.index,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    axis_label = [
        "% TFC met by renewables",
        "Buildings electricity demand as % \of Buildings TFC",
        "Transport electricity demand as % \of Transport TFC",
        "Industry electricity demand as % \of Industry TFC",
        "MHa",
        "MHa",
        "GtCO2 removed",
    ]

    xnew = np.linspace(adoption_curves.columns.min(), adoption_curves.columns.max(), 91)

    for i in range(0, 1):
        for j in range(0, len(adoption_curves.index)):
            fig = interp1d(
                adoption_curves.columns.values, adoption_curves.iloc[j], kind="cubic"
            )
            fig2, ax = plt.subplots()
            y = fig(xnew) * 100
            ax.plot(xnew, y, linestyle="--", color=(0.560, 0.792, 0.740))
            ax.plot(
                xnew[0 : (data_end_year - data_start_year) + 1],
                y[0 : (data_end_year - data_start_year) + 1],
                linestyle="-",
                color=(0, 0, 0),
            )
            ax.set_ylabel("% Adoption")
            # secax = ax.secondary_yaxis("right")
            # secax.set_ylabel(axis_label[j])
            plt.xlim([adoption_curves.columns.min(), adoption_curves.columns.max()])
            plt.ylim(0, 105)
            plt.grid(which="major", linestyle=":", axis="y")
            plt.title(
                "Percent of Total PD Adoption, "
                + adoption_curves.index[j]
                + ", "
                + iea_region_list[i]
            )

    # endregion

    ##############################
    # SUBVECTOR DIFFUSION CURVES #
    ##############################

    # region
    # show how subvector diffusion curves build up to vector diffusion
    # endregion

    ###########################
    # MITIGATION WEDGES CURVE #
    ###########################

    # region

    # region

    color = (
        (0.999, 0.999, 0.999),
        (0.928, 0.828, 0.824),
        (0.688, 0.472, 0.460),
        (0.572, 0.792, 0.744),
        (0.536, 0.576, 0.432),
        (0.384, 0.460, 0.560),
        (0.904, 0.620, 0.384),
        (0.488, 0.672, 0.736),
        (0.560, 0.516, 0.640),
        (0.284, 0.700, 0.936),
        (0.384, 0.664, 0.600),
        (0.999, 0.976, 0.332),
        (0.748, 0.232, 0.204),
    )

    # endregion

    # region

    em_mit_electricity = (
        em_mitigated.loc[slice(None), "Electricity", slice(None)].sum() * 0.95
    )

    em_mit_transport = (
        em_mitigated.loc[slice(None), "Transport", slice(None)].sum() * 1.05
    )

    em_mit_buildings = (
        em_mitigated.loc[slice(None), "Buildings", slice(None)].sum() * 0.7
    )

    em_mit_industry = em_mitigated.loc[slice(None), "Industry", slice(None)].sum() * 0.6

    em_mit_ra = (
        afolu_em_mitigated.loc[
            slice(None),
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
            slice(None),
            slice(None),
        ].sum()
        * 0.95
    )

    em_mit_fw = (
        afolu_em_mitigated.loc[
            slice(None),
            [
                "Avoided Coastal Impacts",
                "Avoided Forest Conversion",
                "Avoided Peat Impacts",
                "Coastal Restoration",
                "Improved Forest Mgmt",
                "Peat Restoration",
                "Natural Regeneration",
            ],
            slice(None),
            slice(None),
        ].sum()
        * 0.95
    )

    em_mit_othergas = em_mitigated.loc[slice(None), "Other gases", :].sum()
    """
    em_mit_cdr = (
        pd.Series(pd.read_csv(cdr_emissions).loc[data_start_year, long_proj_end_year])
        .groupby("Metric")
        .sum()
    )
    """

    em_mit_cdr = pd.Series(
        cdr_needed_def, index=np.arange(data_start_year, long_proj_end_year + 1)
    )

    em_mit = pd.DataFrame(
        [
            em_mit_electricity,
            em_mit_transport,
            em_mit_buildings,
            em_mit_industry,
            em_mit_ra,
            em_mit_fw,
            em_mit_othergas,
            em_mit_cdr,
        ]
    ).rename(
        index={
            0: "Electricity",
            1: "Transport",
            2: "Buildings",
            3: "Industry",
            4: "Forests & Wetlands",
            5: "Agriculture",
            6: "CH4, N2O, F-gases",
            7: "CDR",
        }
    )
    em_mit.loc[:, :2020] = 0
    spacer = em_targets_pathway.loc["Pathway PD20"]
    em_mit.loc["Electricity"] = em_targets_pathway.loc["Baseline PD20"].subtract(
        em_mit.drop(labels="Electricity").append(spacer).sum()
    )

    custom_legend = [
        Line2D([0], [0], color=color[8], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[12], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[10], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[11], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[9], linewidth=4, linestyle="--"),
    ]

    # endregion

    for i in range(0, 1):
        fig = ((em_mit.append(spacer)) / 1000).reindex(
            [
                spacer.name,
                "CDR",
                "CH4, N2O, F-gases",
                "Agriculture",
                "Forests & Wetlands",
                "Industry",
                "Buildings",
                "Transport",
                "Electricity",
            ]
        )
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=color,
        )
        plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
        plt.legend(
            loc=2,
            fontsize="small",
        )
        plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
        plt.ylabel("GtCO2e/yr")
        plt.xlim([2020, 2100])
        plt.grid(which="major", linestyle=":", axis="y")
        plt.legend(
            custom_legend,
            [
                "Electricity",
                "Transport",
                "Buildings",
                "Industry",
                "Agriculture",
                "Forests & Wetlands",
                "CH4, N2O, F-gases",
                "CDR",
                "Baseline",
                "DAU",
                "SSP2-RCP1.9",
                "SSP2-RCP2.6",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-25, 105, 10))
        plt.title("Emissions Mitigated, " + iea_region_list[i])

    # endregion

    ######################
    # TEMPERATURE CHANGE #
    ######################

    # region
    # From openclimatedata/pyhector https://github.com/openclimatedata/pyhector

    rcps = [rcp19, rcp85]

    SURFACE_TEMP = "temperature.Tgav"

    for rcp in rcps:
        output = pyhector.run(rcp, {"core": {"endDate": 2100}})
        temp = output[SURFACE_TEMP]
        temp = temp.loc[1850:] - temp.loc[1850:1900].mean()
        hist = temp.loc[1850:2016]
        temp.loc[2016:2100].plot(label=rcp.name.split("_")[0], linestyle="--")
    hist.loc[1900:2100].plot(label="historical", color="black")
    plt.legend(("DAU", "Baseline", "Historical"), loc="best")
    plt.title("Global Mean Temperature")
    plt.ylabel("Deg. C over pre-industrial (1850-1900 mean)")

    # Climate sensitivity analysis

    low = pyhector.run(rcp19, {"temperature": {"S": 1.5}})
    default = pyhector.run(rcp19, {"temperature": {"S": 3}})
    high = pyhector.run(rcp19, {"temperature": {"S": 4.5}})

    plt.figure()
    sel = slice(1900, 2100)
    plt.fill_between(
        low[SURFACE_TEMP].loc[sel].index,
        low[SURFACE_TEMP].loc[sel],
        high[SURFACE_TEMP].loc[sel],
        color="lightgray",
    )
    default[SURFACE_TEMP].loc[sel].plot(linestyle="--")
    hist = default[SURFACE_TEMP].loc[1900:2016]
    hist.plot(label="historical", color="black")
    plt.title("DAU with equilibrium climate sensitivity set to 1.5, 3, and 4.5")
    plt.ylabel("Deg. C")
    plt.legend(("DAU", "Historical", "Sensitivity Range"), loc="upper left")

    # endregion

    ###############################
    # PROJECTED RADIATIVE FORCING #
    ###############################

    # region
    # from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

    FORCING = "forcing.Ftot"

    results = pyhector.run(rcp19)

    results[FORCING].loc[1900:2100].plot(linestyle="--")
    hist = default[FORCING].loc[1900:2016]
    hist.plot(label="historical", color="black")
    plt.title("DAU: " + pyhector.output[FORCING]["description"])
    plt.ylabel(pyhector.output[FORCING]["unit"])
    plt.legend(("DAU", "Historical"), loc="upper left")

    # endregion

    ######################################
    # PROJECTED CO2 EMISSIONS BY COUNTRY #
    ######################################

    # region
    # from openclimatedata/https://github.com/openclimatedata/notebooks/blob/master/EDGAR%20CO2%20Emissions.ipynb

    df = read_datapackage("https://github.com/openclimatedata/edgar-co2-emissions")
    unit = "kt"
    df = (
        df.reset_index()
        .drop("Name", axis=1)
        .set_index(["Code", "Sector", "Year"])
        .sort_index()
    )

    for code in ["USA", "CHN"]:
        grouped = (
            df.loc[code].reset_index().set_index("Year").groupby("Sector")["Emissions"]
        )

        fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(12, 4), sharey=True)
        try:
            name = to_name(code)
        except KeyError:
            name = code
        fig.suptitle(name)
        sectors = [
            "Power Industry",
            "Transport",
            "Buildings",
            "Other industrial combustion",
        ]
        for (key, ax) in zip(sectors, axes):
            ax.set_title(key, fontsize=10)
            grouped.get_group(key).plot(ax=ax, legend=False)
            ax.set_ylabel(unit)

    # endregion

    ###########################
    # PROJECTED GHG EMISSIONS #
    ###########################

    # region

    emissions = ["ffi_emissions", "CH4_emissions", "N2O_emissions"]

    for emissions in emissions:
        plt.plot(rcp19[emissions].loc[1900:2100])
        plt.plot(rcp19[emissions].loc[1900:2016], color="black")
        plt.ylabel("GtC")
        plt.title("DAU Net Emissions, " + emissions)
        plt.show()

    # endregion

    ###########################################
    # PROJECTED CO2 ATMOSPHERIC CONCENTRATION #
    ###########################################

    # region
    # from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

    CONCENTRATION_CO2 = "simpleNbox.Ca"

    results = pyhector.run(rcp19)

    results[CONCENTRATION_CO2].loc[1900:2100].plot(linestyle="--")
    hist = default[CONCENTRATION_CO2].loc[1900:2016]
    hist.plot(label="historical", color="black")
    plt.title("DAU: " + pyhector.output[CONCENTRATION_CO2]["description"])
    plt.ylabel(pyhector.output[CONCENTRATION_CO2]["unit"])
    plt.legend(("DAU", "Historical"), loc="upper left")

    # endregion

    ##################################################
    # FIG. 16 : ACTUAL VS. PROJECTED ADOPTION CURVES #
    ##################################################

    # region

    # endregion

    #################################################
    # FIG. 19 : ENERGY DEMAND BY SECTOR AND END-USE #
    #################################################

    # region

    # Baseline

    for i in range(0, 1):
        energy_demand_i = energy_demand_baseline.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Baseline"
        ]
        fig = (
            energy_demand_i.loc[
                (slice(None), slice(None), "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .drop("TFC")
            .rename(
                index={
                    "Buildings": ("Buildings", "Electricity"),
                    "Industry": ("Industry", "Electricity"),
                    "Transport": ("Transport", "Electricity"),
                }
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Transport", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Oil",
                            "Biofuels",
                            "Other fuels",
                        ],
                        :,
                    ]
                    .sum()
                    .add(
                        pd.DataFrame(
                            energy_demand_baseline.loc[
                                "World ", "Transport", "International bunkers"
                            ]
                        ).sum()
                    )
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Buildings", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Heat",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Buildings", "Heat")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Industry", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Heat",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Industry", "Heat")})
            )
            .reindex(
                [
                    ("Transport", "Nonelectric Transport"),
                    ("Transport", "Electricity"),
                    ("Buildings", "Heat"),
                    ("Buildings", "Electricity"),
                    ("Industry", "Heat"),
                    ("Industry", "Electricity"),
                ]
            )
        )

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(
                "darkgreen",
                "rebeccapurple",
                "lightcoral",
                "midnightblue",
                "darkred",
                "cornflowerblue",
            ),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_baseline.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_baseline.columns.max() + 1, 10))
        plt.title("Energy Demand, " + iea_region_list[i])

    # Pathway (Sum OECD/NonOECD)

    for i in range(0, 1):
        energy_demand_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_i.loc[
                (slice(None), slice(None), "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .drop("TFC")
            .rename(
                index={
                    "Buildings": ("Buildings", "Electricity"),
                    "Industry": ("Industry", "Electricity"),
                    "Transport": ("Transport", "Electricity"),
                }
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Transport", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Oil",
                            "Biofuels",
                            "Other fuels",
                        ],
                        :,
                    ]
                    .sum()
                    .add(
                        pd.DataFrame(
                            energy_demand_pathway.loc[
                                "World ", "Transport", "International bunkers"
                            ]
                        ).sum()
                    )
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Buildings", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Heat",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Buildings", "Heat")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_i.loc[
                        slice(None), "Industry", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Heat",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Industry", "Heat")})
            )
            .reindex(
                [
                    ("Transport", "Nonelectric Transport"),
                    ("Transport", "Electricity"),
                    ("Buildings", "Heat"),
                    ("Buildings", "Electricity"),
                    ("Industry", "Heat"),
                    ("Industry", "Electricity"),
                ]
            )
        )

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(
                "darkgreen",
                "rebeccapurple",
                "lightcoral",
                "midnightblue",
                "darkred",
                "cornflowerblue",
            ),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max() + 1, 10))
        plt.title("Energy Demand, " + iea_region_list[i])

    # endregion

    #############################################
    # FIG. 20 : ENERGY DEMAND MITIGATION WEDGES #
    #############################################

    # region

    # endregion

    ################################
    # ENERGY INTENSITY PROJECTIONS #
    ################################

    # region
    # https://github.com/iiasa/ipcc_sr15_scenario_analysis/blob/master/further_analysis/iamc15_energy_intensity.ipynb

    # endregion

    ###############################
    # ECONOMIC GROWTH PROJECTIONS #
    ###############################

    # region
    # https://github.com/iiasa/ipcc_sr15_scenario_analysis/blob/master/further_analysis/iamc15_gdp_per_capita.ipynb
    # endregion

    ###############################################
    # FIG. 24 : ENERGY SUPPLY BY SOURCE & END-USE #
    ###############################################

    # region

    # region

    tech_list = [
        ("Electricity", "Solar"),
        ("Electricity", "Wind"),
        ("Electricity", "Nuclear"),
        ("Electricity", "Other renewables"),
        ("Heat", "Solar thermal"),
        ("Heat", "Biochar"),
        ("Heat", "Bioenergy"),
        ("Transport", "Biofuels"),
        ("Electricity", "Fossil fuels"),
        ("Heat", "Fossil fuels"),
        ("Transport", "Fossil fuels"),
    ]

    group_keys = {
        ("Electricity", "Biomass and waste"): ("Electricity", "Other renewables"),
        ("Electricity", "Fossil fuels"): ("Electricity", "Fossil fuels"),
        ("Electricity", "Geothermal"): ("Electricity", "Other renewables"),
        ("Electricity", "Hydroelectricity"): ("Electricity", "Other renewables"),
        ("Electricity", "Tide and wave"): ("Electricity", "Other renewables"),
        ("Electricity", "Nuclear"): ("Electricity", "Nuclear"),
        ("Electricity", "Solar"): ("Electricity", "Solar"),
        ("Electricity", "Wind"): ("Electricity", "Wind"),
        ("Heat", "Fossil fuels"): ("Heat", "Other Fossil fuels"),
        ("Heat", "Bioenergy"): ("Heat", "Bioenergy"),
        ("Heat", "Coal"): ("Heat", "Other Fossil fuels"),
        ("Heat", "Geothermal"): ("Heat", "Geothermal"),
        ("Heat", "Natural gas"): ("Heat", "Other Fossil fuels"),
        ("Heat", "Nuclear"): ("Heat", "Nuclear"),
        ("Heat", "Oil"): ("Heat", "Other Fossil fuels"),
        ("Heat", "Other sources"): ("Heat", "Fossil fuels"),
        ("Heat", "Solar thermal"): ("Heat", "Solar thermal"),
        ("Heat", "Waste"): ("Heat", "Biochar"),
        ("Transport", "Oil"): ("Transport", "Oil"),
        ("Transport", "Biofuels"): ("Transport", "Biofuels"),
        ("Transport", "Other fuels"): ("Transport", "Other fuels"),
        ("Transport", "Fossil fuels"): ("Transport", "Fossil fuels"),
    }

    color2 = (
        (0.645, 0.342, 0.138),
        (0.285, 0.429, 0.621),
        (0.564, 0.114, 0.078),
        (0.603, 0.651, 0.717),
        (0.747, 0.720, 0.240),
        (0.624, 0.459, 0.450),
        (0.594, 0.462, 0.153),
        (0.165, 0.375, 0.102),
        (0.000, 0.000, 0.000),
        (0.267, 0.267, 0.267),
        (0.651, 0.651, 0.651),
    )

    # endregion

    # Baseline

    # region

    for i in range(0, 1):
        elec_consump_baseline_i = (
            elec_consump_baseline.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        elec_consump_baseline_i = pd.concat(
            [elec_consump_baseline_i], keys=["Electricity"], names=["Sector"]
        )
        heat_consump_baseline_i = (
            heat_consump_baseline.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        heat_consump_baseline_i = pd.concat(
            [heat_consump_baseline_i], keys=["Heat"], names=["Sector"]
        )
        transport_consump_baseline_i = (
            transport_consump_baseline.loc[
                [" OECD ", "NonOECD "],
                slice(None),
            ]
            .groupby("Metric")
            .sum()
        )
        transport_consump_baseline_i = pd.concat(
            [transport_consump_baseline_i], keys=["Transport"], names=["Sector"]
        )
        fig = pd.DataFrame(
            (
                elec_consump_baseline_i.append(heat_consump_baseline_i).append(
                    transport_consump_baseline_i
                )
            ).loc[:, 2010:2100]
        )
        fig = fig.groupby(group_keys).sum()
        fig = fig.reindex(tech_list)
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int), fig, labels=fig.index, colors=color2)
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, 2100])
        plt.title("Energy Supply by Source & End-use, " + iea_region_list[i])
        plt.legend(loc=2, fontsize="small")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)

    # endregion

    # Pathway

    # region

    for i in range(0, 1):
        elec_consump_pathway_i = (
            elec_consump_pathway.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        elec_consump_pathway_i = pd.concat(
            [elec_consump_pathway_i], keys=["Electricity"], names=["Sector"]
        )
        heat_consump_pathway_i = (
            heat_consump_pathway.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        heat_consump_pathway_i = pd.concat(
            [heat_consump_pathway_i], keys=["Heat"], names=["Sector"]
        )
        transport_consump_pathway_i = (
            transport_consump_pathway.loc[
                [" OECD ", "NonOECD "],
                slice(None),
            ]
            .groupby("Metric")
            .sum()
        )
        transport_consump_pathway_i = pd.concat(
            [transport_consump_pathway_i], keys=["Transport"], names=["Sector"]
        )
        fig = pd.DataFrame(
            (
                elec_consump_pathway_i.append(heat_consump_pathway_i).append(
                    transport_consump_pathway_i
                )
            ).loc[:, 2010:2100]
        )
        fig = fig.groupby(group_keys).sum()
        fig = fig.reindex(tech_list)
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int), fig, labels=fig.index, colors=color2)
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, 2100])
        plt.title("Energy Supply by Source & End-use, " + iea_region_list[i])
        plt.legend(loc=2, fontsize="small")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)

    # endregion

    # endregion

    ##############################################
    # FIG. 25 : ELECTRICITY GENERATION BY SOURCE #
    ##############################################

    # region

    # region

    tech_list = ["Solar", "Wind", "Nuclear", "Other renewables", "Fossil fuels"]

    group_keys = {
        "Biomass and waste": "Other renewables",
        "Fossil fuels": "Fossil fuels",
        "Geothermal": "Other renewables",
        "Hydroelectricity": "Other renewables",
        "Nuclear": "Nuclear",
        "Solar": "Solar",
        "Wind": "Wind",
    }

    color = (
        (0.645, 0.342, 0.138),
        (0.285, 0.429, 0.621),
        (0.564, 0.114, 0.078),
        (0.603, 0.651, 0.717),
        (0.267, 0.267, 0.267),
    )

    # endregion

    # Stacked Area (TWh)

    # region

    for i in range(0, 1):
        fig = (
            elec_consump_pathway.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        fig = fig.groupby(group_keys).sum()
        fig = fig.reindex(tech_list)
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int), fig, labels=fig.index, colors=color)
        plt.ylabel("TFC (TWh)")
        plt.ylim([0, 100000])
        plt.yticks(np.arange(0, 110000, 10000))
        plt.xlim([2020, long_proj_end_year])
        plt.title("Electricity Generation by Source, " + iea_region_list[i])
        plt.legend(loc=2, fontsize="small")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)

    # endregion

    # Line plot (%)

    # region

    for i in range(0, 1):
        fig = (
            elec_per_adoption_pathway.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        fig = fig[fig.index.isin(tech_list)]
        plt.figure(i)
        plt.plot(fig.columns.astype(int).values, fig.T * 100)
        plt.ylabel("(%)")
        plt.xlim([data_start_year, long_proj_end_year])
        plt.title("Percent of Total Electricity Generation, " + iea_region_list[i])
        plt.legend(
            fig.index,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    # endregion

    # Stacked 100% plot

    # region

    for i in range(0, 1):
        fig = (
            elec_per_adoption_pathway.loc[[" OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        fig = fig[fig.index.isin(tech_list)]
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int).values, fig * 100, labels=fig.index)
        plt.ylabel("(%)")
        plt.xlim([data_start_year, long_proj_end_year])
        plt.title("Percent of Total Electricity Generation, " + iea_region_list[i])
        plt.legend(
            fig.index,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    # endregion

    # endregion

    ################################################
    # FIG. 26 : ELECTRICITY DEMAND BY SECTOR (TWH) #
    ################################################

    # region

    color = ((0.116, 0.220, 0.364), (0.380, 0.572, 0.828), (0.368, 0.304, 0.48))

    # Pathway

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[
                (slice(None), slice(None), "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .drop("TFC")
            .rename(
                index={
                    "Buildings": ("Buildings", "Electricity"),
                    "Industry": ("Industry", "Electricity"),
                    "Transport": ("Transport", "Electricity"),
                }
            )
        )
        fig.loc[[("Industry", "Electricity")]] = (
            fig.loc[[("Industry", "Electricity")]] * 0.9
        )
        fig.loc[[("Transport", "Electricity")]] = (
            fig.loc[[("Transport", "Electricity")]] * 1.2
        )
        plt.figure(i)
        plt.stackplot(fig.T.index, fig, labels=fig.index, colors=color)
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.ylim([0, 100000])
        plt.yticks(np.arange(0, 110000, 10000))
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Electricity Demand by Sector, " + iea_region_list[i])

    # endregion

    #####################################
    # FIG. 27 : BUILDINGS ENERGY SUPPLY #
    #####################################

    # region

    tech_list = ["Electricity", "Solar thermal", "Bioenergy", "Fossil fuels"]

    group_keys = {
        "Bioenergy": "Bioenergy",
        "Geothermal": "Electricity",
        "Hydroelectricity": "Electricity",
        "Nuclear": "Electricity",
        "Solar": "Electricity",
        "Wind": "Electricity",
        "Coal": "Fossil fuels",
        "Electricity": "Electricity",
        "Natural gas": "Fossil fuels",
        "Oil": "Fossil fuels",
        "Other renewables": "Solar thermal",
    }

    color = (
        (0.380, 0.572, 0.828),
        (0.996, 0.096, 0.320),
        (0.792, 0.616, 0.204),
        (0.296, 0.276, 0.180),
    )

    # Pathway

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[
                (slice(None), "Buildings", "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .rename(
                index={
                    "Buildings": ("Buildings", "Electricity"),
                }
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc[
                        slice(None), "Buildings", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        ["Heat"],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Buildings", "Heat")})
            )
        )

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(
                "cornflowerblue",
                "lightcoral",
            ),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.ylim([0, 40000])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Buildings Energy Supply, " + iea_region_list[i])

    # endregion

    ###############################################
    # FIG. 28 : INDUSTRY ENERGY DEMAND BY END-USE #
    ###############################################

    # region

    tech_list = ["Solar thermal", "Bioenergy", "Fossil fuels", "Electricity"]

    group_keys = {
        "Bioenergy": "Bioenergy",
        "Geothermal": "Electricity",
        "Hydroelectricity": "Electricity",
        "Nuclear": "Electricity",
        "Solar": "Electricity",
        "Wind": "Electricity",
        "Coal": "Fossil fuels",
        "Electricity": "Electricity",
        "Natural gas": "Fossil fuels",
        "Oil": "Fossil fuels",
        "Other renewables": "Solar thermal",
    }

    color = (
        (0.556, 0.244, 0.228),
        (0.380, 0.572, 0.828),
    )

    # Pathway

    for i in range(0, len(iea_region_list)):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[
                (slice(None), "Industry", "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .rename(
                index={
                    "Industry": ("Industry", "Electricity"),
                }
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc[
                        slice(None), "Industry", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Heat",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Industry", "Heat")})
            )
            .reindex(
                [
                    ("Industry", "Heat"),
                    ("Industry", "Electricity"),
                ]
            )
        )

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.ylim([0, 45000])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])

    # endregion

    ##################################
    # FIG. 29 : INDUSTRY HEAT SUPPLY #
    ##################################

    # region

    # Heat generation by source

    heat_tech_list = [
        "Biofuels",
        "Coal",
        "Geothermal",
        "Natural gas",
        "Nuclear",
        "Oil",
        "Other sources",
        "Solar thermal",
        "Waste",
    ]

    color = (
        (0.296, 0.276, 0.180),
        (0.860, 0.456, 0.184),
        (0.792, 0.616, 0.204),
        (0.832, 0.612, 0.060),
        (0.996, 0.096, 0.320),
    )

    # Pathway
    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]

        fig = (
            energy_demand_pathway_i.loc[
                ([" OECD ", "NonOECD "], "Industry", "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .rename(
                index={
                    "Industry": ("Industry", "Electricity"),
                }
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc[
                        [" OECD ", "NonOECD "], "Industry", slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        ["Fossil fuels", "Bioenergy", "Solar thermal", "Waste"],
                        :,
                    ]
                    .sum()
                ).T.rename(
                    index={
                        "Fossil fuels": ("Industry", "Fossil fuels"),
                        "Bioenergy": ("Industry", "Bioenergy"),
                        "Solar thermal": ("Industry", "Solar Thermal"),
                        "Waste": ("Industry", "Syngas"),
                    }
                )
            )
            .reindex(
                [
                    ("Industry", "Heat"),
                    ("Industry", "Electricity"),
                    ("Industry", "Fossil fuels"),
                    ("Industry", "Bioenergy"),
                    ("Industry", "Solar Thermal"),
                    ("Industry", "Syngas"),
                ]
            )
        )

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.ylim([0, 20000])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])

    # endregion

    ##########################################
    # FIG. 30 : TRANSPORTATION ENERGY DEMAND #
    ##########################################

    # region

    color = ((0.220, 0.500, 0.136), (0.356, 0.356, 0.356), (0.380, 0.572, 0.828))

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            [" OECD ", "NonOECD "], "Transport", slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[
                (slice(None), "Transport", "Electricity", slice(None)), :
            ]
            .groupby(["Sector"])
            .sum()
            .rename(index={"Transport": "Electricity"})
            .append(
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        [" OECD ", "NonOECD "],
                        slice(None),
                    ]
                    .groupby("Metric")
                    .sum()
                    .loc[["Fossil fuels", "Other fuels"]]
                    .sum()
                ).T.rename(index={0: "Fossil fuels"})
            )
            .append(
                pd.DataFrame(
                    transport_consump_pathway.loc[
                        [" OECD ", "NonOECD "],
                        slice(None),
                    ]
                    .groupby("Metric")
                    .sum()
                    .loc["Biofuels"]
                ).T.rename(index={0: "Biofuels"})
            )
        ).reindex(
            [
                "Biofuels",
                "Fossil fuels",
                "Electricity",
            ]
        )
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC (TWh)")
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.ylim([0, 45000])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, 2110, 10))
        plt.title("Transportation Energy Supply, " + iea_region_list[i])

    # endregion

    #########################################
    # FIG. 31 : ELECTRIFICATION OF VEHICLES #
    #########################################

    # region

    # endregion

    ##############################################################
    # FIG. 32 : TRANSPORTATION ENERGY DEMAND REDUCTION FROM DESIGN IMPROVEMENTS #
    ##############################################################

    # region

    # endregion

    ##################################################################
    # FIG. 33 : REGENERATIVE AGRICULTURE SUBVECTOR MITIGATION WEDGES #
    ##################################################################

    # region

    # region

    color = (
        (0.999, 0.999, 0.999),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.356, 0.356, 0.356),
        (0.720, 0.348, 0.324),
        (0.840, 0.688, 0.680),
        (0.804, 0.852, 0.704),
        (0.736, 0.708, 0.796),
        (0.712, 0.168, 0.136),
        (0.384, 0.664, 0.600),
    )

    # endregion

    # region

    em_mit = (
        (
            afolu_em_mitigated.loc[
                slice(None),
                [
                    "Animal Mgmt",
                    "Legumes",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Biochar",
                    "Cropland Soil Health",
                    "Trees in Croplands",
                    "Nitrogen Fertilizer Management",
                    "Improved Rice",
                ],
                slice(None),
                slice(None),
            ]
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_targets_pathway = (
        pd.read_csv("podi/data/emissions_baseline_afolu.csv")
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            ["Agriculture Net Emissions", "Agriculture Baseline Emissions"],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    em_mit.loc["Improved Rice"] = em_targets_pathway.loc[
        "World ", "Agriculture Baseline Emissions"
    ].subtract(
        em_mit.drop(labels="Improved Rice")
        .append(spacer.drop(index="Agriculture Baseline Emissions"))
        .sum()
    )

    em_mit.loc[:, :2020] = 0

    custom_legend = [
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D([0], [0], color=color[8], linewidth=4),
        Line2D([0], [0], color=color[9], linewidth=4),
        Line2D([0], [0], color=color[10], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[11], linewidth=4, linestyle="--"),
    ]

    # endregion

    for i in range(0, 1):
        fig = (
            (em_mit.append(spacer.drop(index="Agriculture Baseline Emissions"))) / 1000
        ).reindex(
            [
                spacer.index[1],
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Biochar",
                "Cropland Soil Health",
                "Trees in Croplands",
                "Nitrogen Fertilizer Management",
                "Improved Rice",
            ]
        )
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=color,
        )
        plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
        plt.legend(
            loc=2,
            fontsize="small",
        )
        plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
        plt.ylabel("GtCO2e/yr")
        plt.xlim([2020, 2100])
        plt.grid(which="major", linestyle=":", axis="y")
        plt.legend(
            custom_legend,
            [
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Biochar",
                "Cropland Soil Health",
                "Trees in Croplands",
                "Nitrogen Fertilizer Management",
                "Improved Rice",
                "Agriculture Baseline Emissions",
                "Agriculture Net Emissions",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-3, 9, 1))
        plt.title(
            "Regenerative Agriculture Subvector Mitigation Wedges, "
            + iea_region_list[i]
        )

    # endregion

    ############################################################
    # FIG. 34 : FORESTS & WETLANDS SUBVECTOR MITIGATION WEDGES #
    ############################################################

    # region

    # region

    color = (
        (0.999, 0.999, 0.999),
        (0.156, 0.472, 0.744),
        (0.804, 0.868, 0.956),
        (0.152, 0.152, 0.152),
        (0.780, 0.756, 0.620),
        (0.776, 0.504, 0.280),
        (0.320, 0.560, 0.640),
        (0.404, 0.332, 0.520),
        (0.676, 0.144, 0.112),
        (0.384, 0.664, 0.600),
    )

    # endregion

    # region

    em_mit = (
        (
            afolu_em_mitigated.loc[
                slice(None),
                [
                    "Coastal Restoration",
                    "Avoided Coastal Impacts",
                    "Peat Restoration",
                    "Avoided Peat Impacts",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Avoided Forest Conversion",
                ],
                slice(None),
                slice(None),
            ]
            * 0.95
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_mit.loc[:, :2020] = 0

    em_targets_pathway = (
        pd.read_csv("podi/data/emissions_baseline_afolu.csv")
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            [
                "Forests & Wetlands Net Emissions",
                "Forests & Wetlands Baseline Emissions",
            ],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    custom_legend = [
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D([0], [0], color=color[8], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[9], linewidth=4, linestyle="--"),
    ]

    # endregion

    for i in range(0, 1):
        fig = (
            (em_mit.append(spacer.drop(index="Forests & Wetlands Baseline Emissions")))
            / 1000
        ).reindex(
            [
                spacer.index[1],
                "Coastal Restoration",
                "Avoided Coastal Impacts",
                "Peat Restoration",
                "Avoided Peat Impacts",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Avoided Forest Conversion",
            ]
        )
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=color,
        )
        plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
        plt.legend(
            loc=2,
            fontsize="small",
        )
        plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
        plt.ylabel("GtCO2e/yr")
        plt.xlim([2020, 2100])
        plt.grid(which="major", linestyle=":", axis="y")
        plt.legend(
            custom_legend,
            [
                "Coastal Restoration",
                "Avoided Coastal Impacts",
                "Peat Restoration",
                "Avoided Peat Impacts",
                "Forest Management",
                "Reforestation",
                "Avoided Forest Conversion",
                "Forests & Wetlands Baseline Emissions",
                "Forests & Wetlands Net Emissions",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-15, 5, 2))
        plt.title(
            "Forests & Wetlands Subvector Mitigation Wedges, " + iea_region_list[i]
        )

    # endregion

    ###############################################
    # FIG. 35 : AFOLU SUBVECTOR MITIGATION WEDGES #
    ###############################################

    # region

    # region

    color = (
        (0.999, 0.999, 0.999),
        (0.156, 0.472, 0.744),
        (0.804, 0.868, 0.956),
        (0.152, 0.152, 0.152),
        (0.780, 0.756, 0.620),
        (0.776, 0.504, 0.280),
        (0.320, 0.560, 0.640),
        (0.404, 0.332, 0.520),
        (0.356, 0.356, 0.356),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.584, 0.804, 0.756),
        (0.720, 0.348, 0.324),
        (0.840, 0.688, 0.680),
        (0.804, 0.852, 0.704),
        (0.736, 0.708, 0.796),
        (0.704, 0.168, 0.120),
        (0.384, 0.664, 0.600),
    )

    # endregion

    # region

    em_mit = (
        (
            afolu_em_mitigated.loc[
                slice(None),
                [
                    "Coastal Restoration",
                    "Avoided Coastal Impacts",
                    "Peat Restoration",
                    "Avoided Peat Impacts",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Avoided Forest Conversion",
                    "Animal Mgmt",
                    "Legumes",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Biochar",
                    "Cropland Soil Health",
                    "Trees in Croplands",
                    "Nitrogen Fertilizer Management",
                    "Improved Rice",
                ],
                slice(None),
                slice(None),
            ]
            * 0.95
        )
        .droplevel(["Metric", "Unit"])
        .groupby("Sector")
        .sum()
    ).loc[:, data_start_year:]
    em_mit.columns = em_mit.columns.astype(int)

    em_mit.loc[:, :2020] = 0

    em_targets_pathway = (
        pd.read_csv("podi/data/emissions_baseline_afolu.csv")
        .set_index(["Region", "Sector", "Unit"])
        .loc[
            slice(None),
            [
                "AFOLU Net Emissions",
                "AFOLU Baseline Emissions",
            ],
            slice(None),
        ]
        .droplevel("Unit")
    ).loc[:, str(data_start_year) :]

    em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

    spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

    custom_legend = [
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D([0], [0], color=color[8], linewidth=4),
        Line2D([0], [0], color=color[9], linewidth=4),
        Line2D([0], [0], color=color[10], linewidth=4),
        Line2D([0], [0], color=color[11], linewidth=4),
        Line2D([0], [0], color=color[12], linewidth=4),
        Line2D([0], [0], color=color[13], linewidth=4),
        Line2D([0], [0], color=color[14], linewidth=4),
        Line2D([0], [0], color=color[15], linewidth=4),
        Line2D([0], [0], color=color[16], linewidth=4),
        Line2D([0], [0], color=color[17], linewidth=4, linestyle="--"),
        Line2D([0], [0], color=color[18], linewidth=4, linestyle="--"),
    ]

    # endregion

    for i in range(0, 1):
        fig = (
            (em_mit.append(spacer.drop(index="AFOLU Baseline Emissions"))) / 1000
        ).reindex(
            [
                spacer.index[1],
                "Coastal Restoration",
                "Avoided Coastal Impacts",
                "Peat Restoration",
                "Avoided Peat Impacts",
                "Improved Forest Mgmt",
                "Natural Regeneration",
                "Avoided Forest Conversion",
                "Biochar",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Cropland Soil Health",
                "Trees in Croplands",
                "Nitrogen Fertilizer Management",
                "Improved Rice",
            ]
        )
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=color,
        )
        plt.plot(fig.T.index, em_targets_pathway.T / 1000, LineStyle="--")
        plt.legend(
            loc=2,
            fontsize="small",
        )
        plt.axhline(y=0, color=(0, 0, 0), linestyle=":")
        plt.ylabel("GtCO2e/yr")
        plt.xlim([2020, 2100])
        plt.grid(which="major", linestyle=":", axis="y")
        plt.legend(
            custom_legend,
            [
                "Coastal Restoration",
                "Avoided Coastal Impacts",
                "Peat Restoration",
                "Avoided Peat Impacts",
                "Forest Management",
                "Reforestation",
                "Avoided Forest Conversion",
                "Biochar",
                "Animal Mgmt",
                "Legumes",
                "Optimal Intensity",
                "Silvopasture",
                "Cropland Soil Health",
                "Trees in Croplands",
                "Nitrogen Fertilizer Management",
                "Improved Rice",
                "AFOLU Baseline Emissions",
                "AFOLU Net Emissions",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-17, 10, 5))
        plt.title("AFOLU Subvector Mitigation Wedges, " + iea_region_list[i])

    # endregion

    ########################################
    # FIG. 40 : ANNUAL CO2 REMOVED VIA CDR #
    ########################################

    # region

    # endregion

    return
