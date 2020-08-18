#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
import matplotlib.animation as animation
from IPython.display import HTML
from podi.data.iea_weo_etl import iea_region_list


def charts(energy_demand_baseline, energy_demand_pathway):

    # adoption curves (add annual adoption curve to look like PD20 Fig.1)

    for i in range(0, len(iea_region_list)):
        fig = solarpv_percent_adoption.loc[iea_region_list[i]]

        plt.figure(i)
        plt.plot(fig.T.index.values, fig.values * 100)
        plt.ylabel("Adoption (%)")
        plt.xlim([1980, 2100])
        plt.title("Percent Adoption, Solar PV " + iea_region_list[i])

    # YOY adoption percent growth

    for i in range(0, len(iea_region_list)):
        fig = solarpv_adoption_growth.loc[iea_region_list[i]]

        plt.figure(i)
        plt.scatter(fig.T.index.values, fig.values * 100)
        plt.ylabel("Change (%)")
        plt.xlim([1980, 2100])
        plt.title("YOY Adoption Growth, Solar PV " + iea_region_list[i])

    # historical analogies adoption curves

    # mitigation wedges curve

    # projected average global temperature increase above pre-industrial

    # projected greenhouse gas atmospheric concentration (ppm CO2e)

    # projected CO2 atmospheric concentration

    # energy demand by sector and end-use (TWh)
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

    # energy demand mitigation wedges (TWh)

    # energy intensity projections (TWh/GDP)

    # energy supply by source and end-use (TWh)

    # solar PV
    for i in range(0, len(iea_region_list)):
        plt.figure(i)
        plt.plot(
            solarpv_generation.columns.astype(int),
            solarpv_generation.loc[iea_region_list[i]].values,
        )
        plt.ylabel("TFC (TWh)")
        plt.title("Energy Supply, Solar PV " + iea_region_list[i])

    # wind
    # for i in range(0, len(iea_region_list)):
    #    plt.figure(i)
    #    plt.scatter(
    #        wind_generation.columns.astype(int),
    #        wind_generation.loc[iea_region_list[i]].values,
    #        s=0.1,
    #    )
    #    plt.ylabel("TFC (TWh)")
    #    plt.title("Energy Supply, Wind " + iea_region_list[i])

    # electricity generation by source (TWh)

    # electricity demand by sector (TWh)
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

    # buildings energy supply by source (TWh)

    # industry energy demand by end-use (TWh)

    # industry heat supply by source (TWh)

    # transportation energy demand by source (TWh)

    # regenerative agriculture subvector mitigation wedges

    # forests & wetlands subvector mitigation wedges

    # afolu subvector mitigation wedges

    # annual CO2 removed from CDR
    return
