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
ecr_types.py - implements behavior of specific ECR CDR strategies (concrete subclasses
               of abstract ECR parent class)
ncs_types.py - implements behavior of specific NCS CDR strategies (concrete subclasses
               of abstract NCS parent class)
"""

from queue import PriorityQueue, Empty

import cdr.cdr_abstract_types as abstract_types
import cdr.cdr_util as util
import cdr.ecr_types as ecr
import cdr.ncs_types as ncs

__author__ = "Zach Birnholz"
__version__ = "08.14.20"

"""
Stores all CDR approaches available for use in this module.
Implement new CDR approaches in cdr_types.py and ncs_types.py and add them to this list.
If the capture type requires a paired CO2 storage project, add that pairing
to the STORAGE_PAIRINGS list below.
Comment out a technology from this list to temporarily remove it from consideration.
"""
CDR_TECHS = [
    ecr.ExSituEW,
    ecr.LTSSDAC,
    ecr.HTLSDAC,
]

"""
Describes the capture-storage relationship for capture technologies
that require separate storage. Mappings are:
capture type --> [(storage type, [storage __init__ parameters])]
The storage project itself is always given as the first __init__ parameter
and does not need to be specified in the parameter list here.
"""
STORAGE_PAIRINGS = {
    ecr.LTSSDAC: [(ecr.GeologicStorage, [util.AIR_T, util.AIR_P])],
    ecr.HTLSDAC: [(ecr.GeologicStorage, [])],
}


#####################################
#  Primary public-facing functions  #
#####################################


def cdr_mix(
    cdr_reqs: list = util.cdr_needed_def,
    grid_em: list = util.GRID_EM_DEF,
    heat_em: list = util.HEAT_EM_DEF,
    transport_em: list = util.TRANSPORT_EM_DEF,
    fuel_em: list = util.FUEL_EM_DEF,
    start: int = util.START_YEAR,
    end: int = util.END_YEAR,
) -> tuple:
    """
    Main exported function of the module. Generates a nearly cost-optimal mix
    of CDR technologies to meet the required yearly CDR targets, optimized for
    choosing the currently cheapest available mix in each progressive year.
    Please note the units assumed of each of the parameters.

    :param cdr_reqs: time series of CDR targets to be met in each year (MtCO2/yr), from start to end years
    :param grid_em: time series of grid electricity carbon intensity (MtCO2/TWh), from start to end years
    :param heat_em: time series of heat source carbon intensity (tCO2/MWh), from start to end years
    :param transport_em: time series of transportation carbon intensity (tCO2/t*km), from start to end years
    :param fuel_em: time series of liquid fuel carbon intensity (tCO2/MWh), from start to end years
    :param start: the first year to compute the CDR mix for
    :param end: the last year (inclusive) to compute the CDR mix for
    :return: approximately cost-optimal mix of CDR strategies, as a tuple containing:
        0. annual CDR quantity by technology (list of dict, MtCO2/yr split by technology),
        1. annual cost (list of float, MM$/yr),
        2. annual energy requirement (list of tuple of float, TWh/yr split into sectors)
    """
    # 0. set up framework and allow for multiple sequential runs
    abstract_types.CDRStrategy.start_year = abstract_types.CDRStrategy.curr_year = start
    _reset_tech_adopt_limits()
    assert len(cdr_reqs) == (end - start + 1)  # year counts must match up
    _setup_emissions_intensities(grid_em, heat_em, transport_em, fuel_em)

    tech_mix = []  # list of {tech --> deployment} in each year
    cost = []  # list of cost (float) in each year
    energy = []  # list of (elec, heat, transport, non-transport fuel) in each year

    # 1. greedily compute locally optimal CDR mix to cover first year
    projects = _advance_cdr_mix(cdr_reqs[0], start)
    # add as first year of CDR mix
    _add_next_year(projects, tech_mix, cost, energy, start)

    for y in range(1, end - start + 1):
        # 2. clean slate for each new year
        _reset_tech_adopt_limits()
        abstract_types.CDRStrategy.advance_year()

        # 3. determine additional CDR needed for next year, incl. retiring old projects
        _retire_projects(projects)
        geologic_storage_leakage = _get_geologic_storage_leakage(tech_mix)

        existing_cdr = sum(p[0].capacity for p in projects) - geologic_storage_leakage

        # compute additional CDR still needed
        addl_cdr = cdr_reqs[y] - existing_cdr

        if addl_cdr < 0:
            # 4. only need to operate at a fractional capacity for this year
            scaling_factor = (existing_cdr + addl_cdr) / existing_cdr
        else:
            # 4. greedily compute locally optimal CDR mix to cover addl CDR required in this year
            addl_projects = _advance_cdr_mix(addl_cdr, start + y)
            projects.update(addl_projects)
            scaling_factor = 1  # all installed CDR is needed this year

        # 5. add to existing CDR mix
        _add_next_year(projects, tech_mix, cost, energy, start + y, scaling_factor)

    return tech_mix, cost, energy


def cdr_credit(yr: int) -> float:
    """
    Returns the credit price or tax credit for CDR in a given year ($/tCO2),
    based on a linear regression of median carbon prices used in a range of
    other existing IAMs: AIM/CGE 2.0/2.1, GCAM 4.2, GENeSYS-MOD 1.0,
    IMAGE 3.0.1/2, MERGE-ETL 6.0, MESSAGE V.3, MESSAGE-GLOBIOM 1.0,
    MESSAGEix-GLOBIOM 1.0, POLES ADVANCE, POLES CD-LINKS, POLES EMF33,
    REMIND 1.5/1.7, REMIND-MAgPIE 1.5/1.7-3.0, WITCH-GLOBIOM 3.1/4.2/4.4.
    Regression yields $3.656 + $9.167/yr, starting in 2020.
    :param yr: absolute year number, e.g. 2020
    :return: $/tCO2 credit price in specific year
    """
    return max(0.0, 3.656 + 9.167 * (yr - util.START_YEAR))


def get_prospective_cost(
    capture_project: abstract_types.CDRStrategy,
    yr: int,
    storage_pairing: abstract_types.CDRStrategy = None,
):
    """Calculates the prospective levelized $/tCO2 cost of a CDR project over its
    lifetime, adjusted for incidental emissions, carbon credits, and CO2 storage costs.
    :param capture_project: the specific capture project in question
    :param yr: deployment year of the project as an absolute year number, e.g. 2020
    :param storage_pairing: the CO2 storage project paired with the capture project, if any"""
    # credits reduce cost by: sum from y=yr to yr+lifetime of credit_price(y)/(1 + d)^(y-y0)
    credit_reduction = 0
    for y in range(yr, yr + capture_project.get_levelizing_lifetime()):
        credit_reduction += cdr_credit(y) / ((1 + util.DISCOUNT_RATE) ** (y - yr))
    credit_reduction /= capture_project.get_levelizing_lifetime()
    return (
        capture_project.get_adjusted_levelized_cost()
        + (
            storage_pairing.get_adjusted_levelized_cost()
            if storage_pairing is not None
            else 0
        )
        - credit_reduction
    )


##################################
#  Helper functions for cdr_mix  #
##################################


def _setup_emissions_intensities(grid_em, heat_em, transport_em, fuel_em):
    """ Standardizes units and communicates emissions intensities to CDRStrategy hierarchy """
    # 1. Standardize units
    for i in range(len(grid_em)):
        grid_em[i] /= 1000  # convert to tCO2/kWh from MtCO2/TWh
        heat_em[i] /= 1000  # convert to tCO2/kWh from tCO2/MWh
        # (transport_em is already in tCO2/t*km, which is what we want)
        fuel_em[i] /= 1000  # convert to tCO2/kWh from tCO2/MWh

    # 2. Communicate emissions intensities to CDRStrategy hierarchy
    abstract_types.CDRStrategy.GRID_EM = grid_em
    abstract_types.CDRStrategy.HEAT_EM = heat_em
    abstract_types.CDRStrategy.TRANSPORT_EM = transport_em
    abstract_types.CDRStrategy.FUEL_EM = fuel_em
    abstract_types.CDRStrategy.DEFAULT_EM_BASIS = list(
        zip(grid_em, heat_em, transport_em, fuel_em)
    )


def _reset_tech_adopt_limits():
    """Called when advancing years in the CDR adoption game.
    Allows more of each CDR technology to be deployed in each year."""
    for tech in CDR_TECHS:
        tech.reset_adoption_limits()


def _set_up_pq(yr):
    """Creates a priority queue containing each capture/storage pairing,
    enqueued by adjusted levelized cost for the given years.
    Note that we use the levelized cost (sticker price) for CDR comparison here,
    but it is the true curr_year_cost that actually gets billed and tallied
    in _add_next_year."""
    options = PriorityQueue()
    for tech in CDR_TECHS:
        # Enqueue all tech/storage pairings with initial costs as priority
        try:  # deploy test capture project, using util.PROJECT_SIZE as a capacity basis for comparison
            capture_proj = tech(util.PROJECT_SIZE)
        except util.StrategyNotAvailableError:
            continue  # skip this project type for this year
        # undo test deployment so we don't consume some of that class's available deployment for this year
        tech.cumul_deployment -= util.PROJECT_SIZE
        tech.remaining_deployment += util.PROJECT_SIZE

        # pair capture tech with all listed available storage pairings
        storage_pairings = STORAGE_PAIRINGS.get(
            tech, [(None, [])]
        )  # data is [(storage tech, [init params])
        for storage_info in storage_pairings:
            if storage_info[0] is not None:
                try:  # deploy test storage project
                    storage_proj = storage_info[0](capture_proj, *storage_info[1])
                except util.StrategyNotAvailableError:
                    continue  # skip this project type for this year
                # undo test deployment so we don't consume some of that class's available deployment for this year
                storage_info[0].cumul_deployment -= capture_proj.capacity
                storage_info[0].remaining_deployment += util.PROJECT_SIZE
            else:
                storage_proj = None

            # compute cost info and enqueue into PQ
            cost = get_prospective_cost(capture_proj, yr, storage_proj)
            entry = util.PQEntry(tech, storage_info[0], storage_info[1])
            options.put((cost, entry))

    return options


def _advance_cdr_mix(addl_cdr, yr) -> set:
    """
    Greedily computes locally optimal CDR mix to cover additional CDR required.
    Meets the CDR requirement by deploying the cheapest technology until that
    technology reaches its annual deployment limit or until it is no longer the
    cheapest technology.
    """
    print(
        f"\r** CDR OPTIMIZATION ** Starting _advance_cdr_mix for year {yr}...", end=""
    )
    new_projects = set()
    options = _set_up_pq(yr)

    mtco2_deployed = 0
    while mtco2_deployed < addl_cdr:
        # get cheapest project type
        try:
            next_project_type = options.get_nowait()[
                1
            ]  # (cost, (capture class, storage class, [storage init params]))
        except Empty:
            # there are no more available project types -- we're out of CDR for this year
            if util.ACCEPT_DEFICIT:
                # "deploy" enough ecr.Deficit to cover this deficit
                deficit_proj = ecr.Deficit(capacity=addl_cdr - mtco2_deployed)
                new_projects.add((deficit_proj, None))
                mtco2_deployed += deficit_proj.capacity
            else:
                raise util.NotEnoughCDRError(
                    f"There was not enough CDR available to meet the {addl_cdr} MtCO2 "
                    f"required in year {yr}. Only {mtco2_deployed} MtCO2 of CDR was deployed. "
                    f"To allow the model to run to completion anyways under these conditions, "
                    f"set the cdr_util.ACCEPT_DEFICIT flag to True."
                )
        else:
            # generate project instance
            try:
                capture_proj, storage_proj = _generate_next_project(next_project_type)
            except util.StrategyNotAvailableError:
                # can't use this project type anymore for this year, don't re-enqueue
                continue

            # add project to mix
            new_projects.add((capture_proj, storage_proj))
            mtco2_deployed += capture_proj.capacity

            # re-enqueue it in options with its new adjusted cost
            options.put(
                (
                    get_prospective_cost(capture_proj, yr, storage_proj),
                    next_project_type,
                )
            )

    return new_projects


def _generate_next_project(next_project_type: util.PQEntry) -> tuple:
    # deploy capture project, if available
    try:
        capture_proj = next_project_type.capture_class()
    except util.StrategyNotAvailableError as e1:
        # skip this project type due to capture unavailability
        raise e1
    # deploy paired storage project, if needed and available
    if next_project_type.storage_class:
        try:
            storage_proj = next_project_type.storage_class(
                capture_proj, *next_project_type.storage_params
            )
        except util.StrategyNotAvailableError as e2:
            # undo capture deployment
            next_project_type.capture_class.remaining_deployment += (
                capture_proj.capacity
            )
            # can't use this project type anymore due to unavailability of storage, so don't re-enqueue
            raise e2
    else:
        storage_proj = None

    return capture_proj, storage_proj


def _add_next_year(
    projects: set,
    tech_mix: list,
    cost: list,
    energy: list,
    yr: int,
    scaling_factor: float = 1,
):
    """
    Updates tech_mix, cost, and energy with information about the next year's projects.
    :param projects: the projects running in the next year (set of (capture_proj, storage_proj))
    :param tech_mix: list of annual CDR deployments, grouped by technology
    :param cost: list of annual total CDR costs
    :param energy: list of annual CDR energy use, grouped by energy source
    :param scaling_factor: fraction of installed CDR tech that actually needs to be operated in this year
    """
    new_cost = 0
    new_energy = [0, 0, 0, 0]
    new_tech_deployment = dict()

    # sum and group updated total cost, energy, and deployment of each technology
    for proj in projects:  # these are (capture_project, storage_project)
        # 1. add project's cost
        # note that capacity is in MtCO2, not tCO2 (10 ** 6), but we return in MM$ (10 ** -6), so there is no conversion
        # Although adjusted_levelized_cost was used for the basis of comparing the cheapest technologies,
        # we use adjusted_curr_year_cost here to reflect the amounts that are actually billed in each year.
        new_cost += proj[0].get_adjusted_curr_year_cost() * proj[0].capacity + (
            proj[1].get_adjusted_curr_year_cost() * proj[1].capacity
            if proj[1] is not None
            else 0
        )

        # 2. add project's energy use
        # note that capacity is in MtCO2, not tCO2 (10 ** 6) but we want TWh, not kWh (10 ** -9), hence the (10 ** -3)
        p0_energy = tuple(
            x * proj[0].capacity / 1000 for x in proj[0].get_adjusted_energy()
        )
        p1_energy = (
            tuple(x * proj[1].capacity / 1000 for x in proj[1].get_adjusted_energy())
            if proj[1] is not None
            else (0, 0, 0, 0)
        )
        for i in range(len(new_energy)):
            new_energy[i] += p0_energy[i] + p1_energy[i]

        # 3. add project's capacity, adjusted for fraction that will actually be used this year
        # (assuming that the reduction in utilization is applied evenly across all projects regardless of cost)
        classes = proj[0].__class__, proj[1].__class__ if proj[1] is not None else None
        if classes in new_tech_deployment:
            new_tech_deployment[classes] += (
                scaling_factor * proj[0].capacity
            )  # only count capture project capacity
        else:
            new_tech_deployment[classes] = scaling_factor * proj[0].capacity

    # 4. Add info for new year to cost, energy, and tech_mix.
    # If there is too much CDR installed (scaling_factor < 1), then don't count the excess variable O&M/energy use
    # but still pay the CAPEX and fixed O&M for those non-operating projects (we assume this is 1/2 of total cost)
    cost.append(
        new_cost * (1 + 2 * scaling_factor) / 2
        - sum(new_tech_deployment.values()) * cdr_credit(yr)
    )
    energy.append(tuple(x * scaling_factor for x in new_energy))
    tech_mix.append(new_tech_deployment)


def _retire_projects(projects: set) -> int:
    """Removes projects that have reached the end of their lifetimes as well as the
    oldest projects from the mix for technologies with negative adoption curves in
    order to not exceed those technologies' potential adoption.
    The oldest projects technologies that are scaling down are retired here rather
    than the cheapest projects because the oldest projects will either be:
    (1) for ECR - likely the most expensive or nearest to retirement anyway, or
    (2) for NCS - the specific projects/CO2 sinks that are reaching saturation
    :return: The CDR capacity that was retired (MtCO2/yr)
    """
    projects_by_age = sorted(
        projects, key=lambda p: p[0].age, reverse=True
    )  # sorted by capture proj age, oldest first
    adoption_limits = {tech: tech.adopt_limits() for tech in CDR_TECHS}
    if util.ACCEPT_DEFICIT:
        adoption_limits[ecr.Deficit] = ecr.Deficit.adopt_limits()
    retiring_projects = set()
    retiring_capacity = 0

    for proj_pair in projects_by_age:
        capture_proj = proj_pair[0]
        capture_proj.advance_age()
        if (
            adoption_limits[capture_proj.__class__] < 0
            or capture_proj.should_be_retired()
        ):
            proj_capacity = _retire_project_pair(proj_pair, retiring_projects)
            retiring_capacity += proj_capacity
            adoption_limits[capture_proj.__class__] += proj_capacity

    projects -= retiring_projects
    return retiring_capacity


def _retire_project_pair(proj_pair, retiring_projects) -> int:
    """Retires the capture/storage projects in the given project pair.
    Adds the pair to retiring_projects. Returns the capacity retired."""
    retiring_capacity = proj_pair[0].capacity
    retiring_projects.add(proj_pair)
    proj_pair[0].retire()
    if proj_pair[1] is not None:
        proj_pair[1].retire()
    return retiring_capacity


def _get_geologic_storage_leakage(tech_mix):
    """ Returns MtCO2/yr leaked from cumulative geologic storage """
    geologic_storage_leakage = 0
    for tech in tech_mix[-1]:
        if tech[1] is not None and tech[1].__class__ == ecr.GeologicStorage.__class__:
            geologic_storage_leakage += tech_mix[-1][tech] * util.RESERVOIR_LEAKAGE_RATE
    return geologic_storage_leakage


def main():
    # Test run
    result = cdr_mix()
    print("\n\n === CDR MODULE OUTPUT === \n")
    for yr in range(len(result[0])):
        print(f"** Year {yr + util.START_YEAR} **")
        print("Technologies: ")
        for k, v in sorted(result[0][yr].items(), key=lambda item: item[0][0].__name__):
            print(
                f'  {k[0].__name__} --> {k[1].__name__ if k[1] else "(None)"}: {round(v, 2)}'
            )
        print(f"Total CDR deployed (MtCO2/yr): {round(sum(result[0][yr].values()), 2)}")
        print(
            f"Total cost (MM$), including carbon credit benefit: {round(result[1][yr], 2)}"
        )
        print(f"  $/tCO2: {round(result[1][yr] / util.cdr_needed_def[yr], 2)}")
        print("Energy use: ")
        for i, energy in enumerate(
            ["Electricity (TWh)", "Heat (TWh)", "Transport (TWh)", "Fuels (TWh)"]
        ):
            print(f"  {energy}: {round(result[2][yr][i], 2)}")
        print()


if __name__ == "__main__":
    main()
