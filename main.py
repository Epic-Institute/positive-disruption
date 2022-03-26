#!/usr/bin/env python

# region
from unicodedata import name
import warnings
import numpy as np
import pandas as pd
from podi.energy import energy
from podi.energy_supply import energy_supply
from podi.afolu import afolu
from podi.afolu2030 import afolu2030
from podi.emissions import emissions
from podi.results_analysis import results_analysis
from podi.cdr.cdr_main import cdr_mix
from podi.curve_smooth import curve_smooth
from podi.climate import climate
from podi.cdr.cdr_util import (
    grid_em_def,
    heat_em_def,
    transport_em_def,
    fuel_em_def,
)

warnings.simplefilter(action="ignore", category=FutureWarning)
regions = pd.read_fwf("podi/data/IEA/Regions.txt").rename(columns={"REGION": "Region"})


data_start_year = 1990
data_end_year = 2020
proj_end_year = 2050

# endregion

# Choose a scenario name, which will create output data sets with the scenario name appended, e.g. energy_pathway.csv
scenario = "pathway"

##########
# ENERGY #
##########

# region

recalc_energy = False
if recalc_energy is True:
    energy("pathway", data_start_year, data_end_year, proj_end_year)
    index = [
        "Scenario",
        "Region",
        "Sector",
        "Subsector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Hydrogen",
        "Flexible",
        "Non-Energy Use",
    ]

    energy_pathway = pd.DataFrame(
        pd.read_csv("podi/data/energy_" + scenario + ".csv")
    ).set_index(index)
    energy_pathway.columns = energy_pathway.columns.astype(int)

else:
    index = [
        "Scenario",
        "Region",
        "Sector",
        "Subsector",
        "Product_category",
        "Product_long",
        "Product",
        "Flow_category",
        "Flow_long",
        "Flow",
        "Hydrogen",
        "Flexible",
        "Non-Energy Use",
    ]

    energy_pathway = pd.DataFrame(
        pd.read_csv("podi/data/energy_" + scenario + ".csv")
    ).set_index(index)
    energy_pathway.columns = energy_pathway.columns.astype(int)


# endregion

#########
# AFOLU #
#########

# region
ncsmx2030 = False

if ncsmx2030 is True:
    afolu_em_baseline, afolu_per_adoption_baseline, afolu_per_max_baseline = afolu2030(
        "baseline"
    )

    afolu_em_pathway, afolu_per_adoption_pathway, afolu_per_max_pathway = afolu2030(
        "pathway"
    )

    afolu_em = afolu_em_baseline.append(afolu_em_pathway)

    afolu_per_adoption = afolu_per_adoption_baseline.append(afolu_per_adoption_pathway)

    afolu_per_max = afolu_per_max_baseline.append(afolu_per_max_pathway)
else:
    afolu_em_baseline, afolu_per_adoption_baseline, afolu_per_max_baseline = afolu(
        "baseline"
    )

    afolu_em_pathway, afolu_per_adoption_pathway, afolu_per_max_pathway = afolu(
        "pathway"
    )

    afolu_em = afolu_em_baseline.append(afolu_em_pathway)

    afolu_per_adoption = afolu_per_adoption_baseline.append(afolu_per_adoption_pathway)

    afolu_per_max = afolu_per_max_baseline.append(afolu_per_max_pathway)

afolu_em.loc[
    slice(None),
    slice(None),
    [
        "Deforestation",
        "3B_Manure-management",
        "3D_Rice-Cultivation",
        "3D_Soil-emissions",
        "3E_Enteric-fermentation",
        "3I_Agriculture-other",
    ],
    slice(None),
    "baseline",
] = afolu_em.loc[
    slice(None),
    slice(None),
    [
        "Deforestation",
        "3B_Manure-management",
        "3D_Rice-Cultivation",
        "3D_Soil-emissions",
        "3E_Enteric-fermentation",
        "3I_Agriculture-other",
    ],
    slice(None),
    "pathway",
].values

# endregion

#############
# EMISSIONS #
#############

# region

podi.data.iea_weo_em_etl

em_baseline, em_targets_baseline, em_hist = emissions(
    "baseline",
    energy_demand,
    elec_consump,
    heat_consump,
    heat_per_adoption,
    transport_consump,
    afolu_em,
    "podi/data/emissions_additional.csv",
    "podi/data/iamc_data.csv",
    data_start_year,
    data_end_year,
)

em_pathway, em_targets_pathway, em_hist = emissions(
    "pathway",
    energy_demand,
    elec_consump,
    heat_consump,
    heat_per_adoption,
    transport_consump,
    afolu_em,
    "podi/data/emissions_additional.csv",
    "podi/data/iamc_data.csv",
    data_start_year,
    data_end_year,
)

em = em_baseline.append(em_pathway)

em_mitigated = (
    em_baseline.groupby(["Region", "Sector", "Metric"]).sum()
    - em_pathway.groupby(["Region", "Sector", "Metric"]).sum()
)

# endregion

#######
# CDR #
#######

# region

cdr_pathway = pd.read_csv("podi/data/cdr_curve.csv").set_index(
    ["Region", "Sector", "Scenario"]
)
cdr_pathway.columns = cdr_pathway.columns.astype(int)

cdr_subvs = []

for scenario in ["pathway"]:

    cdr_pathway2, cdr_cost_pathway, cdr_energy_pathway = cdr_mix(
        cdr_pathway.loc["World ", "Carbon Dioxide Removal", scenario]
        .loc[2010:]
        .to_list(),
        grid_em_def,
        heat_em_def,
        transport_em_def,
        fuel_em_def,
        2010,
        2100,
    )

    cdr_pathway2 = (
        pd.DataFrame(cdr_pathway2, index=em_mitigated.loc[:, 2010:].columns)
        .T.fillna(0)
        .drop(
            index=pd.DataFrame(cdr_pathway2, index=em_mitigated.loc[:, 2010:].columns)
            .T.fillna(0)
            .iloc[
                pd.DataFrame(cdr_pathway2, index=em_mitigated.loc[:, 2010:].columns)
                .T.fillna(0)
                .index.str.contains("Deficit", na=False)
            ]
            .index
        )
    )

    cdr_subvs = pd.DataFrame(cdr_subvs).append(
        pd.concat([cdr_pathway2], keys=["World "], names=["Region"])
    )

    cdr_subvs = (
        cdr_subvs.droplevel(1)
        .assign(Metric=["Enhanced Weathering", "Other", "LTSSDAC", "HTLSDAC"])
        .set_index("Metric", append=True)
    )

    cdr_subvs = curve_smooth(cdr_subvs, "quadratic", 9).clip(lower=0)

    cdr_subvs = pd.concat(
        [cdr_subvs], names=["Sector"], keys=["Carbon Dioxide Removal"]
    )
    cdr_subvs["Scenario"] = "pathway"
    cdr_subvs = cdr_subvs.reset_index().set_index(
        ["Region", "Sector", "Metric", "Scenario"]
    )
    cdr_subvs_baseline = (cdr_subvs * 0).droplevel("Scenario")
    cdr_subvs_baseline["Scenario"] = "baseline"
    cdr_subvs_baseline = cdr_subvs_baseline.reset_index().set_index(
        ["Region", "Sector", "Metric", "Scenario"]
    )
    cdr_subvs = cdr_subvs.append(cdr_subvs_baseline)


cdr_fill = cdr_subvs.loc[:, 2011:2030] * 0
cdr_fill.columns = np.arange(1990, 2010, 1)
cdr = cdr_fill.join(cdr_subvs)

# check if energy oversupply is at least energy demand needed for CDR
"""
if (
    sum(
        elec_consump_cdr_pathway,
        heat_consump_cdr_pathway,
    )
    > cdr_energy_pathway
):
    print("Electricity oversupply does not meet CDR energy demand for pathway Scenario")
"""
# endregion

###########
# CLIMATE #
###########

# region

conc_baseline, temp_baseline, sea_lvl_baseline = climate(
    "baseline", "podi/data/climate.csv"
)
conc_pathway, temp_pathway, sea_lvl_pathway = climate(
    "pathway", "podi/data/climate.csv"
)

# endregion

####################
# RESULTS ANALYSIS #
####################

# region

adoption_curves = []
sadoption_curves = []
for j in ["baseline", "pathway"]:
    for i in range(0, len(region_list)):
        adoption_curves = pd.DataFrame(adoption_curves).append(
            results_analysis(
                region_list[i],
                j,
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
                data_start_year,
                data_end_year,
            )[0].replace(np.nan, 0)
        )

        sadoption_curves = pd.DataFrame(sadoption_curves).append(
            results_analysis(
                region_list[i],
                j,
                energy_demand,
                elec_consump,
                elec_per_adoption,
                heat_consump,
                heat_per_adoption,
                transport_consump,
                transport_per_adoption,
                afolu_per_adoption,
                cdr_subvs,
                em,
                em_mitigated,
                data_start_year,
                data_end_year,
            )[1].replace(np.nan, 0)
        )


# endregion

########
# NDCS #
########

# region

em_mit_ndc = []

for i in range(0, len(region_list)):
    if region_list[i] in [
        "World ",
        "US ",
        "EUR ",
        "SAFR ",
        "RUS ",
        "JPN ",
        "CHINA ",
        "BRAZIL ",
        "INDIA ",
    ]:
        em_ndc = (
            pd.read_csv("podi/data/emissions_ndcs.csv")
            .set_index(["Region"])
            .loc[region_list[i]]
        )

        em_ndc = pd.DataFrame(
            (
                em_baseline.loc[region_list[i]].sum().loc[[2025, 2030, 2050]] / 1000
            ).values
            - (em_ndc).values
        ).rename(index={0: 2025, 1: 2030, 2: 2050}, columns={0: "em_mit"})

        em_ndc["Region"] = region_list[i]
    else:
        em_ndc = []

    em_mit_ndc = pd.DataFrame(em_mit_ndc).append(em_ndc)

# endregion
