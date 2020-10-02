#!/usr/bin/env python

# region
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
import matplotlib.animation as animation
from IPython.display import HTML
from podi.data.iea_weo_etl import iea_region_list
import pyam
from scipy.interpolate import interp1d, UnivariateSpline
from matplotlib.animation import FuncAnimation
from podi.energy_supply import (
    data_end_year,
    data_start_year,
    long_proj_start_year,
    long_proj_end_year,
)
import pymagicc
from pymagicc import scenarios
from podi.emissions import em, em_targets

# endregion


def charts(energy_demand_baseline, energy_demand_pathway):

    #########################################################
    # FIG. 3 : PROJECTED MARKET DIFFUSION CURVES FOR THE V7 #
    #########################################################

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

    ####################################
    # FIG. 4 : MITIGATION WEDGES CURVE #
    ####################################

    # region

    color = (
        (0.560, 0.516, 0.640),
        (0.488, 0.672, 0.736),
        (0.904, 0.620, 0.384),
        (0.384, 0.460, 0.560),
        (0.536, 0.576, 0.432),
        (0.572, 0.792, 0.744),
        (0.688, 0.472, 0.460),
        (0.928, 0.828, 0.824),
    )

    color2 = (
        (0.748, 0.232, 0.204),
        (0.384, 0.664, 0.600),
        (0.284, 0.700, 0.936),
        (0.999, 0.976, 0.332),
    )

    em_mit_electricity = (
        em_mitigated.loc[slice(None), "Electricity", slice(None)]
        .groupby("Metric")
        .sum()
        .sum()
    )

    em_mit_transport = (
        em_mitigated.loc[slice(None), "Heat", [""]].groupby("Metric").sum().sum()
    )

    em_mit_buildings = (
        em_mitigated.loc[slice(None), "Heat", [""]].groupby("Metric").sum().sum()
    )

    em_mit_industry = (
        em_mitigated.loc[slice(None), "Industry", slice(None)]
        .groupby("Metric")
        .sum()
        .sum()
    )

    # note for AFOLU using em not em_mitigated
    em_mit_ra = em.loc[
        slice(None),
        "AFOLU",
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
    ].sum()

    em_mit_fw = em.loc[
        slice(None),
        "AFOLU",
        [
            " Avoided Coastal Impacts ",
            " Avoided Forest Conversion ",
            " Avoided Peat Impacts ",
            " Coastal Restoration ",
            " Improved Forest Mgmt ",
            " Peat Restoration ",
            " Natural Regeneration ",
        ],
    ].sum()

    em_mit_othergas = (
        em_mitigated.loc[slice(None), "Industry", ["CH4", "N2O", "F-Gases"]]
        .groupby("Metric")
        .sum()
        .sum()
    )

    em_mit_cdr = cdr_needed_def

    for i in range(0, 1):
        fig = em.loc[["OECD ", "NonOECD "]].groupby("Metric").sum()
        plt.figure(i)
        plt.plot(fig.columns.astype(int).values, fig.T)
        plt.plot(fig.columns.values, em_targets, linestyle="-", colors=color2)
        plt.ylabel("Gt CO2e/yr")
        plt.xlim([data_start_year, long_proj_end_year])
        plt.title("Mitigation Wedges, " + iea_region_list[i])
        plt.legend(
            fig.index,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    # endregion

    ###############################################################
    # FIG. 5 : PROJECECTD AVERAGE GLOBAL TEMPERATURE INCREASE ABOVE PRE-INDUSTRIAL #
    ###############################################################

    # region
    # https://github.com/openclimatedata/pyhector/blob/master/pyhector/emissions/RCP26_emissions.csv
    # https://github.com/openscm/pymagicc

    for name, scen in scenarios.items():
        results = pymagicc.run(scen)
        results_df = pd.DataFrame(results, index="time")

        global_temp_time_rows = (results_df.variable == "Surface Temperature") & (
            results_df.region == "World"
        )

        temp = (
            results_df.value[global_temp_time_rows].loc[1850:]
            - results_df.value[global_temp_time_rows].loc[1850:1900].mean()
        )
        temp.plot(label=name)

    plt.legend()
    plt.title("Global Mean Temperature Projection")
    plt.ylabel("°C over pre-industrial (1850-1900 mean)")
    plt.legend(loc="best")
    plt.show()

    # endregion

    ################################################################
    # FIG. 6 : PROJECECTD GREENHOUSE GAS ATMOSPHERIC CONCENTRATION #
    ################################################################

    # region

    # https://github.com/openscm/pymagicc

    # endregion

    #####################################################
    # FIG. 7 : PROJECECTD CO2 ATMOSPHERIC CONCENTRATION #
    #####################################################

    # region

    # https://github.com/openscm/pymagicc

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
        energy_demand_baseline_i = energy_demand_baseline.loc[
            iea_region_list[i], slice(None), slice(None), "Baseline"
        ]
        fig = (
            energy_demand_baseline_i.loc[(slice(None), "Electricity", slice(None)), :]
            .drop("TFC")
            .append(
                pd.DataFrame(
                    energy_demand_baseline_i.loc["Transport"]
                    .loc[["Oil", "Biofuels", "Other fuels"], :]
                    .sum()
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_baseline_i.loc["Buildings"]
                    .loc[
                        [
                            "Coal",
                            "Oil",
                            "Natural gas",
                            "Heat",
                            "Bioenergy",
                            "Other renewables",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Buildings", "Heat")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_baseline_i.loc["Industry"]
                    .loc[
                        [
                            "Coal",
                            "Oil",
                            "Natural gas",
                            "Heat",
                            "Bioenergy",
                            "Other renewables",
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
        plt.xlim([10, 90])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(10, 100, 10))
        plt.title("Energy Demand, " + iea_region_list[i])

    # Pathway (World)

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            ["World "], slice(None), slice(None), "Pathway"
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
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc[
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
                    energy_demand_pathway_i.loc[
                        slice(None), "Buildings", slice(None), slice(None)
                    ]
                    .groupby(["Metric"])
                    .sum()
                    .loc[
                        [
                            "Coal",
                            "Oil",
                            "Natural gas",
                            "Bioenergy",
                            "Heat",
                            "Other renewables",
                        ],
                        :,
                    ]
                    .sum()
                ).T.rename(index={0: ("Buildings", "Heat")})
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
                            "Coal",
                            "Oil",
                            "Natural gas",
                            "Bioenergy",
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
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Energy Demand, " + iea_region_list[i])

    # Pathway (Sum OECD/NonOECD)

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            ["OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
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
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc[
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
                    energy_demand_pathway_i.loc[
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
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Energy Demand, " + iea_region_list[i])

    # endregion

    #############################################
    # FIG. 20 : ENERGY DEMAND MITIGATION WEDGES #
    #############################################

    # region

    # endregion

    ##########################################
    # FIG. 21 : ENERGY INTENSITY PROJECTIONS #
    ##########################################

    # region

    # endregion

    ###############################################
    # FIG. 24 : ENERGY SUPPLY BY SOURCE & END-USE #
    ###############################################

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
        ("Heat", "Fossil fuels"): ("Heat", "Fossil fuels"),
        ("Heat", "Bioenergy"): ("Heat", "Bioenergy"),
        ("Heat", "Coal"): ("Heat", "Fossil fuels"),
        ("Heat", "Geothermal"): ("Heat", "Geothermal"),
        ("Heat", "Natural gas"): ("Heat", "Fossil fuels"),
        ("Heat", "Nuclear"): ("Heat", "Nuclear"),
        ("Heat", "Oil"): ("Heat", "Fossil fuels"),
        ("Heat", "Other sources"): ("Heat", "Other sources"),
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

    for i in range(0, 1):
        elec_consump_pathway_i = (
            elec_consump_pathway.loc[["OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        elec_consump_pathway_i = pd.concat(
            [elec_consump_pathway_i], keys=["Electricity"], names=["Sector"]
        )
        heat_consump_pathway_i = (
            heat_consump_pathway.loc[["OECD ", "NonOECD "], slice(None)]
            .groupby("Metric")
            .sum()
        )
        heat_consump_pathway_i = pd.concat(
            [heat_consump_pathway_i], keys=["Heat"], names=["Sector"]
        )
        transport_consump_pathway_i = (
            transport_consump_pathway.loc[
                ["OECD ", "NonOECD "],
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

    ##############################################
    # FIG. 25 : ELECTRICITY GENERATION BY SOURCE #
    ##############################################

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

    for i in range(0, 1):
        fig = (
            elec_consump_pathway.loc[["OECD ", "NonOECD "], slice(None)]
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

    # Line plot (%)

    for i in range(0, len(iea_region_list)):
        fig = elec_per_adoption_pathway.loc[iea_region_list[i], slice(None)]
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

    # Stacked 100% plot

    for i in range(0, 1):
        fig = (
            elec_per_adoption_pathway.loc[["OECD ", "NonOECD "], slice(None)]
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

    ################################################
    # FIG. 26 : ELECTRICITY DEMAND BY SECTOR (TWH) #
    ################################################

    # region

    color = ((0.116, 0.220, 0.364), (0.380, 0.572, 0.828), (0.368, 0.304, 0.48))

    # Pathway

    for i in range(0, 1):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            ["OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
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
            ["OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
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
            ["OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
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
            ["OECD ", "NonOECD "], slice(None), slice(None), "Pathway"
        ]

        fig = (
            energy_demand_pathway_i.loc[
                (["OECD ", "NonOECD "], "Industry", "Electricity", slice(None)), :
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
                        ["OECD ", "NonOECD "], "Industry", slice(None)
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
            ["OECD ", "NonOECD "], "Transport", slice(None), "Pathway"
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
                        ["OECD ", "NonOECD "],
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
                        ["OECD ", "NonOECD "],
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

    # endregion

    ############################################################
    # FIG. 34 : FORESTS & WETLANDS SUBVECTOR MITIGATION WEDGES #
    ############################################################

    # region

    # endregion

    ###############################################
    # FIG. 35 : AFOLU SUBVECTOR MITIGATION WEDGES #
    ###############################################

    # region

    # Stacked plot

    for i in range(0, len(iea_region_list)):
        fig = afolu_em_mitigated.loc[
            iea_region_list[i], slice(None), slice(None), slice(None)
        ]
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int).values, fig / 1e6, labels=this.values)
        plt.ylabel("Gt CO2/yr")
        plt.xlim([data_start_year, long_proj_end_year])
        plt.title("AFOLU Emissions Mitigated, " + iea_region_list[i])
        plt.legend(
            this.values,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    # endregion

    ########################################
    # FIG. 40 : ANNUAL CO2 REMOVED VIA CDR #
    ########################################

    # region

    # endregion

    return
