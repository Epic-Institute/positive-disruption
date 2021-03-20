#!/usr/bin/env python

import pandas as pd
from podi.adoption_curve import adoption_curve
from numpy import NaN
import numpy as np


def afolu(scenario):
    afolu = pd.read_excel(
        "podi/data/Positive Disruption NCS Vectors.xlsx",
        sheet_name=[
            "Input data 3",
            "Avoided pathways input",
            "Historical Observations",
            "Pathway - analog crosswalk",
            "Analogs",
        ],
    )

    # max extent

    # region

    max_extent = afolu["Input data 3"][
        afolu["Input data 3"]["Metric"] == "Max extent"
    ].drop(columns=["Metric", "Model", "Scenario", "Region", "Country", "Unit"])

    max_extent["Duration 1 (Years)"] = np.where(
        (
            (max_extent["Duration 1 (Years)"].isna())
            | (max_extent["Duration 1 (Years)"] > 2100 - 2019)
        ),
        2100 - 2019,
        max_extent["Duration 1 (Years)"],
    )

    max_extent["Value 2"] = np.where(
        max_extent["Value 2"].isna(), max_extent["Value 1"], max_extent["Value 2"]
    )

    max_extent["Duration 2 (Years)"] = np.where(
        (max_extent["Duration 2 (Years)"].isna()),
        max_extent["Duration 1 (Years)"],
        max_extent["Duration 2 (Years)"],
    )

    max_extent["Value 3"] = np.where(
        max_extent["Value 3"].isna(), max_extent["Value 2"], max_extent["Value 3"]
    )

    max_extent["Duration 3 (Years)"] = np.where(
        max_extent["Duration 3 (Years)"].isna(),
        max_extent["Duration 2 (Years)"],
        max_extent["Duration 3 (Years)"],
    )

    max_extent2 = pd.DataFrame(
        index=[
            max_extent["iso"],
            max_extent["Subvector"],
            max_extent["Duration 1 (Years)"],
            max_extent["Value 2"],
            max_extent["Duration 2 (Years)"],
        ],
        columns=np.arange(data_end_year, long_proj_end_year + 1, 1),
        dtype=float,
    )
    max_extent2.loc[:, 2019] = max_extent["Value 1"].values
    max_extent2.loc[:, 2100] = max_extent["Value 1"].values
    max_extent2.interpolate(axis=1, limit_area="inside", inplace=True)

    """
    max_extent2 = max_extent2.apply(
        lambda x: x[int(data_end_year + x.name[2])] = (max_extent["Value 2"]), axis=1)
    """
    # endregion

    # avg mitigation potential flux

    # region

    flux = afolu["Input data 3"][
        afolu["Input data 3"]["Metric"] == "Avg mitigation potential flux"
    ].drop(columns=["Metric", "Model", "Scenario", "Region", "Country", "Unit"])

    flux["Duration 1 (Years)"] = np.where(
        (
            (flux["Duration 1 (Years)"].isna())
            | (flux["Duration 1 (Years)"] > 2100 - 2019)
        ),
        2100 - 2019,
        flux["Duration 1 (Years)"],
    )

    flux["Value 2"] = np.where(flux["Value 2"].isna(), flux["Value 1"], flux["Value 2"])

    flux["Duration 2 (Years)"] = np.where(
        (flux["Duration 2 (Years)"].isna()),
        flux["Duration 1 (Years)"],
        flux["Duration 2 (Years)"],
    )

    flux["Value 3"] = np.where(flux["Value 3"].isna(), flux["Value 2"], flux["Value 3"])

    flux["Duration 3 (Years)"] = np.where(
        flux["Duration 3 (Years)"].isna(),
        flux["Duration 2 (Years)"],
        flux["Duration 3 (Years)"],
    )

    flux2 = pd.DataFrame(
        index=[
            flux["iso"],
            flux["Subvector"],
            flux["Duration 1 (Years)"],
            flux["Value 2"],
            flux["Duration 2 (Years)"],
        ],
        columns=np.arange(data_end_year, long_proj_end_year + 1, 1),
        dtype=float,
    )
    flux2.loc[:, 2019] = flux["Value 1"].values
    flux2.loc[:, 2100] = flux["Value 1"].values
    flux2.interpolate(axis=1, limit_area="inside", inplace=True)

    """
    flux2 = flux2.apply(
        lambda x: x[int(data_end_year + x.name[2])] = (flux["Value 2"]), axis=1)
    """
    # endregion

    # avoided pathways

    # region

    avoid = afolu["Avoided pathways input"].drop(
        columns=["Model", "Scenario", "Region"]
    )

    avoid["Mitigation (CO2)"] = (
        avoid["Initial Extent (Mha)"].values
        * avoid["Rate of Improvement"].values
        * avoid["Mitigation (Mg CO2/ha)"].values
    )

    avoid2 = pd.DataFrame(
        index=[
            avoid["Country"],
            avoid["Subvector"],
            avoid["Initial Extent (Mha)"],
            avoid["Initial Loss Rate (%)"],
            avoid["Rate of Improvement"],
            avoid["Mitigation (Mg CO2/ha)"],
        ],
        columns=np.arange(data_end_year, long_proj_end_year + 1, 1),
        dtype=float,
    ).fillna(0)

    avoid2 = avoid2.apply(
        lambda x: x
        + x.name[5]
        * x.name[2]
        * (1 + min((x.name[3] + x.name[4] * (x.index - 2018)), 0)),
        axis=1,
    )

    # endregion

    afolu["Historical Observations"]

    cw = afolu["Pathway - analog crosswalk"][["Sub-vector", "Analog Name"]]

    acurves = (
        pd.DataFrame(afolu["Analogs"])
        .drop(columns=["Note", "Units", "Actual start year"])
        .set_index(["Analog name", "Max (Mha)"])
    )
    acurves.columns = acurves.loc[NaN, NaN].astype(int)
    acurves.columns.rename("Year", inplace=True)
    acurves.drop(index=NaN, inplace=True)
    acurves.interpolate(axis=1, limit_area="inside", inplace=True)
    acurves = acurves.apply(lambda x: x / x.name[1], axis=1)
    acurves = acurves.apply(lambda x: x - x[1], axis=1)
    acurves.columns = np.arange(2020, 2064, 1)
    acurves.columns = np.arange(2020, 2064, 1)

    # Compute adoption curves of historical analogs
    proj_per_adoption = acurves.apply(
        lambda x: adoption_curve(
            x.dropna().rename(x.name[0]),
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

    per = per.apply(lambda x: x - x[2020], axis=1)
    per = per.apply(lambda x: x / x[2100], axis=1)

    # project adoption by applying s-curve growth to max extent
    max_extent = pd.DataFrame(
        afolu.loc[afolu["Metric"].str.contains("Max extent", na=False)]
        .set_index(["Region", "Sector", "Metric", "Unit", "Scenario"])
        .loc[:, per.columns.values.astype(str)]
        .loc[slice(None), slice(None), slice(None), slice(None), scenario]
        .droplevel(["Metric", "Unit"])
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
        .loc[slice(None), slice(None), slice(None), slice(None), scenario]
    )
    avg_flux.columns = avg_flux.columns.astype(int)

    proj_adoption = proj_adoption * avg_flux

    afolu_adoption = proj_adoption
    afolu_per_adoption = per

    afolu_adoption = pd.concat(
        [afolu_adoption.droplevel(level=2)],
        keys=["Emissions"],
        names=["Metric"],
    ).reorder_levels(["Region", "Sector", "Metric", "Unit"])

    afolu_adoption.columns = afolu_adoption.columns.astype(int)
    afolu_per_adoption.columns = afolu_per_adoption.columns.astype(int)

    return afolu_adoption, afolu_per_adoption
