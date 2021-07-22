#!/usr/bin/env python

''' Contains the management modelling '''

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
        - prune_rate (1/ha/day)
        - prune_rate_mass (t DM/ha/day)

    Notes
    -----
    The legacy version (2014) made use of a "goal frond mass"
    to determine the prune rate in terms of mass (t DM/ha/day).

    This current version revolves around goal frond count(s) (!)
    from which the mass prune rate follows.

    '''

    parameters = yaml.load('''
        planting_density:
            value: 138
            unit: '1/ha'
            info: 'The planting density.'
            source: ''
            uncertainty: 1%
        prune_period:
            value: 3
            unit: 'month'
            info: 'How often the site is pruned.'
            source: 'Based on the actual schedule of an estate manager.'
            uncertainty: 10%
        first_prune_month:
            value: 0
            unit: 'month'
            info: 'Which month of the year is
                    the first month of periodic pruning e.g. January -> 0th month.'
            source: 'Choice.'
            uncertainty: 10%
        t_start_periodic_pruning:
            value: 48
            unit: 'month'
            info: 'The start of the periodic pruning.
                    --- note, a work-around, read the docs of the management class.'
            source: 'Based on pictures in the booklet
                        Oil Palm Vegetative Measurement Manual, MPOB, 2017.'
            uncertainty: 10%
        fronds_goal_count_t0:
            value: 50
            unit: '1/palm'
            info: 'The desired number of fronds for a young palm (t0=0 YAP).'
            source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                        An analysis of the growth of leaf area of
                        oil palm in indonesia.'
            uncertainty: 10%
        fronds_goal_count_t1:
            value: 40
            unit: '1/palm'
            info: 'The desired number of fronds for a young palm (t0=0 YAP).'
            source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                        An analysis of the growth of leaf area of
                        oil palm in indonesia.'
            uncertainty: 10%
        ''', Loader=yaml.SafeLoader)

    units = yaml.load('''
        frond_count: 1/ha
        fronds_goal_count: 1/ha
        fronds_goal_count_per_palm: 1/ha
        is_periodic_pruning_month: bool
        planting_density: palms/ha
        potential_periodic_prune_rate: 1/ha/day
        prune_rate: 1/ha/day
        prune_rate_harvest: 1/ha/day
        prune_rate_mass: kg_DM/ha/day
        prune_rate_periodic: 1/ha/day
        ''', Loader=yaml.SafeLoader)

    _prefix = 'management'

    def __init__(self,palm=None):

        # e.g. to get the age of the palm
        self._palm = palm
        self.frond_count = 0

    @property
    def _MAP(self):
        ''' Months after planting (months). '''
        if self._palm is None:
            #proto-typing
            return 0
        else:
            return self._palm.MAP

    def get_frond_count(self):
        """ Get the number of fronds (1/ha). """
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.count

    @property
    def planting_density(self):
        ''' The planting density (1/ha). '''
        if self._palm is None:
            return self.parameters['planting_density']['value']
        else:
            return self._palm.planting_density

    @property
    def prune_rate_mass(self):
        ''' Prune rate (kg_DM/ha/day) in terms of frond DM mass. '''

        if self._palm is None:
            return 0
        else:
            # % pruned per month
            prune_fraction = self.prune_rate/self._palm.fronds.count
            return prune_fraction*self._palm.fronds.mass

    @property
    def prune_rate(self):
        ''' Prune rate (1/ha/day) in terms of frond count. '''
        if self._palm is None:
            return 0
        else:
            pruning = self.prune_rate_periodic + self.prune_rate_harvest
            return pruning

    @property
    def potential_periodic_prune_rate(self):
        ''' Periodic prune rate (1/ha/day). '''
        if self._palm is None:
            return 0
        else:
            timespan = 30 # days
            available = self.frond_count - self.prune_rate_harvest
            target = self.fronds_goal_count
            target_change = max(0, available - target)
            target_rate = target_change/timespan
            return target_rate

    @property
    def _prune_period(self):
        ''' Prune period. '''
        return self.parameters['prune_period']['value']

    @property
    def is_periodic_pruning_month(self):
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
    def prune_rate_periodic(self):
        ''' Periodic prune rate (1/ha/day).

        For the time being, since we do not model senescence.
        We act as if before bunch production sets on
        fronds are pruned monthly to keep
        the count around 50 fronds/palm.

        After this age the main pruning is actually periodical.
        '''
        if self._palm is None:
            return 0
        elif self.is_periodic_pruning_month:
            return self.potential_periodic_prune_rate
        else:
            return 0

    @property
    def prune_rate_harvest(self):
        ''' Harvest related prune rate (1/ha/day). '''
        if self._palm is None:
            return 0
        else:
            return 0 #max(0, self._palm.generative.bunch_count)

    @property
    def fronds_goal_count_per_palm(self):
        ''' The goal number of fronds (1/palm). '''
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
        ''' The goal number of fronds (1/ha). '''

        return self.planting_density*self.fronds_goal_count_per_palm

    def update(self):
        """ Update the state of the management. """
        self.frond_count = self.get_frond_count()