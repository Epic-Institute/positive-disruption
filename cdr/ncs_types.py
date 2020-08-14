#!/usr/bin/env python3
"""
ncs_types.py
Implements behavior of all individual NCS (natural CDR) strategies.
All NCS strategies provide info about their (1) adoption limits/potential,
(2) cost, (3) energy use, (4) project lifetime, and (5) incidental emissions.
#5 is not necessary if calculations for 1-3 are already done on a net CO2 basis.
One instance of each class represents one deployed CDR project.

All classes defined here must be added to CDR_TECHS in cdr_main.py in order
to be put under consideration when developing the cost-optimal CDR mix.
"""

__author__ = "Zach Birnholz"
__version__ = "08.14.20"

from cdr.cdr_abstract_types import CDRStrategy, NCS
import cdr.cdr_util as util

###################################################################
# THIS FILE IS FOR SPECIFIC NCS (natural) STRATEGIES.             #
# EACH CDR STRATEGY MUST HAVE:                                    #
#    1. annual adoption limits (MtCO2/yr), with the header        #
#          @classmethod                                           #
#          def adopt_limits(cls) -> float:                        #
#                                                                 #
#    2. curr_year_cost ($/tCO2), with the header                  #
#          @util.once_per_year                                    #
#          def marginal_levelized_cost(self) -> float:           #
#                                                                 #
#    3. marginal_levelized_cost ($/tCO2), with the header        #
#          @util.cacheit                                          #
#          def marginal_levelized_cost(self) -> float:           #
#                                                                 #
#    4. marginal_energy_use (kWh/tCO2), with the header           #
#          @util.cacheit                                          #
#          def marginal_energy_use(self) -> tuple:                #
#       returning a tuple containing the energy used from         #
#       (electricity, heat, transportation, non-transport fuels)  #
#                                                                 #
#    5. A default project lifetime (yrs), defined at the class    #
#       level as:                                                 #
#          default_lifetime = ___                                 #
#                                                                 #
#    And for ECR only:                                            #
#    6. incidental emissions (tCO2/tCO2), with the header         #
#          @util.once_per_year                                    #
#          def incidental_emissions(self) -> float:               #
#                                                                 #
#    Also, if you desire a project capacity/granularity other     #
#    than the default defined in crd_util.PROJECT_SIZE, then      #
#    override __init__ as                                         #
#          def __init__(self, capacity=new_default_capacity):     #
#              super().__init__(capacity=new_default_capacity)    #
#    replacing new_default_capacity with                          #
#    with your desired numerical value.                           #
#                                                                 #
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
#          in a year, given the current cls.active_deployment (MtCO2/yr)
#          and cls.cumul_deployment (MtCO2/yr), in the absence of any other
#          competing CDR strategies. """
#         pass
#
#     @util.once_per_year
#     def curr_year_cost(self) -> float:
#         """ Returns the raw $/tCO2 (in 2020$) cost of the project in the year given
#          by self.age. This is not adjusted for the impacts of incidental emissions
#          or CDR credits and, in addition to being based on the project’s current age,
#          is likely based on the project’s capacity (self.capacity) and its original
#          deployment level (self.deployment_level), which represents the technology’s
#          cumulative deployment (MtCO2/yr) at the time of this project’s creation.
#          In theory, levelizing each of the yearly costs from this function over the
#          lifetime of the project should yield the same result as the
#          marginal_levelized_cost function. """
#         pass
#
#     @util.cacheit
#     def marginal_levelized_cost(self) -> float:
#         """ Returns the single levelized "sticker price" $/tCO2 (in 2020$) of the
#          project, used for comparison with other CDR projects. This is not adjusted
#          for the impacts of incidental emissions or CDR credits and is based on the
#          project’s capacity (self.capacity) and its original deployment level
#          (self.deployment_level), which represents the technology’s cumulative deployment
#          (MtCO2/yr) at the time of this project’s creation. It is 'marginal' in the
#          sense that this project was the marginal project at the time of its deployment. """
#         pass
#
#     @util.cacheit
#     def marginal_energy_use(self) -> tuple:
#         """ Returns kWh used/tCO2 captured as a tuple:
#          (electricity, heat, transportation, non-transportation fuels) """
#         pass
#
#     # ONLY IF ABOVE CALCULATIONS ARE NOT ALREADY ON A NET BASIS
#     @util.once_per_year
#     def incidental_emissions(self) -> float:
#         """ Returns tCO2 emitted/tCO2 captured """
#         pass
#
##################################

""" Add NCS classes here """
# TODO
