#!/usr/bin/env python3
"""
cdr_util.py
Defines and exports constants and utility functions
used in the cdr optimization module.
"""

__author__ = "Zach Birnholz"
__version__ = "08.10.20"

from functools import wraps
import math

import numpy as np

# Setting the ACCEPT_DEFICIT flag to True deploys a catch-all "deficit" CDRStrategy
# to account for a CDR deficit in a year rather than throwing a NotEnoughCDRError.
ACCEPT_DEFICIT = True

####################
# Global constants #
####################

START_YEAR = 2020
END_YEAR = 2100

PROJECT_SIZE = 1  # MtCO2/yr

DISCOUNT_RATE = 0.05  # assumed for CDR

KWH_PER_GJ = 277.8  # kWh/GJ

ELEC_COST = 0.0966  # $/kWh for electricity

HEAT_COST = 5.385 / KWH_PER_GJ  # $/kWh for natural gas

TRANSPORT_COST = 0.05  # $/t*km

FUEL_COST = 0.179  # $/kWh for fuel


####################################
# Default cdr_mix input parameters #
####################################

"""
Default MtCO2/yr of CDR needed, from Epic PD21 model.
"""
cdr_needed_def = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    10,
    50,
    100,
    150,
    200,
    250,
    300,
    348,
    386,
    428,
    475,
    527,
    584,
    647,
    717,
    794,
    879,
    973,
    1076,
    1189,
    1314,
    1450,
    1600,
    1763,
    1942,
    2136,
    2347,
    2576,
    2824,
    3092,
    3379,
    3688,
    4018,
    4370,
    4744,
    5138,
    5554,
    5990,
    6445,
    6917,
    7405,
    7907,
    8420,
    8941,
    9468,
    9999,
    10529,
    11057,
    11578,
    12091,
    12593,
    13081,
    13553,
    14008,
    14444,
    14860,
    15255,
    15628,
    15980,
    16310,
    16619,
    16907,
    17175,
    17423,
    17652,
    17863,
    18057,
    18236,
    18399,
]

"""
Default MtCO2/TWh emissions of grid electricity, from Epic PD21 model.
"""
GRID_EM_DEF = [
    0.357,
    0.354,
    0.352,
    0.350,
    0.348,
    0.346,
    0.344,
    0.342,
    0.340,
    0.338,
    0.336,
    0.334,
    0.332,
    0.329,
    0.327,
    0.325,
    0.323,
    0.321,
    0.319,
    0.317,
    0.315,
    0.313,
    0.311,
    0.309,
    0.307,
    0.305,
    0.302,
    0.300,
    0.298,
    0.296,
    0.294,
    0.292,
    0.290,
    0.288,
    0.286,
    0.284,
    0.282,
    0.280,
    0.278,
    0.275,
    0.273,
    0.271,
    0.269,
    0.267,
    0.265,
    0.263,
    0.261,
    0.259,
    0.257,
    0.255,
    0.253,
    0.250,
    0.248,
    0.246,
    0.244,
    0.242,
    0.240,
    0.238,
    0.236,
    0.234,
    0.232,
    0.230,
    0.228,
    0.226,
    0.223,
    0.221,
    0.219,
    0.217,
    0.215,
    0.213,
    0.211,
    0.209,
    0.207,
    0.205,
    0.203,
    0.201,
    0.198,
    0.196,
    0.194,
    0.192,
    0.190,
]

"""
Default tCO2/t*km for transport emissions intensity, based on the below transport mode split
and assumed to decline linearly towards 0 by 2100,
from https://www.epa.gov/sites/production/files/2018-03/documents/emission-factors_mar_2018_0.pdf
where it is given in kg/short ton-mile.
Used here in tCO2/t*km (using 1/(1000 * 1.46) conversion factor).
"""
# Assumed 30.7:10.5:2.4 trucking:shipping:rail mix
# based on relative global energy use of freight transport modes,
# from https://www.eia.gov/outlooks/aeo/data/browser/#/?id=51-IEO2019
TRUCKING_RAT, SHIPPING_RAT, RAIL_RAT = 30.7, 10.5, 2.4

TRANSPORT_EM_DEF = [
    np.average([0.202, 0.059, 0.023], weights=[TRUCKING_RAT, SHIPPING_RAT, RAIL_RAT])
    / (1000 * 1.46)
    * (END_YEAR - t)
    / (END_YEAR - START_YEAR)
    for t in range(START_YEAR, END_YEAR + 1)
]

# kWh/(t*km) for transportation mix, formerly simply set to 0.263.
# Individual transport mode energy intensities from Renforth (2012).
TRANSPORT_KWH_PER_TKM = np.average(
    [0.365, 0.06, 0.058], weights=[TRUCKING_RAT, SHIPPING_RAT, RAIL_RAT]
)

"""
Default tCO2/MWh for heat production, assumed to decline linearly towards 0 by 2100,
from https://www.epa.gov/sites/production/files/2018-03/documents/emission-factors_mar_2018_0.pdf
where it is given as 66.33 kgCO2/mmBTU of heat & steam.
Used here in tCO2/MWh (using 1/(1000*0.2931) conversion factor).
"""
HEAT_EM_DEF = [
    0.226305 * (END_YEAR - t) / (END_YEAR - START_YEAR)
    for t in range(START_YEAR, END_YEAR + 1)
]

"""
Default tCO2/MWh for liquid fuels (assumed to be simply diesel), assumed to decline linearly towards 0 by 2100,
using 10.21 kgCO2/gal from https://www.epa.gov/sites/production/files/2018-03/documents/emission-factors_mar_2018_0.pdf
and 117,100 Btu/gal (net) for biodiesel from https://tedb.ornl.gov/wp-content/uploads/2020/02/TEDB_Ed_38.pdf#page=391
"""
FUEL_EM_DEF = [
    0.2975 * (END_YEAR - t) / (END_YEAR - START_YEAR)
    for t in range(START_YEAR, END_YEAR + 1)
]


###################
#  DAC constants  #
###################

DAC_FIRST_YEAR = 2025

LTSSDAC_FIRST_DEPLOYMENT = HTLSDAC_FIRST_DEPLOYMENT = 1

LTSSDAC_UTILIZATION = HTLSDAC_UTILIZATION = 0.9  # assume 90% utilization

MAX_LTSSDAC = 23500  # MtCO2/yr deployment

MAX_HTLSDAC = 11500  # MtCO2/yr deployment

#################################
# Enhanced weathering constants #
#################################

A_WARM = 5.128 * (10 ** 6)  # km2, total available warm ag area
A_TEMP = 2.774 * (10 ** 6)  # km2, total available temperate ag area

SPREADING_DENSITY = 15000  # t rock/km2 ag land (M)

CO2_PER_ROCK = 0.3  # tCO2/t rock for basalt (P)

GRAIN_SIZE = 20  # micrometers in diameter

MAX_EX_SITU_EW = 4500  # MtCO2/yr deployment


#########################
# CO2 storage constants #
#########################

AIR_T = 288.15  # K, for compression
AIR_P = 0.101325  # MPa, for compression

WELLHEAD_T = 313.15  # K, for compression
HTLSDAC_T = 318.15  # K, for compression

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
    return b * (cumul_adopt - cumul_adopt ** 2 / M)


def learning(
    cumul_deploy: int, init_deploy: float, LR: float, floor: float = 0.0
) -> float:
    """Returns the fractional amount (for cost, energy use, etc.) remaining
    after one-factor learning for the given cumulative deployment"""
    return max(floor, (1 - LR) ** (math.log2(cumul_deploy / init_deploy)))


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


###################################################################
# Decorator for optimizing repeated function calls on CDR objects #
###################################################################


def once_per_year(f):
    """For expensive functions that will return the same value in each
    individual year and are unique to each CDRProject instance."""
    prev_info = dict()  # self --> (age, value) of last function call

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        # key is self pointer because we are caching results per CDR project
        if self in prev_info and self.age == prev_info[self][0]:
            # return cached value for repeated function call on this project at this age
            return prev_info[self][1]
        else:
            result = f(self, *args, **kwargs)
            prev_info[self] = (self.age, result)
            return result

    return wrapper


def cacheit(f):
    """For expensive functions that will return the same value every time
    but are unique to each CDRProject instance."""
    cache = dict()

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        # key is self pointer because we are caching results per CDR project
        if self in cache:
            return cache[self]
        else:
            result = f(self, *args, **kwargs)
            cache[self] = result
            return result

    return wrapper
