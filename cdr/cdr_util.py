#!/usr/bin/env python3
"""
cdr_util.py
Defines and exports constants and utility functions
used in the cdr optimization module.
"""

__author__ = "Zach Birnholz"
__version__ = "07.23.20"

import math

DEBUG_MODE = False  # True suppresses adoption limitations

####################
# Global constants #
####################

START_YEAR = 2020
END_YEAR = 2100

DISCOUNT_RATE = 0.07  # assumed for CDR

ELEC_COST = 0.0966  # $/kWh for electricity

HEAT_COST = 5.385  # $/GJ for natural gas

FUEL_COST = 0.179  # $/kWh for fuel

TRANSPORT_COST = 0.05  # $/t*km

KWH_PER_GJ = 277.8  # kWh/GJ

###################
#  DAC constants  #
###################

DAC_FIRST_YEAR = 2025
LTSSDAC_FIRST_DEPLOYMENT = HTLSDAC_FIRST_DEPLOYMENT = 1


#################################
# Enhanced weathering constants #
#################################

A_WARM = 5.128 * (10 ** 6)  # km2, total available warm ag area
A_TEMP = 2.774 * (10 ** 6)  # km2, total available temperate ag area

SPREADING_DENSITY = 15000  # t rock/km2 ag land (M)

CO2_PER_ROCK = 0.3  # tCO2/t rock for basalt (P)

GRAIN_SIZE = 20  # micrometers in diameter


#####################
# Utility functions #
#####################

def logistic_inverse_slope(M: float, a: float, b: float, cumul_adopt: int) -> float:
    """Annual adoption limit for logistic function"""
    return b * (cumul_adopt - cumul_adopt**2 / M)


def learning(cumul_deploy: int, init_deploy: float, LR: float) -> float:
    """Returns the fractional amount (for cost, energy use, etc.) remaining
    after one-factor learning for the given cumulative deployment"""
    return (1 - LR) ** (math.log2(cumul_deploy / init_deploy))


def crf(d, n_yrs) -> float:
    """Calculates the capital recovery factor given a discount rate and lifetime"""
    return (d * (1 + d) ** n_yrs) / ((1 + d) ** n_yrs - 1)


#####################
# Custom exceptions #
#####################

class StrategyNotAvailableError(Exception):
    pass


class StrategyNotImplementedError(Exception):
    pass
