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

PROJECT_SIZE = 1  # MtCO2/yr

DISCOUNT_RATE = 0.07  # assumed for CDR

KWH_PER_GJ = 277.8  # kWh/GJ

ELEC_COST = 0.0966  # $/kWh for electricity

HEAT_COST = 5.385 / KWH_PER_GJ  # $/kWh for natural gas

TRANSPORT_COST = 0.05  # $/t*km

FUEL_COST = 0.179  # $/kWh for fuel

# TODO replace 0.263 (kWh/t*km) with actual transportation energy intensity for the current year
TRANSPORT_KWH_PER_TKM = 0.263  # kWh/(t*km) for transportation mix

###################
#  DAC constants  #
###################

DAC_FIRST_YEAR = 2025

LTSSDAC_FIRST_DEPLOYMENT = HTLSDAC_FIRST_DEPLOYMENT = 1

LTSSDAC_UTILIZATION = HTLSDAC_UTILIZATION = 0.9  # assume 90% utilization

#################################
# Enhanced weathering constants #
#################################

A_WARM = 5.128 * (10 ** 6)  # km2, total available warm ag area
A_TEMP = 2.774 * (10 ** 6)  # km2, total available temperate ag area

SPREADING_DENSITY = 15000  # t rock/km2 ag land (M)

CO2_PER_ROCK = 0.3  # tCO2/t rock for basalt (P)

GRAIN_SIZE = 20  # micrometers in diameter


#########################
# CO2 storage constants #
#########################

AIR_T = 288.15       # K, for compression
AIR_P = 0.101325     # MPa, for compression

WELLHEAD_T = 313.15  # K, for compression
HTLSDAC_T = 318.15   # K, for compression

COMPRESS_EFF = 0.8  # isoentropic efficiency

PIPELINE_LENGTH = 100  # mi
PIPELINE_CAPACITY = 10 * (10 ** 6)  # tCO2/yr

PIPELINE_COST = 0.0234 * PIPELINE_LENGTH  # $/tCO2

PIPELINE_LEAKAGE = 3.74  # tCO2/mi*yr

WELL_CAPACITY = 7300  # tCO2/yr

INJECTION_COST = 9.91  # $/tCO2

RESERVOIR_LEAKAGE_RATE = 0.0001  # 0.01%/yr


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


def crf(n_yrs, d=DISCOUNT_RATE) -> float:
    """Calculates the capital recovery factor given a discount rate and lifetime"""
    return (d * (1 + d) ** n_yrs) / ((1 + d) ** n_yrs - 1)


#################################
# Custom classes and exceptions #
#################################

class StrategyNotAvailableError(Exception):
    pass


class StrategyNotImplementedError(Exception):
    pass


class NotEnoughCDRError(Exception):
    pass


class PQEntry:
    """ For bundling capture/storage class priority queue entries """
    def __init__(self, capture_class, storage_class, storage_params):
        self.storage_class = storage_class
        self.capture_class = capture_class
        self.storage_params = storage_params
