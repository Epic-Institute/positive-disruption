#!/usr/bin/env python3
"""
cdr_abstract_types.py
Defines the inheritance hierarchy used for CDR classes.
Allows CDR strategies to keep track of their characteristics
at the class and instance level.

If you are simply defining new CDR strategies, do that in
cdr_types.py instead.
"""

__author__ = "Zach Birnholz"
__version__ = "07.23.20"


import cdr.cdr_util as util
from abc import ABC, abstractmethod
import inspect
import math
import numpy as np


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

    def __init__(self, capacity=1):
        # capacity is in MtCO2/yr

        # ensure subclass is set up correctly
        if self.__class__.default_lifetime is None:
            raise util.StrategyNotImplementedError(f'The CDR strategy {self.__class__.__name__} '
                                                   f'has not defined a default project lifetime.')
        if not util.DEBUG_MODE and self.__class__.remaining_deployment < capacity:
            raise util.StrategyNotAvailableError(f'The CDR strategy {self.__class__.__name__} does not '
                                                 f'have enough adoption potential left for this year.')

        # record the deployment of this project
        self.__class__.cumul_deployment += capacity
        self.__class__.remaining_deployment -= capacity
        self.capacity = capacity
        self.deployment_level = self.__class__.cumul_deployment  # includes this project
        self.lifetime = self.__class__.default_lifetime
        self.age = 0

    def __init_subclass__(cls, **kwargs):
        """ Allow each CDR strategy to track its own deployment
            and adoption limits at the class level """
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            # each concrete class gets its own counter
            cls.cumul_deployment = 0
            # and its own annual deployment tracker
            if cls.adopt_limits() == float('inf'):
                cls.remaining_deployment = float('inf')  # to avoid overflow errors with math.ceil
            else:
                cls.remaining_deployment = math.ceil(cls.adopt_limits())

    @staticmethod
    def advance_year():
        CDRStrategy.curr_year += 1

    @classmethod
    def reset_adoption_limits(cls):
        """Resets remaining deployment limits for a new year"""
        cls.remaining_deployment = math.ceil(cls.adopt_limits())

    def advance_age(self):
        self.age += 1

    def should_be_retired(self) -> bool:
        """ Must call advance_age before this check to avoid being off by one
        (as self.age starts at 0). """
        return self.age >= self.lifetime

    @abstractmethod
    def is_engineered(self) -> bool:
        """Should return True for ECR, False for NCS"""
        return NotImplemented

    @classmethod
    @abstractmethod
    def adopt_limits(cls) -> float:
        """Computes annual adoption/deployment limit (MtCO2 capacity/yr)
        based on current cumulative deployment of this technology using
        cls.cumul_deployment (MtCO2/yr)"""
        return NotImplemented

    @abstractmethod
    def marginal_cost(self) -> float:
        """Computes marginal cost ($/tCO2) as a function of cumulative deployment (MtCO2/yr).
        Cumulative deployment is accessible via self.deployment_level"""
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

    def get_eff_factor(self):
        em = self.incidental_emissions()
        if em > 1:
            raise util.StrategyNotImplementedError(f'The strategy {self.__class__.__name__} emits more than '
                                                   f'one tCO2 per tCO2 captured. This is either an implementation '
                                                   f'error or a flawed CDR strategy.')
        return 1 - self.incidental_emissions()

    def get_adjusted_cost(self):
        """ Returns cost of this project, adjusted for incidental emissions
        so as to only count CDR on a net CO2 basis """
        return self.marginal_cost() / self.get_eff_factor()

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

    def incidental_emissions(self) -> float:
        # All NCS CO2 values are already computed on a net basis.
        return 0.0


class ECR(CDRStrategy):
    """
    ECR represents an Engineered Carbon Removal technique.
    """
    def is_engineered(self) -> bool:
        return True

    def incidental_emissions(self) -> float:
        """ Default behavior is simply adding the energy use in each sector
         by its respective emissions rate. """
        energy_basis = self.marginal_energy_use()
        yr = CDRStrategy.curr_year - CDRStrategy.start_year
        em_basis = self.__class__.GRID_EM[yr], self.__class__.HEAT_EM[yr], \
            self.__class__.TRANSPORT_EM[yr], self.__class__.FUEL_EM[yr]
        return np.dot(energy_basis, em_basis)
