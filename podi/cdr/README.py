# CDR Module Structure

The following files play the following roles:

1. **cdr_main.py:** implements yearly optimization framework and is the module’s main public interface; exports the cdr_mix function, the primary public-facing function.
2. **cdr_util.py:** defines constants and utility functions used throughout the module.
3. **cdr_abstract_types.py:** defines the inheritance hierarchy for CDR project objects.
4. **ecr_types.py:** implements behavior of specific ECR CDR strategies.
5. **ncs_types.py:** implements behavior of specific NCS CDR strategies.

<br/><br/>

# Module inputs and outputs

Inputs | Outputs
------ | -------
Annual MtCO2 CDR requirements | Cost-optimal mix of CDR capacity in each year, by CDR technology (MtCO2/yr)
Start year and end year | Total cost in each year (MM$), adjusted for CDR credits
Emissions intensity of: **1)** Grid electricity (tCO2/TWh), **2)** Heat production (tCO2/MWh), **3)** Transportation (tCO2/t*km), **4)** Liquid fuels (tCO2/MWh) | Annual energy use (TWh), separated into: **1)** Grid electricity, **2)** Heat use, **3)** Transportation, **4)** Liquid fuels

<br/><br/>

# Optimization Process

Here is the basic logic and the underlying set of assumptions for the current process to determine an approximately cost-optimal mix of CDR technologies in each year.

## The Process
* For each year:
    * Handle project retirements
        * Retire old plants that have reached the end of their lifetimes
        * Remove capacity for de-adopting technologies (e.g. natural carbon sinks that are saturating or other technologies with negative growth curves)
            * The capacity that is removed for de-adopting technologies is that of the oldest installed plants for that technology. These are either the most expensive or the closest to retirement anyways.
    * Determine how much additional CDR needs to be deployed in that year
	    * Computed as the difference between the previous year’s existing global CDR capacity and the current year’s required CDR capacity, plus any retirements listed above or CO2 leakage from geologic storage.
    * Rank each available technology by cost, using a priority queue.
    * Deploy 1 MtCO2 of CDR at a time from the cheapest technology until it either runs out or is no longer the cheapest technology, or until the required CDR quota has been filled.
        * Note that the currently cheapest technology may change during a year if one technology is exhausted or becomes more expensive.
        * Storage is deployed along with some capture projects, if required.
    * This yields a technology mix that minimizes the cost in each consecutive year, where each decision is made with no consideration given to following years.

## Calculations
* *Effective CDR factor* for a project (i.e. net tCO2 removed per tCO2 capacity) = `1-x`
    * *x* is tons incidental CO2 emissions (e.g. from energy production) per ton CO2 removed.
* Costs are based on each 1 MtCO2/yr project’s levelized cost, their net CDR efficiency (accounting for incidental emissions), and the annual carbon price.
    * ![cost equation](https://latex.codecogs.com/svg.latex?%5Cfrac%7B%5Ctextup%7Bnew%5C%26space%3Bcost%7D%7D%7BtCO_2%7D%3D%5Cleft%5C%28%5Cfrac%7Bcost%7D%7BtCO_2%7D%5Cright%5C%29_%7Bbaseline%7D%2A%5Cfrac%7B1%7D%7B%5Ctextup%7Beffective%26space%3BCDR%26space%3Bfactor%7D%7D-%5Cfrac%7B1%7D%7BT%7D%2A%5Csum_%7By%3Dy_0%7D%5E%7By_0%26plus%3BT%7D%5Cfrac%7B%5Ctextup%7Bcredit%26space%3Bprice%7D%28y%29%7D%7B%281%26plus%3Br%29%5E%7B%28y-y_0%29%7D%7D)
    * *T* is lifetime, *y_0* is project deployment year, *r* is discount rate.
* Energy use is based on each 1 MtCO2/yr project’s base energy use (per tCO2) and adjusted for its net CDR efficiency. Split into electricity/heat/transportation/fuels.
    * ![energy equation](https://latex.codecogs.com/svg.latex?%5Cfrac%7B%5Ctextup%7Bnew%5C%26space%3Benergy%7D%7D%7BtCO_2%7D%3D%5Cleft%5C%28%5Cfrac%7Benergy%7D%7BtCO_2%7D%5Cright%5C%29_%7Bbaseline%7D%2A%5Cfrac%7B1%7D%7B%5Ctextup%7Beffective%26space%3BCDR%26space%3Bfactor%7D%7D)
* Max annual adoption potential (limit to how much new capacity can be deployed in a year) for each technology is the slope of its market penetration curve, in the absence of competing CDR technologies, at its current deployment level.
    * For example, given a logistic adoption function ![logistic equation](https://latex.codecogs.com/svg.latex?N%28t%29%3DM%5Cleft%5C%5B%5Cfrac%7Be%5E%7B%28a%26plus%3Bbt%29%7D%7D%7B1%26plus%3Be%5E%7B%28a%26plus%3Bbt%29%7D%7D%5Cright%5C%5D) and some current adoption level *n*, the slope of this logistic curve at the point where the adoption level (y-value) equals *n* is ![slope equation](https://latex.codecogs.com/svg.latex?b%2A%5Cleft%5C%28n-%5Cfrac%7Bn%5E2%7D%7BM%7D%5Cright%5C%29%3D%5Ctextup%7Bslope%26space%3Bof%26space%3B%7DN%28t%29%5Ctextup%7B%26space%3Bwhere%26space%3B%7DN%5Ctextup%7B%26space%3Bequals%26space%3B%7Dn), which is the value of ![prime inverse equation](https://latex.codecogs.com/svg.latex?N%27%5Cleft%5C%28N%5E%7B-1%7D%28n%29%5Cright%5C%29), i.e. the adoption slope at the time on the logistic graph corresponding to adoption level *n*.

## Assumptions
* CDR is simultaneously deployed all at once at the beginning of each year.
* 5% discount rate.
* DAC, EW, and geologic storage projects have constant costs throughout their lifetime.
* The capture step is assumed to be the limiting step, so geologic storage is assumed to have unlimited potential.
* DAC projects can achieve up to a 90% reduction in CAPEX via learning.
* Storage projects are levelized using the same lifetime as their paired capture project.
* Transportation mix has a (trucking : shipping : rail) split of (30.7 : 10.5 : 2.4), based on the relative global energy use of freight transport modes in the [EIA 2019 energy outlook.](https://www.eia.gov/outlooks/aeo/data/browser/#/?id=51-IEO2019)
* Default energy source emissions intensity assumptions described in cdr_util.
* All electricity is assumed to come from the grid.
* All liquid fuels are assumed to be diesel.
* In the event that there is more existing CDR capacity than needed for a year, energy costs and variable O&M are scaled down to reflect the decreased utilization. Capital costs and fixed O&M are assumed to be 1/2 of total costs and are still summed in full in such situations.

# Extending this module

## Current Class Structure

Each MtCO2/yr of CDR is represented in the optimization framework as a concrete instance of an ECR or NCS subclass of the CDRStrategy abstract superclass (currently all project objects have a capacity of 1 MtCO2/yr). The current inheritance hierarchy is as follows:
 
![CDR inheritance structure](./images/cdr_inheritance_structure.png)

Yellow classes are abstract classes that cannot be instantiated. Blue classes are concrete classes that have already been implemented. Green classes are concrete classes that have not yet been implemented.

## Adding new CDR strategies

All new CDR strategies should be implemented as concrete subclasses of ECR (in erc_types.py) or NCS (in ncs_types.py), depending on which best characterizes them. These concrete classes act as factories for individual CDR projects deployed in the optimization framework. Implement new strategies in the appropriate file, and then add them to the `CDR_TECHS` list near the top of cdr_main.py.

If a capture strategy requires storage paired with it to truly be CDR, then add that relationship to the `STORAGE_PAIRINGS` dict in cdr_main.py, along with any parameters that would need to be supplied to the paired storage project's `__init__`. This is the case for DAC, for example, as DAC without storing the captured CO2 underground is not actually carbon dioxide removal.

Each CDR strategy must implement the following features:

1. **Annual adoption limits (MtCO2/yr)**, returning the maximum MtCO2/yr of new capacity of this technology that can be deployed in the current year in the absence of any competing CDR strategies, based on its current active deployment level in MtCO2/yr (accessible via `cls.active_deployment`), its cumulative deployment (`cls.cumul_deployment`), and for resources that are time-sensitive its total MtCO2 captured across years (`cls.cdr_performed`).
    * Values can go negative if a carbon sink is saturating and can capture less CO2 this year than it could in the previous year.
    * Has the header:
```
    @classmethod 
    def adopt_limits(cls) -> float:
```

2. **Project’s cost in a particular year ($/tCO2)**, returning the raw $/tCO2 (in 2020$) cost of the project in the year given by `self.age`. This is **not** adjusted for the impacts of incidental emissions or CDR credits and, in addition to being based on the project’s current age, is likely based on the project’s capacity (self.capacity) and its original deployment level (`self.deployment_level`), which represents the technology’s cumulative deployment (MtCO2/yr) at the time of this project’s creation. Has the header:
    * In theory, levelizing each of the yearly costs from this function over the lifetime of the project should yield the same result as the marginal_levelized_cost function below.
```
    @util.once_per_year
    def curr_year_cost(self) -> float:
```

3. **Project’s levelized cost ($/tCO2)**, returning the “sticker price” $/tCO2 (in 2020$) of the project used for comparison with other CDR projects. This is **not** adjusted for the impacts of incidental emissions or CDR credits and is based on the project’s capacity (`self.capacity`) and its original deployment level (`self.deployment_level`).
    * Should account for cost declines via learning curves, if applicable.
    * Has the header:
```
    @util.cacheit
    def marginal_levelized_cost(self) -> float:
```

4. **Project’s energy use (kWh/tCO2)**, returning the project’s energy use, in kWh/tCO2, separated into (electricity, heat, transportation, fuel).
    * Should account for energy efficiency improvements via learning curves, if applicable.
    * Has the header:
```
    @util.cacheit
    def marginal_energy_use(self) -> tuple:
```

5. **A default project lifetime (years)**, representing the number of years until the model automatically retires individual projects of this type of old age, defined at the class level as:
```
    default_lifetime = ___ (insert lifetime here, as int)
```

And for ECR only:

6. **Project’s incidental emissions (tCO2/tCO2)**, returning the tCO2 emitted per tCO2 captured.
    * If the only incidental emissions are from energy use, then this function can be omitted in order to simply use the default function defined in ECR.
    * This may be omitted for NCS because those calculations are assumed to already be done on a net basis
    * Has the header:
```
    @util.once_per_year
    def incidental_emissions(self) -> float: 
```

Additionally, if you desire a project capacity/granularity for a CDR strategy other than the default defined in `crd_util.PROJECT_SIZE`, then override `__init__` for the new class, replacing `new_default_capacity` with your desired numerical value (in MtCO2/yr):
```
def __init__(self, capacity=new_default_capacity):
    super().__init__(capacity=new_default_capacity)
    # along with any further necessary initialization here
```

## Updating optimization process

The optimization takes place in `cdr_main.py` and relies on the CDR strategy framework built up in `cdr_abstract_types.py`, `ecr_types.py`, and `ncs_types.py`. Technologies are selected for deployment in the `_advance_cdr_mix` function, and yearly statistics (cost, energy, deployment) are tabulated in `_add_next_year`. Look in those two places to extend or refine optimization functionality and refer to the documentation in the code for specifics.

Additionally, here are a couple areas with known potential for improvement:

1. The nature of the current greedy algorithm (always deploying the cheapest available technology) may cause it to miss truly optimal solutions within an individual year. For example, if DAC gets cheaper with each MtCO2 deployment, then deploying 100% DAC in a year may be the cost-optimal strategy, even if DAC was not originally the cheapest technology in that year.

2. The optimization model currently runs in about 30 seconds for the full time range when dealing with LTSS-DAC, HTLS-DAC, ExSituEW, and GeologicStorage. At the moment, the cost and energy calculation step in `_add_next_year` (not the technology selection step) take up the most processing time. Future improvements to efficiency should look here first.
