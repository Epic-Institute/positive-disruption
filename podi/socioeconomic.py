#!/usr/bin/env python

import pandas as pd


def socioeconomic(data_source):
    socioeconomic = pd.read_csv(data_source).fillna(0)

    return socioeconomic
