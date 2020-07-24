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
import cdr.cdr_abstract_types as abstract_types
from collections import defaultdict
from queue import PriorityQueue, Empty
import itertools

__author__ = "Zach Birnholz"
__version__ = "07.23.20"

"""
Stores all CDR approaches available for use in this module.
Implement new CDR approaches in cdr_types.py and add them to this list.
If the capture type requires a paired CO2 storage project, add that pairing
to the STORAGE_PAIRINGS list below.
Comment out a technology from this list to temporarily remove it from consideration.
"""
CDR_TECHS = [
    types.ExSituEW,
    types.LTSSDAC,
    types.HTLSDAC,
]

"""
Describes the capture-storage relationship for capture technologies
that require separate storage. Mappings are:
capture type --> [(storage type, [storage init parameters])]
The storage project itself is always given as the first init parameter
and does not need to be specified here
"""
STORAGE_PAIRINGS = {
    types.LTSSDAC: [(types.GeologicStorage, [util.AIR_T, util.AIR_P])],
    types.HTLSDAC: [(types.GeologicStorage, [])],
}


#####################################
#  Primary public-facing functions  #
#####################################

def cdr_mix(cdr_reqs: list, grid_em: list, heat_em: list, transport_em: list, fuel_em: list,
            start: int = util.START_YEAR, end: int = util.END_YEAR) -> tuple:
    """
    Main exported function of the module. Generates a nearly cost-optimal mix
    of CDR technologies to meet the required yearly CDR targets, optimized for
    choosing the currently cheapest available mix in each progressive year.
    Please note the units assumed of each of the parameters.

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
    # 0. setup framework
    if start != util.START_YEAR:
        abstract_types.CDRStrategy.start_year = abstract_types.CDRStrategy.curr_year = start
        _reset_tech_adopt_limits()

    _setup_emissions_intensities(grid_em, heat_em, transport_em, fuel_em)

    tech_mix = []  # list of {tech --> deployment} in each year
    cost = []  # list of cost (float) in each year
    energy = []  # list of (elec, heat, transport, non-transport fuel) in each year

    # 1. greedily compute locally optimal CDR mix to cover first year
    projects = _advance_cdr_mix(cdr_reqs[0], start,
                                grid_em[0], heat_em[0], transport_em[0], fuel_em[0])
    # add as first year of CDR mix
    _add_next_year(projects, tech_mix, cost, energy)

    for y in range(1, end - start + 1):
        # 2. clean slate for each new year
        _reset_tech_adopt_limits()
        abstract_types.CDRStrategy.advance_year()

        # 3. determine additional CDR needed for next year, incl. retiring old projects
        # age and retire projects
        retirement = _age_and_retire_projects(projects)
        # account for CO2 leakage from geologic storage
        geologic_storage_leakage = 0
        for tech in tech_mix[-1]:
            if tech[1] is not None and tech[1].__class__ == types.GeologicStorage.__class__:
                geologic_storage_leakage += tech_mix[-1][tech] * util.RESERVOIR_LEAKAGE_RATE
        existing_cdr = cdr_reqs[y - 1] - sum(retirement.values()) - geologic_storage_leakage

        # compute additional CDR still needed
        addl_cdr = cdr_reqs[y] - existing_cdr

        # 4. greedily compute locally optimal CDR mix to cover addl CDR required in this year
        addl_projects = _advance_cdr_mix(addl_cdr, start + y, grid_em[y], heat_em[y], transport_em[y], fuel_em[y])
        projects.update(addl_projects)
        # add to existing CDR mix
        _add_next_year(projects, tech_mix, cost, energy)

    return tech_mix, cost, energy


def cdr_credit(yr: int) -> float:
    """
    Returns the credit price or tax credit for CDR in a given year ($/tCO2)
    :param yr: absolute year number, e.g. 2020
    :return: $/tCO2 credit price in specific year
    """
    # assume initial credit price of $50/tCO2 (based on 45Q tax credit)
    # and a 5% per year increase
    return 50 * (1.05 ** (yr - util.START_YEAR))


def get_true_cost(capture_project: types.CDRStrategy, yr, storage_pairing: types.CDRStrategy = None):
    """ Calculates the true $/tCO2 cost of a CDR project, adjusted for
    incidental emissions, carbon credits, and CO2 storage costs.
    :param capture_project: the specific capture project in question
    :param yr: absolute year number, e.g. 2020
    :param storage_pairing: the CO2 storage project paired with the capture project, if any """
    # credits reduce cost by: sum from y=yr to yr+lifetime of credit_price(y)/(1 + d)^(y-y0)
    credit_reduction = 0
    for y in range(yr, yr + capture_project.get_levelizing_lifetime()):
        credit_reduction += cdr_credit(y) / ((1 + util.DISCOUNT_RATE) ** (y - yr))
    credit_reduction /= capture_project.get_levelizing_lifetime()
    return capture_project.get_adjusted_cost() + \
        (storage_pairing.get_adjusted_cost() if storage_pairing is not None else 0) \
        - credit_reduction


##################################
#  Helper functions for cdr_mix  #
##################################

def _advance_cdr_mix(addl_cdr, yr, grid_em, heat_em, transport_em, fuel_em) -> tuple:
    """
    Greedily computes locally optimal CDR mix to cover additional CDR required.
    Meets the CDR requirement by deploying the cheapest technology until that
    technology reaches its annual deployment limit or until it is no longer the
    cheapest technology.
    """
    new_projects = set()
    options = _set_up_pq(yr)

    mtco2_deployed = 0
    while mtco2_deployed < addl_cdr:
        # get cheapest project type
        try:
            next_project_type = options.get(False)[1]  # (cost, (capture class, storage class, [storage init params]))
        except Empty:
            raise util.NotEnoughCDRError(f'There was not enough CDR available to meet the {addl_cdr} MtCO2 '
                                         f'required in year {yr}. Only {mtco2_deployed} MtCO2 of CDR was deployed.')

        # generate project instance
        try:
            capture_proj, storage_proj = _generate_next_project(next_project_type)
        except util.StrategyNotAvailableError:
            # can't use this project type anymore for this year, don't re-enqueue
            continue

        # add project to mix
        new_projects.add((capture_proj, storage_proj))
        mtco2_deployed += util.PROJECT_SIZE

        # re-enqueue it in options with its new adjusted cost
        options.put((get_true_cost(capture_proj, yr, storage_proj), next_project_type))

    return new_projects


def _generate_next_project(next_project_type: util.PQEntry) -> tuple:
    # deploy capture project, if available
    try:
        capture_proj = next_project_type.capture_class(util.PROJECT_SIZE)
    except util.StrategyNotAvailableError as e1:
        # skip this project type
        raise e1
    # deploy paired storage project, if needed and available
    if next_project_type.storage_class:
        try:
            storage_proj = next_project_type.storage_class(capture_proj, *next_project_type.storage_params)
        except util.StrategyNotAvailableError as e2:
            # undo capture deployment
            next_project_type.capture_class.remaining_deployment += capture_proj.capacity
            # can't use this project type anymore, don't re-enqueue
            raise e2
    else:
        storage_proj = None

    return capture_proj, storage_proj


def _set_up_pq(yr):
    """ Creates a priority queue containing each capture/storage pairing,
     enqueued by adjusted cost for the given years. """
    options = PriorityQueue()
    for tech in CDR_TECHS:
        # Enqueue all tech/storage pairings with initial costs as priority
        try:  # deploy test capture project
            capture_proj = tech(util.PROJECT_SIZE)
        except util.StrategyNotAvailableError:
            continue  # skip this project type for this year
        # undo test deployment so we don't consume some of that class's available deployment
        tech.cumul_deployment -= util.PROJECT_SIZE
        tech.remaining_deployment += util.PROJECT_SIZE

        # pair capture tech with all listed available storage pairings
        storage_pairings = STORAGE_PAIRINGS.get(tech, [(None, [])])  # data is [(storage tech, [init params])
        for storage_info in storage_pairings:
            if storage_info[0] is not None:
                try:  # deploy test storage project
                    storage_proj = storage_info[0](capture_proj, *storage_info[1])
                except util.StrategyNotAvailableError:
                    continue  # skip this project type for this year
                # undo test deployment so we don't consume some of that class's available deployment
                storage_info[0].cumul_deployment -= capture_proj.capacity
                storage_info[0].remaining_deployment += util.PROJECT_SIZE
            else:
                storage_proj = None

            # compute cost info and enqueue into PQ
            cost = get_true_cost(capture_proj, yr, storage_proj)
            entry = util.PQEntry(tech, storage_info[0], storage_info[1])
            options.put((cost, entry))

    return options


def _setup_emissions_intensities(grid_em, heat_em, transport_em, fuel_em):
    """ Communicates emissions intensities to CDRStrategy hierarchy """
    abstract_types.CDRStrategy.GRID_EM = grid_em
    abstract_types.CDRStrategy.HEAT_EM = heat_em
    abstract_types.CDRStrategy.TRANSPORT_EM = transport_em
    abstract_types.CDRStrategy.FUEL_EM = fuel_em


def _age_and_retire_projects(projects: set) -> defaultdict:
    """ Removes old projects from the provided projects set.
    Returns the capacity of CDR that was retired, grouped by technology. """
    retiring_projects = set()
    retiring_capacity = defaultdict()

    for proj_pair in projects:
        capture_proj = proj_pair[0]
        capture_proj.advance_age()
        if capture_proj.should_be_retired():
            retiring_capacity[capture_proj.__class__] += capture_proj.capacity  # no longer part of CDR fleet
            retiring_projects.add(proj_pair)  # can't remove from projects during iteration

    projects -= retiring_projects
    return retiring_capacity


def _add_next_year(projects: set, tech_mix: list, cost: list, energy: list):
    """
    Updates tech_mix, cost, and energy with information about the next year's projects.
    :param projects: the projects running in the next year (set of (capture_proj, storage_proj))
    :param tech_mix: list of annual CDR deployments, grouped by technology
    :param cost: list of annual total CDR costs
    :param energy: list of annual CDR energy use, grouped by energy source
    """
    # new cost of all projects, skipping non-existent storage pairings
    cost.append(sum(proj.get_adjusted_cost() * proj.capacity * (10 ** 6)
                    for proj in itertools.chain(*projects) if proj is not None))
    # sum sector energy uses of individual projects to get new overall energy use by sector,
    # skipping non-existent storage pairings
    energy.append(tuple(map(sum, zip((0, 0, 0, 0),
                                     *((x * proj.capacity * (10 ** 6) for x in proj.get_adjusted_energy())
                                       for proj in filter(lambda y: y is not None, itertools.chain(*projects)))
                                     )
                            )))
    # sum and group new deployment of each technology
    new_tech_deployment = dict()
    for proj in projects:  # these are (capture_project, storage_project)
        classes = proj[0].__class__, proj[1].__class__ if proj[1] is not None else None
        if classes in new_tech_deployment:
            new_tech_deployment[classes] += proj[0].capacity  # count capture project capacity
        else:
            new_tech_deployment[classes] = proj[0].capacity
    tech_mix.append(new_tech_deployment)


def _reset_tech_adopt_limits():
    """ Called when advancing years in the CDR adoption game.
    Allows more of each CDR technology to be deployed in each year. """
    for tech in CDR_TECHS:
        tech.reset_adoption_limits()
