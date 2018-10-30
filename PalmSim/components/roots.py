#!/usr/bin/env python

''' Contains the root modelling. '''

import yaml
import numpy as np

from .helpers import add_dumps

from .constants import DAYS_PER_MONTH
from .constants import DEFAULT_PLANTING_DENSITY

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

    parameters = yaml.load('''

    specific_maintenance:
        value: 0.0022
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                Photosynthese et productivite du palmier a huile en liaison
                avec les facteurs climatiques.
                Table ?.'
        uncertainty: 20%

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Taken from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    In turn based on van Kraalingen, D.W.G., 1989.
                    See text below table II and table III.'
        uncertainty: 10%

    loss_param_a:
        value: 0.013
        unit: '1/month'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%

    loss_param_b:
        value: 0.06
        unit: 't/ha/mo'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%

    potential_growth_rate:
        value: 1.35
        unit: 'kg/palm/month'
        info: 'The potential growth rate'
        source: 'Based on Corley et al., 1971, Productivity of the Oil Palm in Malaysia.'
        uncertainty: 5%

    ''')

    initial_values = yaml.load('''
    mass:
        value: 4
        uncertainty: 50%
        unit: 't_DM/palm'
        info: 'Initial weight of the plant part.'
        source: 'Based on Corley, 1971.'
    ''')

    units = yaml.load('''

    assim_growth: 't_CH2O/ha/mo'
    maintenance_requirement: 't_CH2O/ha/mo'
    mass: 't_DM/ha'
    mass_change_rate: 't_DM/ha/mo'
    mass_growth_rate: 't_DM/ha/mo'
    mass_loss_rate: 't_DM/ha/mo'
    potential_growth_rate: 't_DM/ha/mo'
    potential_growth_rate_per_palm : 'kg_DM/ha/mo'
    potential_sink_strength: 't_CH2O/ha/mo'

    ''')

    _prefix = 'roots'

    _log = []

    def __init__(self,palm=None):

        self._palm = palm

        # convert from kg/plant -> ton/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass = 0.001*self._planting_density*mass_per_palm

        # only used for testing - e.g. to see if the roots grow
        # when supplied with assimilates.
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~

    @property
    def log(self):
        return self._log

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
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    #~~~~~~~~~~~~~~

    def update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month.'''

        self._update(dt=dt)

    def _update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month. '''

        # t_DM/ha
        self.mass += self.mass_change_rate*dt

    #~~~~~~~~~~~~~~

    @property
    def mass_change_rate(self):
        ''' Mass change rate (t/ha/mo). '''
        res = self.mass_growth_rate - self.mass_loss_rate

        if res < 0:
            self.log.append('WARNING: Root mass change rate < 0 : {:}'.format(res))

        return max(0, res)

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (t/ha/mo). '''

        c = self.parameters['conversion_efficiency']['value']

        return c*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Loss of root mass (DM t/ha/mo).

        Note, the Hoffman version involved a trivial bound:

        L = min(1*M,a*M+b)

        where 1*M acts as the trivial bound;
        the bound is met at around 0.06 DM ton/ha.
        '''

        mass = self.mass

        a = self.parameters['loss_param_a']['value']
        b = self.parameters['loss_param_b']['value']

        return  a*mass + b

    #~~~~~~~~~~~~~~~~~~

    @property
    def assim_growth(self):
        ''' Assimilates for growth (t_CH2O/ha/mo).

        Determined by the potential sink strength
        in relation to that of the other modelled
        organs.
        '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_roots

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (t_CH2O/ha/mo). '''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate/c

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/mo). '''

        c = self.parameters['potential_growth_rate']['value']

        return c

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (t/ha/mo). '''

        v = self.potential_growth_rate_per_palm

        # [kg/palm] : [t/ha] = 0.001 * PD
        return 0.001*v*self._planting_density

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement (t_CH2O/ha/mo). '''

        c = self.parameters['specific_maintenance']['value']

        return DAYS_PER_MONTH*c*self.mass
