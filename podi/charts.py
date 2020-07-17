#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter
import matplotlib.animation as animation
from IPython.display import HTML
from podi.data.iea_weo_etl import region_list


def charts(energy_demand_baseline, energy_demand_pathway):

    # adoption curves (add annual adoption curve to look like PD20 Fig.1)

    # historical analogies adoption curves

    # mitigation wedges curve

    # projected average global temperature increase above pre-industrial

    # projected greenhouse gas atmospheric concentration (ppm CO2e)

    # projected CO2 atmospheric concentration

    # energy demand by sector and end-use (TWh)
    for i in range(0, len(region_list)):
        energy_demand_pathway2 = energy_demand_pathway.loc[
            region_list[i], slice(None), slice(None)
        ]
        fig = (
            energy_demand_pathway2.loc[(slice(None), "Electricity"), :]
            .drop("TFC")
            .append(
                pd.DataFrame(
                    energy_demand_pathway2.loc["Transport"]
                    .loc[["Oil", "Biofuels", "Other fuels"], :]
                    .sum()
                ).T.rename(index={0: ("Transport", "Nonelectric Transport")})
            )
            .append(
                pd.DataFrame(
                    energy_demand_pathway2.loc["Buildings"]
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
                    energy_demand_pathway2.loc["Industry"]
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
        plt.title("Energy Demand, " + region_list[i])

    # energy demand mitigation wedges (TWh)

    # energy intensity projections (TWh/GDP)

    # energy supply by source and end-use (TWh)

    # electricity generation by source (TWh)

    # electricity demand by sector (TWh)

    # buildings energy supply by source (TWh)

    # industry energy demand by end-use (TWh)

    # industry heat supply by source (TWh)

    # transportation energy demand by source (TWh)

    # regenerative agriculture subvector mitigation wedges

    # forests & wetlands subvector mitigation wedges

    # afolu subvector mitigation wedges

    # annual CO2 removed from CDR
    return
