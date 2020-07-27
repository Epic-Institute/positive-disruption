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
# *********************************
# * EXAMPLE SKELETON ECR PROJECT: *
# *********************************
#
# class ExampleECR(ECR):
#     """ Brief description of this ECR technology.
#         (provide any relevant examples) """
#     default_lifetime = ____  # fill this in - represents individual project's lifetime
#     # levelizing_lifetime = ____  # only needed if default_lifetime is float('inf'); a good choice is 30
#
#     @classmethod
#     def adopt_limits(cls) -> float:
#         """ Returns the maximum MtCO2/yr capacity that can be installed
#          in a year, given the current cls.cumul_deployment (MtCO2/yr),
#          in the absence of any other competing CDR strategies. """
#         pass
#
#     def marginal_cost(self) -> float:
#         """ Returns the $/tCO2 cost of this project based on self.deployment_level,
#          but NOT adjusted for impacts of incidental emissions or CDR credits.
#          self.deployment_level represents this strategy's cumulative deployment
#          (MtCO2/yr) at the time this project was deployed.
#          It is 'marginal' in the sense that this project was the marginal project
#          at the time of its deployment. """
#         pass
#
#     def marginal_energy_use(self) -> tuple:
#         """ Returns kWh used/tCO2 captured as a tuple:
#          (electricity, heat, transportation, non-transportation fuels) """
#         pass
#
#     def incidental_emissions(self) -> float:
#         """ Returns tCO2 emitted/tCO2 captured """
#         pass
#
##################################

class LTSSDAC(ECR):
    """ Low-temperature Solid Sorbent Direct Air Capture
        (Climeworks and Global Thermostat approach) """
    default_lifetime = 20
    cumul_deployment = util.LTSSDAC_FIRST_DEPLOYMENT  # assumed starting in 2025

    @classmethod
    def adopt_limits(cls) -> float:
        # LTSSDAC adoption is assumed to be logistic.
        # M, a, b, and vertical shift derivation outlined in adoption curve writeup
        if CDRStrategy.curr_year < util.DAC_FIRST_YEAR:
            return 0
        else:
            vertical_shift = 57.134346 - util.LTSSDAC_FIRST_DEPLOYMENT
            return util.logistic_inverse_slope(23500, -8.636, 0.1746, cls.cumul_deployment + vertical_shift)

    def marginal_cost(self) -> float:
        capex = self._capex_new() * util.crf(n_yrs=self.get_levelizing_lifetime()) / util.LTSSDAC_UTILIZATION
        opex = self._capex_new() * 0.037
        energy_basis = self.marginal_energy_use()
        energy = util.learning(self.deployment_level, util.LTSSDAC_FIRST_DEPLOYMENT, 0.137) * (
            energy_basis[0] * util.ELEC_COST + energy_basis[1] * util.HEAT_COST
        )
        return capex + opex + energy

    def marginal_energy_use(self) -> tuple:
        learning = util.learning(self.deployment_level, util.LTSSDAC_FIRST_DEPLOYMENT, 0.137)
        return 303 * learning, 1330 * learning, 0, 0

    # LTSSDAC uses default ECR incidental_emissions function

    def _capex_new(self):
        """ Returns current CAPEX, adjusted for one-factor learning """
        return 979 * util.learning(self.deployment_level, util.LTSSDAC_FIRST_DEPLOYMENT, 0.15)


class HTLSDAC(ECR):
    """ High-temperature Liquid Solvent Direct Air Capture
            (Carbon Engineering approach) """
    default_lifetime = 25
    cumul_deployment = util.HTLSDAC_FIRST_DEPLOYMENT  # assumed starting in 2025

    @classmethod
    def adopt_limits(cls) -> float:
        if CDRStrategy.curr_year < util.DAC_FIRST_YEAR:
            return 0
        else:
            vertical_shift = 880.6986515 - util.HTLSDAC_FIRST_DEPLOYMENT
            return util.logistic_inverse_slope(11500, -3.407, 0.0917, cls.cumul_deployment + vertical_shift)

    def marginal_cost(self) -> float:
        capex = self._capex_new() * util.crf(n_yrs=self.get_levelizing_lifetime()) / util.LTSSDAC_UTILIZATION
        opex = self._capex_new() * 0.037
        energy_basis = self.marginal_energy_use()
        energy = energy_basis[0] * util.ELEC_COST + energy_basis[1] * util.HEAT_COST
        return capex + opex + energy

    def marginal_energy_use(self) -> tuple:
        return 357, 1458, 0, 0

    # HTLSDAC uses default ECR incidental_emissions function

    def _capex_new(self):
        """ Returns current CAPEX, adjusted for one-factor learning """
        return 1132 * util.learning(self.deployment_level, util.LTSSDAC_FIRST_DEPLOYMENT, 0.1)


class ExSituEW(ECR):
    """Ex-situ particle-spreading enhanced weathering on agricultural fields"""
    # EW projects can be maintained indefinitely given proper support
    default_lifetime = float('inf')
    levelizing_lifetime = 30  # used for crf; 30 chosen for comparison with DAC

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
            (util.crf(n_yrs=self.get_levelizing_lifetime()) + ExSituEW._d(util.GRAIN_SIZE))

    def marginal_energy_use(self) -> tuple:
        """ Returns (electricity, heat, transport, non-transport fuel) energy in kWh/tCO2.
        It is 'marginal' in the sense that this project was on the margin of EW
        at the time of its deployment."""
        elec = 1839 * (util.GRAIN_SIZE ** -1.168) * util.learning(12828 + self.deployment_level, 12828, 0.08)
        heat = 0
        transport = self._total_transport_per_t_rock() * util.TRANSPORT_KWH_PER_TKM / util.CO2_PER_ROCK
        fuel = 26 / util.CO2_PER_ROCK
        if self.age == 0:
            # full rock application needed in first year
            return elec, heat, transport, fuel
        else:
            # only partial application needed in subsequent years
            d = ExSituEW._d(util.GRAIN_SIZE)
            return elec * d, heat * d, transport * d, fuel * d

    # ExSituEW uses default ECR incidental_emissions function

    # helper functions for ex-situ EW
    def _cost_per_t_rock(self) -> float:
        mining = 10  # $/t rock
        grinding_capex_opex = 23.80 * util.crf(n_yrs=self.get_levelizing_lifetime()) + 2.18
        energy_basis = self.marginal_energy_use()
        grinding_energy = energy_basis[0] * util.ELEC_COST * util.learning(12828 + self.deployment_level, 12828, 0.08)
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
        """Warm component of total transport (t*km)"""
        max_mass = util.SPREADING_DENSITY * (util.A_WARM + util.A_TEMP)
        return integrate.quad(
            # warm transport distance function, applied to m = m_rock * (A_WARM/A_TOTAL)
            # where distance = { 272.44 km * (m / (M*A_warm))^2.137,       m / (M*A_warm) <= 0.8072
            #                  { 8.2817 km * e^(3.7607 * (m / (M*A_warm)), m / (M*A_warm) >  0.8072
            lambda m_rock: (
                272.44 * math.pow(m_rock / max_mass, 2.137) if m_rock / max_mass <= 0.8072
                else 8.2817 * math.exp(3.7607 * m_rock / max_mass)
            ),
            rock_init, rock_new + rock_init
        )[0]

    @staticmethod
    def _temperate_transport(rock_new, rock_init):
        """Temperate component of total transport (t*km)"""
        return integrate.quad(
            # temperate transport distance function, applied to m = m_rock * (A_TEMP/A_TOTAL)
            # where distance = 8.3052 km * e^(m / (M*A_temp))
            lambda m_rock: 8.3052 * math.exp(4.5962 * m_rock / (util.SPREADING_DENSITY * (util.A_TEMP + util.A_WARM))),
            rock_init, rock_new + rock_init
        )[0]


class GeologicStorage(ECR):
    """ Traditional geologic storage paired with an
     engineered capture approach"""
    default_lifetime = float('inf')  # lifetime depends on paired project from __init__

    def __init__(self, paired_project: CDRStrategy, compress_t: float = None, compress_p1: float = None):
        super().__init__(paired_project.capacity)
        if (compress_t is None) != (compress_p1 is None):
            raise TypeError('Both or neither of the compress_t and compress_p1 arguments to '
                            'GeologicStorage __init__ must be None.')
        # details about this storage project depend on the paired capture project
        self.paired_project = paired_project
        self.compress_temp = compress_t
        self.compress_pres = compress_p1
        self.lifetime = paired_project.lifetime

    @classmethod
    def adopt_limits(cls) -> float:
        return float('inf')  # assuming no limits on geologic storage

    def marginal_cost(self) -> float:
        if self.compress_temp is not None:
            compress_capex_opex = (100.8 * util.crf(self.get_levelizing_lifetime()) + 3.9) / 10
            compress_energy = self._calc_compression_energy(self.compress_temp, self.compress_pres) * util.ELEC_COST
            compress_cost = compress_capex_opex + compress_energy
        else:
            compress_cost = 0  # no compression needed
        return compress_cost + util.PIPELINE_COST + util.INJECTION_COST

    def marginal_energy_use(self) -> tuple:
        # calculate individual compression, pipeline, and injection energy usage
        if self.compress_temp is not None:
            compression_elec = self._calc_compression_energy(self.compress_temp, self.compress_pres)
        else:
            compression_elec = 0  # no compression needed
        transport_scale_factor = util.PIPELINE_LENGTH / util.PIPELINE_CAPACITY
        pipeline_elec = 837900 * transport_scale_factor
        pipeline_transport = 494940 * util.TRANSPORT_KWH_PER_TKM / self.lifetime * transport_scale_factor
        pipeline_fuel = 5343.16 * util.KWH_PER_GJ / self.lifetime * transport_scale_factor
        inject_elec = self._calc_compression_energy(util.WELLHEAD_T, 10.7, 15)
        inject_transport = 67819920 / util.WELL_CAPACITY * util.TRANSPORT_KWH_PER_TKM / self.lifetime

        # combine into total energy usages
        total_elec = compression_elec + pipeline_elec + inject_elec
        total_transport = pipeline_transport + inject_transport
        total_fuel = pipeline_fuel
        return total_elec, 0, total_transport, total_fuel

    def incidental_emissions(self) -> float:
        """ Emissions are energy emissions plus pipeline leakage """
        pipeline_leakage = util.PIPELINE_LEAKAGE * util.PIPELINE_LENGTH / util.PIPELINE_CAPACITY
        return super().incidental_emissions() + pipeline_leakage

    @staticmethod
    def _calc_compression_energy(temp, p1=util.AIR_P, p2=11):
        """ Calculates minimum compression energy (kWh/tCO2) at the given temperature """
        t1 = 0.9942 * 8.3145 * temp / 44.01
        t2 = 4 * 1.293759 / (1.293759 - 1)
        t3 = math.pow(p2 / p1, ((1.293759 - 1) / (4 * 1.293759))) - 1
        return t1 * t2 * t3 / util.COMPRESS_EFF / 1000 * util.KWH_PER_GJ
