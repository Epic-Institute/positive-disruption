#!/usr/bin/env python3
"""
cdr_main.py
Main file for CDR module. The CDR module implements a methodology to estimate
cost-efficient mixes of CDR strategies as a function of carbon price levels
and timing, from present through 2100. Strategies include natural climate
solutions (NCS) and engineered carbon dioxide removal (ECR).

Implements this methodology using a greedy algorithm to approximate a solution
to the knapsack problem of meeting a certain CDR target in each year at the
lowest cost. This algorithm is greedy in the sense that it seeks to achieve
the lowest cost in the current year, without regard for the consequences to
cost in future years. This decision was made to reflect the short-term mindset
that is likely to prevail in the policy decision-making and market forces
surrounding CDR implementation.

CDR folder directory:
cdr_main.py (this file) - optimization framework, main public interface; exports the
                          cdr_mix function, which performs the task outlined above
cdr_util.py - defines constants and utility functions used throughout the module
cdr_abstract_types.py - defines the inheritance hierarchy for CDR project objects
cdr_types.py - implements behavior of specific CDR strategies (concrete subclasses
               of abstract CDR parent classes)
"""

import cdr.cdr_util as util
import cdr.cdr_types as types

__author__ = "Zach Birnholz"
__version__ = "07.23.20"


"""
Stores all CDR approaches available for use in this module.
Add other approaches here as ecr (engineered) or ncs (natural),
supply the technology name and the name of their cost/adoption/
energy use/incidental emissions functions here. Implement those
functions below the (TODO - come up with a marker) line at the bottom of the file.
Comment out a technology from the list to temporarily remove it from consideration.
"""
CDR_TECHS = [
    types.ExSituEW,
    types.LTSSDAC,
    types.HTLSDAC,
]


#####################################
#  Primary public-facing functions  #
#####################################

def cdr_mix(cdr_reqs: list, grid_em: list, heat_em: list, transport_em: list, fuel_em: list,
            start: int = util.START_YEAR, end: int = util.END_YEAR) -> tuple:
    """
    Main exported function of the module. Generates a nearly cost-optimal mix
    of CDR technologies to meet the required yearly CDR targets, optimized for
    choosing the currently cheapest available mix in each progressive year.

    :param cdr_reqs: timeseries of CDR targets to be met in each year (MtCO2/yr), from start to end years
    :param grid_em: timeseries of grid electricity carbon intensity (tCO2/kWh), from start to end years
    :param transport_em: timeseries of heat source carbon intensity (tCO2/t*km), from start to end years
    :param transport_em: timeseries of transportation carbon intensity (tCO2/t*km), from start to end years
    :param fuel_em: timeseries of liquid fuel carbon intensity (tCO2/kWh), from start to end years
    :param start: the first year to compute the CDR mix for
    :param end: the last year (inclusive) to compute the CDR mix for
    :return: approximately cost-optimal mix of CDR strategies, as a tuple containing:
        0. annual CDR quantity by technology (list of dict, MtCO2/yr split by technology),
        1. annual cost (list of float, $/yr),
        2. annual energy requirement (list of tuple of float, kWh/yr split into sectors)
    """
    cumul_deploy = {tech: 0 for tech in CDR_TECHS}
    tech_mix = []
    cost = []
    energy = []
    projects = set()

    # 1. greedily compute locally optimal CDR mix to cover first year
    _advance_cdr_mix(tech_mix, cost, energy, cdr_reqs[0], cumul_deploy, grid_em, transport_em)

    for y in range(1, end - start + 1):
        # 2. determine additional CDR needed for next year, incl. retiring old projects
        # age and retire projects
        retiring_capacity = _age_and_retire_projects(projects)
        existing_cdr = cdr_reqs[y - 1] - retiring_capacity

        # compute additional CDR still needed
        addl_cdr = cdr_reqs[y] - existing_cdr

        # 3. greedily compute locally optimal CDR mix to cover addl CDR required in this year
        _advance_cdr_mix(tech_mix, cost, energy, addl_cdr, cumul_deploy, grid_em, transport_em)
    return tech_mix, cost, energy


def cdr_credit(year_num: int) -> float:
    """
    Returns the credit price or tax credit for CDR in a given year ($/tCO2)
    :param year_num: zero-indexed year number, where 0 represents START_YEAR
    :return: $/tCO2 credit price in specific year
    """
    # assume initial price of $50/tCO2 (based on 45Q tax credit)
    # and a 5% per year increase
    return 50 * (1.05 ** year_num)


##################################
#  Helper functions for cdr_mix  #
##################################

def _advance_cdr_mix(tech_mix, cost, energy, addl_cdr, cumul_deploy, grid_em, heat_em, transport_em, fuel_em):
    """
    Greedily computes locally optimal CDR mix to cover additional CDR required.
    Meets the CDR requirement by deploying the cheapest technology until that
    technology reaches its annual deployment limit or until it is no longer the
    cheapest technology.
    Modifies tech_mix, cost, and energy parameters.
    """
    mtco2_deployed = 0
    while mtco2_deployed < addl_cdr:
        mtco2_deployed += 1
        # TODO - implement this priority queue game as described above
        pass


def _age_and_retire_projects(projects):
    """ Removes old projects from the provided projects set.
    Returns the capacity of CDR that was retired. """
    retiring_projects = set()
    retiring_capacity = 0

    for proj in projects:
        proj.advance_age()
        if proj.should_be_retired():
            retiring_capacity += proj.capacity  # no longer part of CDR fleet
            retiring_projects.add(proj)

    projects -= retiring_projects
    return retiring_capacity
