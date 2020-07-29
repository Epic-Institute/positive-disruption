#!/usr/bin/env python3
"""
ncs_types.py
Implements behavior of all individual NCS (natural CDR) strategies.
All NCS strategies provide info about their (1) adoption limits/potential,
(2) cost, (3) energy use, and (4) incidental emissions. #4 is not necessary
if calculations for 1-3 are already done on a net CO2 basis.
One instance of each class represents one deployed CDR project.

All classes defined here must be added to CDR_TECHS in cdr_main.py in order
to be put under consideration when developing the cost-optimal CDR mix.
"""

__author__ = "Zach Birnholz"
__version__ = "07.29.20"

import cdr.cdr_util as util
from cdr.cdr_abstract_types import CDRStrategy, NCS

###################################################################
# DEFINE NEW SPECIFIC NCS STRATEGIES HERE.                        #
# EACH STRATEGY MUST HAVE:                                        #
#    1. annual adoption limits (MtCO2/yr), with the header        #
#          @classmethod                                           #
#          def adopt_limits(cls) -> float:                        #
#                                                                 #
#    2. marginal_cost ($/tCO2), with the header                   #
#          @util.cacheit                                          #
#          def marginal_cost(self) -> float:                      #
#                                                                 #
#    3. marginal_energy_use (kWh/tCO2), with the header           #
#          @util.cacheit                                          #
#          def marginal_energy_use(self) -> tuple:                #
#       returning a tuple containing the energy used from         #
#       (electricity, heat, transportation, non-transport fuels)  #
#                                                                 #
#    And for ECR only:                                            #
#    4. incidental emissions (tCO2/tCO2), with the header         #
#          @util.once_per_year                                    #
#          def incidental_emissions(self) -> float:               #
#                                                                 #
#    5. A default project lifetime (yrs), defined at the class    #
#       level as:                                                 #
#          default_lifetime = ___                                 #
###################################################################

# *********************************
# * EXAMPLE SKELETON NCS PROJECT: *
# *********************************
#
# class ExampleNCS(NCS):
#     """ Brief description of this NCS technology.
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

""" TODO - waiting for TNC """
