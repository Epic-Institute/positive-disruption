#!/usr/bin/env python

import pandas as pd
from numpy import NaN
from podi.curve_smooth import curve_smooth

iamc_data = pd.read_excel(
    "podi/data/iamc15_scenario_data_all_regions_r2.0.xlsx", engine="openpyxl"
).set_index(["Model", "Region", "Scenario", "Variable", "Unit"])


iamc_data = iamc_data.interpolate(axis=1).replace(NaN, 0)

"""
iamc_data = curve_smooth(iamc_data, "quadratic", 4)
"""

iamc_data.to_csv("podi/data/iamc_data.csv", index=True)
