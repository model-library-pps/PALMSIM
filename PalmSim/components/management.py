#!/usr/bin/env python

########
# README
########

''' Provides the management model.

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

from .helpers import add_dumps

from .constants import DEFAULT_PLANTING_DENSITY

import numpy as np

@add_dumps
class Management(object):
    ''' Models the management of a palm plantation.

    Main (instance) variables:
        - planting_density (1/ha)
        - prune_rate_mass (t DM/ha/month)
        - prune_rate_count (1/ha/month)

    Notes
    -----
    The legacy version (2014) made use of a "goal frond mass"
    to determine the prune rate in terms of mass (t DM/ha/month).

    This current version instead revolves around goal frond count(s) (!)
    from which the prune rate in terms of mass follows.

    '''

    default_parameters = yaml.load('''
    planting_density:
        value: 138
        unit: '1/ha'
        info: 'The planting density.'
        source: ''
        error: 1%
    prune_period:
        value: 3
        unit: 'month'
        info: 'How often the site is pruned.'
        source: 'Based on the actual schedule of an estate manager.'
        error: 10%
    first_prune_month:
        value: 0
        unit: 'month'
        info: 'Which month of the year is
                the first month of periodic pruning e.g. January -> 0th month.'
        source: 'Choice.'
        error: 10%
    t_start_periodic_pruning:
        value: 48
        unit: 'month'
        info: 'The start of the periodic pruning.
                --- note, a work-around, read the docs of the management class.'
        source: 'Based on pictures in the booklet
                    Oil Palm Vegetative Measurement Manual, MPOB, 2017.'
        error: 10%
    fronds_goal_count_t0:
        value: 50
        unit: '1/palm'
        info: 'The desired number of fronds for a young palm (t0=0 YAP).'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.'
        error: 10%
    fronds_goal_count_t1:
        value: 40
        unit: '1/palm'
        info: 'The desired number of fronds for a young palm (t0=0 YAP).'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.'
        error: 10%
    ''')

    variable_units = dict(goal_mass_fronds = 'tonne_DM/ha',
                            planting_density = 'palms/ha',
                            prune_rate       = 'tonne_DM/ha',
                            )

    _name = 'management'
    _prefix = _name

    _version = '2.0.1'

    def __init__(self,palm=None):

        # e.g. to get the age of the palm
        self._palm = palm
        self.parameters = deepcopy(self.default_parameters)
        self.frond_count = 0

    def get_frond_count(self):
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.count

    @property
    def planting_density(self):
        ''' The planting density (1/ha). '''
        return self.parameters['planting_density']['value']

    @property
    def _MAP(self):
        ''' Months after planting (months). '''
        if self._palm is None:
            #proto-typing
            return 0
        else:
            return self._palm.MAP

    @property
    def prune_rate_mass(self):
        ''' Prune rate (tonne_DM/ha/month) in terms of frond DM mass.

        Y = f*M/dt, here dt := 1.

        '''

        if self._palm is None:
            return 0
        else:
            # % pruned per month
            prune_fraction = self.prune_rate_count/self._palm.fronds.count
            return prune_fraction*self._palm.fronds.mass

    @property
    def prune_rate_count(self):
        ''' Prune rate (1/ha/month) in terms of frond count. '''
        if self._palm is None:
            return 0
        else:
            periodic_pruning = self.prune_rate_count_periodic
            harvest_pruning = self.prune_rate_count_harvest
            pruning = periodic_pruning + harvest_pruning
            return pruning

    @property
    def prune_rate_count_periodic_potential(self):
        ''' Periodic prune rate (1/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return max(0,self.frond_count -\
                             self.fronds_goal_count -\
                              self.prune_rate_count_harvest)

    @property
    def _prune_period(self):
        ''' Periodic prune rate (1/month). '''
        return self.parameters['prune_period']['value']

    @property
    def is_periodic_pruning(self):
        ''' Whether this month there is periodic pruning (bool). '''
        t_start = self.parameters['t_start_periodic_pruning']['value']
        first_month = self.parameters['first_prune_month']['value']

        MAP = self._MAP

        if self._MAP <= t_start:
            return 1
        elif ((MAP - first_month) % self._prune_period == 0):
            return 1
        else:
            return 0

    @property
    def prune_rate_count_periodic(self):
        ''' Periodic prune rate (1/ha/month).

        For the time being, since we do not model senescence.
        We act as if before bunch production sets on
        fronds are pruned monthly to keep
        the count around 50 fronds/palm.

        After this age the main pruning is actually periodical.
        '''
        if self._palm is None:
            return 0
        elif self.is_periodic_pruning:
            return self.prune_rate_count_periodic_potential
        else:
            return 0

    @property
    def prune_rate_count_harvest(self):
        ''' Harvest related prune rate (1/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return max(0,self._palm.organs.bunch_count)

    @property
    def fronds_goal_count_alt(self):
        ''' The goal number of fronds/ha.

        References
        ----------

        Gerritsma, W. and Soebagyo, F.X., 1998.
        An analysis of the growth of leaf area of oil palm in indonesia.
        Fig.2
        '''
        t = self._MAP

        y1 = self.parameters['fronds_goal_count_t1']['value']
        y0 = self.parameters['fronds_goal_count_t0']['value']

        # months
        t1 = 360
        t0 = 0

        # The slope
        a = (y1-y0)/(t1-t0)
        y = a*(t-t0) + y0

        return y

    @property
    def fronds_goal_count(self):
        ''' The goal number of fronds/ha.

        References
        ----------

        Gerritsma, W. and Soebagyo, F.X., 1998.
        An analysis of the growth of leaf area of oil palm in indonesia.
        Fig.2
        '''

        return self.planting_density*self.fronds_goal_count_alt

    def update(self):
        self.frond_count = self.get_frond_count()

LatestManagement = Management