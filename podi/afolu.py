#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve


def afolu(scenario):
    afolu = pd.read_csv("podi/data/afolu_input.csv")

    # get parameters from historical analogy adoption and compute adoption curve
    proj_per_adoption = (
        (
            pd.DataFrame(
                afolu.loc[
                    afolu["Metric"].str.contains(
                        "Historical analogy adoption", na=False
                    )
                ]
            )
            .set_index(["Region", "Sector", "Metric", "Unit", "Scenario"])
            .astype(float)
            .apply(pd.DataFrame.pct_change, axis=1)
            .droplevel(["Metric", "Unit"])
        )
        .fillna(0)
        .loc[["OECD ", "NonOECD "], slice(None), scenario]
        .droplevel(["Scenario"])
    )

    proj_per_adoption.columns = proj_per_adoption.columns.astype(int)

    proj_per_adoption = proj_per_adoption.apply(
        lambda x: adoption_curve(
            x.drop(columns=["Region"]).rename(x.name[1]),
            x.name[0],
            scenario,
            "AFOLU",
        ),
        axis=1,
    )

    per = []
    for i in range(0, len(proj_per_adoption.index)):
        per = pd.DataFrame(per).append(proj_per_adoption[proj_per_adoption.index[i]].T)

    per.set_index(proj_per_adoption.index, inplace=True)

    # project adoption by applying s-curve growth to max extent
    max_extent = pd.DataFrame(
        afolu.loc[afolu["Metric"].str.contains("Max extent", na=False)]
        .set_index(["Region", "Sector", "Metric", "Unit", "Scenario"])
        .loc[:, per.columns.values.astype(str)]
        .loc[["OECD ", "NonOECD "], slice(None), slice(None), slice(None), scenario]
        .droplevel(["Metric", "Unit", "Scenario"])
    )
    max_extent.columns = max_extent.columns.astype(int)

    proj_adoption = per * max_extent

    # multiply by avg mitigation potential flux to get emissions mitigated
    avg_flux = pd.DataFrame(
        afolu.loc[
            afolu["Metric"].str.contains("Avg mitigation potential flux", na=False)
        ]
        .set_index(["Region", "Sector", "Metric", "Unit", "Scenario"])
        .loc[:, per.columns.values.astype(str)]
        .loc[["OECD ", "NonOECD "], slice(None), slice(None), slice(None), scenario]
        .droplevel(["Scenario"])
    )
    avg_flux.columns = avg_flux.columns.astype(int)

    proj_adoption = proj_adoption * avg_flux

    afolu_adoption = proj_adoption
    afolu_per_adoption = per

    if scenario == "Baseline":
        afolu_adoption = afolu = pd.read_csv(
            "podi/data/afolu_input_baseline.csv"
        ).set_index(["Region", "Sector", "Metric", "Unit"])

    return afolu_adoption, afolu_per_adoption
