#!/usr/bin/env python

########
# README
########

''' Fronds modelled in more detailed via cohorts of fronds that have phenology.

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
import sys

from copy import deepcopy

from components.helpers import GAUGE_PLANTING_DENSITY
from components.helpers import DAYS_PER_MONTH
from components.helpers import add_dumps

from scipy import interpolate

import pandas as pd
import random
import numpy as np

from math import exp

#################
# Parametrization
#################
DEFAULT_RACHIS_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0022
            unit: 'g_CH2O/g_DM/day'
            info: 'The specific maintenance.'
            source: ''
        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: ''
        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, in months after leaf initiation.'
            source: ''
        t_growth_end_t0:
            value: 16
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for young palm---rather qualitative for the moment.'
            source: 'Adam et al., 2011.'
        t_growth_end_t1:
            value: 24
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for mature palm---rather qualitative for the moment.'
            source: 'Adam et al., 2011.'
        mean_density:
            value: .5
            unit: 'kg_DM/meter'
            info: 'The overall density (weighted mean over the length).'
            source: 'Initial guess.'
        ''')

RACHIS_VARIABLE_METADATA = yaml.load('''
    mass:
        unit: 'kg_DM'
    length:
        unit: 'm'
    potential_mass:
        unit: 'kg_DM'
    MAI:
        unit: 'month'
    mean_density:
        unit: 'kg_DM/m'
    assim_growth:
        unit: 'kg_CH2O/month'
    conversion_efficiency:
        unit: 'g_DM/g_CH2O'
    specific_maintenance_requirement:
        unit: 'g_CH2O/g_DM/day'
    maintenance_requirement:
        unit: 'kg_CH2O/month'
    mass_growth_rate:
        unit: 'kg_DM/month'
    mass_growth_rate_potential:
        unit: 'kg_DM/month'
    relative_sink_strength:
        unit: '1'
    potential_sink_strength:
        unit: 'kg_CH2O/month'
    _t_growth_end:
        unit: 'month'
    potential_rachis_length:
        unit: 'm'
    potential_length_growth_rate:
        unit: 'm/month'
    potential_mass_growth_rate:
        unit: 'kg_DM/month'
    ''')

##################
# Helper functions
##################

def make_quadratic_function(x1,x2,A):
    ''' Returns a strictly positive quadratic function.

    We use the fact that "the area below a parabola" is 2/3*height*base.

    Parameters
    ----------
    x1: left x s.t. y = 0
    x2: right x s.t. y = 0
    A: area under parabola

    Returns
    -------
    A quadratic function x -> y.

    '''

    # base width
    W = x2 - x1

    # max height
    h = 1.5*A/W

    # scaling s.t. y = h at x = hw
    hw = .5*(x2-x1)

    def func(x):
        if x <= x1:
            return 0
        elif x >= x2:
            return 0
        else:
            return max(0,-h*(x-x1)*(x-x2)/(hw)**2)

    return func

def sigmoid(x,x0,k):
    ''' A sigmoidal function: the logistic function:

        y = 1/(1+exp(-k(x-x0)))

    Note, for x = x0, y = 0.5 and dy = 1/(4*k).
    '''
    return 1/(1+np.exp(-k*(x-x0)))

@add_dumps
class Rachis(object):
    ''' A model of a frond rachis.

    Here we only consider active/green fronds.
    I.e. in real life at a certain age fronds
    snap and senesce. This is not modelled.

    We model
        - dry mass
        - length
        - growth
    '''
    _name = 'rachis'
    _prefix = _name
    _version = '2.1.1'

    default_parameters = DEFAULT_RACHIS_PARAMETERS
    _variable_metadata = RACHIS_VARIABLE_METADATA

    def __init__(self, owner = None):
        ''' Initialization.

        Each organ element may belong to an organ
        via the "_owner" property.

        '''
        self.parameters = self.default_parameters
        self._owner = owner

        # state
        self.MAI = 0
        self.length = 0
        self.mass = 0
        self.potential_sink_strength = 0

        # parameters
        self.conversion_efficiency = self.parameters['conversion_efficiency']['value']
        self.specific_maintenance_requirement = self.parameters['specific_maintenance']['value']

        # rate
        #self.potential_sink_strength = self.get_potential_sink_strength()

        # dummy variable for proto-typing
        self._assim_growth = 0
        self._owner_MAP = 36

    @property
    def _t_growth_end(self):
        t = self._MAP/12

        y0 = self.parameters['t_growth_end_t0']['value']
        y1 = self.parameters['t_growth_end_t1']['value']

        t0 = 12*3
        t1 = 12*15

        res = (y1-y0)/(t1-t0)*(t-t0) + y0

        return max(res,y0)

    @property
    def _MAP(self):
        ''' Months after planting.

        Used to i.a. calculate the potential rachis.
        '''
        if self._owner is None:
            return self._owner_MAP
        else:
            return self._owner._MAP

    @property
    def _potential_growth_function(self):
        ''' The potential growth in terms of fraction/month.

        E.g. 0.1 corresponds to 10%/month of potential growth.
        '''
        return  make_quadratic_function(self.parameters['t_growth_start']['value'],
                                      self._t_growth_end,
                                      1,
                                      )
    ###########
    # Potential
    ###########
    @property
    def mean_density(self):
        ''' In kg_DM/meter.

        For the time being rachis modelled as
        a cylinder: Nice Msc project to do better.
        '''
        return self.parameters['mean_density']['value']

    @property
    def potential_mass(self):
        ''' For the time being, a function of rachis length:

        pot. mass = pot. rachis length * mean density

        '''
        mean_density = self.mean_density
        potential_rachis_length = self.potential_rachis_length

        return mean_density*potential_rachis_length

    @property
    def potential_rachis_length(self):
        ''' Attained if sufficient resources.'''
        MAP = self._MAP

        a = 6.7
        b = 2.8
        c = .45

        #YAP
        t = MAP/12

        return a/(1+b*exp(-c*t))

    @property
    def potential_length_growth_rate(self):
        MAI = self.MAI # months after initiation
        r = self._potential_growth_function(MAI)
        return r*self.potential_rachis_length

    @property
    def potential_mass_growth_rate(self):
        ''' The potential mass growth rate (kg DM/month).'''
        MAI = self.MAI # months after initiation
        r = self._potential_growth_function(MAI)
        return r*self.potential_mass

    ###############
    # Sink-strength
    ###############
    def get_potential_sink_strength(self):
        ''' Potential sink strength (kg CH2O/month).

        Follows from the potential mass growth rate and the
        conversion efficiency.
        '''
        return self.potential_mass_growth_rate/self.conversion_efficiency

    @property
    def relative_sink_strength(self):
        ''' The sink strength relative to the other elements (1). '''
        if self._owner is None:
            # assume it is stand-alone
            return 1
        else:
            if self._owner.potential_sink_strength > 0:
                return self.potential_sink_strength / \
                        self._owner.potential_sink_strength
            else:
                return 0

    @property
    def assim_growth(self):
        ''' The realised sink strength (kg CH2O/month). '''
        if self._owner is None:
            # assume proto-typing
            return self._assim_growth
        else:
            return self.relative_sink_strength * \
                    self._owner.assim_growth_organ

    @property
    def mass_growth_rate(self):
        ''' The realised mass growth rate (kg DM/month). '''
        res = self.assim_growth*self.conversion_efficiency
        cap = self.potential_mass_growth_rate
        #return res
        return min(cap,res)

    #############
    # Maintenance
    #############
    @property
    def maintenance_requirement(self):
        ''' The maintenance resp. requirement (kg CH2O/month). '''
        return self.mass*self.specific_maintenance_requirement*DAYS_PER_MONTH

    ########
    # Update
    ########

    # Note, updating is managed by the owner.
    # -- since the realised mass growth
    # is context sensitive! (sibling sub-organs).

    def update_state(self,dt=1):
        ''' Update the organ a time-step size dt default 1 month. '''
        self.mass += self.mass_growth_rate*dt
        self.length += self.potential_length_growth_rate*dt

    def update_age(self,dt=1):
        ''' Update the age of the organ -- and set the sink strength. '''
        self.MAI += dt
        self.potential_sink_strength = self.get_potential_sink_strength()

    def update(self,dt=1):
        self.update_state(dt=dt)
        self.update_age(dt=dt)

    @property
    def variable_units(self):
        return {k:self._variable_metadata[k]['unit'] for k in self._variable_metadata}

DEFAULT_LEAFLETS_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0083
            unit: 'g_CH2O/g_DM/day'
            info: 'The specific maintenance.'
            source: ''
        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: ''
        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, in months after leaf initiation.'
            source: ''
        t_growth_end_t0:
            value: 16
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for young palm---rather qualitative for the moment.'
            source: 'Based on Adam et al., 2011.'
        t_growth_end_t1:
            value: 24
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for mature palm---rather qualitative for the moment.'
            source: 'Based on Adam et al., 2011.'
        t_open_start_t0:
            value: 16
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for young palm---rather qualitative for the moment.'
            source: 'Based on Adam et al., 2011.'
        t_open_start_t1:
            value: 24
            unit: 'month'
            info: 'The end of growth,
                    in months after leaf initiation,
                    for mature palm---rather qualitative for the moment.'
            source: 'Based on Adam et al., 2011.'
        t_open_end:
            value: 3
            unit: 'month'
            info: 'The end of the opening phase
                    in terms of months after the start
                    of the opening phase (i.e. a duration).'
            source: 'Based on Adam et al., 2011.'
        mean_density:
            value: 0.1
            unit: 'kg_DM/meter**2'
            info: 'A.k.a. the specific leaf area.'
            source: 'Initial guess based on the density of stiff paper
                        which is around 100g/m2.'
        ''')

LEAFLETS_VARIABLE_METADATA = yaml.load('''
    mass:
        unit: 'kg_DM'
    potential_mass:
        unit: 'kg_DM'
    age:
        unit: 'month'
    assim_growth:
        unit: 'kg_CH2O/month'
    conversion_efficiency:
        unit: 'g_DM/g_CH2O'
    specific_maintenance_requirement:
        unit: 'g_CH2O/g_DM/day'
    maintenance_requirement:
        unit: 'kg_CH2O/month'
    mass_growth_rate:
        unit: 'kg_DM/month'
    mass_growth_rate_potential:
        unit: 'kg_DM/month'
    relative_sink_strength:
        unit: '1'
    potential_sink_strength:
        unit: 'kg_CH2O/month'
    ''')

@add_dumps
class Leaflets(object):
    ''' '''
    _name = 'leaflets'
    _prefix = _name
    _version = '2.1.1'

    default_parameters = DEFAULT_LEAFLETS_PARAMETERS
    _variable_metadata = LEAFLETS_VARIABLE_METADATA

    def __init__(self, owner = None):
        ''' Initialization.

        Each organ element may belong to an organ
        via the "_owner" property.

        '''
        self.parameters = self.default_parameters
        self._owner = owner

        # state
        self.MAI = 0
        self.mass = 0
        self.potential_sink_strength = 0

        # parameters
        self.conversion_efficiency = self.parameters['conversion_efficiency']['value']
        self.specific_maintenance_requirement = self.parameters['specific_maintenance']['value']

        # rate
        #self.potential_sink_strength = self.get_potential_sink_strength()

        # dummy variable for proto-typing
        self._assim_growth = 0
        self._owner_MAP = 36

    @property
    def _t_growth_end(self):
        t = self._MAP/12

        y0 = self.parameters['t_growth_end_t0']['value']
        y1 = self.parameters['t_growth_end_t1']['value']

        t0 = 12*3
        t1 = 12*15

        res = (y1-y0)/(t1-t0)*(t-t0) + y0

        return max(res,y0)

    @property
    def _t_open_start(self):
        t = self._MAP/12

        y0 = self.parameters['t_open_start_t0']['value']
        y1 = self.parameters['t_open_start_t1']['value']

        t0 = 12*3
        t1 = 12*15

        res = (y1-y0)/(t1-t0)*(t-t0) + y0

        return max(res,y0)

    @property
    def _MAP(self):
        ''' Months after planting.

        Used to i.a. calculate the potential rachis.
        '''
        if self._owner is None:
            return self._owner_MAP
        else:
            return self._owner._MAP

    @property
    def _potential_mass_growth_function(self):
        ''' The potential growth in terms of fraction/month.

        E.g. 0.1 corresponds to 10%/month of potential growth.
        '''
        return  make_quadratic_function(self.parameters['t_growth_start']['value'],
                                      self._t_growth_end,
                                      self.potential_mass,
                                      )

    @property
    def openness(self):
        t_open_end = self.parameters['t_open_end']['value']
        t_half_open = self._t_open_start + t_open_end

        # here we divide by 4 since we use the logistic function
        open_rate = t_open_end/4
        return sigmoid(self.MAI,t_half_open,k = open_rate)

    ###########
    # Potential
    ###########
    @property
    def mean_density(self):
        ''' In kg_DM/meter**2. '''
        return self.parameters['mean_density']['value']

    @property
    def potential_mass(self):
        ''' For the time being, a function of rachis length:

        pot. mass = pot. leaf area * mean density

        '''
        return self.mean_density*self.potential_area

    @property
    def potential_area(self):
        ''' Attained if sufficient resources.'''
        MAP = self._MAP

        a = 12.2
        b = 2.5
        c = .36

        #YAP
        t = MAP/12

        return a*exp(-b*exp(-c*t))

    @property
    def leaf_area(self):
        return self.potential_area*self.openness

    @property
    def potential_mass_growth_rate(self):
        ''' The potential mass growth rate (kg DM/month).'''
        return self._potential_mass_growth_function(self.MAI)

    ###############
    # Sink-strength
    ###############
    def get_potential_sink_strength(self):
        ''' Potential sink strength (kg CH2O/month).

        Follows from the potential mass growth rate and the
        conversion efficiency.
        '''
        return self.potential_mass_growth_rate/self.conversion_efficiency

    @property
    def relative_sink_strength(self):
        ''' The sink strength relative to the other elements (1). '''
        if self._owner is None:
            # assume it is stand-alone
            return 1
        else:
            if self._owner.potential_sink_strength > 0:
                return self.potential_sink_strength / \
                        self._owner.potential_sink_strength
            else:
                return 0

    @property
    def assim_growth(self):
        ''' The realised sink strength (kg CH2O/month). '''
        if self._owner is None:
            # assume proto-typing
            return self._assim_growth
        else:
            return self.relative_sink_strength * \
                    self._owner.assim_growth_organ

    @property
    def mass_growth_rate(self):
        ''' The realised mass growth rate (kg DM/month). '''
        res = self.assim_growth*self.conversion_efficiency
        cap = self.potential_mass_growth_rate
        #return res
        return min(cap,res)

    #############
    # Maintenance
    #############
    @property
    def maintenance_requirement(self):
        ''' The maintenance resp. requirement (kg CH2O/month). '''
        return self.mass*self.specific_maintenance_requirement*DAYS_PER_MONTH

    ########
    # Update
    ########

    # Note, updating is managed by the owner.
    # -- since the realised mass growth
    # is context sensitive! (sibling sub-organs).

    def update_state(self,dt=1):
        ''' Update the organ a time-step size dt default 1 month. '''
        self.mass += self.mass_growth_rate*dt

    def update_age(self,dt=1):
        ''' Update the age of the organ -- and set the sink strength. '''
        self.MAI += dt
        self.potential_sink_strength = self.get_potential_sink_strength()

    def update(self,dt=1):
        self.update_state(dt=dt)
        self.update_age(dt=dt)

    @property
    def variable_units(self):
        return {k:self._variable_metadata[k]['unit'] for k in self._variable_metadata}

@add_dumps
class Frond(object):
    ''' '''

    _variable_metadata = {}

    _name = 'Frond'
    _version = '2.1.1'

    def __init__(self,manager):
        self.parameters = None
        self._manager = manager

        # components - here only a stalk
        self.rachis = Rachis(owner=self)
        self.leaflets = Leaflets(owner=self)
        self.components = [self.rachis,self.leaflets]

        # state
        self.multiplicity = 1
        self.MAI = 0

        # rate
        self.relative_sink_strength = 0

    @property
    def _MAP(self):
        ''' The palm age in months after planting (month). '''
        if self._manager is None:
            return 0
        else:
            if self._manager._palm is None:
                return 0
            else:
                return self._manager._palm.MAP

    ###############
    # Sink-strength
    ###############

    @property
    def potential_sink_strength(self):
        ''' The potential sink strength (kg_CH2O/month). '''
        return sum([x.potential_sink_strength for x in self.components])

    def get_relative_sink_strength(self):
        ''' Sink strength relative to other organs (1), a partitioning fraction. '''
        if self._manager is None:
            # assume it is the only one
            return 1
        else:
            cohort_sink_strength = self.multiplicity*self.potential_sink_strength
            total_sink_strength = 1000*self._manager.potential_sink_strength

            if total_sink_strength == 0:
                return 0
            else:
                # kg_CH2O/all organ cohorts
                res = cohort_sink_strength/total_sink_strength
                return res

    @property
    def assim_growth_cohort(self):
        ''' Assimilates for growth (kg_CH20/cohort organs/month). '''

        if self._manager is None:
            #proto-typing only
            return self.potential_sink_strength*self.multiplicity
        else:
            # ton --> kg
            assim_growth_generative = 1000 * self._manager.assim_growth

            return self.relative_sink_strength*assim_growth_generative

    @property
    def assim_growth_organ(self):
        ''' Assimilates for growth (kg_CH20/organ/month). '''
        if self.multiplicity > 0:
            return self.assim_growth_cohort/self.multiplicity
        else:
            return 0

    ######
    # Mass
    ######

    @property
    def potential_mass(self):
        ''' The potential mass (kg_DM). '''
        return sum([x.potential_mass for x in self.components])

    @property
    def mass(self):
        ''' The mass (kg_DM). '''
        return sum([x.mass for x in self.components])

    @property
    def mass_growth_rate(self):
        ''' The mass growth rate (kg_DM/month). '''
        return sum([x.mass_growth_rate for x in self.components])

    @property
    def potential_mass_growth_rate(self):
        ''' The mass growth rate (kg_DM/month). '''
        return sum([x.potential_mass_growth_rate for x in self.components])

    #############
    # Maintenance
    #############
    @property
    def maintenance_requirement(self):
        ''' The maintenance requirement (kg_CH2O/month). '''
        return sum([x.maintenance_requirement for x in self.components])

    ##########
    # Update
    ##########
    def update(self,dt=1):
        ''' Update the cohort a time-step. '''
        self._update(dt=dt)

    def set_relative_sink_strength(self):
        ''' Set the relative sink strength. '''
        res = self.get_relative_sink_strength()
        self.relative_sink_strength = res

    def _update(self,dt=1):
        ''' Update the cohort a time-step.

        Note
        ----
        We assume abortion fraction is "small"
        s.t. we can use 1-N*epsilon ~= (1-epsilon)**N.
        E.g. 1.01**10 = 1.105 ~= 1 + 10*0.01
        '''

        for component in self.components:
            component.update_state(dt=dt)

        for component in self.components:
            component.update_age(dt=dt)

        self.MAI += dt

    ########
    # Copy
    ########

    def to_comprehensive_dict(self):
        ''' Returns a dict containing comprehensive info. '''
        d = self.to_dict()
        for component in self.components:
            d.update(component.to_prefixed_dict())
        return d

    ########
    # Other
    ########
    @property
    def variable_units(self):
        return {k:self._variable_metadata[k]['unit'] for k in self._variable_metadata}

@add_dumps
class Organs(object):
    ''' The interface between the palm and the cohorts.

    Acts like a manager i.e. manages the flow of assimilates
    to the cohorts, handles the initiation of new cohorts,
    deletal of in-active cohorts, etc.

    '''
    _variable_metadata = yaml.load('''
    assim_growth:
        unit: 'tonne_DM/ha/month'
    bunch_production:
        unit: 'tonne_DM/ha/month'
    count:
        unit: '1/ha'
    count_females:
        unit: '1/ha'
    count_indeterminates:
        unit: '1/ha'
    count_males:
        unit: '1/ha'
    fraction_initiated:
        unit: '1'
    frond_initiation_rate:
        unit: '1/palm/month'
    initial_multiplicity:
        unit: '1/cohort'
    maintenance_requirement:
        unit: 'tonne_DM/month'
    mass:
        unit: 'tonne_DM/ha'
    mass_females:
        unit: 'tonne_DM/ha'
    mass_indeterminates:
        unit: 'tonne_DM/ha'
    mass_males:
        unit: 'tonne_DM/ha'
    max_age:
        unit: 'month'
    mean_age:
        unit: 'month'
    multiplicity:
        unit: '1/ha'
    potential_sink_strength:
        unit: 'tonne_DM/ha/month'
    bunch_weight:
        unit: 'kg_DM'
    bunch_count:
        unit: '1/ha/month'
    onset_multiplicity_factor:
        unit: '1'
    bunch_failure_fraction:
        unit: '1'
    inflorescence_abortion_fraction:
        unit: '1'
    number_of_cohorts:
        unit: '1'
    female_fraction:
        unit: '1'
    assim_growth_females:
        unit: 'tonne_CH2O/ha/month'
    assim_growth_indeterminates:
        unit: 'tonne_CH2O/ha/month'
    assim_growth_males:
        unit: 'tonne_CH2O/ha/month'
    mesocarp_oil_content:
        unit: '1'
    yield_FM_yearly:
        unit: 'tonne_FM/year'
    ''')

    default_parameters = yaml.load('''
    soil_moisture_specific_female_fraction_decrease:
        value: 1.5
        unit: '1'
        info: 'Decrease of the female fraction per unit drop of soil moisture content past the threshold.'
        source: 'Calibration to measured bunch counts --- ask the author.'
        uncertainty: 20%
    female_fraction_decrease_threshold:
        value: .8
        unit: '1'
        info: 'The soil moisture content below which sex ratio response sets in.'
        source: 'Calibration to measured bunch counts --- ask the author.'
        uncertainty: 20%
    female_fraction_young:
        value: [0.95,3]
        unit: '1,YAP'
        info: 'The fraction female for a "young" palm. - 3 YAP, note we are explicitly qualitative here.'
        source: 'Based on the associated qualitative statement found on p.26 in Advances in Oil Palm Research Volume 1, 2000.'
        uncertainty: 20%
    female_fraction_old:
        value: [0.35,30]
        unit: '1,YAP'
        info: 'The fraction female for a "young" palm.'
        source: 'Based on the associated qualitative statement found on p.26 in Advances in Oil Palm Research Volume 1, 2000.'
        uncertainty: 20%
    female_fraction_minimum:
        value: 0.1
        unit: '1,YAP'
        info: 'The minimum fraction female --- expected to be a plant characteristic.'
        source: 'Based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 26. figure 5..'
        uncertainty: 20%
    bunch_FM_to_DM_ratio:
        value: 2
        unit: '1'
        info: 'The fresh to dry mass of a bunch.'
        source: 'Corley and Tinker chapter 5.'
    '''
    )

    _name = 'organs'
    _prefix = _name
    _version = '0.0'

    def __init__(self,palm=None):
        self.cohorts = []
        self._palm = palm

        # rate
        self._assim_growth = 0
        self.assim_growth = 0
        self.potential_sink_strength = 0
        self._initiation_rate = 0

        # param
        self.parameters = deepcopy(self.default_parameters)

        # pool of cohorts marked for deletion
        self.to_delete = []

    @property
    def _water_deficit(self):
        ''' The water deficit - relative to the critical deficit.'''
        if self._palm is None:
            return 0
        else:
            return self._palm.soil.critical_deficit_exceedance

    @property
    def _soil_moisture_content(self):
        ''' The water deficit - relative to the critical deficit.'''
        if self._palm is None:
            return 1
        else:
            return self._palm.soil.moisture_content

    @property
    def _age(self):
        ''' The palm age in months after planting. '''
        if self._palm is None:
            return 40
        else:
            return self._palm.MAP

    ##############
    # Inter-facing
    ##############
    @property
    def _planting_density(self):
        if self._palm is None:
            return GAUGE_PLANTING_DENSITY
        else:
            return self._palm.planting_density

    @property
    def frond_initiation_rate(self):
        ''' New indeterminate cohorts (1/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return float(self._palm.fronds.initiation_rate)

    @property
    def maintenance_requirement(self):
        ''' The generative maintenance requirement. '''
        return 0.001*sum([x.maintenance_requirement*x.multiplicity for x in self.cohorts])

    ###############
    # Sink-strength
    ###############
    def get_potential_sink_strength(self):
        ''' The total potential sink strength (tonne_CH2O/ha/month). '''
        return 0.001*sum([x.potential_sink_strength*x.multiplicity for x in self.cohorts])

    def get_assim_growth(self):
        ''' The assimilates for generative growth. (kg_CH2O/month) '''
        if self._palm is None:
            return self._assim_growth
        else:
            return self._palm.assimilates.assim_growth_generative

    ########
    # Update
    ########
    def update(self,dt=1):

        # Calculated in the PalmSim's "assimilates" object.
        self.assim_growth = self.get_assim_growth()

        # Update existing cohorts:
        #   - update each cohort
        #       - mass growth (mass)
        #       - abortion (multiplicity)
        #       - age
        self.update_existing_cohorts(dt=dt)

        # Differentiate and split each
        # "mature" indeterminate cohort to make a
        #   - female cohort
        #   - male cohort
        self.update_sex()

        # Add new indeterminate cohorts
        self.update_new_cohorts(dt=dt)

        # Delete delete-able
        # (metabolically in-active) cohorts:
        #   - Male's past maturity age
        #   - Female's past harvestible age
        #   - Empty cohorts (multiplicity ~= 0)

        self.to_delete = [x for x in self.cohorts if x.delete]

        self.cohorts = [x for x in self.cohorts if not x.delete]

        # Potential/relative SS is independent of RSS
        # Potential determines realized SS thus should be set
        # before calculating realized SS.
        self.potential_sink_strength = self.get_potential_sink_strength()
        self.set_relative_sink_strengths()

    def set_relative_sink_strengths(self):
        ''' Sets the relative sink strengh of the cohorts. '''
        for cohort in self.cohorts:
            cohort.set_relative_sink_strength()

    def update_existing_cohorts(self,dt):
        ''' Updates the existing cohorts. '''
        for cohort in self.cohorts:
            cohort.update(dt=dt)

    def update_sex(self):
        ''' Updates the cohorts by applying sex differentiation. '''

        cohorts_ = []

        for cohort in self.cohorts:

            if (cohort.sex == 'indeterminate') \
                    and (cohort.age > cohort.age_of_differentiation):

                    f = cohort.to_female()
                    m = cohort.to_male()

                    cohorts_.append(f)
                    cohorts_.append(m)

            else:
                cohorts_.append(cohort)

        self.cohorts = cohorts_

    def update_new_cohorts(self,dt=1):
        # introduce new cohorts

        new_cohort = Indeterminate(manager=self)
        new_cohort.multiplicity = self.initiation_rate*dt

        self.cohorts.append(new_cohort)

    ################
    # Mass
    ################
    @property
    def mass(self):
        ''' The total generative mass (tonne_DM/ha). '''
        temp = [x.multiplicity*x.mass for x in self.cohorts]
        return 0.001*sum(temp)

    ##############
    # Cohort Sets
    ##############
    @property
    def bunches(self):
        return [x for x in self.females if x.is_harvestible]

    @property
    def females(self):
        ''' Female cohorts. '''
        return [x for x in self.cohorts if  x.sex == 'female']

    @property
    def males(self):
        ''' Male cohorts. '''
        return [x for x in self.cohorts if  x.sex == 'male']

    @property
    def indeterminates(self):
        ''' Indeterminate cohorts. '''
        return [x for x in self.cohorts if  x.sex == 'indeterminate']

    ###############
    # Bunch details
    ###############
    @property
    def mesocarp_oil_content(self):
        bunch_count = self.bunch_count
        if bunch_count > 0:
            res = sum([x.mesocarp_oil_content for x in self.bunches])
            return res/bunch_count
        else:
            return 0

    @property
    def bunch_production(self):
        '''(tonne_DM/month)'''
        return 0.001*sum([x.multiplicity*x.mass for x in self.bunches])

    @property
    def yield_FM_yearly(self):
        ''' (tonne_FM/year). '''
        months_per_year = 12
        ratio = self.parameters['bunch_FM_to_DM_ratio']['value']
        return months_per_year*ratio*self.bunch_production

    @property
    def bunch_count(self):
        '''(tonne_DM/month)'''
        return sum([x.multiplicity for x in self.bunches])

    @property
    def bunch_weight(self):
        '''(kg_DM/bunch)'''
        if self.bunch_count == 0:
            return 0
        else:
            return 1000*self.bunch_production/self.bunch_count

    ##################
    # Abortion details
    ##################

    @property
    def inflorescence_abortion_fraction(self):
        ''' The mean of the non-zero values for the female cohorts (1). '''

        N = len(self.females)
        if N > 0:
            values = [x.inflorescence_abortion_fraction for x in self.females]
            nzvalues = [x for x in values if x > 0]
            M = len(nzvalues)
            if M > 0:
                return sum(nzvalues)/M
            else:
                return 0
        else:
            return 0

    @property
    def bunch_failure_fraction(self):
        ''' The mean of the non-zero values for the female cohorts (1). '''

        N = len(self.females)
        if N > 0:
            values = [x.bunch_failure_fraction for x in self.females]
            nzvalues = [x for x in values if x > 0]
            M = len(nzvalues)
            if M > 0:
                return sum(nzvalues)/M
            else:
                return 0
        else:
            return 0

    ######################
    # Assimilation details
    ######################
    @property
    def assim_growth_females(self):
        ''' Assimilates for growth (kg_DM/cohort/month). '''
        return 0.001*sum([x.assim_growth_cohort for x in self.females])

    @property
    def assim_growth_males(self):
        ''' Assimilates for growth (kg_DM/cohort/month). '''
        return 0.001*sum([x.assim_growth_cohort for x in self.males])

    @property
    def assim_growth_indeterminates(self):
        ''' Assimilates for growth (kg_DM/cohort/month). '''
        return 0.001*sum([x.assim_growth_cohort for x in self.indeterminates])

    #################
    # Fraction female
    #################
    @property
    def _female_fraction(self):
        ''' The female fraction at sex determination (1). '''
        y1,x1 = self.parameters['female_fraction_young']['value']
        y2,x2 = self.parameters['female_fraction_old']['value']

        x = self._age/12

        c = (y2-y1)/(x2-x1)

        y = c*(x-x1) + y1

        if y>y1:
            return y1
        elif y<y2:
            return y2
        else:
            return y

    @property
    def female_fraction(self):
        ''' The female fraction at sex determination (1). '''

        coeff = self.parameters['soil_moisture_specific_female_fraction_decrease']['value']
        threshold = self.parameters['female_fraction_decrease_threshold']['value']
        driver = self._soil_moisture_content

        modifier = 1-coeff*max(0,threshold-driver)

        minimum = self.parameters['female_fraction_minimum']['value']

        return min(max(minimum,modifier*self._female_fraction),1)


    #############
    # New cohorts
    #############
    @property
    def onset_multiplicity_factor(self):
        ''' Mimics sigmoidal on-set of number of inflorescence. '''
        return sigmoid(self._age,16,.1)

    @property
    def initiation_rate(self):
        ''' New indeterminate cohorts (1/ha/month). '''
        if self._palm is None:
            return self._initiation_rate
        else:
            return self.frond_initiation_rate*self._planting_density*self.onset_multiplicity_factor

    @property
    def _planting_density(self):
        ''' The multiplicity of the cohort at initiation (1). '''
        if self._palm is None:
            return 1
        else:
            return self._palm.planting_density

    #########
    # Trivia
    #########
    @property
    def number_of_cohorts(self):
        ''' The number of cohorts. '''
        return len(self.cohorts)

    @property
    def variable_units(self):
        ''' The units of the variables. '''
        return {k:self._variable_metadata[k]['unit'] for k in self._variable_metadata}

    @property
    def _instance_variables(self):
        ''' The variables to output upon calling "to_dict". '''
        return ['mass',
                'bunch_weight',
                'bunch_count',
                'frond_initiation_rate',
                'onset_multiplicity_factor',
                #'multiplicity_next_cohort',
                'potential_sink_strength',
                'bunch_production',
                #'initial_multiplicity',
                'yield_FM_yearly',
                'bunch_failure_fraction',
                'inflorescence_abortion_fraction',
                'number_of_cohorts',
                'female_fraction',
                'assim_growth',
                'assim_growth_females',
                'assim_growth_indeterminates',
                'assim_growth_males',
                'mesocarp_oil_content']