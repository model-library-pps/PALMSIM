#!/usr/bin/env python

''' Contains the trunk modelling.

'''

import yaml

from .helpers import add_dumps
from .helpers import Spline

from .constants import DAYS_PER_MONTH
from .constants import DEFAULT_PLANTING_DENSITY

@add_dumps
class Trunk(object):
    ''' Trunk related logic.

    The instance of this class (singleton design pattern)
    "the trunk" models a hectare of oil palm trunks.

    Main variable:
        trunk mass

    Main parameters:
        potential growth rate vs YAP

    Notes
    -----
    The potential growth rate determines the sink strength
    which again determines the assimilats for mass growth.
    - see the reference below.

    Mass loss is taken to be zero at all times.

    References
    ----------
    Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971.
    Productivity of the oil palm in Malaysia.
    '''

    parameters = yaml.load('''

    specific_maintenance:
        value: 0.0005
        unit: 'kg_CH2O/kg_DM/day'
        info: 'The specific maintenance.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
        uncertainty: 20%

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
        uncertainty: 10%

    mass_loss_rate:
        value: 0.0
        unit: 't/ha/day'
        info: 'The mass loss rate.'
        source: 'Assumption: the trunk loses no mass --- first made by Alba/Hoffman.'
        uncertainty: 0%

    potential_growth_rates:
        value: [[0, 1.6],
                 [3, 9.5],
                 [6, 19.6],
                 [9, 22.8],
                 [12, 19.2],
                 [15, 13.5],
                 [18, 8.6],
                 [21, 5.2],
                 [24, 3.0],
                 [27, 1.7]]
        unit: 'YAP, kg/palm/year'
        info: 'The potential growth rate at different points in time, determines the potential sink strength and thus assimilate partitioning.'
        source: 'Obtained by fitting a Gompertz function to the mass reported in Corley, R.H.V. and Gray, B.S. and Siew Kee, NG, 1971. Productivity of the oil palm in Malaysia.'
        uncertainty: 10%

    ''')

    initial_values = yaml.load('''
    mass:
        value: 2
        unit: 'kg_DM/plant'
        info: 'Trunk mass at 0 MAP.'
        source: 'Based on Corley, 1971.'
        uncertainty: 10%
    ''')

    units = yaml.load('''

    assim_growth: 't_CH2O/ha/day'
    maintenance_requirement: 't_CH2O/ha/day'
    mass: 't_DM/ha'
    mass_change_rate: 't_DM/ha/day'
    mass_per_palm: 'kg_DM/palm'
    mass_change_rate_per_palm: 'kg_DM/palm/day'
    mass_growth_rate: 't_DM/ha/day'
    mass_loss_rate: 't_DM/ha/day'
    potential_growth_rate: 't_DM/ha/day'
    potential_growth_rate_per_palm: 'kg_DM/palm/day'
    potential_sink_strength: 't_CH2O/ha/day'

    ''')

    _prefix = 'trunk'

    def __init__(self,palm=None):

        self._palm = palm

        # convert from kg/plant -> ton/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass = 0.001*self._planting_density*mass_per_palm

        # convert potential growth rate values (pgr) to a pgr function
        # - a (cubic: k=3) spline
        pgrs = self.parameters['potential_growth_rates']['value']
        self._potential_growth_rate_spline = Spline(pgrs,k=3)

        # only used for testing - e.g. to see that the trunks grow
        # when supplied with assimilates
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~

    @property
    def _planting_density(self):
        ''' Planting density (1/ha). '''
        if self._palm is None:
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    @property
    def _YAP(self):
        ''' Years after planting (year). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.YAP

    #~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        ''' Update state by dt days.'''

        self.mass += self.mass_change_rate*dt

        assert self.mass >= 0

    #~~~~~~~~~~~~~~~~

    @property
    def mass_change_rate(self):
        ''' Mass change rate (t_DM/ha/day). '''

        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass change rate (t_DM/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Mass loss rate (t_DM/ha/day)'''

        return self.parameters['mass_loss_rate']['value']

    #~~~~~~~~~~~~~~~

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/day). '''

        YAP = self._YAP

        yearly_rate = self._potential_growth_rate_spline.calc(YAP)

        daily_rate = yearly_rate/365

        return daily_rate

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (t_DM/ha/day). '''

        # [kg/palm] : [t/ha] = 0.001 * PD

        return 0.001*self._planting_density*self.potential_growth_rate_per_palm

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (t_CH2O/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate/c

    @property
    def assim_growth(self):
        ''' Assimilates for growth (t_CH2O/ha/day). '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_trunk

    #~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):

        ''' Maintenance requirement (t_CH2O/ha/day).

        Maintenance = specific_maintenance (g_CH2O/g_DM/day) * mass (t_DM/ha)
        '''

        c = self.parameters['specific_maintenance']['value']

        res = c * self.mass

        return res

    #~~~~~~~~~~~~~~

    @property
    def mass_per_palm(self):
        ''' Mass change rate (kg_DM/palm). '''
        return 1000*(1/self._planting_density)*self.mass

    @property
    def mass_change_rate_per_palm(self):
        ''' Mass change rate (kg_DM/palm/day). '''
        return 1000*(1/self._planting_density)*self.mass_change_rate
