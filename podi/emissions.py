#!/usr/bin/env python

import pandas as pd

emissions_factors = pd.read_excel("data/emissions_factors.xlsx")

energy_supply = pd.read_csv("data/energy_supply.csv")

additional_emissions = pd.read_excel("data/additional_emissions.xlsx")

energy_supply_emitters = "filter to coal, oil, gas, alternative fuels"

emissions = energy_supply_emitters.mul(
    emissions_factors[emissions_factors.Value].loc[:, 2018:]
)

cement_emissions = additional_emissions[additional_emissions.source == "cement"]

emissions = emissions.append(additional_emissions.Cement)
