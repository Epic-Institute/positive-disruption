#!/usr/bin/env python

import pandas as pd


def afolu(data_source):
    afolu = pd.read_csv(data_source).fillna(0)

    return afolu
