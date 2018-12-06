#!/usr/bin/env python

''' Contains the frond modelling class. '''

import yaml

from .helpers import add_dumps

from .constants import METERS_PER_HECTARE
from .constants import DAYS_PER_MONTH
from .constants import DEFAULT_PLANTING_DENSITY

import numpy as np

@add_dumps
class Fronds(object):
    ''' Models fronds.

    Palm age determines leaf area per frond and frond
    initiation rate.

    Frond count and leaf area per frond determine leaf area index.

    Leaf area index and incoming radiation determine the
    production of assimilates.

    Mass is updated according to
        - mass growth: assimilation
        - mass loss: pruning

    Mass furthermore determines the maintenance requirement.

    References
    ----------
    Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.

    '''

    parameters = yaml.load('''

    specific_maintenance_rachis:
        value: 0.002
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance of the rachis.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                Photosynthese et productivite du palmier a huile en liaison
                avec les facteurs climatiques.
                Tableau II. After Gray, 1969.'
        uncertainty: 5%

    specific_maintenance_leaflets:
        value: 0.0083
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance of the leaflets.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    Tableau II. Mesures realiseses a La Me.'
        uncertainty: 5%

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency of the fronds.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    In turn based on van Kraalingen, D.W.G., 1989.
                    See text below table II and table III.'
        uncertainty: 5%

    fraction_rachis:
        value: 0.75
        unit: '1'
        info: 'Mass of the rachis/frond mass
                not clear if frond mass includes/excludes petiole.'
        source: '?'
        uncertainty: 5%

    fraction_leaflets:
        value: 0.25
        unit: '1'
        info: 'Mass of the leaflets/frond mass
                not clear if frond mass includes/excludes petiole.'
        source: '?'
        uncertainty: 5%

    specific_leaf_area:
        value: 3.1
        unit: 'm**2/kg_DM'
        info: 'The specific leaf area. Not used, only for checking.'
        source: 'Presumably derived by dividing reported leaf area/
                    leaf mass found in the paper by Corley, R.H.V.
                    and Gray, B.S. and Ng, S.K., 1971:
                    Productivity of the oil palm in Malaysia.'
        uncertainty: 10%

    LUE:
        value: 4.2
        unit: 'g_CH2O/MJ'
        info: 'The light use efficiency.'
        source: 'Based on a more detailed hourly light-response
                    model (copied from SUCROS) using oil palm LR measurements by Breure, Gerritsma.'
        uncertainty: 10%

    WUE:
        value: 0.09
        unit: 't_CH2O/ha/mm'
        info: 'The potential water use efficiency.'
        source: 'An estimate given a production of 8.8 t_CH2O/ha/month and transpiration of 150 mm/month.'
        uncertainty: 20%

    k:
        value: 0.33
        unit: '1'
        info: 'The canopy light extinction coefficient.'
        source: 'Based on the thesis by Gerritsma, W., 1988.'
        uncertainty: 5%

    leaf_area_a:
        value: 12.13
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    leaf_area_b:
        value: 2.47
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    leaf_area_c:
        value: 0.36
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_a:
        value: 22.48
        unit: '1/palm/year'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_b:
        value: 1.5
        unit: '1'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_c:
        value: 0.27
        unit: '1/year'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_max:
        value: 42
        unit: '1/year'
        info: 'The upper limit on the frond initiation rate.'
        source: 'Roughly based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    potential_growth_rate:
        value: 4
        unit: 'kg_DM/palm/month'
        info: 'The potential growth rate'
        source: 'Based on Corley et al., 1971.'
        uncertainty: 5%

    ''')

    initial_values = yaml.load('''
    mass:
        value: 30
        uncertainty: 0
        unit: 'kg_DM/plant'
        info: 'Frond mass at 0 MAP.'
        source: 'Based on Corley, 1971.'
    count:
        value: 30
        uncertainty: 0
        unit: 'count/plant'
        info: 'Frond count at 0 MAP.'
        source: 'Based on Woittiez, L. et al. 2017, and Advances in Oil Palm Research Volume 1, 2000. p. 27.'
    ''')

    units = yaml.load('''

        assim_growth                   : 'kg_CH2O/ha/day'
        assim_produced                 : 'kg_CH2O/ha/day'
        count                          : '1/ha'
        count_per_palm                 : '1/palm'
        fraction_intercepted           : '1'
        intercepted_solar_energy       : 'GJ/ha/day'
        total_leaf_area                : 'm2/ha'
        leaf_area_index                : '1'
        maintenance_requirement        : 'kg_CH2O/ha/day'
        mass                           : 'kg_DM/ha'
        mass_change_rate               : 'kg_DM/ha/day'
        mass_change_rate_yearly        : 'kg_DM/ha/year'
        mass_change_rate_per_palm      : 'kg_DM/palm/year'
        mass_growth_rate               : 'kg_DM/ha/day'
        mass_loss_rate                 : 'kg_DM/ha/day'
        mean_leaf_area                 : 'm2'
        plastochron                    : 'day'
        leaf_area_per_palm             : 'm2'
        initiation_rate                : '1/palm/day'
        intercepted_PAR                : 'GJ/ha/day'
        specific_leaf_area             : 'cm2/g_DM'
        prune_rate                     : 'kg_DM/ha/day'
        mass_per_palm                  : 'kg/palm'
        mass_per_frond                 : 'kg/frond'
        count_change_rate              : '1/ha/day'
        count_growth_rate              : '1/ha/day'
        count_loss_rate                : '1/ha/day'
        LUE                            : 'g_CH2O/MJ PAR'
        potential_growth_rate          : 'kg_DM/ha/day'
        potential_growth_rate_per_palm : 'kg_DM/palm/day'
        potential_sink_strength        : 'kg_CH2O/ha/day'
        prune_rate                     : '1/ha/day'
        prune_rate_mass                : 'kg_DM/ha/day'
        prune_rate_rachis_mass         : 'kg_DM/ha/day'
        prune_rate_leaflets_mass       : 'kg_DM/ha/day'

    ''')

    _prefix = 'fronds'

    def __init__(self,palm=None):

        self._palm = palm

        # convert from kg/plant -> t/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass  = self._planting_density*mass_per_palm

        # convert from 1/plant -> 1/ha
        count_per_palm = self.initial_values['count']['value']
        self.count = self._planting_density*count_per_palm

        # for testing only
        self._PAR_ = 500
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~~~

    @property
    def _planting_density(self):
        ''' The planting density (1/ha). '''
        if self._palm is None:
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    @property
    def _MAP(self):
        ''' Months after planting; Palm age (month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    @property
    def _DAP(self):
        ''' Days after planting; Palm age (days). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.DAP

    @property
    def _PAR(self):
        ''' Radiation (PAR) (MJ/m2/day). '''

        if self._palm is None:
            return self._PAR_
        else:
            return self._palm.weather.PAR

    @property
    def _relative_transpiration_rate(self):
        ''' Evapotranspiration (mm/month).

        Note, we consider the evaporation (soil)
        to be negligible (closed canopy).'''

        if self._palm is None:
            return 1
        else:
            return self._palm.soil.relative_transpiration_rate

    @property
    def prune_rate_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        if self._palm is None:
            return 0
        else:
            # prune me!
            return self._palm.management.prune_rate_mass

    @property
    def prune_rate_rachis_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        c = self.parameters['fraction_rachis']['value']

        return c*self.prune_rate_mass

    @property
    def prune_rate_leaflets_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        c = self.parameters['fraction_leaflets']['value']

        return c*self.prune_rate_mass

    #~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        ''' Update state by dt days.'''
        self._update(dt=dt)

    def _update(self,dt=1):
        ''' Update state by dt days. '''
        self._update_mass(dt=dt)
        self._update_count(dt=dt)

    def _update_mass(self,dt=1):
        ''' Update the mass (t_DM/ha) by dt days. '''

        self.mass += (1/365)*self.mass_change_rate*dt

    def _update_count(self,dt=1):
        ''' Update the count (1/ha) by dt days. '''
        self.count += self.count_change_rate*dt

    #~~~~~~~~~~~~~~~~

    @property
    def mass_change_rate(self):
        ''' Mass change rate (kg_DM/ha/day). '''
        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (kg_DM/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Mass loss rate (kg_DM/ha/day).

        Due to pruning. See also the management sub-model's
        prune variables.
        '''
        return self.prune_rate_mass

    @property
    def mass_change_rate_yearly(self):
        ''' Mass change rate (kg_DM/ha/year). '''

        return 365*self.mass_change_rate

    @property
    def potential_growth_realization(self):
        ''' Actual growth : potential growth (1). '''

        return self.mass_growth_rate/self.potential_growth_rate

    #~~~~~~~~~~~~~~~~

    @property
    def count_change_rate(self):
        ''' Fround count change rate (1/ha/day).

        The difference between growth and loss.
        See associated growth and loss rate properties.
        '''
        return self.count_growth_rate - self.count_loss_rate

    @property
    def count_growth_rate(self):
        ''' Fround count growth rate (1/ha/day). '''
        return self.initiation_rate*self._planting_density

    @property
    def initiation_rate(self):

        ''' The frond initiation_rate/count growth rate (1/day).

        Uses a fit to field observations; a Gompertz function

        R = (1/365)*a*(1+b*exp(-c*(t/12))

        R the frond initiation_rate rate (1/palm/month)
        t year after planting
        a the asymptotic rate (1/palm/year)
        b the initial relative offset from the asymptote (1)
        c the typical time scale (year)

        Is based on:

            Gerritsma, W. and Soebagyo, F.X., 1998.
            An analysis of the growth of leaf area of oil palm in indonesia.
            Table 3, experiment 1, 143 palms/ha density.

        '''

        a = self.parameters['initiation_rate_a']['value']
        b = self.parameters['initiation_rate_b']['value']
        c = self.parameters['initiation_rate_c']['value']

        cap = self.parameters['initiation_rate_max']['value']

        # YAP
        t = self._DAP/365

        # (1/year/palm)
        yearly_naive = a*(1+b*np.exp(-c*(t)))

        yearly = min(cap,yearly_naive)

        # (1/day/palm)
        daily = yearly/365

        return float(daily)

    @property
    def count_loss_rate(self):
        ''' Fround count loss rate (1/ha/day).

        Determined strictly by the pruning regime.
        '''
        return self.prune_rate

    @property
    def prune_rate(self):
        ''' Frond prune rate (1/ha/day).

        Determined strictly by the pruning regime.
        '''
        if self._palm is None:
            return 0
        else:
            return self._palm.management.prune_rate

    @property
    def plastochron(self):
        ''' Days between consecutive frond initiation (days). '''
        return 1/self.initiation_rate

    @property
    def count_per_palm(self):
        return self.count/self._planting_density

    #~~~~~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement equals that for rachis plus leaflets. '''
        return self._maintenance_rachis + self._maintenance_leaflets

    @property
    def _maintenance_rachis(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance_rachis']['value']

        return c * self._mass_rachis

    @property
    def _maintenance_leaflets(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance_leaflets']['value']

        return c * self._mass_leaflets

    #~~~~~~~~~~~~~~~~

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (kg_CH2O/ha/day)'''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate/c

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/day). '''

        monthly_rate = self.parameters['potential_growth_rate']['value']

        daily_rate = monthly_rate/30

        return daily_rate

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (kg_DM/ha/day) '''

        v = self.potential_growth_rate_per_palm

        return v*self._planting_density

    @property
    def assim_growth(self):
        ''' Assimilates for growth (kg_CH2O/ha/day). '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_fronds

    #~~~~~~~~~~~~~~~~

    @property
    def leaf_area_index(self):
        ''' The LAI (total leaf area/ total ground area). '''

        # 0.0001 ha/m2
        return 0.0001*self.total_leaf_area

    @property
    def total_leaf_area(self):
        ''' The total leaf area (m2). '''
        return self.mean_leaf_area*self.count

    @property
    def mean_leaf_area(self):
        ''' Leaf area per leaf.

        Based on the following paper:

        Gerritsma, W. and Soebagyo, F.X., 1998.
        An analysis of the growth of leaf area of oil palm in indonesia.

        See Fig. 1 and Table 1.
        '''

        # YAP
        t = self._DAP/365

        a = self.parameters['leaf_area_a']['value'] # 12 +- 1
        b = self.parameters['leaf_area_b']['value'] # 2.47 +- 0.1
        c = self.parameters['leaf_area_c']['value'] # 0.36 +- 0.04

        return a*np.exp(-b*np.exp(-c*(t)))

    @property
    def leaf_area_per_palm(self):
        ''' Calculates the leaf area per palm (m2/palm). '''
        return self.total_leaf_area/self._planting_density

    @property
    def specific_leaf_area(self):
        ''' Specific leaf area (m2 leaf/kg leaf). '''

        c = self.parameters['fraction_leaflets']['value']

        leaflet_mass_per_frond = c*self.mass_per_frond

        return self.mean_leaf_area/leaflet_mass_per_frond

    #~~~~~~~~~~~~

    @property
    def assim_produced(self):
        ''' Assimilates produced (kg_CH2O/day/ha). '''

        # g_CH2O/MJ -> kg_CH2O/GJ
        LUE = self.LUE

        # (GJ/ha/day)
        intercepted_PAR = self.intercepted_PAR

        rT = self._relative_transpiration_rate

        return rT * LUE * intercepted_PAR

    @property
    def LUE(self):
        ''' The light-use efficiency (g_CH2O/MJ). '''
        return self.parameters['LUE']['value']

    @property
    def intercepted_PAR(self):
        ''' The intercepted radiation (PAR) (GJ/ha/day). '''

        # (MJ/m2/day)
        PAR = self._PAR

        # 9 MJ/m2/day --> ~ 9*10000/1000 = 90 GJ/ha/day
        # 1 MJ/m2 = 10 GJ/ha

        c = 10

        # (1)
        fraction_intercepted = self.fraction_intercepted

        return c * fraction_intercepted * PAR

    @property
    def fraction_intercepted(self):
        ''' The fraction of PAR intercepted (1).

        Uses the Lambert-Beer estimate.
        '''

        LAI = self.leaf_area_index

        k = self.parameters['k']['value']

        return (1 - np.exp(-k*LAI))

    #~~~~~~~~~~~~

    @property
    def _mass_rachis(self):
        ''' The mass of the rachis (t_DM/ha). '''

        c = self.parameters['fraction_rachis']['value']

        return c * self.mass

    @property
    def _mass_leaflets(self):
        ''' The mass of the leaflets (t_DM/ha). '''

        c = self.parameters['fraction_leaflets']['value']

        return c * self.mass

    @property
    def mass_per_palm(self):
        ''' Frond mass per palm (kg_DM/palm). '''
        return self.mass / self._planting_density

    @property
    def mass_change_rate_per_palm(self):
        ''' Mass change rate (kg_DM/palm/year). '''
        return (1/self._planting_density)*self.mass_change_rate_yearly

    @property
    def mass_per_frond(self):
        ''' Mass per frond (kg_DM/frond). '''
        return self.mass / self.count

