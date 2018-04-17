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

    default_parameters = yaml.load('''
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
        unit: 'tonne_CH2O/TJ'
        info: 'The light use efficiency.'
        source: 'Based on a more detailed hourly light-response
                    model (copied from SUCROS) using oil palm LR measurements by Breure, Gerritsma.'
        uncertainty: 10%
    WUE:
        value: 0.09
        unit: 'tonne_CH2O/ha/mm'
        info: 'The potential water use efficiency.'
        source: 'An estimate given a production of 8.8 tonne_CH2O/ha/month and transpiration of 150 mm/month.'
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
        source: 'Based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%
    opening_age:
        value: 24
        unit: 'month'
        info: 'The age at which the frond opens, in months after initiation.'
    potential_growth_rate:
        value: 0.008
        unit: 'tonne_DM/palm/month'
        info: 'The potential growth rate'
        source: 'Based on Corley et al., 1971.'
        uncertainty: 5%
    ''')

    default_initial_values = yaml.load('''
    mass:
        value: 30
        uncertainty: 0
        unit: 'kg_DM/plant'
        info: 'Initial weight of the fronds.'
        source: 'Based on Corley, 1971.'
    count:
        value: 30
        uncertainty: 0
        unit: 'count/plant'
        info: 'Initial number of open fronds.'
        source: 'Based on Woittiez, L. et al. 2017, and Advances in Oil Palm Research Volume 1, 2000. p. 27.'
    ''')

    variable_units = dict(assim_growth                  = 'tonne_CH2O/ha/month',
                          assim_produced                = 'tonne_CH2O/ha/month',
                          count                         = '1/ha',
                          count_alt                    = '1/palm',
                          fraction_intercepted      = '1',
                          intercepted_solar_energy      = 'TJ/ha/month',
                          leaf_area                     = 'ha',
                          leaf_area_index               = '1',
                          maintenance_requirement       = 'tonne_CH2O/ha/month',
                          mass                          = 'tonne_DM/ha',
                          mass_change_rate              = 'tonne_DM/ha/month',
                          mass_growth_rate              = 'tonne_DM/ha/month',
                          mass_loss_rate                = 'tonne_DM/ha/month',
                          mean_leaf_area            = 'm**2',
                          plastochron                   = 'day',
                          leaf_area_per_palm            = 'm**2',
                          initiation_rate               = '1/palm/month',
                          specific_leaf_area            = 'cm**2/g_DM',
                          prune_rate                    = 'tonne_DM/ha/month',
                          mass_per_palm                 = 'kg/palm',
                          mass_per_frond                = 'kg/frond',
                          count_change_rate             = '1/ha/month',
                          count_growth_rate             = '1/ha/month',
                          count_loss_rate               = '1/ha/month',
                          LUE = 'g_CH2O/MJ PAR',
                          potential_growth_rate = 'tonne_DM/ha/month',
                          sink_strength_potential = 'tonne_CH2O/ha/month',
                          prune_rate_count = '1/ha/month',
                          prune_rate_mass = 'tonne_DM/ha/month',
                          )

    _attribute_sort_order = ['mass','count','assim','maint','leaf']

    _style = 'LegacyBase'
    _version = 'v0.01'
    _name = 'fronds'
    _prefix = _name

    def __init__(self,palm=None):

        self._palm = palm
        self.parameters = deepcopy(self.default_parameters)

        self.initial_values = self.default_initial_values

        self.mass  = 10**-3*self._planting_density*self.initial_values['mass']['value']
        self.count = self._planting_density*self.initial_values['count']['value']

    _fraction_rachis               = Parameter('fraction_rachis')
    _fraction_leaflets             = Parameter('fraction_leaflets')
    _specific_maintenance_rachis   = Parameter('specific_maintenance_rachis')
    _specific_maintenance_leaflets = Parameter('specific_maintenance_leaflets')
    _conversion_efficiency         = Parameter('conversion_efficiency')
    _LUE                           = Parameter('LUE')
    _C3                            = Parameter('C3')
    _k                             = Parameter('k')
    _initiation_rate_a             = Parameter('initiation_rate_a')
    _initiation_rate_b             = Parameter('initiation_rate_b')
    _initiation_rate_c             = Parameter('initiation_rate_c')
    _initiation_rate_max           = Parameter('initiation_rate_max')
    _potential_growth_rate         = Parameter('potential_growth_rate')
    _WUE                           = Parameter('WUE')

    @property
    def _instance_variables(self):
        return ['assim_growth',
                #'LUE',
                'assim_produced',
                'count',
                'count_alt',
                'fraction_intercepted',
                #'intercepted_solar_energy',
                'leaf_area',
                'plastochron',
                #'leaf_area_index',
                'maintenance_requirement',
                'mass',
                'mass_change_rate',
                'mass_growth_rate',
                'mass_loss_rate',
                'mean_leaf_area',
                #'leaf_area_per_palm',
                'initiation_rate',
                'specific_leaf_area',
                'potential_growth_rate',
                'sink_strength_potential',
                'prune_rate_count',
                'prune_rate_mass',
                #'mass_per_palm',
                'mass_per_frond',
                'count_change_rate',
                'count_growth_rate',
                'count_loss_rate'
                ]

    #############
    # Interfacing
    #############
    @property
    def _planting_density(self):
        ''' The planting density (1/ha). '''
        if self._palm is None:
            return GAUGE_PLANTING_DENSITY
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
    def _radiation_PAR_per_month(self):
        ''' Radiation (PAR) per ground area/month (GJ/m**2/month). '''

        if self._palm is None:
            I = 500 # J/m**2/s
            GJ_PER_J = 10**-9
            SECONDS_PER_MONTH = DAYS_PER_MONTH*6*60*60
            return I*SECONDS_PER_MONTH*GJ_PER_J
        else:
            return self._palm.weather.radiation_PAR_per_month

    @property
    def _relative_transpiration(self):
        ''' Evapotranspiration (mm/month).

        Note, we consider the evaporation (soil)
        to be negligible (closed canopy).'''

        if self._palm is None:
            return 1
        else:
            return self._palm.soil.relative_transpiration

    @property
    def prune_rate_mass(self):
        ''' Prune rate (tonne_DM/ha/month). '''

        if self._palm is None:
            return 0
        else:
            # prune me!
            return self._palm.management.prune_rate_mass

    ###############
    # Sink strength
    ###############
    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (tonne_DM/ha/month) '''
        return self._planting_density*self._potential_growth_rate

    @property
    def sink_strength_potential(self):
        ''' Potential sink strength (tonne_CH2O/ha/month)'''
        return self.potential_growth_rate/self._conversion_efficiency

    @property
    def assim_growth(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''

        if self._palm is None:
            return 0
        else:
            return self._palm.assimilates.assim_growth_fronds

    ###################
    # Mass change rates
    ###################
    @property
    def mass_change_rate(self):
        ''' Mass change rate (tonne_DM/ha/month). '''
        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (tonne_DM/ha/month). '''

        return self._conversion_efficiency*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Mass loss rate (tonne_DM/ha/month).

        Due to pruning. See also the management sub-model's
        prune variables.
        '''
        return self.prune_rate_mass

    ######
    # Mass
    ######

    @property
    def _mass_rachis(self):
        ''' The mass of the rachis (tonne_DM/ha). '''
        return self._fraction_rachis * self.mass

    @property
    def _mass_leaflets(self):
        ''' The mass of the leaflets (tonne_DM/ha). '''
        return self._fraction_leaflets * self.mass

    @property
    def mass_per_palm(self):
        ''' Frond mass per palm (kg_DM/palm). '''
        return 1000*self.mass/self._planting_density

    @property
    def mass_per_frond(self):
        ''' Mass per frond (kg_DM/frond). '''
        return 1000*self.mass/self.count

    ###################
    # Count change rate
    ###################
    @property
    def count_growth_rate(self):
        ''' Fround count growth rate (1/ha/month). '''
        return self.initiation_rate*self._planting_density

    @property
    def prune_rate_count(self):
        ''' Frond prune rate (1/ha/month).

        Determined strictly by the pruning regime.
        '''
        if self._palm is None:
            return 0
        else:
            return self._palm.management.prune_rate_count

    @property
    def count_loss_rate(self):
        ''' Fround count loss rate (1/ha/month).

        Determined strictly by the pruning regime.
        '''
        return self.prune_rate_count

    @property
    def count_change_rate(self):
        ''' Fround count change rate (1/ha/month).

        The difference between growth and loss.
        See associated growth and loss rate properties.
        '''
        return self.count_growth_rate - self.count_loss_rate

    @property
    def initiation_rate(self):

        ''' The frond initiation_rate/count growth rate (1/month).

        Uses a fit to field observations; a Gompertz function

        R = (1/12)*a*(1+b*exp(-c*(t/12))

        R the frond initiation_rate rate (1/palm/month)
        t year after planting
        a the asymptotic rate (1/palm/year)
        b the initial relative offset from the asymptote (1)
        c the typical time scale (year)

        Is inspired by:

            Gerritsma, W. and Soebagyo, F.X., 1998.
            An analysis of the growth of leaf area of oil palm in indonesia.
            Table 3, experiment 1, 143 palms/ha density.

        '''

        a = self._initiation_rate_a
        b = self._initiation_rate_b
        c = self._initiation_rate_c
        cap = self._initiation_rate_max

        # in months
        t = self._MAP
        t_year = t/12

        # (1/year/palm)
        initiation_rate_yearly = min(cap,a*(1+b*np.exp(-c*(t_year))))

        # (1/month/palm)
        initiation_rate_ = initiation_rate_yearly/12

        return float(initiation_rate_)

    @property
    def plastochron(self):
        ''' Days between consecutive frond initiation (days). '''
        return DAYS_PER_MONTH/self.initiation_rate

    @property
    def count_alt(self):
        return self.count/self._planting_density

    #############
    # Maintenance
    #############
    @property
    def _maintenance_rachis(self):
        ''' Maintenance requirement (tonne_CH2O/ha/month). '''
        return DAYS_PER_MONTH * \
                self._specific_maintenance_rachis * \
                self._mass_rachis

    @property
    def _maintenance_leaflets(self):
        ''' Maintenance requirement (tonne_CH2O/ha/month). '''
        return DAYS_PER_MONTH * \
                self._specific_maintenance_leaflets * \
                self._mass_leaflets

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement equals that for rachis plus leaflets. '''
        return self._maintenance_rachis + self._maintenance_leaflets

    ###########
    # Leaf Area
    ###########
    @property
    def mean_leaf_area(self):
        ''' Leaf area per leaf.

        As a function of years after planting.
        Inspired by the following paper:

            Gerritsma, W. and Soebagyo, F.X., 1998.
            An analysis of the growth of leaf area of oil palm in indonesia.

            See Fig. 1 and Table 1.

        A Gompertz function is said to give the best description
        of leaf area as a function of palm age:

        L = a*exp(-b*exp(-c*(t/12)))

        L leaf area per leaf
        t months after planting
        a asymptotic leaf area per leaf
        b translation coefficient
        c growth rate

        '''

        # annotation: typical value found in literature +- spread
        t = self._MAP
        a = self.parameters['leaf_area_a']['value'] # 12 +- 1
        b = self.parameters['leaf_area_b']['value'] # 2.47 +- 0.1
        c = self.parameters['leaf_area_c']['value'] # 0.36 +- 0.04

        return a*np.exp(-b*np.exp(-c*(t/12)))

    @property
    def leaf_area_per_palm(self):
        ''' Calculates the leaf area per palm (m**2/palm). '''
        return METERS_PER_HECTARE*self.leaf_area/self._planting_density

    @property
    def leaf_area(self):
        ''' Calculates the leaf area per hectare of ground (ha leaf/ha ground). '''

        return (10**-4)*self.mean_leaf_area*self.count

    @property
    def leaf_area_index(self):
        ''' The LAI (total leaf area/ total ground area). '''
        return self.leaf_area

    @property
    def specific_leaf_area(self):
        ''' Specific leaf area (m**2 leaf/kg leaf). '''
        return self.mean_leaf_area/self.mass_per_frond

    #################
    # Photo-synthesis
    #################
    @property
    def assim_produced(self):
        ''' Assimilates produced (tonne_CH2O/month/ha).

        Calculated as
            LUE * I * rT
        with rT the relative transpiration rate.
        '''

        # (tonne_CH2O/TJ == g_CH2O/MJ)
        LUE = self.LUE

        # (GJ/ha/month)
        intercepted_solar_energy = self.intercepted_solar_energy

        rT = self._relative_transpiration

        return rT*LUE*intercepted_solar_energy

    @property
    def LUE(self):
        ''' The light-use efficiency (g_CH2O/MJ). '''
        return self._LUE

    @property
    def intercepted_solar_energy(self):
        ''' The intercepted radiation (PAR) (TJ/ha/month).

        Intercepted PAR (TJ/ha/month) = fraction intercepted (1)
                                        * monthly PAR (10**-3 TJ/m2/month)
                                        * base_area (10**4*m2)

        '''

        PAR = self._radiation_PAR_per_month # (GJ/m**2/month)
        fraction_intercepted = self.fraction_intercepted # (1)

        # Note: 10 TJ/ha == 1 GJ/m**2

        return 10*fraction_intercepted*PAR

    @property
    def fraction_intercepted(self):

        '''
        The fraction of PAR intercepted (1).

        Uses the following relationship (Lambert-Beer):

        f = (1-exp(-k*LAI))

        with

        f: the fraction of light intercepted by the canopy (1).
        LAI: leaf area index (ha leaf/ha ground).
        k: the light extinction coefficient/light absorbancy (1).

        '''

        LAI = self.leaf_area_index
        k = self._k

        return (1-np.exp(-k*LAI))

    @property
    def k(self):
        ''' Light-extinction coefficient. '''
        return self._k

    ########
    # Update
    ########
    def update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month.'''

        self._update(dt=dt)

    def _update(self,dt=1):
        ''' Update state by a (dt=1) (30-day) month. '''
        self._update_mass(dt=dt)
        self._update_count(dt=dt)

    def _update_mass(self,dt=1):
        ''' Update the mass. '''

        # tonne_DM/ha
        self.mass += self.mass_change_rate*dt

    def _update_count(self,dt=1):
        ''' Update the count. '''
        self.count += self.count_change_rate*dt

LatestFronds = Fronds