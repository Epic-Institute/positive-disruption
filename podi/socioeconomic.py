#!/usr/bin/env python

import pandas as pd


def socioeconomic(scenario, data_source):
    socioeconomic = pd.read_csv(data_source).fillna(0)
    socioeconomic = socioeconomic[socioeconomic["Scenario"] == scenario]

    return socioeconomic
