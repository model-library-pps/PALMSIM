#!/usr/bin/env python

########
# README
########

''' Provides the soil-water balance models.

Developed for Python 3.
'''

########
# Header
########

__author__ = "Willem Hekman"
__copyright__ = "Copyright 2018, PPS"
__credits__ = ["Willem Hekman"]
__license__ = "Copyleft,see http://models.pps.wur.nl/content/licence_agreement"
__version__ = "1.0.0.1"
__maintainer__ = "Willem Hekman"
__email__ = "willem.hekman@wur.nl"
__status__ = "Development"

##################
# Import Libraries
##################

import yaml
from copy import deepcopy

from components.helpers import Parameter
from components.helpers import add_dumps
from components.helpers import METERS_PER_HECTARE
from components.helpers import DAYS_PER_MONTH
from components.helpers import GAUGE_PLANTING_DENSITY

import numpy as np

@add_dumps
class Roots(object):
    ''' A class which models a field of roots.

    Main instance variables:
        - mass

    Note, mass determines the maintenance requirement.

    Main parameters:
        potential growth rates

    The potential growth rate determines the sink strenght which
    determines the assimilats for mass growth.

    Note, as an ad hoc assumption, mass loss/turnover is a fraction
    of the standing mass plus a constant rate.
    '''

    default_parameters = yaml.load('''
    specific_maintenance:
        value: 0.0022
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                Photosynthese et productivite du palmier a huile en liaison
                avec les facteurs climatiques.
                Table ?.'
        uncertainty: 5%
    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    In turn based on van Kraalingen, D.W.G., 1989.
                    See text below table II and table III.'
        uncertainty: 5%
    loss_param_a:
        value: 0.013
        unit: '1/month'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%
    loss_param_b:
        value: 0.06
        unit: 'tonne_DM/ha/month'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%
    potential_growth_rate:
        value: 0.00135
        unit: 'tonne_DM/palm/month'
        info: 'The potential growth rate'
        source: 'Based on Corley et al., 1971, Productivity of the Oil Palm in Malaysia.'
        uncertainty: 5%
    ''')

    default_initial_values = yaml.load('''
    mass:
        value: 20
        uncertainty: 50%
        unit: 'tonne_DM/palm'
        info: 'Initial weight of the plant part.'
        source: 'Based on a root:shoot ratio of around 1:1. See also, Advances in Oil Palm Research Volume 1, 2000. p. 26.'
    ''')

    variable_units = dict(assim_growth                  = 'tonne_CH2O/ha/month',
                          maintenance_requirement       = 'tonne_CH2O/ha/month',
                          mass                          = 'tonne_DM/ha',
                          mass_change_rate              = 'tonne_DM/ha/month',
                          mass_growth_rate              = 'tonne_DM/ha/month',
                          mass_loss_rate                = 'tonne_DM/ha/month',
                          potential_growth_rate = 'tonne_DM/ha/month',
                          sink_strength_potential = 'tonne_CH2O/ha/month',
                          )

    _attribute_sort_order = ['mass','assim','maint']

    _name = 'roots'
    _style = 'Legacy'
    _version = '1.0.0.1'
    _prefix = _name

    def __init__(self,palm=None):

        self._palm = palm

        self.parameters = deepcopy(self.default_parameters)

        self.initial_values = self.default_initial_values

        # t/ha
        self.mass  = 0.001*self._planting_density*self.initial_values['mass']['value']

    _loss_param_a         = Parameter('loss_param_a')
    _loss_param_b         = Parameter('loss_param_b')
    _specific_maintenance = Parameter('specific_maintenance')
    _conversion_efficiency= Parameter('conversion_efficiency')
    _potential_growth_rate= Parameter('potential_growth_rate')

    ###############
    # Interface
    ###############
    @property
    def _MAP(self):
        ''' Months after planting. '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    @property
    def _planting_density(self):
        if self._palm is None:
            return GAUGE_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    ###############
    # Sink-strength
    ###############
    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (tonne_DM/ha/month). '''
        return self._planting_density*self._potential_growth_rate

    @property
    def sink_strength_potential(self):
        ''' Potential sink strength (tonne_CH2O/ha/month). '''
        return self.potential_growth_rate/self._conversion_efficiency

    @property
    def assim_growth(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''

        if self._palm is None:
            return 0
        else:
            return self._palm.assimilates.assim_growth_roots

    ########
    # Mass
    ########
    @property
    def mass_change_rate(self):
        ''' Mass change rate (tonne_DM/ha/month). '''
        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass change rate (tonne_DM/ha/month).

        Parameters
        ----------
        conversion_efficiency: float, conversion efficiency (g_DM/g_CH2O)
        assim_growth: float, assimilates for growth (tonne_CH2O/ha/month)
        '''

        return self._conversion_efficiency*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Loss of root mass (DM ton/ha/month).

        Notes
        -----
        Based on the legacy version. Quite ad hoc.

        L = a*M + b

        where

        L : loss of root mass (g_DM/palm/day)
        M : root mass (kg_DM/palm)

        a = 0.013 : mass loss fraction (1/month)
        b = 0.06 : mass loss rate (DM ton/ha/month)

        Notes
        -----
        In the legacy version

        L = min(1*M,a*M+b)

        where 1*M acts as a trivial bound;
        the bound is met at around 0.06 DM ton.

        Here we do without this trivial bound.

        '''

        mass_ = self.mass

        a = self._loss_param_a
        b = self._loss_param_b

        return  a*mass_ + b

    #############
    # Maintenance
    #############
    @property
    def maintenance_requirement(self):

        ''' Maintenance requirement (tonne_CH2O/ha/month). '''

        return max(0,DAYS_PER_MONTH*self._specific_maintenance*self.mass)

    ##########
    # Updating
    ##########
    def update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month.'''

        self._update(dt=dt)

    def _update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month. '''

        # tonne_DM/ha
        self.mass += self.mass_change_rate*dt

LatestRoots = Roots