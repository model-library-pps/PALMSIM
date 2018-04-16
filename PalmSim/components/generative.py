#!/usr/bin/env python

########
# README
########

''' Provides the inflorescence models.

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

#################
# Parametrization
#################
DEFAULT_STALK_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%
        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%
        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, in months after leaf initiation.'
            source: 'Based on Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        t_growth_end:
            value: 33
            unit: 'month'
            info: 'The end of potential growth, in months after leaf initiation.'
            source: 'Based on Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        potential_mass_t0:
            value: .5
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        potential_mass_t1:
            value: 5
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        ''')

DEFAULT_MESOCARP_FIBERS_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%
        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%
        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        t_growth_end:
            value: 5
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        potential_mass_t0:
            value: 2
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        potential_mass_t1:
            value: 20
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        ''')

DEFAULT_MESOCARP_OIL_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%
        conversion_efficiency:
            value: 0.42
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%
        t_growth_start:
            value: 3
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        t_growth_end:
            value: 5
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        potential_mass_t0:
            value: 3
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        potential_mass_t1:
            value: 30
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        ''')

DEFAULT_KERNEL_PARAMETERS = yaml.load('''
        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%
        conversion_efficiency:
            value: 0.42
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%
        t_growth_start:
            value: 2
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        t_growth_end:
            value: 6
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%
        potential_mass_t0:
            value: .5
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        potential_mass_t1:
            value: 5
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        ''')

##################
# Helper functions
##################
def mean(ls):
    ''' The mean of a list of floats.

    E.g. mean([1,0,0,1]) -> 0.5.

    '''
    N = len(ls)
    if N == 0:
        # empty list...
        return 0
    else:
        s = sum(ls)
        return ls/N

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

def make_linear_function(x1,y1,x2,y2):
    ''' Returns a "line" f(x) through (x1,y1) and (x2,y2). '''
    c = (y2-y1)/(x2-x1)
    def f(x):
        return c*(x-x1) + y1
    return f

@add_dumps
class SubOrgan(object):
    ''' An abstract base class for "organ elements" (e.g. stalk).

    Key properties:
        potential_mass : the potential mass.
        sink_strength_potential : potential sink strength.
        relative_sink_strength : sink strength relative to sibling sub-organs.
        _owner : reference to the parent organ (the owner).

    Is contained in the (mean) organ which co-determines a cohort.

    The potential sink strength from which all follows
    is a function of age parametrized via
    a start time/end time of growth and a potential mass.

    This potential sink strength determines the relative sink strength
    and thus the realised sink strength (assimilates for growth),
    and so the mass growth rate.

    '''
    _name = ''
    _version = '1.0.0.1'

    default_parameters = yaml.load('''
        specific_maintenance:
            value: 0.0005
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'

        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'

       ''')

    _variable_metadata = yaml.load('''
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
        unit: 'tonne_CH2O/tonne_DM/day'
    maintenance_requirement:
        unit: 'kg_CH2O/month'
    mass_growth_rate:
        unit: 'kg_DM/month'
    mass_growth_rate_potential:
        unit: 'kg_DM/month'
    relative_sink_strength:
        unit: '1'
    sink_strength_potential:
        unit: 'kg_CH2O/month'
    ''')

    def __init__(self, organ = None, potential_mass = None):
        ''' Initialization.

        Each organ element may belong to an organ
        via the "_owner" property.

        '''
        self.parameters = self.default_parameters
        self._owner = organ

        if potential_mass is None:
            self.potential_mass = self.get_potential_mass()
        else:
            self.potential_mass = potential_mass

        self._potential_growth_function = \
            make_quadratic_function(self.parameters['t_growth_start']['value'],
                                      self.parameters['t_growth_end']['value'],
                                      self.potential_mass,
                                      )

        # state
        self.mass = 0
        self.age = 0

        # parameters
        self.conversion_efficiency = self.parameters['conversion_efficiency']['value']
        self.specific_maintenance_requirement = self.parameters['specific_maintenance']['value']

        # rate
        self.sink_strength_potential = self.get_sink_strength_potential()

        # dummy variable for proto-typing
        self._assim_growth = 0

    ##############
    # Init-related
    ##############
    def get_potential_mass(self):
        ''' A linear function of palm age.

        Parametrized via y0 the potential mass
        for the first fruits (x0) and y1 the
        potential mass at the end of a typical
        field life-time (x1) -- 30 years after planting:

        y = (y1-y0)/(x1-x0)*(x-x0) + y0 .

        '''
        y0 = self.parameters['potential_mass_t0']['value']

        if self._owner is None:
            return y1
        else:
            MAP = self._owner._MAP
            y1 = self.parameters['potential_mass_t1']['value']

            # here hard-coded..
            MAP0 = 0
            MAP1 = 360

            # a linear interpolation
            c = (y1-y0)/(MAP1-MAP0)

            res = c*(MAP-MAP0) + y0

            if res < y0:
                return y0
            else:
                return res

    ###############
    # Sink-strength
    ###############
    def get_sink_strength_potential(self):
        ''' Potential sink strength (kg CH2O/month).

        Follows from the potential mass growth rate and the
        conversion efficiency.
        '''
        return self.mass_growth_rate_potential/self.conversion_efficiency

    @property
    def mass_growth_rate_potential(self):
        ''' The potential mass growth rate (kg DM/month).

        Is a function of palm age.
        '''
        return self._potential_growth_function(self.age)

    @property
    def relative_sink_strength(self):
        ''' The sink strength relative to the other elements (1). '''
        if self._owner is None:
            # assume it is stand-alone
            return 1
        else:
            if self._owner.sink_strength_potential > 0:
                return self.sink_strength_potential / \
                        self._owner.sink_strength_potential
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

    ######
    # Mass
    ######
    @property
    def mass_growth_rate(self):
        ''' The realised mass growth rate (kg DM/month). '''
        res = self.assim_growth*self.conversion_efficiency
        cap = self.mass_growth_rate_potential
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

    def update_mass(self,dt=1):
        ''' Update the organ a time-step size dt default 1 month. '''
        self.mass += self.mass_growth_rate*dt

    def update_age(self,dt=1):
        ''' Update the age of the organ -- and set the sink strength. '''
        self.age += dt
        self.sink_strength_potential = self.get_sink_strength_potential()

    #############
    # Copy-method
    #############
    def copy(self):
        ''' Makes a copy.

        Involves making a new object of the same type
        -- the duplicate -- and making sure the duplicate
        has the same state/rates.

        '''
        constructor = type(self)
        duplicate = constructor(potential_mass = self.potential_mass)

        # carry over state (of basic types: float)
        duplicate.mass = self.mass
        duplicate.age = self.age
        duplicate.sink_strength_potential = duplicate.get_sink_strength_potential()

        return duplicate

    #########
    # Trivia
    #########
    @property
    def owner_age(self):
        ''' The age of the owning organ. '''
        if self._owner is None:
            return 0
        else:
            return self._owner.age

    @property
    def variable_units(self):
        return {k:self._variable_metadata[k]['unit'] for k in self._variable_metadata}

class Stalk(SubOrgan):
    ''' Models a stalk.'''
    _name = 'stalk'
    _prefix = _name
    default_parameters = DEFAULT_STALK_PARAMETERS

class MesocarpFibers(SubOrgan):
    ''' Models a mesocarp fibers.'''
    _name = 'mesocarp_fibers'
    _prefix = _name
    default_parameters = DEFAULT_MESOCARP_FIBERS_PARAMETERS

class MesocarpOil(SubOrgan):
    ''' Models a mesocarp oil.'''
    _name = 'mesocarp_oil'
    _prefix = _name
    default_parameters = DEFAULT_MESOCARP_OIL_PARAMETERS

class Kernel(SubOrgan):
    ''' Models a kernel.'''
    _name = 'kernel'
    _prefix = _name
    default_parameters = DEFAULT_KERNEL_PARAMETERS

@add_dumps
class Cohort(object):
    '''An abstract base class for organ cohorts.

    A cohort is represented by a "mean" organ,
    and a multiplicity denoting the number of
    organs in the cohort.

    Concrete subclasses: Indeterminate, Male, Female.

    Key Properties:
        age : months after initiation
        age_of_differentiation : -
        mass : mass of the mean organ
        multiplicity : number of organs in cohort

    '''

    _variable_metadata = yaml.load('''
    age:
        unit: 'month'
    age_of_differentiation:
        unit: 'month'
    assim_growth_cohort:
        unit: 'kg_CH2O/cohort/month'
    assim_growth_organ:
        unit: 'kg_CH2O/organ/month'
    female_fraction:
        unit: '1'
    maintenance_requirement:
        unit: 'kg_CH2O/month'
    mass:
        unit: 'kg_DM'
    potential_mass:
        unit: 'kg_DM'
    mass_growth_rate:
        unit: 'kg_DM/month'
    mass_growth_rate_potential:
        unit: 'kg_DM/month'
    multiplicity:
        unit: '1/cohort'
    sink_strength:
        unit: 'kg_CH2O/month'
    sink_strength_potential:
        unit: 'kg_CH2O/organ/month'
    relative_sink_strength:
        unit: '1'
    abortion_fraction:
        unit: '1'
    bunch_failure_fraction:
        unit: '1'
    delete:
        unit: 'bool'
    has_flowered:
        unit: 'bool'
    inflorescence_abortion_fraction:
        unit: '1'
    is_harvestible:
        unit: 'bool'
    mesocarp_oil_content:
        unit: '1'
    relative_sink_strength:
        unit: '1'
    trigger_flowering:
        unit: 'bool'
    ''')

    _name = 'Cohort'
    _version = '0.0'

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
    def sink_strength_potential(self):
        ''' The potential sink strength (kg_CH2O/month). '''
        return sum([x.sink_strength_potential for x in self.components])

    def get_relative_sink_strength(self):
        ''' Sink strength relative to other organs (1), a partitioning fraction. '''
        if self._manager is None:
            # assume it is the only one
            return 1
        else:
            cohort_sink_strength = self.multiplicity*self.sink_strength_potential
            total_sink_strength = 1000*self._manager.sink_strength_potential

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
            return self.sink_strength_potential*self.multiplicity
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
    def mass_growth_rate_potential(self):
        ''' The mass growth rate (kg_DM/month). '''
        return sum([x.mass_growth_rate_potential for x in self.components])

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
            component.update_mass(dt=dt)

        for component in self.components:
            component.update_age(dt=dt)

        survival_fraction = max(0,(1-self.abortion_fraction*dt))
        self.multiplicity *= survival_fraction

        self.age += dt

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

    @property
    def abortion_fraction(self):
        ''' The abortion fraction (1/month). '''
        return self._abortion_fraction

class Indeterminate(Cohort):
    ''' Models a cohort of indeterminate inflorescences.

    For convenience sake, at the moment, an inflorescense
    '''
    default_parameters = yaml.load('''
        age_of_differentiation:
            value: 7
            unit: 'month'
            info: 'The number of months until sex differentiation.'
            source: 'Adam et al. 2011, see fig 3. Measured bunch count analysis --- to be published.'
        abortion_fraction:
            value: 0
            unit: '1/month'
            info: 'Monthly aborted fraction before sex differentiation.'
            source: 'Estimated to be insignificantly small e.g. not mentioned in Adam et al. 2011.'
        ''')

    _name = 'indeterminate'
    _version = '0.0'
    sex = 'indeterminate'
    def __init__(self,manager=None):
        self.parameters = deepcopy(self.default_parameters)
        self._manager = manager

        # components - here only a stalk
        self.stalk = Stalk(self)

        # state
        self.multiplicity = 1
        self.age = 0

        # rate
        self.relative_sink_strength = 0

        # param
        self._abortion_fraction = self.parameters['abortion_fraction']['value']
        self.age_of_differentiation = self.parameters['age_of_differentiation']['value']

        self._female_fraction = 0.9

    @property
    def components(self):
        ''' The sub-organs. '''
        return [self.stalk]

    @property
    def female_fraction(self):
        ''' Fraction female at sex determination (1). '''
        if self._manager is None:
            return self._female_fraction
        else:
            return self._manager.female_fraction

    def to_male(self):
        ''' Converts the indeterminate to a male inflorescence. '''
        m = Male(self._manager)
        m.stalk = self.stalk.copy()
        m.stalk._owner = m
        m.components = [m.stalk]
        m.age = self.age

        # fractionality
        f = 1 - self.female_fraction

        # Pass on cohort multiplicity/relative sink strength
        m.multiplicity = f*self.multiplicity
        m.relative_sink_strength = f*self.relative_sink_strength

        return m

    def to_female(self):
        ''' Converts the indeterminate to a female inflorescence. '''
        m = Female(self._manager)

        # Pass on cohort mean organ state/components
        m.stalk = self.stalk.copy()
        m.stalk._owner = m
        m.components = [m.stalk]
        m.age = self.age

        # fractionality
        f = self.female_fraction

        # Pass on cohort multiplicity/relative sink strength
        m.multiplicity = f*self.multiplicity
        m.relative_sink_strength = f*self.relative_sink_strength

        return m

    ########
    # Trivia
    ########

    @property
    def delete(self):
        return self.age > self.age_of_differentiation

class Female(Cohort):
    _name = 'female'
    _version = '0.0'

    default_parameters = yaml.load('''
            inflorescence_abortion_fraction:
                value: 0.05
                unit: '1/month'
                info: 'Total aborted fraction during inflorescence abortion.'
                source: 'Based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 62.'
            inflorescence_abortion_t0:
                value: -3
                unit: 'month'
                info: 'The start of the period in which inflorescence abortion occurs relative to the time of anthesis.'
                source: 'Based on Adam et al. 2011, see fig 3.'
            inflorescence_abortion_t1:
                value: -2
                unit: 'month'
                info: 'The end of the period in which inflorescence abortion occurs relative to the time of anthesis.'
                source: 'Based on Adam et al. 2011, see fig 3.'
            bunch_failure_fraction:
                value: 0.1
                unit: '1/month'
                info: 'Total aborted fraction during bunch abortion.'
                source: 'Based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 62.'
            bunch_failure_t0:
                value: 2
                unit: 'month'
                info: 'The start of the period in which bunch failure occurs relative to the time of anthesis.'
                source: 'Based on Adam et al. 2011, see fig 3.'
            bunch_failure_t1:
                value: 3
                unit: 'month'
                info: 'The end of the period in which bunch failure occurs relative to the time of anthesis.'
                source: 'Based on Adam et al. 2011, see fig 3.'
            anthesis_age:
                value: 33
                unit: 'month'
                info: 'The age at which the anthesis takes place in terms of months after frond initiation.'
                source: 'Based on Adam et al. 2011, see fig 3.'
            moisture_content_deficit_bunch_failure_increase:
                value: .8
                unit: '1'
                info: 'Increase in bunch failure fraction per soil moisture content decrease.'
                source: 'Initial guess: less sensitive than sex ratio and bunch failure.'
            moisture_content_deficit_bunch_failure_threshold:
                value: .2
                unit: '1'
                info: 'Moisture content below wgucg bunch failure response sets in.'
                source: 'Initial guess: less sensitive than sex ratio and bunch failure.'
            moisture_content_deficit_inflorescence_abortion_increase:
                value: 1.
                unit: '1/mm/month'
                info: 'Increase in inflorescence abortion fraction per soil moisture content decrease.'
                source: 'Initial guess: less sensitive than sex ratio, more sensitive than bunch failure.'
            moisture_content_deficit_inflorescence_abortion_threshold:
                value: .4
                unit: '1'
                info: 'Moisture content below which inflorescence abortion response sets in.'
                source: 'Initial guess: less sensitive than sex ratio, more sensitive than bunch failure.'
            age_of_maturity:
                value: 6
                unit: 'month'
                info: 'The age at which the fruit is harvestible, in months after anthesis.'
                source: 'Adam et al. 2011, see fig 3.'
            ''')

    sex = 'female'
    def __init__(self,manager=None):
        self.parameters = deepcopy(self.default_parameters)
        self._manager = manager

        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # state
        self.multiplicity = 1
        self.age = 0
        self.has_flowered = False

        # rate
        self.relative_sink_strength = 0

        # param
        self._anthesis_age = self.parameters['anthesis_age']['value']
        self._age_of_maturity = self._anthesis_age + self.parameters['age_of_maturity']['value']

        self._inflorescence_abortion_t0 = self.parameters['inflorescence_abortion_t0']['value']
        self._inflorescence_abortion_t1 = self.parameters['inflorescence_abortion_t1']['value']

        self._bunch_failure_t0 = self.parameters['bunch_failure_t0']['value']
        self._bunch_failure_t1 = self.parameters['bunch_failure_t1']['value']


        # proto-typical value
        self._water_deficit_ = 0
        self._soil_moisture_content_ = 1

    ##########
    # Update
    ##########
    def update(self,dt=1):
        ''' Update the cohort a time-step. '''

        self._update(dt=dt)

        if self.trigger_flowering:
            self.set_fruit()

    @property
    def _water_deficit(self):
        if self._manager is None:
            return self._water_deficit_
        else:
            return self._manager._water_deficit

    @property
    def _soil_moisture_content(self):
        if self._manager is None:
            return self._soil_moisture_content_
        else:
            return self._manager._soil_moisture_content

    @property
    def abortion_fraction(self):
        ''' The monthly abortion fraction.

        In terms of both floral and bunch abortion.
        '''
        return self.inflorescence_abortion_fraction + self.bunch_failure_fraction

    @property
    def inflorescence_abortion_fraction(self):
        t = self.age - self._anthesis_age

        if (t >= self._inflorescence_abortion_t0) and (t < self._inflorescence_abortion_t1):
            return self._inflorescence_abortion_fraction
        else:
            return 0

    @property
    def _inflorescence_abortion_fraction(self):

        base = self.parameters['inflorescence_abortion_fraction']['value']

        t1 = self._inflorescence_abortion_t1
        t0 = self._inflorescence_abortion_t0

        timespan =  t1-t0

        driver = self._soil_moisture_content
        threshold = self.parameters['moisture_content_deficit_inflorescence_abortion_threshold']['value']
        slope = self.parameters['moisture_content_deficit_inflorescence_abortion_increase']['value']

        # onset when driver < threshold
        modifier = slope*max(0,threshold-driver)

        return (base + modifier)/timespan

    @property
    def bunch_failure_fraction(self):

        t = self.age - self._anthesis_age

        if (t >= self._bunch_failure_t0) and (t < self._bunch_failure_t1):
            return self._bunch_failure_fraction
        else:
            return 0

    @property
    def _bunch_failure_fraction(self):

        base = self.parameters['bunch_failure_fraction']['value']

        t1 = self._bunch_failure_t1
        t0 = self._bunch_failure_t0

        timespan = t1-t0

        driver = self._soil_moisture_content
        threshold = self.parameters['moisture_content_deficit_bunch_failure_threshold']['value']
        slope = self.parameters['moisture_content_deficit_bunch_failure_increase']['value']

        # onset when driver < threshold
        modifier = slope*max(0,threshold-driver)

        return (base + modifier)/timespan

    def set_fruit(self):
        self.mesocarp_oil = MesocarpOil(self)
        self.mesocarp_fibers = MesocarpFibers(self)
        self.kernel = Kernel(self)
        self.components = [self.stalk,
                            self.mesocarp_fibers,
                            self.mesocarp_oil,
                            self.kernel]
        self.has_flowered = True

    @property
    def trigger_flowering(self):
        ''' A boolean indicating whether "set_fruit" should be triggered. '''
        return self.age > self._anthesis_age and not self.has_flowered

    @property
    def is_harvestible(self):
        ''' Indicates whether this cohort is harvestible. '''
        return self.age == self._age_of_maturity

    @property
    def delete(self):
        ''' Indicates whether this cohort may be discarded (metabolically inactive). '''
        return self.age > self._age_of_maturity

    @property
    def mesocarp_oil_content(self):
        ''' Mesocarp oil content (DM/DM). '''
        if self.has_flowered:
            return self.mesocarp_oil.mass/self.mass
        else:
            return 0

class Male(Cohort):
    _name = 'male'
    _version = '0.0'

    default_parameters = yaml.load('''
            age_of_anthesis:
                value: 33
                unit: 'month'
                info: 'The age at which the anthesis takes place in terms of months after frond initiation.'
                source: 'Adam et al. 2011, see fig 3.'
            ''')

    sex = 'male'
    def __init__(self,manager=None):
        self.parameters = deepcopy(self.default_parameters)
        self._manager = manager

        # components
        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # state
        self.multiplicity = 1
        self.age = 0
        self.has_flowered = False

        # rate
        self.relative_sink_strength = 0

        # param
        self.age_of_anthesis = self.parameters['age_of_anthesis']['value']

        self._abortion_fraction = 0

    @property
    def delete(self):
        return self.age > self.age_of_anthesis

def sigmoid(x,x0,k):
    return 1/(1+np.exp(-k*(x-x0)))

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
    sink_strength_potential:
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
        unit: 'tonne_FM/ha/year'
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
        value: [0.6,3]
        unit: '1,YAP'
        info: 'The fraction female for a "young" palm. - 3 YAP, note we are explicitly qualitative here.'
        source: 'Based on the associated qualitative statement found on p.26 in Advances in Oil Palm Research Volume 1, 2000.'
        uncertainty: 20%
    female_fraction_old:
        value: [0.3,30]
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
        self.sink_strength_potential = 0
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
    def get_sink_strength_potential(self):
        ''' The total potential sink strength (tonne_CH2O/ha/month). '''
        return 0.001*sum([x.sink_strength_potential*x.multiplicity for x in self.cohorts])

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
        self.sink_strength_potential = self.get_sink_strength_potential()
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
                'sink_strength_potential',
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