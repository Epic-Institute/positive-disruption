#!/usr/bin/env python

import pandas as pd

atlas = pd.read_excel("podi/data/NCS Atlas country list.xlsx", usecols=[0])

afolu = pd.read_csv("podi/data/afolu_tnc_input.csv")

final = []

for i in range(0, len(atlas)):
    afolu["Region"] = atlas.loc[i].values[0]
    final = pd.DataFrame(final).append(afolu)

final.to_csv("final.csv", index=False)
