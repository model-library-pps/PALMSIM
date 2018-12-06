#!/usr/bin/env python

''' Contains the root modelling. '''

import yaml
import numpy as np

from .helpers import add_dumps
from .helpers import Spline

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
        value: 0.000433
        unit: '1/day'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%

    loss_param_b:
        value: 0.0018
        unit: 't/ha/day'
        info: 'Co-determines the mass loss rate of the roots.'
        source: 'The legacy version; PalmSim 2014.'
        uncertainty: 20%

    potential_growth_rates:
        value: [[0, 4.5],
                 [3, 4.5],
                 [6, 4.5],
                 [9, 4.5],
                 [12, 4.5],
                 [15, 4.5],
                 [18, 4.5],
                 [21, 4.5],
                 [24, 4.5],
                 [27, 4.5]]
        unit: 'YAP, kg/palm/year'
        info: 'The potential growth rate at different points in time, determines the potential sink strength and thus assimilate partitioning.'
        source: 'Obtained by fitting a Gompertz function to the mass reported in Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971. Productivity of the oil palm in Malaysia.'
        uncertainty: 10%

    ''')

    initial_values = yaml.load('''

        mass:
            value: 4
            uncertainty: 20%
            unit: 't_DM/palm'
            info: 'Initial weight of the plant part.'
            source: 'Based on Corley, 1971.'
    ''')

    units = yaml.load('''

        assim_growth: 't_CH2O/ha/day'
        maintenance_requirement: 't_CH2O/ha/day'
        mass: 't_DM/ha'
        mass_per_palm: 'kg_DM/palm'
        mass_change_rate: 't_DM/ha/day'
        mass_growth_rate: 't_DM/ha/day'
        mass_loss_rate: 't_DM/ha/day'
        potential_growth_rate: 't_DM/ha/day'
        potential_growth_rate_per_palm : 'kg_DM/ha/day'
        potential_sink_strength: 't_CH2O/ha/day'

    ''')

    _prefix = 'roots'

    _log = []

    def __init__(self,palm=None):

        self._palm = palm

        # convert from kg/plant -> ton/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass = 0.001*self._planting_density*mass_per_palm

        # convert potential growth rate values (pgr) to a pgr function
        # - a (cubic: k=3) spline
        pgrs = self.parameters['potential_growth_rates']['value']
        self._potential_growth_rate_spline = Spline(pgrs,k=3)

        # only used for testing - e.g. to see if the roots grow
        # when supplied with assimilates.
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~

    @property
    def _YAP(self):
        ''' Years after planting (year). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.YAP

    @property
    def _planting_density(self):
        if self._palm is None:
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    #~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        ''' Update state by dt days.'''

        self.mass += self.mass_change_rate*dt

        assert self.mass >= 0


    @property
    def mass_change_rate(self):
        ''' Mass change rate (t_DM/ha/day). '''

        return self.mass_growth_rate - self.mass_loss_rate

    #~~~~~~~~~~~~~~~~

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (t/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Loss of root mass (DM t/ha/day). '''

        mass = self.mass

        a = self.parameters['loss_param_a']['value']
        b = self.parameters['loss_param_b']['value']

        return  a*mass + b

    #~~~~~~~~~~~~~~~~~~

    @property
    def mass_per_palm(self):
        ''' Mass change rate (kg_DM/palm). '''
        return 1000*(1/self._planting_density)*self.mass

    #~~~~~~~~~~~~~~~~~~

    @property
    def assim_growth(self):
        ''' Assimilates for growth (t_CH2O/ha/day).

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
        ''' Potential sink strength (t_CH2O/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate/c

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/day). '''

        YAP = self._YAP

        yearly_rate = self._potential_growth_rate_spline.calc(YAP)

        daily_rate = yearly_rate/365

        loss_rate = 1000*self.mass_loss_rate/self._planting_density

        corrected_rate = daily_rate + loss_rate

        return corrected_rate

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (t_DM/ha/day). '''

        # [kg/palm] : [t/ha] = 0.001 * PD

        return 0.001*self._planting_density*self.potential_growth_rate_per_palm

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement (t_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance']['value']

        return c*self.mass
