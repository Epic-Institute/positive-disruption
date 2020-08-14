#!/usr/bin/env python3
"""
cdr_abstract_types.py
Defines the inheritance hierarchy used for CDR classes.
Allows CDR strategies to keep track of their characteristics
at the class and instance level.

If you are simply defining new CDR strategies, do that in
ecr_types.py (for engineered projects) or
ncs_types.py (for natural projects) instead.
"""

__author__ = "Zach Birnholz"
__version__ = "08.14.20"


from abc import ABC, abstractmethod
import inspect
import math
import numpy as np

import cdr.cdr_util as util


class CDRStrategy(ABC):
    """
    Abstract base class for CDR inheritance hierarchy, which
    represents a generic CDR project.

    ECR and NCS classes implement the is_engineered function.
    All concrete CDR subclasses must implement the four remaining abstract functions.
    """

    start_year = curr_year = util.START_YEAR  # available to all CDR types

    default_lifetime = None  # to be overridden by subclasses
    levelizing_lifetime = None  # for subclasses with infinite (float('inf')) lifetimes

    # values from model, to be set when the CDR process actual runs
    GRID_EM = None
    HEAT_EM = None
    TRANSPORT_EM = None
    FUEL_EM = None
    DEFAULT_EM_BASIS = None

    def __init__(self, capacity=util.PROJECT_SIZE):
        # capacity is in MtCO2/yr

        # ensure subclass is set up correctly
        if self.__class__.default_lifetime is None:
            raise util.StrategyNotImplementedError(
                f"The CDR strategy {self.__class__.__name__} "
                f"has not defined a default project lifetime."
            )
        if self.__class__.remaining_deployment < capacity:
            raise util.StrategyNotAvailableError(
                f"The CDR strategy {self.__class__.__name__} does not "
                f"have enough adoption potential left for this year."
            )

        # record the deployment of this project
        self.__class__.cumul_deployment += capacity
        self.__class__.remaining_deployment -= capacity
        self.__class__.active_deployment += capacity
        self.capacity = capacity
        self.deployment_level = self.__class__.cumul_deployment  # includes this project
        self.lifetime = self.__class__.default_lifetime
        self.age = 0

    def __init_subclass__(cls, **kwargs):
        """ Allow each CDR strategy to track its own deployment
            and adoption limits at the class level """
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            # each concrete class gets its own deployment counter
            cls.cumul_deployment = 0  # all capacity ever deployed
            cls.active_deployment = 0  # all capacity currently deployed
            cls.cdr_performed = 0  # total MtCO2 captured by this strategy
            # and its own annual deployment tracker
            if cls.adopt_limits() == float("inf"):
                cls.remaining_deployment = float(
                    "inf"
                )  # to avoid overflow errors with math.ceil
            else:
                cls.remaining_deployment = math.ceil(cls.adopt_limits())

    @staticmethod
    def advance_year():
        CDRStrategy.curr_year += 1

    @classmethod
    def reset_adoption_limits(cls):
        """Resets remaining deployment limits for a new year"""
        limits = cls.adopt_limits()
        if limits != float("inf"):
            cls.remaining_deployment = math.ceil(cls.adopt_limits())
        cls.cdr_performed += cls.active_deployment

    def advance_age(self):
        self.age += 1

    def should_be_retired(self) -> bool:
        """ Must call advance_age before this check to avoid being off by one
        (as self.age starts at 0). """
        return self.age >= self.lifetime

    def retire(self):
        """ This method can be called any time (regardless of return value of
        should_be_retired), in case projects need to be retired early. """
        self.__class__.active_deployment -= self.capacity

    @abstractmethod
    def is_engineered(self) -> bool:
        """Should return True for ECR, False for NCS"""
        return NotImplemented

    @classmethod
    @abstractmethod
    def adopt_limits(cls) -> float:
        """Computes annual adoption/deployment limit (MtCO2 capacity/yr)
        based on current cumulative deployment of this technology using
        cls.cumul_deployment (MtCO2/yr) and/or CDRStrategy.curr_year """
        return NotImplemented

    @abstractmethod
    def curr_year_cost(self) -> float:
        """ Returns the raw $/tCO2 (in 2020$) cost of the project in the year given
        by self.age. This is not adjusted for the impacts of incidental emissions
        or CDR credits and, in addition to being based on the project’s current age,
        is likely based on the project’s capacity (self.capacity) and its original
        deployment level (self.deployment_level), which represents the technology’s
        cumulative deployment (MtCO2/yr) at the time of this project’s creation.
        In theory, levelizing each of the yearly costs from this function over the
        lifetime of the project should yield the same result as the
        marginal_levelized_cost function. """
        return NotImplemented

    @abstractmethod
    def marginal_levelized_cost(self) -> float:
        """ Returns the single "sticker price" $/tCO2 (in 2020$) of the project, used for
        comparison with other CDR projects. This is not adjusted for the impacts of
        incidental emissions or CDR credits and is based on the project’s capacity
        (self.capacity) and its original deployment level (self.deployment_level),
        which represents the technology’s cumulative deployment (MtCO2/yr) at the
        time of this project’s creation. It is 'marginal' in the sense that this
        project was the marginal project at the time of its deployment. """
        return NotImplemented

    @abstractmethod
    def marginal_energy_use(self) -> tuple:
        """Computes energy use (kWh/tCO2) for the next MtCO2/yr capacity
        as a function of cumulative deployment (MtCO2/yr), broken into three
        sectors and packaged into a tuple as follows:
        0. electricity use
        1. heat use
        2. transportation energy use
        3. non-transport liquid fuel use
        """
        return NotImplemented

    @abstractmethod
    def incidental_emissions(self) -> float:
        """Computes incidental emissions (tCO2 emitted/tCO2 captured)"""
        return NotImplemented

    @util.once_per_year
    def get_eff_factor(self):
        em = self.incidental_emissions()
        if em > 1:
            raise util.StrategyNotImplementedError(
                f"The strategy {self.__class__.__name__} emits more than "
                f"one tCO2 per tCO2 captured. This is either an implementation "
                f"error or a flawed CDR strategy."
            )
        return 1 - em

    @util.once_per_year
    def get_adjusted_levelized_cost(self):
        return self.marginal_levelized_cost() / self.get_eff_factor()

    @util.once_per_year
    def get_adjusted_curr_year_cost(self):
        """ Returns cost of this project, adjusted for incidental emissions
        so as to only count CDR on a net CO2 basis """
        return self.curr_year_cost() / self.get_eff_factor()

    @util.once_per_year
    def get_adjusted_energy(self):
        eff_factor = self.get_eff_factor()
        return tuple(x / eff_factor for x in self.marginal_energy_use())

    def get_levelizing_lifetime(self):
        if self.__class__.levelizing_lifetime is not None:
            return self.__class__.levelizing_lifetime
        else:
            return self.lifetime


class NCS(CDRStrategy):
    """
    NCS represents a natural cdr technique (Natural Climate Solution).
    """

    def is_engineered(self) -> bool:
        return False

    def __init_subclass__(cls, **kwargs):
        """ Allow each NCS strategy to track its own additional
            characteristics at the class level, if desired in the future """
        super().__init_subclass__(**kwargs)
        # initialize any NCS-specific class variables here

    def incidental_emissions(self) -> float:
        # All NCS CO2 values are already computed on a net basis.
        return 0.0


class ECR(CDRStrategy):
    """
    ECR represents an Engineered Carbon Removal technique.
    """

    def is_engineered(self) -> bool:
        return True

    def __init_subclass__(cls, **kwargs):
        """ Allow each ECR strategy to track its own additional
            characteristics at the class level, if desired in the future """
        super().__init_subclass__(**kwargs)
        # initialize any ECR-specific class variables here

    @util.once_per_year
    def incidental_emissions(self) -> float:
        """ Default behavior is simply multiplying the energy use in each sector
         by its respective emissions rate and summing across sectors. """
        energy_basis = self.marginal_energy_use()
        yr = CDRStrategy.curr_year - CDRStrategy.start_year
        return float(np.dot(energy_basis, CDRStrategy.DEFAULT_EM_BASIS[yr]))
