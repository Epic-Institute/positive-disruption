#!/usr/bin/env python

import pandas as pd

tech_parameters = pd.read_csv("podi/data/tech_parameters (copy).csv").dropna()

oecd_group = (
    "NAM ",
    "US ",
    "EUR ",
    "EU ",
    "SAFR ",
    "JPN ",
    "AdvancedECO ",
)
non_group = (
    "World ",
    "CSAM ",
    "BRAZIL ",
    "AFRICA ",
    "ME ",
    "EURASIA ",
    "RUS ",
    "ASIAPAC ",
    "CHINA ",
    "INDIA ",
    "ASEAN ",
    "DevelopingECO ",
)

oecd_params = tech_parameters[tech_parameters["IEA Region"] == " OECD "]
non_params = tech_parameters[tech_parameters["IEA Region"] == "NonOECD "]

for i in range(0, len(oecd_group)):
    oecd_params = oecd_params.append(
        oecd_params[oecd_params["IEA Region"] == " OECD "].replace(
            " OECD ", oecd_group[i]
        )
    )

for i in range(0, len(non_group)):
    non_params = non_params.append(
        non_params[non_params["IEA Region"] == "NonOECD "].replace(
            "NonOECD ", non_group[i]
        )
    )

params = oecd_params.append(non_params)

params.to_csv("podi/data/tech_parameters.csv", index=False)
