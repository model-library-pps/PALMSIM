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

from components.helpers import Spline
from components.helpers import Parameter
from components.helpers import add_dumps
from components.helpers import METERS_PER_HECTARE
from components.helpers import DAYS_PER_MONTH
from components.helpers import GAUGE_PLANTING_DENSITY

@add_dumps
class Trunk(object):
    ''' A class which models a field of trunks.

    Main instance variables:
        - mass

    Note, mass determines the maintenance requirement.

    Main parameters:
        potential growth rates

    The potential growth rate determines the sink strenght which
    determines the assimilats for mass growth.
    Note, the potential trunk growth rate is modelled as
    a function of months after planting,
    since we observe that the trunk growth slows
    down with age (presumably linked to the frond opening rate slowing).
    See the reference listed below.

    Note, (DM) mass loss is taken to be zero.

    References
    ----------
    Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971.
    Productivity of the oil palm in Malaysia.
    '''

    default_parameters = yaml.load('''
    specific_maintenance:
        value: 0.0005
        unit: 'tonne_CH2O/tonne_DM/day'
        info: 'The specific maintenance.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
        uncertainty: 5%
    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
        uncertainty: 5%
    mass_loss_rate:
        value: 0.0
        unit: 'tonne_DM/ha/day'
        info: 'The mass loss rate.'
        source: 'Assumption by Hoffman/Alba.'
        uncertainty: 5%
    potential_growth_rates:
        value: [[0,1.1],[60,1.1],[120,1.1],[180,.9],[240,0.63],[360,0.225]]
        unit: '[month,tonne_DM/palm/month]'
        info: 'The potential growth rate at different points in time, determines the potential sink strength and thus assimilate partitioning.'
        source: 'Loosely based on reported growth rates found in Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971. Productivity of the oil palm in Malaysia.'
        uncertainty: 5%
    ''')

    default_initial_values = yaml.load('''
    mass:
        value: 20
        uncertainty: 10%
        unit: 'kg_DM/plant'
        info: 'Initial weight of the plant part.'
        source: 'Based Advances in Oil Palm Research Volume 1, 2000. p. 26.'
    ''')

    variable_units = dict(assim_growth                  = 'tonne_CH2O/ha/month',
                          maintenance_requirement       = 'tonne_CH2O/ha/month',
                          mass                          = 'tonne_DM/ha',
                          mass_change_rate              = 'tonne_DM/ha/month',
                          mass_alt                      = 'kg_DM/palm',
                          mass_change_rate_alt          = 'kg_DM/palm/month',
                          mass_growth_rate              = 'tonne_DM/ha/month',
                          mass_loss_rate                = 'tonne_DM/ha/month',
                          potential_growth_rate         = 'tonne_DM/ha/month',
                          sink_strength_potential       = 'tonne_CH2O/ha/month',
                          )

    _attribute_sort_order = ['mass','assim','maint']

    _name = 'trunk'
    _style = 'Legacy'
    _version = 'v0.01'
    _prefix = _name

    def __init__(self,palm=None):

        self._palm = palm
        self.parameters = deepcopy(self.default_parameters)

        self.initial_values = self.default_initial_values

        # t/ha
        self.mass  = 0.001*self._planting_density*self.initial_values['mass']['value']

        self._potential_growth_rate_spline = Spline(self.parameters['potential_growth_rates']['value'],k=3)

    _mass_loss_rate       = Parameter('mass_loss_rate')
    _specific_maintenance = Parameter('specific_maintenance')
    _conversion_efficiency= Parameter('conversion_efficiency')

    ###########
    # Interface
    ###########
    @property
    def _planting_density(self):
        ''' Planting density (1/ha). '''
        if self._palm is None:
            return GAUGE_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    @property
    def _MAP(self):
        ''' Months after planting (month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    ###############
    # Sink-strength
    ###############
    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (tonne_DM/ha/month). '''
        MAP = self._MAP
        return self._planting_density*self._potential_growth_rate_spline.calc(MAP)/1000

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
            return self._palm.assimilates.assim_growth_trunk

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
        ''' Mass loss rate (tonne_DM/ha/month)'''
        return self._mass_loss_rate

    @property
    def mass_alt(self):
        ''' Mass change rate (kg_DM/palm). '''
        return (1/self._planting_density)*10**3*self.mass

    @property
    def mass_change_rate_alt(self):
        ''' Mass change rate (kg_DM/palm/month). '''
        return (1/self._planting_density)*10**3*self.mass_change_rate


    #############
    # Maintenance
    #############
    @property
    def maintenance_requirement(self):

        ''' Maintenance requirement (tonne_CH2O/ha/month).

        Maintenance = days_per_month (days/month)
                        *specific_maintenance (g_CH2O/g_DM/day)
                        *mass (tonne_DM/ha)
        '''

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

        if self.mass < 0:
            self.mass = 0

LatestTrunk = Trunk
