#!/usr/bin/env python

import pandas as pd
from podi.data.iea_weo_etl import iea_region_list
import numpy
from podi.adoption_curve import adoption_curve


def afolu(scenario):
    afolu = pd.read_csv("podi/data/afolu_input.csv")

    # filter for scenario
    afolu = afolu.loc[afolu["Scenario"] == scenario]

    afolu = afolu.loc[afolu["Region"] == "World "]

    # get parameters from historical analogy adoption and compute adoption curve
    proj_per_adoption = (
        pd.DataFrame(
            afolu.loc[
                afolu["Variable"].str.contains("Historical analogy adoption", na=False)
            ]
        )
        .set_index(["Region", "Variable", "Unit", "Scenario"])
        .astype(float)
        .apply(pd.DataFrame.pct_change, axis=1)
        .droplevel(["Region", "Unit", "Scenario"])
    ).fillna(0)

    proj_per_adoption = proj_per_adoption.apply(
        adoption_curve, axis=1, args=([region, scenario])
    )

    per = []
    for i in range(0, len(proj_per_adoption.index)):
        per = pd.DataFrame(per).append(proj_per_adoption[proj_per_adoption.index[i]].T)

    per.set_index(proj_per_adoption.index, inplace=True)

    # project adoption by applying s-curve growth to observed adoption
    foo = pd.DataFrame(
        afolu.loc[afolu["Variable"].str.contains("Max extent")]
        .set_index(["Region", "Variable", "Unit", "Scenario"])
        .loc[:, per.columns.values.astype(str)]
    )

    foo.columns = foo.columns.astype(int)

    proj_per_adoption = per.apply(lambda x: x * foo, axis=1)[0]

    # multiply by avg mitigation potential flux to get emissions mitigated
    foo = pd.DataFrame(
        afolu.loc[afolu["Variable"].str.contains("Avg mitigation potential flux")]
        .set_index(["Region", "Variable", "Unit", "Scenario"])
        .loc[:, per.columns.values.astype(str)]
    )

    foo.columns = foo.columns.astype(int)

    proj_adoption = proj_per_adoption.apply(lambda x: x * foo, axis=1)[0]
    this = pd.DataFrame(
        pd.DataFrame(proj_per_adoption.index.levels[1]).apply(
            lambda x: x.str.split(pat="|", expand=True).values[0][-2], axis=1
        )
    )

    this2 = pd.DataFrame(
        pd.DataFrame(proj_adoption.index.levels[1]).apply(
            lambda x: x.str.split(pat="|", expand=True).values[0][1], axis=1
        )
    )

    this3 = pd.DataFrame(
        pd.DataFrame(proj_adoption.index.levels[1]).apply(
            lambda x: x.str.split(pat="|", expand=True).values[0][0], axis=1
        )
    )

    proj_adoption["Variable2"] = this.values
    proj_adoption.reset_index(inplace=True)
    proj_adoption.set_index(
        ["Region", "Variable", "Variable2", "Unit", "Scenario"], inplace=True
    )

    per.set_index(proj_adoption.index, inplace=True)

    afolu_adoption = proj_adoption.droplevel(["Scenario"])
    afolu_per_adoption = per.droplevel(["Scenario"])

    return afolu_adoption