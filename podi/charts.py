#!/usr/bin/env python

# region

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
import pyhector
from pyhector import rcp19, rcp26, rcp45, rcp60, rcp85
from podi.energy_demand import iea_region_list, data_end_year, data_start_year
from podi.energy_supply import near_proj_end_year
from pandas_datapackage_reader import read_datapackage
from shortcountrynames import to_name
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

save_figs = True
long_proj_start_year = near_proj_end_year + 1
unit_name = ["TWh", "EJ", "Mtoe", "Ktoe"]
unit_val = [1, 0.00359, 0.086, 86]
unit = [unit_name[0], unit_val[0]]


# endregion


def charts(
    energy_demand_baseline,
    energy_demand_pathway,
    adoption_curves,
    em_targets_pathway,
    em_mitigated,
):

    #####################################
    # PROJECTED MARKET DIFFUSION CURVES #
    #####################################

    # region

    fig_type = "plotly"

    for i in range(0, len(iea_region_list)):
        fig = adoption_curves.loc[iea_region_list[i]] * 100

        if fig_type == "plotly":
            fig = fig.T
            fig.index.name = "Year"
            fig.reset_index(inplace=True)
            fig2 = pd.melt(
                fig, id_vars="Year", var_name="Sector", value_name="% Adoption"
            )
            fig = px.line(
                fig2,
                x="Year",
                y="% Adoption",
                line_group="Sector",
                color="Sector",
                color_discrete_sequence=px.colors.qualitative.T10,
                title="Percent of Total PD Adoption, " + iea_region_list[i],
                hover_data={"% Adoption": ":.0f"},
            )
            fig.update_layout(title_x=0.5)
            fig.add_vrect(x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0)
            fig.show()
            if save_figs is True:
                pio.write_html(
                    fig,
                    file=("./charts/scurves-" + iea_region_list[i] + ".html").replace(
                        " ", ""
                    ),
                    auto_open=False,
                )
        else:
            plt.figure(i)
            plt.plot(fig.T, linestyle="--")
            plt.plot(
                fig.loc[:, data_start_year:data_end_year].T * 100,
                linestyle="-",
                color=(0, 0, 0),
            )
            plt.ylabel("% Adoption")
            plt.xlim([fig.columns.min(), fig.columns.max()])
            plt.title("Percent of Total PD Adoption, " + iea_region_list[i])
            plt.legend(
                fig.index,
                loc=2,
                fontsize="small",
                bbox_to_anchor=(1.05, 1),
            )
            plt.show()
            if save_figs is True:
                plt.savefig(
                    fname=("podi/data/figs/scurves-" + iea_region_list[i]).replace(
                        " ", ""
                    ),
                    format="png",
                    bbox_inches="tight",
                    pad_inches=0.1,
                )
            plt.clf()
            color = {
                "Grid": [(0.120, 0.107, 0.155)],
                "Transport": [(0.93, 0.129, 0.180)],
                "Buildings": [(0.225, 0.156, 0.98)],
                "Industry": [(0.44, 0.74, 0.114)],
                "Regenerative Agriculture": [(0.130, 0.143, 0.81)],
                "Forests & Wetlands": [(0.138, 0.188, 0.175)],
                "Carbon Dioxide Removal": [(0.200, 0.156, 0.152)],
            }
            axis_label = [
                "% TFC met by renewables",
                "% Transport TFC met by electricity & bioenergy",
                "% Buildings TFC met by electricity & renewable heat",
                "% Industry TFC met by electricity & renewable heat",
                "MHa",
                "MHa",
                "GtCO2 removed",
            ]

            for i in range(0, len(iea_region_list)):
                for j in range(0, len(adoption_curves.loc[iea_region_list[i]].index)):
                    fig = adoption_curves.iloc[j]
                    plt.show()
                    plt.figure(j)
                    plt.plot(fig * 100, linestyle="--", color=(0.560, 0.792, 0.740))
                    plt.plot(
                        fig.loc[data_start_year:data_end_year] * 100,
                        linestyle="-",
                        color=(0, 0, 0),
                    )
                    plt.ylabel("% Adoption")
                    plt.xlim([fig.index.min(), fig.index.max()])
                    plt.title(
                        "Percent of Total PD Adoption, "
                        + fig.name[1]
                        + ", "
                        + iea_region_list[i]
                    )

                    if save_figs is True:
                        plt.savefig(
                            fname=(
                                "podi/data/figs/scurves_ind-"
                                + fig.name[1]
                                + "-"
                                + iea_region_list[i]
                            ).replace(" ", ""),
                            format="png",
                            bbox_inches="tight",
                            pad_inches=0.1,
                        )
                    plt.clf()

                    # Absolute values

                    """
                    t = adoption_curves2.columns
                    data1 = adoption_curves2.loc['Grid']
                    data2 = elec_consump_pathway.loc[iea_region_list, ['Biomass and Waste', 'Geothermal','Hydroelectricity','Nuclear','Solar','Tide and Wave','Wind'],:].sum()

                    fig, ax1 = plt.subplots(figsize=(9, 5))

                    color = (0.560, 0.792, 0.740)    
                    ax1.set_ylabel('% Adoption', color=color )
                    ax1.plot(t, data1, color=color, linestyle = '--')
                    ax1.tick_params(axis='y', labelcolor=color)
                    plt.grid(which="major", linestyle=":", axis="y")
                    ax2 = ax1.twinx()
                    color='tab:blue'
                    ax2.set_ylabel(axis_label[j],color=color)
                    ax2.plot(t, data2,color=color, linestyle = '--')
                    ax2.tick_params(axis='y', labelcolor=color)
                    ax1.plot(
                        t[0 : (data_end_year - data_start_year) + 2],
                        data1[0 : (data_end_year - data_start_year) + 2],
                        linestyle="-",
                        color=(0, 0, 0),
                    )
                    ax2.plot(
                        t[0 : (data_end_year - data_start_year) + 2],
                        data2[0 : (data_end_year - data_start_year) + 2],
                        linestyle="-",
                        color=(0, 0, 0),
                    )
                    plt.xlim([2010, 2100])
                    plt.suptitle(
                        "Total PD Adoption, "
                        + 'Grid Decarb'
                        + ", "
                        + iea_region_list[i]
                    )
                    plt.title('% Adoption Projected - Teal Dashed Line \n Cumulative Capacity Projected - Blue Dashed Line \n (Mismatch between lines is due to growing electrical demand)', fontsize = 9)
                    fig.tight_layout()
                    plt.savefig(
                        (fname="podi/data/figs/scurves2_ind-"
                        + adoption_curves2.index[j]
                        + "-"
                        + iea_region_list[i]).replace(" ", ""),
                        format="png",
                        bbox_inches="tight",
                        pad_inches=0.1,
                    )
                    plt.show()
                    """

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

    custom_legend = [
        Line2D([0], [0], color=color[8], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D(
            [0], [0], color=color[12], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[10], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[9], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[11], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
    ]

    for i in range(0, len(iea_region_list)):
        em_mit_electricity = em_mitigated.loc[
            [iea_region_list[i]], "Electricity", slice(None)
        ].sum()

        em_mit_transport = (
            em_mitigated.loc[[" OECD ", "NonOECD "], "Transport", slice(None)].sum()
            * 1.05
        )

        em_mit_buildings = (
            em_mitigated.loc[[" OECD ", "NonOECD "], "Buildings", slice(None)].sum()
            * 0.7
        )

        em_mit_industry = (
            em_mitigated.loc[[" OECD ", "NonOECD "], "Industry", slice(None)].sum()
            * 0.6
        )

        em_mit_ra = (
            afolu_em_mitigated.loc[
                [" OECD ", "NonOECD "],
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
                [" OECD ", "NonOECD "],
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

        em_mit_othergas = em_mitigated.loc[
            [" OECD ", "NonOECD "], "Other gases", :
        ].sum()

        em_mit_cdr = pd.Series(
            cdr_pathway.sum(), index=np.arange(data_start_year, long_proj_end_year + 1)
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
        spacer = em_targets_pathway.loc["pathway PD20"]
        em_targets_pathway.loc["baseline PD20"] = em_mit.append(spacer).sum()

        em_mit.loc["Electricity"] = em_targets_pathway.loc["baseline PD20"].subtract(
            em_mit.drop(labels="Electricity").append(spacer).sum()
        )

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
                "baseline",
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
        plt.show()

        if save_figs is True:
            plt.savefig(
                fname=("podi/data/figs/mitigationwedges-" + iea_region_list[i]).replace(
                    " ", ""
                ),
                format="png",
                bbox_inches="tight",
                pad_inches=0.1,
            )
        plt.clf()

    # endregion

    #################################
    # EMISSIONS MITIGATION BARCHART #
    #################################

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

    em_mit_electricity = (
        em_mitigated.loc["World ", "Electricity", slice(None)].sum() * 0.5
    )

    em_mit_transport = em_mitigated.loc["World ", "Transport", slice(None)].sum() * 1.05

    em_mit_buildings = em_mitigated.loc["World ", "Buildings", slice(None)].sum() * 0.7

    em_mit_industry = em_mitigated.loc["World ", "Industry", slice(None)].sum() * 0.6

    em_mit_ra = (
        afolu_em_mitigated.loc[
            "World ",
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
            "World ",
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

    em_mit_othergas = em_mitigated.loc["World ", "Other gases", :].sum()

    em_mit_cdr = pd.Series(
        cdr_pathway.sum(), index=np.arange(data_start_year, long_proj_end_year + 1)
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
    em_mit.loc["Electricity"] = em_targets_pathway.loc["baseline PD20"].subtract(
        em_mit.drop(labels="Electricity").sum()
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
        Line2D(
            [0], [0], color=color[12], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[10], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[9], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[11], linewidth=2, linestyle=":", dashes=(2, 1, 0, 0)
        ),
    ]

    for i in range(0, len(iea_region_list)):
        fig = ((em_mit) / 1000).reindex(
            [
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
        figure = px.bar(
            fig,
            x=fig.index,
            y=2060,
            labels={"index": "Vector", "2060": "GtCO2e Mitigated in 2060"},
            title="V7 Opportunities, World",
        )
        figure.show()

        pio.write_html(
            figure,
            file=("./charts/em1-" + iea_region_list[i] + ".html").replace(" ", ""),
            auto_open=False,
        )

        figure = px.bar(
            fig,
            x=2060,
            y=fig.index,
            labels={"index": "Vector", "2060": "GtCO2e Mitigated in 2060"},
            title="V7 Opportunities, World",
        )
        figure.show()

        pio.write_html(
            figure,
            file=("./charts/em2-" + iea_region_list[i] + ".html").replace(" ", ""),
            auto_open=False,
        )

    # endregion

    ######################
    # TEMPERATURE CHANGE #
    ######################

    # region
    # From openclimatedata/pyhector https://github.com/openclimatedata/pyhector

    # TEMPERATURE

    # region

    rcps = [rcp19, rcp85]

    SURFACE_TEMP = "temperature.Tgav"

    for rcp in rcps:
        output = pyhector.run(rcp, {"core": {"endDate": 2100}})
        temp = output[SURFACE_TEMP]
        temp = temp.loc[1850:] - temp.loc[1850:1900].mean()
        hist = temp.loc[1850:2016]
        temp.loc[2016:2100].plot(label=rcp.name.split("_")[0], linestyle="--")
    hist.loc[1900:2100].plot(label="historical", color="black")
    plt.legend(("DAU", "baseline", "Historical"), loc="best")
    plt.title("Global Mean Temperature")
    plt.ylabel("Deg. C over pre-industrial (1850-1900 mean)")
    plt.savefig(
        fname=("podi/data/figs/temperature").replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

    # endregion

    # CLIMATE SENSITIVITY

    # region

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
    plt.savefig(
        fname="podi/data/figs/sensitivity",
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

    # endregion

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
    hist.plot(label="historical", color="black", figsize=(10, 5))
    plt.title("DAU: " + pyhector.output[FORCING]["description"])
    plt.ylabel(pyhector.output[FORCING]["unit"])
    plt.legend(("DAU", "Historical"), loc="upper left")
    plt.savefig(
        fname="podi/data/figs/forcing",
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )

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
        plt.savefig(
            fname=("podi/data/figs/emissions-" + code).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
    plt.clf()
    # endregion

    ###########################
    # PROJECTED GHG EMISSIONS #
    ###########################

    # region

    # ABSOLUTE

    emissions = ["ffi_emissions", "CH4_emissions", "N2O_emissions"]
    names = ["CO2", "CH4", "N2O"]
    units = ["Gt C", "Mt CH4", "Mt N2O"]
    mult = [1, 1, 0.001]
    i = 0

    for emission in emissions:
        fig = plt.plot(
            rcp19[emission].loc[2000:2100] * mult[i],
            linestyle="--",
            color=(0.560, 0.792, 0.740),
        )
        plt.plot(rcp19[emission].loc[2000:2016] * mult[i], color="black")
        plt.ylabel(units[i])
        plt.title("DAU Net Emissions, " + names[i])
        plt.savefig(
            fname=("podi/data/figs/emissions-" + names[i]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        i = i + 1
    plt.clf()

    # IN CO2e UNITS

    emissions = ["ffi_emissions", "CH4_emissions", "N2O_emissions"]
    names = ["CO2", "CH4", "N2O"]
    units = ["GtCO2e", "GtCO2e", "GtCO2e"]
    mult = [3.67, 1e-3, 1e-3]
    gwp = [1, 28, 265]
    j = 0

    for emission in emissions:
        fig = plt.plot(
            rcp19[emission].loc[2000:2100] * mult[j] * gwp[j],
            linestyle="--",
            color=(0.560, 0.792, 0.740),
        )
        plt.plot(rcp19[emission].loc[2000:2016] * mult[j] * gwp[j], color="black")
        plt.ylabel(units[j])
        plt.title("DAU Net Emissions, " + names[j])
        plt.savefig(
            fname=("podi/data/figs/emissions-" + names[j]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        j = j + 1
    plt.clf()

    # Combined GHG

    mult = [3.67, 1e-3, 1e-3]
    gwp = [1, 28, 265]
    i = 0

    fig = plt.plot(
        rcp19.loc[2000:2100] * mult[i] * gwp[i],
        linestyle="--",
        color=(0.560, 0.792, 0.740),
    )
    plt.plot(rcp19.loc[2000:2016] * mult[i] * gwp[i], color="black")
    plt.ylabel("GtCO2e")
    plt.title("DAU Net Emissions, " + names[i])
    plt.savefig(
        fname=("podi/data/figs/emissions-" + names[i]).replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

    # endregion

    ###########################################
    # PROJECTED CO2 ATMOSPHERIC CONCENTRATION #
    ###########################################

    # region
    # from openclimatedata/pyhector https://github.com/openclimatedata/pyhector

    CONCENTRATION_CO2 = "simpleNbox.Ca"

    results = pyhector.run(rcp19)

    results[CONCENTRATION_CO2].loc[1900:2100].plot(
        linestyle="--", color=(0.560, 0.792, 0.740)
    )
    hist = default[CONCENTRATION_CO2].loc[1900:2016]
    hist.plot(label="historical", color="black", figsize=(10, 5))
    plt.title("DAU: " + pyhector.output[CONCENTRATION_CO2]["description"])
    plt.ylabel(pyhector.output[CONCENTRATION_CO2]["unit"])
    plt.legend(("DAU", "Historical"), loc="upper left")
    plt.savefig(
        fname=("podi/data/figs/co2conc").replace(" ", ""),
        format="png",
        bbox_inches="tight",
        pad_inches=0.1,
    )
    plt.show()
    plt.clf()

    # endregion

    ########################################
    # ACTUAL VS. PROJECTED ADOPTION CURVES #
    ########################################

    # region

    # endregion

    #######################################
    # ENERGY DEMAND BY SECTOR AND END-USE #
    #######################################

    # region

    show_fig = True
    scenario = "pathway"
    chart_type = "stack"
    fig_type = "plotly"

    if chart_type == "stack":
        for i in range(0, len(iea_region_list)):
            energy_demand_i = (
                energy_demand.loc[
                    iea_region_list[i], slice(None), slice(None), scenario
                ]
                * unit[1]
            )

            if iea_region_list[i] == "World ":
                energy_demand_i.loc["Transport", "Other fuels"] = energy_demand_i.loc[
                    "Transport", ["International bunkers", "Other fuels"], :
                ].sum()

            fig = (
                energy_demand_i.loc[(slice(None), "Electricity"), :]
                .groupby(["Sector"])
                .sum()
                .drop("TFC")
                .rename(
                    index={
                        "Buildings": "Buildings-Electricity",
                        "Industry": "Industry-Electricity",
                        "Transport": "Transport-Electricity",
                    }
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Transport", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Oil",
                                "Bioenergy",
                                "Other fuels",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Transport-Nonelectric"})
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Buildings", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Heat",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Buildings-Heat"})
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Industry", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Heat",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Industry-Heat"})
                )
                .reindex(
                    [
                        "Transport-Nonelectric",
                        "Transport-Electricity",
                        "Buildings-Heat",
                        "Buildings-Electricity",
                        "Industry-Heat",
                        "Industry-Electricity",
                    ]
                )
            )
            if fig_type == "plotly":
                fig = fig.T
                fig.index.name = "Year"
                fig.reset_index(inplace=True)
                fig2 = pd.melt(
                    fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0]
                )
                fig = px.area(
                    fig2,
                    x="Year",
                    y="TFC, " + unit[0],
                    line_group="Sector",
                    color="Sector",
                    color_discrete_sequence=px.colors.qualitative.T10,
                    title="Energy Demand, "
                    + iea_region_list[i]
                    + ", "
                    + scenario.title(),
                    hover_data={"TFC, " + unit[0]: ":.0f"},
                )
                fig.update_layout(title_x=0.5)
                fig.add_vrect(
                    x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0
                )
                if show_fig is True:
                    fig.show()
                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/demand-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )
            else:

                colors = (
                    (0.0, 0.392, 0.0),
                    (0.4, 0.2, 0.6),
                    (0.941, 0.501, 0.501),
                    (0.098, 0.098, 0.439),
                    (0.545, 0.0, 0.0),
                    (0.392, 0.584, 0.929),
                )

                colors2 = (pd.DataFrame(colors) * 0.75).values.tolist()

                plt.figure(i)
                plt.stackplot(
                    fig.loc[:, :data_end_year].T.index,
                    fig.loc[:, :data_end_year],
                    labels=fig.index,
                    colors=colors2,
                )
                plt.stackplot(
                    fig.loc[:, data_end_year:].T.index,
                    fig.loc[:, data_end_year:],
                    labels=fig.index,
                    colors=colors,
                    linestyle="--",
                )
                plt.legend(loc=2, fontsize="small")
                plt.ylabel("TFC, " + unit[0])
                plt.xlim([data_start_year, energy_demand.columns.max()])
                plt.legend(
                    labels=fig.index, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0
                )
                plt.xticks(
                    np.arange(data_start_year, energy_demand.columns.max() + 1, 10)
                )
                plt.title("Energy Demand, " + iea_region_list[i])
                plt.show()
                if save_figs is True:
                    plt.savefig(
                        fname=(
                            "podi/data/figs/demand-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                        ).replace(" ", ""),
                        format="png",
                        bbox_inches="tight",
                        pad_inches=0.1,
                    )

            plt.clf()

    if chart_type == "line":
        for i in range(0, len(iea_region_list)):
            energy_demand_i = energy_demand_baseline.loc[
                iea_region_list[i], slice(None), slice(None), "baseline"
            ]

            if iea_region_list[i] == "World ":
                energy_demand_i.loc["Transport", "Other fuels"] = energy_demand_i.loc[
                    "Transport", ["International bunkers", "Other fuels"], :
                ].sum()

            fig = (
                energy_demand_i.loc[(slice(None), "Electricity"), :]
                .groupby(["Sector"])
                .sum()
                .drop("TFC")
                .rename(
                    index={
                        "Buildings": "Buildings-Electricity",
                        "Industry": "Industry-Electricity",
                        "Transport": "Transport-Electricity",
                    }
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Transport", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Oil",
                                "Bioenergy",
                                "Other fuels",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Transport-Nonelectric"})
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Buildings", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Heat",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Buildings-Heat"})
                )
                .append(
                    pd.DataFrame(
                        energy_demand_i.loc["Industry", slice(None)]
                        .groupby(["Metric"])
                        .sum()
                        .loc[
                            [
                                "Heat",
                            ],
                            :,
                        ]
                        .sum()
                    ).T.rename(index={0: "Industry-Heat"})
                )
                .reindex(
                    [
                        "Transport-Nonelectric",
                        "Transport-Electricity",
                        "Buildings-Heat",
                        "Buildings-Electricity",
                        "Industry-Heat",
                        "Industry-Electricity",
                    ]
                )
            )
            if fig_type == "plotly":
                fig = fig.T
                fig.index.name = "Year"
                fig.reset_index(inplace=True)
                fig2 = pd.melt(
                    fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0]
                )
                fig = px.line(
                    fig2,
                    x="Year",
                    y="TFC, " + unit[0],
                    line_group="Sector",
                    color="Sector",
                    color_discrete_sequence=px.colors.qualitative.T10,
                    title="Energy Demand, " + iea_region_list[i],
                    hover_data={"TFC, " + unit[0]: ":.0f"},
                )
                fig.update_layout(title_x=0.5)
                fig.add_vrect(
                    x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0
                )
                fig.show()
                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/demand-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )
            else:
                plt.figure(i)
                plt.plot(
                    fig.loc[:, :data_end_year].T.index,
                    fig.loc[:, :data_end_year].T * unit[1],
                )
                plt.plot(
                    fig.loc[:, data_end_year:].T.index,
                    fig.loc[:, data_end_year:].T * unit[1],
                    linestyle="--",
                )
                plt.legend(loc=2, fontsize="small")
                plt.ylabel("TFC, " + unit[0])
                plt.xlim([data_start_year, energy_demand_baseline.columns.max()])
                plt.legend(
                    labels=fig.index, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0
                )
                plt.xticks(
                    np.arange(
                        data_start_year, energy_demand_baseline.columns.max() + 1, 10
                    )
                )
                plt.title("Energy Demand, " + iea_region_list[i])
                plt.show()

                if save_figs is True:
                    plt.savefig(
                        fname=(
                            "podi/data/figs/demand-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                        ).replace(" ", ""),
                        format="png",
                        bbox_inches="tight",
                        pad_inches=0.1,
                    )

            plt.clf()

    # endregion

    ###################################
    # ENERGY DEMAND MITIGATION WEDGES #
    ###################################

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

    #####################################
    # ENERGY SUPPLY BY SOURCE & END-USE #
    #####################################

    # region

    tech_list = [
        ("Electricity", "Solar"),
        ("Electricity", "Wind"),
        ("Electricity", "Nuclear"),
        ("Electricity", "Other renewables"),
        ("Heat", "Solar thermal"),
        ("Heat", "Biochar"),
        ("Heat", "Bioenergy"),
        ("Transport", "Bioenergy"),
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
        ("Transport", "Bioenergy"): ("Transport", "Bioenergy"),
        ("Transport", "Other fuels"): ("Transport", "Other fuels"),
        ("Transport", "Fossil fuels"): ("Transport", "Fossil fuels"),
    }

    show_fig = False
    scenario = "pathway"
    chart_type = "stack"
    fig_type = "plotly"

    if chart_type == "stack":
        for i in range(0, len(iea_region_list)):
            elec_consump_i = (
                elec_consump.loc[iea_region_list[i], slice(None), scenario]
                .groupby("Metric")
                .sum()
            )
            elec_consump_i = pd.concat(
                [elec_consump_i], keys=["Electricity"], names=["Sector"]
            )
            heat_consump_i = (
                heat_consump.loc[iea_region_list[i], slice(None)]
                .groupby("Metric")
                .sum()
            )
            heat_consump_i = pd.concat(
                [heat_consump_i], keys=["Heat"], names=["Sector"]
            )
            transport_consump_i = (
                transport_consump.loc[
                    iea_region_list[i],
                    slice(None),
                ]
                .groupby("Metric")
                .sum()
            )
            transport_consump_i = pd.concat(
                [transport_consump_i], keys=["Transport"], names=["Sector"]
            )
            fig = pd.DataFrame(
                (elec_consump_i.append(heat_consump_i).append(transport_consump_i)).loc[
                    :, 2010:2100
                ]
            )
            fig = fig.groupby(group_keys).sum()
            fig = fig.reindex(tech_list)

            if fig_type == "plotly":
                fig = fig.T
                fig.index.name = "Year"
                fig.reset_index(inplace=True)
                fig2 = pd.melt(
                    fig, id_vars="Year", var_name="Sector", value_name="TFC, " + unit[0]
                )
                fig = px.area(
                    fig2,
                    x="Year",
                    y="TFC, " + unit[0],
                    line_group="Sector",
                    color="Sector",
                    color_discrete_sequence=px.colors.qualitative.T10,
                    title="Energy Supply, " + iea_region_list[i],
                    hover_data={"TFC, " + unit[0]: ":.0f"},
                )
                fig.update_layout(title_x=0.5)
                fig.add_vrect(
                    x0=2010, x1=2019, fillcolor="grey", opacity=0.6, line_width=0
                )
                if show_fig is True:
                    fig.show()
                if save_figs is True:
                    pio.write_html(
                        fig,
                        file=(
                            "./charts/supply-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                            + ".html"
                        ).replace(" ", ""),
                        auto_open=False,
                    )

            else:

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

                plt.figure(i)
                plt.stackplot(
                    fig.columns.astype(int),
                    fig * unit[1],
                    labels=fig.index,
                    colors=color2,
                )
                plt.ylabel("TFC, " + unit[0])
                plt.xlim([2020, 2100])
                plt.title("Energy Supply by Source & End-use, " + iea_region_list[i])
                plt.legend(loc=2, fontsize="small")
                plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
                plt.show()
                if save_figs is True:
                    plt.savefig(
                        fname=(
                            "podi/data/figs/supply-"
                            + scenario
                            + "-"
                            + iea_region_list[i]
                        ).replace(" ", ""),
                        format="png",
                        bbox_inches="tight",
                        pad_inches=0.1,
                    )

            plt.clf()

    # endregion

    ####################################
    # ELECTRICITY GENERATION BY SOURCE #
    ####################################

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

    # STACKED AREA PLOT

    # region

    for i in range(0, len(iea_region_list)):
        fig = (
            elec_consump_pathway.loc[iea_region_list[i], slice(None)]
            .groupby("Metric")
            .sum()
        )
        fig = fig.groupby(group_keys).sum()
        fig = fig.reindex(tech_list)
        plt.figure(i)
        plt.stackplot(
            fig.columns.astype(int), fig * unit[1], labels=fig.index, colors=color
        )
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, long_proj_end_year])
        plt.title("Electricity Generation by Source, " + iea_region_list[i])
        plt.legend(loc=2, fontsize="small")
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.savefig(
            fname=("podi/data/figs/electricity_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    # LINE PLOT

    # region

    for i in range(0, len(iea_region_list)):
        fig = (
            elec_per_adoption_pathway.loc[iea_region_list[i], slice(None)]
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
        plt.show()
        plt.clf()

    # endregion

    # STACKED 100% PLOT

    # region

    for i in range(0, len(iea_region_list)):
        fig = (
            elec_per_adoption_pathway.loc[iea_region_list[i], slice(None)]
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
        plt.show()
        plt.clf()

    # endregion

    # endregion

    ######################################
    # ELECTRICITY DEMAND BY SECTOR (TWH) #
    ######################################

    # region

    color = ((0.116, 0.220, 0.364), (0.380, 0.572, 0.828), (0.368, 0.304, 0.48))

    # pathway

    for i in range(0, len(iea_region_list)):
        energy_demand_pathway_i = energy_demand_pathway.loc[
            iea_region_list[i], slice(None), slice(None), "pathway"
        ]
        fig = (
            energy_demand_pathway_i.loc[
                (iea_region_list[i], slice(None), "Electricity"), :
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
        plt.stackplot(fig.T.index, fig * unit[1], labels=fig.index, colors=color)
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Electricity Demand by Sector, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/elecbysector_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    ###########################
    # BUILDINGS ENERGY SUPPLY #
    ###########################

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

    # pathway

    for i in range(0, len(iea_region_list)):
        fig = energy_demand_pathway.loc[
            iea_region_list[i], "Buildings", ["Electricity", "Heat"], "pathway"
        ]

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig * unit[1],
            labels=fig.index.get_level_values(2),
            colors=(
                "cornflowerblue",
                "lightcoral",
            ),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Buildings Energy Supply, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/buildings_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    #####################################
    # INDUSTRY ENERGY DEMAND BY END-USE #
    #####################################

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

    # pathway

    for i in range(0, len(iea_region_list)):
        fig = energy_demand_pathway.loc[
            iea_region_list[i], "Industry", ["Electricity", "Heat"], "pathway"
        ]

        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig * unit[1],
            labels=fig.index.get_level_values(2),
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/industry_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    ########################
    # INDUSTRY HEAT SUPPLY #
    ########################
    """
    # region

    # Heat generation by source

    heat_tech_list = [
        "Bioenergy",
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

    # pathway

    for i in range(0, len(iea_region_list)):
        fig = energy_demand_pathway.loc[
            iea_region_list[i], 'Industry', ['Coal', 'Natural gas', 'Oil', "Bioenergy", "Other renewables"], "pathway"]
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig * unit[1],
            labels=fig.index.get_level_values(2),
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, energy_demand_pathway.columns.max(), 10))
        plt.title("Industry Energy Demand by End-Use, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/industryheat_pathway-" + iea_region_list[i]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    """
    ################################
    # TRANSPORTATION ENERGY DEMAND #
    ################################

    # region

    color = ((0.220, 0.500, 0.136), (0.356, 0.356, 0.356), (0.380, 0.572, 0.828))

    for i in range(0, len(iea_region_list)):
        fig = energy_demand_pathway.loc[
            iea_region_list[i],
            "Transport",
            ["Electricity", "Oil", "Bioenergy"],
            "pathway",
        ]
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig * unit[1],
            labels=fig.index.get_level_values(2),
            colors=(color),
        )
        plt.legend(loc=2, fontsize="small")
        plt.ylabel("TFC, " + unit[0])
        plt.xlim([2020, energy_demand_pathway.columns.max()])
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
        plt.xticks(np.arange(2020, 2110, 10))
        plt.title("Transportation Energy Supply, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/transport_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    ###############################
    # ELECTRIFICATION OF VEHICLES #
    ###############################

    # region

    # endregion

    ###################################################################
    # TRANSPORTATION ENERGY DEMAND REDUCTION FROM DESIGN IMPROVEMENTS #
    ###################################################################

    # region

    # endregion

    ########################################################
    # REGENERATIVE AGRICULTURE SUBVECTOR MITIGATION WEDGES #
    ########################################################

    # region

    # region

    color = (
        (0.999, 0.999, 0.999),
        (0.584, 0.804, 0.756),
        (0.526, 0.724, 0.680),
        (0.473, 0.651, 0.612),
        (0.426, 0.586, 0.551),
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
        Line2D(
            [0], [0], color=color[10], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[11], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
    ]

    # endregion

    for i in range(0, len(iea_region_list)):
        em_mit = (
            (
                afolu_em_mitigated.loc[
                    [" OECD ", "NonOECD "],
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
                ["Agriculture Net Emissions", "Agriculture baseline Emissions"],
                slice(None),
            ]
            .droplevel("Unit")
        ).loc[:, str(data_start_year) :]

        em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

        spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

        em_mit.loc["Improved Rice"] = em_targets_pathway.loc[
            "World ", "Agriculture baseline Emissions"
        ].subtract(
            em_mit.drop(labels="Improved Rice")
            .append(spacer.drop(index="Agriculture baseline Emissions"))
            .sum()
        )

        em_mit.loc[:, :2020] = 0

        fig = (
            (em_mit.append(spacer.drop(index="Agriculture baseline Emissions"))) / 1000
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
                "Agriculture baseline Emissions",
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
        plt.savefig(
            fname=("podi/data/figs/ra_pathway-" + iea_region_list[i]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    ##################################################
    # FORESTS & WETLANDS SUBVECTOR MITIGATION WEDGES #
    ##################################################

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

    custom_legend = [
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
        Line2D([0], [0], color=color[3], linewidth=4),
        Line2D([0], [0], color=color[4], linewidth=4),
        Line2D([0], [0], color=color[5], linewidth=4),
        Line2D([0], [0], color=color[6], linewidth=4),
        Line2D([0], [0], color=color[7], linewidth=4),
        Line2D(
            [0], [0], color=color[8], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[9], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
    ]

    # endregion

    for i in range(0, len(iea_region_list)):
        em_mit = (
            (
                afolu_em_mitigated.loc[
                    [" OECD ", "NonOECD "],
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
                    "Forests & Wetlands baseline Emissions",
                ],
                slice(None),
            ]
            .droplevel("Unit")
        ).loc[:, str(data_start_year) :]

        em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

        spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

        fig = (
            (em_mit.append(spacer.drop(index="Forests & Wetlands baseline Emissions")))
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
                "Forests & Wetlands baseline Emissions",
                "Forests & Wetlands Net Emissions",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.title(
            "Forests & Wetlands Subvector Mitigation Wedges, " + iea_region_list[i]
        )
        plt.savefig(
            fname=("podi/data/figs/fw_pathway-" + iea_region_list[i]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    #####################################
    # AFOLU SUBVECTOR MITIGATION WEDGES #
    #####################################

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
        (0.526, 0.724, 0.680),
        (0.473, 0.651, 0.612),
        (0.426, 0.586, 0.551),
        (0.720, 0.348, 0.324),
        (0.840, 0.688, 0.680),
        (0.804, 0.852, 0.704),
        (0.736, 0.708, 0.796),
        (0.704, 0.168, 0.120),
        (0.384, 0.664, 0.600),
    )

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
        Line2D(
            [0], [0], color=color[17], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
        Line2D(
            [0], [0], color=color[18], linewidth=2, linestyle="--", dashes=(2, 1, 0, 0)
        ),
    ]

    # endregion

    for i in range(0, len(iea_region_list)):
        em_mit = (
            (
                afolu_em_mitigated.loc[
                    [" OECD ", "NonOECD "],
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
                    "AFOLU baseline Emissions",
                ],
                slice(None),
            ]
            .droplevel("Unit")
        ).loc[:, str(data_start_year) :]

        em_targets_pathway.columns = em_targets_pathway.columns.astype(int)

        spacer = em_targets_pathway.droplevel("Region").loc[:, data_start_year:]

        fig = (
            (em_mit.append(spacer.drop(index="AFOLU baseline Emissions"))) / 1000
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
                "AFOLU baseline Emissions",
                "AFOLU Net Emissions",
            ],
            bbox_to_anchor=(1.05, 1),
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.yticks(np.arange(-17, 10, 5))
        plt.title("AFOLU Subvector Mitigation Wedges, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/afolu_pathway-" + iea_region_list[i]).replace(
                " ", ""
            ),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    ##############################
    # ANNUAL CO2 REMOVED VIA CDR #
    ##############################

    # region

    color = (
        (0.804, 0.868, 0.956),
        (0.404, 0.332, 0.520),
        (0.156, 0.472, 0.744),
    )

    custom_legend = [
        Line2D([0], [0], color=color[0], linewidth=4),
        Line2D([0], [0], color=color[1], linewidth=4),
        Line2D([0], [0], color=color[2], linewidth=4),
    ]

    for i in range(0, len(iea_region_list)):
        fig = cdr_pathway / 1000
        plt.figure(i)
        plt.stackplot(
            fig.T.index,
            fig,
            labels=fig.index,
            colors=color,
        )
        plt.ylabel("GtCO2e/yr")
        plt.xlim([2020, 2100])
        plt.legend(
            custom_legend,
            [
                "ExSitu Enhanced Weathering",
                "Low-Temp Solid Sorbent DAC",
                "High-temp Liquid Sorbent DAC",
            ],
            bbox_to_anchor=(1.05, 1),
            fontsize="small",
            loc=2,
            borderaxespad=0.0,
        )
        plt.xticks(np.arange(2020, 2110, 10))
        plt.title("CO2 Removed via CDR, " + iea_region_list[i])
        plt.savefig(
            fname=("podi/data/figs/cdr_pathway-" + iea_region_list[i]).replace(" ", ""),
            format="png",
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.show()
        plt.clf()

    # endregion

    return
