#!/usr/bin/env python

# Takes tech_parameters.csv with values for one region, and extends it to multiple regions listed in Regions.txt

import pandas as pd

tech_parameters = pd.read_csv("podi/data/tech_parameters.csv")
regions = (
    pd.read_fwf("podi/data/IEA/Regions.txt")
    .rename(columns={"REGION": "Region"})
    .squeeze()
).str.lower()


for region in regions:
    tech_parameters2 = tech_parameters.replace("world", region)
    tech_parameters2.to_csv(
        "podi/data/tech_parameters.csv", mode="a", header=False, index=False
    )
