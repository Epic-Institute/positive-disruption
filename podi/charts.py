#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
import matplotlib.animation as animation
from IPython.display import HTML
from podi.data.iea_weo_etl import iea_region_list
import pyam
from scipy.interpolate import make_interp_spline, BSpline


def charts(energy_demand_baseline, energy_demand_pathway):

    # Fig. 3: Projected Market Diffusion Curves for the V7
    for i in range(0, len(iea_region_list)):
        # fig = dataframe of percent of max mitigation for each vector

        plt.figure(i)
        plt.plot(fig.columns.astype(int).values, fig.T * 100)
        plt.ylabel("(%)")
        plt.xlim([data_start_year, long_proj_end_year])
        plt.title("Percent of Total PD Adoption, " + iea_region_list[i])
        plt.legend(
            fig.index,
            loc=2,
            fontsize="small",
            bbox_to_anchor=(1.05, 1),
            borderaxespad=0.0,
        )

    # Fig. 4: Mitigation Wedges Curve
    # https://pyam-iamc.readthedocs.io/en/stable/examples/plot_stack.html#sphx-glr-examples-plot-stack-py

    for i in range(0, len(iea_region_list)):

        # fig = dataframe of percent of max mitigation for each vector

        plt.figure(i)
        plt.plot(fig.columns.astype(int).values, fig.T)
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

    # Fig. 5: Projected average global temperature increase above pre-industrial
    # https://github.com/openscm/pymagicc

    # Fig. 6: Projected greenhouse gas atmospheric concentration
    # https://github.com/openscm/pymagicc

    # Fig. 7: Projected CO2 atmospheric concentration
    # https://github.com/openscm/pymagicc

    # Fig. 16: Actual vs. Projected Adoption Curves

    # Fig. 19: Energy demand by sector and end-use

    # Baseline
    for i in range(0, len(iea_region_list)):
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

    # Pathway
    for i in range(0, len(iea_region_list)):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            iea_region_list[i], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[(slice(None), "Electricity", slice(None)), :]
            .drop("TFC")
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc["Transport"]
                    .loc[["Oil", "Biofuels", "Other fuels"], :]
                    .sum()
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc["Buildings"]
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
                    energy_demand_pathway_i.loc["Industry"]
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

    # Fig. 20: Energy Demand Mitigation Wedges

    # Fig. 21: Energy Intensity Projections

    # Fig. 24: Energy Supply by Source and End-use

    # Fig. 25: Electricity Generation by Source
    tech_list = [
        "Biomass and waste",
        "Fossil fuels",
        "Geothermal",
        "Hydroelectricity",
        "Nuclear",
        "Solar",
        "Wind",
    ]

    for i in range(0, len(iea_region_list)):
        fig = elec_consump.loc[iea_region_list[i], slice(None)]
        fig = fig[fig.index.isin(tech_list)]
        plt.figure(i)
        plt.stackplot(fig.columns.astype(int), fig, labels=fig.index)
        plt.ylabel("TFC (TWh)")
        plt.title("Electricity Generation by Source, " + iea_region_list[i])
        plt.legend(loc=2, fontsize="small")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)

    # Fig. 25.1: Electricity Generation by Source (%)
    # Line plot
    for i in range(0, len(iea_region_list)):
        fig = elec_percent_adoption.loc[iea_region_list[i], slice(None)]
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

    # Stacked plot
    for i in range(0, len(iea_region_list)):
        fig = elec_percent_adoption.loc[iea_region_list[i], slice(None)]
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

    # Fig. 26: Electricity Demand by Sector (TWh)
    # Baseline
    for i in range(0, len(iea_region_list)):
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

    # Pathway
    for i in range(0, len(iea_region_list)):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            iea_region_list[i], slice(None), slice(None), "Pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[(slice(None), "Electricity", slice(None)), :]
            .drop("TFC")
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc["Transport"]
                    .loc[["Oil", "Biofuels", "Other fuels"], :]
                    .sum()
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway_i.loc["Buildings"]
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
                    energy_demand_pathway_i.loc["Industry"]
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

    # Fig. 27: Buildings Energy Supply

    # Fig. 28: Industry Energy Demand by End-Use

    # Fig. 29: Industry Heat Supply

    # Fig. 30: Transportation Energy Demand

    # Fig. 31: Electrification of Vehicles

    # Fig. 32: Transportation Energy Demand Reduction from Design Improvements

    # Fig. 33: Regenerative Agriculture Subvector Mitigation Wedges

    # Fig. 34: Forests & Wetlands Subvector Mitigation Wedges

    # Fig. 35: AFOLU Subvector Mitigation Wedges

    # Fig. 40: Annual CO2 Removed via CDR

    return
