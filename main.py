#!/usr/bin/env python

# region

from podi.energy_demand import energy_demand, data_start_year
from podi.energy_supply import energy_supply, long_proj_end_year
from podi.afolu import afolu
from podi.emissions import emissions
from podi.results_analysis import results_analysis
import podi.data.iea_weo_etl
import podi.data.iea_weo_em_etl
import podi.data.gcam_etl
import pandas as pd

from podi.cdr.cdr_util import (
    cdr_needed_def,
    grid_em_def,
    heat_em_def,
    transport_em_def,
    fuel_em_def,
)
from podi.cdr.cdr_main import cdr_mix
from podi.curve_smooth import curve_smooth
from podi.climate import climate
import time
import numpy as np
from podi.adoption_curve import adoption_curve
from podi.energy_demand_hist import energy_demand_hist
from numpy import NaN

pd.set_option("mode.use_inf_as_na", True)
start_time = time.monotonic()

region_list = pd.read_csv("podi/data/region_list.csv", header=None, squeeze=True)
# region_list = ["World "]

# endregion

#################
# ENERGY DEMAND #
#################

# region

podi.data.gcam_etl
podi.data.iea_weo_etl

energy_demand_baseline = energy_demand(
    "baseline",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/rs_energy_efficiency.csv",
    "podi/data/rs_heat_pumps.csv",
    "podi/data/rs_solar_thermal.csv",
    "podi/data/rs_trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand_pathway = energy_demand(
    "pathway",
    "podi/data/energy_demand_historical.csv",
    "podi/data/energy_demand_projection.csv",
    "podi/data/rs_energy_efficiency.csv",
    "podi/data/rs_heat_pumps.csv",
    "podi/data/rs_solar_thermal.csv",
    "podi/data/rs_trans_grid.csv",
    "podi/data/cdr_energy.csv",
)

energy_demand = energy_demand_baseline.append(energy_demand_pathway)

# Toggle for energy hist data further than 2010
energy_demand_hist2 = energy_demand_hist(energy_demand_baseline)
energy_demand = energy_demand_hist2.join(energy_demand.loc[:, 2019:]).replace(NaN, 0)

# endregion

#################
# ENERGY SUPPLY #
#################

# region
params = pd.read_csv("podi/data/params.csv")
params.drop(params.index, inplace=True)
params.to_csv("podi/data/params.csv", index=False)

(
    elec_consump_baseline,
    elec_per_adoption_baseline,
    elec_consump_cdr_baseline,
    heat_consump_baseline,
    heat_per_adoption_baseline,
    heat_consump_cdr_baseline,
    transport_consump_baseline,
    transport_per_adoption_baseline,
    transport_consump_cdr_baseline,
) = energy_supply(
    "baseline",
    energy_demand.loc[slice(None), slice(None), slice(None), ["baseline"]],
    region_list,
)

(
    elec_consump_pathway,
    elec_per_adoption_pathway,
    elec_consump_cdr_pathway,
    heat_consump_pathway,
    heat_per_adoption_pathway,
    heat_consump_cdr_pathway,
    transport_consump_pathway,
    transport_per_adoption_pathway,
    transport_consump_cdr_pathway,
) = energy_supply(
    "pathway",
    energy_demand.loc[slice(None), slice(None), slice(None), ["pathway"]],
    region_list,
)

elec_consump = elec_consump_baseline.append(elec_consump_pathway)
elec_per_adoption = elec_per_adoption_baseline.append(elec_per_adoption_pathway)
heat_consump = heat_consump_baseline.append(heat_consump_pathway)
heat_per_adoption = heat_per_adoption_baseline.append(heat_per_adoption_pathway)
transport_consump = transport_consump_baseline.append(transport_consump_pathway)
transport_per_adoption = transport_per_adoption_baseline.append(
    transport_per_adoption_pathway
)

# endregion

#########
# AFOLU #
#########

# region

afolu_em_baseline, afolu_per_adoption_baseline, afolu_per_max_baseline = afolu(
    "baseline"
)

afolu_em_pathway, afolu_per_adoption_pathway, afolu_per_max_pathway = afolu("pathway")

afolu_em = afolu_em_baseline.append(afolu_em_pathway)

afolu_per_adoption = afolu_per_adoption_baseline.append(afolu_per_adoption_pathway)

afolu_per_max = afolu_per_max_baseline.append(afolu_per_max_pathway)

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
        long_proj_end_year,
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
