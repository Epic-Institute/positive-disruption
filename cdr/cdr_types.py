#!/usr/bin/env python3
"""
cdr_types.py
Implements behavior of all individual CDR strategies, including both natural
natural and engineered CDR strategies. All strategies provide info about
their (1) adoption limits/potential, (2) cost, (3) energy use, and
(4) incidental emissions. One instance of each class represents
one deployed CDR project.

All classes defined here must be added to CDR_TECHS in cdr_main.py in order
to be put under consideration when developing the cost-optimal CDR mix.
"""

__author__ = "Zach Birnholz"
__version__ = "07.23.20"

import cdr.cdr_util as util
from cdr.cdr_abstract_types import CDRStrategy, NCS, ECR
import math
from scipy import integrate
import numpy as np

###########################################
# DEFINE NEW SPECIFIC CDR STRATEGIES HERE #
# as NCS (natural) or ECR (engineered)    #
###################################################################
# EACH STRATEGY MUST HAVE:                                        #
#    1. annual adoption limits (MtCO2/yr), with the header        #
#          @classmethod                                           #
#          def adopt_limits(cls) -> float:                        #
#                                                                 #
#    2. marginal_cost ($/tCO2), with the header                   #
#          def marginal_cost(self) -> float:                      #
#                                                                 #
#    3. marginal_energy_use (kWh/tCO2), with the header           #
#          def marginal_energy_use(self) -> tuple:                #
#       returning a tuple containing the energy used from         #
#       (electricity, heat, transportation, non-transport fuels)  #
#                                                                 #
#    And for ECR only:                                            #
#    4. incidental emissions (tCO2/tCO2), with the header         #
#        def incidental_emissions(self) -> float:                 #
#                                                                 #
#    5. A default project lifetime (yrs), defined at the class    #
#       level as:                                                 #
#          default_lifetime = ___                                 #
###################################################################

#############################
#   NATURAL CDR STRATEGIES  #
#    (subclasses of NCS)    #
#############################
""" TODO - waiting for TNC """


#############################
# ENGINEERED CDR STRATEGIES #
#    (subclasses of ECR)    #
#############################
class LTSSDAC(ECR):
    """ Low-temperature Solid Sorbent Direct Air Capture
        (Climeworks and Global Thermostat approach) """
    default_lifetime = 20

    @classmethod
    def adopt_limits(cls) -> float:
        # LTSSDAC adoption is assumed to be logistic.
        # M, a, b, and vertical shift derivation outlined in adoption curve writeup
        if CDRStrategy.curr_year < util.DAC_FIRST_YEAR:
            return 0
        else:
            return util.logistic_inverse_slope(23500, -8.636, 0.1746,
                                               cls.cumul_deployment + 57.134346 - util.LTSSDAC_FIRST_DEPLOYMENT)

    def marginal_cost(self) -> float:
        pass

    def marginal_energy_use(self) -> tuple:
        pass

    def incidental_emissions(self) -> float:
        pass


class HTLSDAC(ECR):
    """ High-temperature Liquid Solvent Direct Air Capture
            (Carbon Engineering approach) """
    default_lifetime = 25

    @classmethod
    def adopt_limits(cls) -> float:
        if CDRStrategy.curr_year < util.DAC_FIRST_YEAR:
            return 0
        else:
            return util.logistic_inverse_slope(11500, -3.407, 0.0917,
                                               cls.cumul_deployment + 880.6986515 - util.HTLSDAC_FIRST_DEPLOYMENT)

    def marginal_cost(self) -> float:
        pass

    def marginal_energy_use(self) -> tuple:
        pass

    def incidental_emissions(self) -> float:
        pass


class ExSituEW(ECR):
    """Ex-situ particle-spreading enhanced weathering on agricultural fields"""
    # EW projects can be maintained indefinitely given proper support
    default_lifetime = float('inf')
    LEVELIZING_LIFETIME = 30  # used for crf; 30 chosen for comparison with DAC

    @classmethod
    def adopt_limits(cls) -> float:
        # EW adoption is assumed to be logistic.
        # M, a, b, and vertical shift derivation outlined in adoption curve writeup
        return util.logistic_inverse_slope(4500, -6.258, 0.0994, cls.cumul_deployment + 9.5)

    def marginal_cost(self) -> float:
        """Returns $/tCO2 for this project.
        It is 'marginal' in the sense that this project was
        on the margin of EW at the time of its deployment. """

        tCO2 = self.capacity * (10 ** 6)  # capacity is in MtCO2 but we need tCO2
        total_cost = ExSituEW._rock_needed(tCO2) * self._cost_per_t_rock()

        # compute levelized $/tCO2
        return total_cost / tCO2 * \
            (util.crf(util.DISCOUNT_RATE, ExSituEW.LEVELIZING_LIFETIME) + ExSituEW._d(util.GRAIN_SIZE))

    def marginal_energy_use(self) -> tuple:
        """ Returns (electricity, heat, transport, non-transport fuel) energy in kWh/tCO2.
        It is 'marginal' in the sense that this project was on the margin of EW
        at the time of its deployment."""
        elec = 1839 * (util.GRAIN_SIZE ** -1.168) * util.learning(12828 + self.deployment_level, 12828, 0.08)
        heat = 0
        # TODO replace 0.263 (kWh/t*km) with actual transportation energy intensity for the current year
        transport = self._total_transport_per_t_rock() * 0.263 / util.CO2_PER_ROCK
        fuel = 26 / util.CO2_PER_ROCK
        if self.age == 0:
            # full rock application needed in first year
            return elec, heat, transport, fuel
        else:
            # only partial application needed in subsequent years
            d = ExSituEW._d(util.GRAIN_SIZE)
            return elec * d, heat * d, transport * d, fuel * d

    def incidental_emissions(self) -> float:
        energy_basis = self.marginal_energy_use()
        em_basis = 0, *4  # placeholder
        # TODO - determine how to access emissions intensity of each resource given CDRStrategy.current_year
        # yr = CDRStrategy.current_year
        # em_basis = grid_em_intensity[yr], heat_em_intensity[yr], transport_em_intensity[yr], fuel_em_intensity[yr]
        return np.dot(energy_basis, em_basis)

    # helper functions for ex-situ EW
    def _cost_per_t_rock(self) -> float:
        mining = 10  # $/trock
        grinding_capex_opex = 23.80 * util.crf(util.DISCOUNT_RATE, ExSituEW.LEVELIZING_LIFETIME) + 2.18
        grinding_energy = self.energy[0] * util.ELEC_COST * util.learning(12828 + self.deployment_level, 12828, 0.08)
        transportation = self._total_transport_per_t_rock() * util.TRANSPORT_COST * \
            (0.75 + 0.25 * util.learning(109 + self.deployment_level, 109, 0.21))
        spreading = 21 * util.FUEL_COST
        return mining + grinding_capex_opex + grinding_energy + transportation + spreading

    @staticmethod
    def _d(grain_size: float) -> float:
        """calculates dissolution rate (1/yr) for basalt"""
        return 69.18 * (grain_size ** -1.24) * (10 ** -10.53) * 140.7 * 3.155 * (10 ** 7)

    @staticmethod
    def _rock_needed(tCO2) -> float:
        """Returns tonnes of rock needed to capture the given tCO2 in one year.
        Calculated using m_rock = (A_warm + A_temp) * M
        and R_CO2 = (0.95 * A_warm + 0.35 * A_temp) * M * P * d(x) """
        num = tCO2 * (1 + util.A_WARM / util.A_TEMP)
        denom = util.CO2_PER_ROCK * ExSituEW._d(util.GRAIN_SIZE) * (0.95 * util.A_WARM / util.A_TEMP + 0.35)
        return num / denom

    def _total_transport_per_t_rock(self) -> float:
        """Computes total t*km of transportation required for this project
        to achieve its stated tCO2/yr capacity in its first year"""
        # capacity is in MtCO2 but we need tCO2
        rock_new = ExSituEW._rock_needed(self.capacity * (10 ** 6))
        rock_init = ExSituEW._rock_needed((self.deployment_level - self.capacity) * (10 ** 6))
        warm_transport = ExSituEW._warm_transport(rock_new, rock_init)
        temp_transport = ExSituEW._temperate_transport(rock_new, rock_init)
        return (warm_transport + temp_transport) / rock_new

    @staticmethod
    def _warm_transport(rock_new, rock_init):
        """Warm component of total transport"""
        max_mass = util.SPREADING_DENSITY * (util.A_WARM + util.A_TEMP)
        return integrate.quad(
            # warm transport distance function, applied to m_rock * (A_WARM/A_TOTAL)
            lambda m_rock: (
                272.44 * math.pow(m_rock / max_mass, 2.137) if m_rock / max_mass <= 0.8072
                else 8.2817 * math.exp(3.7607 * m_rock / max_mass)
            ),
            rock_init, rock_new + rock_init
        )[0]

    @staticmethod
    def _temperate_transport(rock_new, rock_init):
        """Temperate component of total transport"""
        return integrate.quad(
            # temperate transport distance function, applied to m = m_rock * (A_TEMP/A_TOTAL)
            # where distance = 8.3052*e^(m/(M*A_temp))
            lambda m_rock: 8.3052 * math.exp(4.5962 * m_rock / (util.SPREADING_DENSITY * (util.A_TEMP + util.A_WARM))),
            rock_init, rock_new + rock_init
        )[0]
