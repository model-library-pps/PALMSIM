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

from .helpers import Parameter
from .helpers import add_dumps
from .helpers import METERS_PER_HECTARE
from .helpers import DAYS_PER_MONTH
from .helpers import GAUGE_PLANTING_DENSITY

import numpy as np

def sigmoid(x,x0,k):
    return 1/(1+np.exp(-k*(x-x0)))

def prioritized_partitioning(S,Ds):
    ''' Hard-priority partitioning of supply S given demands Ds.

    Priority governed by the order of Ds.

    Parameters
    ----------
    S: float, supply
    Ds: array-float, demands

    Returns
    -------
    Ss: array-float, s.t. sum(Ss) = S, Ss[0] <= Ds[0], .

    Examples
    --------
    >>> prioritized_partitioning(2,[1.5,1])
    [1.5,.5]

    >>> prioritized_partitioning(2,[1,1])
    [1,1]

    >>> prioritized_partitioning(2,[2,1])
    [2,0]

    >>> prioritized_partitioning(4,[2,1])
    [2,2]
    '''

    # output
    Ss = []

    for D in Ds[:-1]:
        # D < S
        if D < S:
            Ss.append(D)
            S -= D

        # D > S
        else:
            Ss.append(S)
            S = 0

    Ss.append(S)

    Ss = np.array(Ss)
    Ss[Ss < 0] = 0

    return Ss

def proportionate_partitioning(S,Ds):
    ''' No-priority partitioning of supply S given demands Ds.

    Parameters
    ----------
    S: float, supply
    Ds: array-float, demands

    Returns
    -------
    Ss: array-float, s.t. sum(Ss) = S, Ss/Ds = constant.

    Examples
    --------
    >>> proportionate_partitioning(6,[2,1])
    [4,2]

    >>> proportionate_partitioning(2,[1,1])
    [1,1]

    '''

    total_demand = sum(Ds)

    scalar = S/total_demand

    return np.array([scalar*D for D in Ds])

def parametrized_partitioning(S,Ds,k):
    ''' Partitioning of supply S given demands Ds
    where k in [0,1] sets the level of prioritization.

    I.e. k = 1 -> fully prioritized, k = 0 -> fully proportionate.
    Linear combination thereof for 0 < k < 1.
    '''

    return k*prioritized_partitioning(S,Ds) + \
            (1-k)*proportionate_partitioning(S,Ds)

@add_dumps
class Assimilates(object):
    ''' Models the distribution of assimilates.

    Notes
    -----
    To prevent confusion all variable names do start with 'assim'
    otherwise this object would have variables e.g. 'growth_trunk'
    which might not make sense

    Introduces minimal complexity and uncertainty at the cost of
    leaving the assimilates for reproductive growth broken:
    there is no sink limit on the assimilates for male growth
    these thus equal the assimilates for generative growth.
    Should be extended (at least) in the following way:
    - implement this sink limit on the assimilates for male growth.
    - implement sink limits on the assimilates per single (m/f) reproductive organ.

    Reference
    ---------
    .. Hoffmann, M.P., Castaneda Vera, A., van Wijk, M.T., Giller, K.E., Oberthür,
    T., Donough, C., Whitbread, A.M., (2014)Simulating potential growth and
    yield of oil palm (Elaeis guineensis) with PALMSIM: Model description,
    evaluation and application. Agricultural Systems, 131, 1-10.
    '''

    default_parameters = yaml.load('''
        vegetative_priority:
            value: .8
            unit: '1'
            info: 'The priority given to assimilates for vegetative growth -- 0: according to sink strength, 1: full priority.'
            source: 'Based on the figure found in Corley, ch. 5, p. 100 (attributed to Squire, 1990) and furthermore Legros et al. 2009.'
        ''')

    variable_units = dict(
                        assim_growth_fronds             = 'tonne_CH2O/ha/month',
                        assim_growth_generative         = 'tonne_CH2O/ha/month',
                        assim_growth_male               = 'tonne_CH2O/ha/month',
                        max_assim_growth_male           = 'tonne_CH2O/ha/month',
                        assim_growth_roots              = 'tonne_CH2O/ha/month',
                        assim_growth_total              = 'tonne_CH2O/ha/month',
                        assim_growth_trunk              = 'tonne_CH2O/ha/month',
                        assim_growth_vegetative         = 'tonne_CH2O/ha/month',
                        assim_maintenance_female        = 'tonne_CH2O/ha/month',
                        assim_maintenance_fronds        = 'tonne_CH2O/ha/month',
                        assim_maintenance_generative    = 'tonne_CH2O/ha/month',
                        assim_maintenance_male          = 'tonne_CH2O/ha/month',
                        assim_maintenance_roots         = 'tonne_CH2O/ha/month',
                        assim_maintenance_total         = 'tonne_CH2O/ha/month',
                        assim_maintenance_trunk         = 'tonne_CH2O/ha/month',
                        assim_maintenance_vegetative    = 'tonne_CH2O/ha/month',
                        assim_produced                  = 'tonne_CH2O/ha/month',
                        sink_strength_potential_vegetative = 'tonne_CH2O/ha/month',
                        assim_roots_fraction = '1',
                        assim_trunk_fraction = '1',
                        assim_fronds_fraction = '1',
                        )

    _style = 'Sink-Based'
    _version = '1.0.0.1'
    _name = 'assimilates'
    _prefix = ''

    def __init__(self,palm=None):
        '''
        Upon calling the set_attributes() method
        the state agrees with the current state
        of the palm (if there is any -- none during prototyping) and its components.
        '''

        self._palm = palm

        self.parameters = deepcopy(self.default_parameters)

        self._vegetative_priority = self.parameters['vegetative_priority']['value']

        self.sink_strength_potential_generative = 0
        self.sink_strength_potential_vegetative = 0

        # proto-typical variables --- only used during proto-typing.
        self.set_prototypical_variables()

        # the attributes set by set attributes make up the state.
        self.set_attributes()

    @property
    def _instance_variables(self):
        ''' The instance variable names (a list). '''
        return ['assim_growth_fronds',
                'assim_growth_generative',
                'assim_growth_roots',
                'assim_growth_total',
                'assim_growth_trunk',
                'assim_growth_vegetative',
                'assim_maintenance_fronds',
                'assim_maintenance_generative',
                'assim_maintenance_vegetative',
                'assim_maintenance_roots',
                'assim_maintenance_total',
                'assim_maintenance_trunk',
                'assim_produced',
                'assim_roots_fraction',
                'assim_trunk_fraction',
                'assim_fronds_fraction',
                ]

    @property
    def _MAP(self):
        ''' Months after planting (month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    def update(self):
        ''' Entails setting the instance variable values by
        dividing the assimilate supply to meet the demand. '''
        self.set_attributes()

    def set_prototypical_variables(self):
        # proto-typical variables --- only used during proto-typing.
        self._assim_roots_fraction = 0.1
        self._assim_trunk_fraction = 0.1
        self._assim_fronds_fraction = 0.8

    def set_attributes(self):
        ''' Set all the instance variable values. '''

        self.sink_strength_potential_vegetative = self.get_sink_strength_potential_vegetative()
        self.sink_strength_potential_generative = self.get_sink_strength_potential_generative()
        self.assim_produced               = self.get_assim_produced()
        self.assim_maintenance_fronds     = self.get_assim_maintenance_fronds()
        self.assim_maintenance_trunk      = self.get_assim_maintenance_trunk()
        self.assim_maintenance_roots      = self.get_assim_maintenance_roots()
        self.assim_maintenance_vegetative = self.get_assim_maintenance_vegetative()
        self.assim_maintenance_generative = self.get_assim_maintenance_generative()
        self.assim_maintenance_total      = self.get_assim_maintenance_total()
        self.assim_growth_total           = self.get_assim_growth_total()
        self.assim_growth_vegetative      = self.get_assim_growth_vegetative()
        self.assim_growth_fronds          = self.get_assim_growth_fronds()
        self.assim_growth_roots           = self.get_assim_growth_roots()
        self.assim_growth_trunk           = self.get_assim_growth_trunk()
        self.assim_growth_generative      = self.get_assim_growth_generative()

    ########
    # Supply
    ########

    def get_assim_produced(self):
        if self._palm is None:
            return 0.
        else:
            return self._palm.fronds.assim_produced

    ##########################
    # Potential sink strengths
    ##########################

    @property
    def sink_strength_potential_total(self):
        return self.sink_strength_potential_fronds + \
                self.sink_strength_potential_trunk + \
                self.sink_strength_potential_roots + \
                self.sink_strength_potential_generative

    @property
    def sink_strength_potential_fronds(self):
        ''' Potential sink strength (tonne_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.sink_strength_potential

    @property
    def sink_strength_potential_trunk(self):
        ''' Potential sink strength (tonne_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.trunk.sink_strength_potential

    @property
    def sink_strength_potential_roots(self):
        ''' Potential sink strength (tonne_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.roots.sink_strength_potential

    @property
    def sink_strength_potential_organs(self):
        ''' Potential sink strength (tonne_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.organs.sink_strength_potential

    def get_sink_strength_potential_vegetative(self):
        ''' Sink strength (tonne_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.sink_strength_potential + \
                    self._palm.trunk.sink_strength_potential + \
                    self._palm.roots.sink_strength_potential

    def get_sink_strength_potential_generative(self):
        ''' Potential sink strength (tonne_CH20/ha/month). '''
        return self.sink_strength_potential_organs

    ###################
    # Maintenance rates
    ###################

    def get_assim_maintenance_fronds(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.fronds.maintenance_requirement

    def get_assim_maintenance_trunk(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.trunk.maintenance_requirement

    def get_assim_maintenance_roots(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.roots.maintenance_requirement

    def get_assim_maintenance_vegetative(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        return self.assim_maintenance_roots \
                + self.assim_maintenance_trunk \
                + self.assim_maintenance_fronds

    def get_assim_maintenance_generative(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.organs.maintenance_requirement

    def get_assim_maintenance_total(self):
        ''' Assimilates for maintenance (tonne_CH2O/ha/month). '''
        return self.assim_maintenance_vegetative + self.assim_maintenance_generative

    ########
    # Growth
    ########
    def get_assim_growth_total(self):

        assim_growth_total = self.assim_produced-self.assim_maintenance_total

        if assim_growth_total >= 0:
            return assim_growth_total
        else:
            return 0

    def get_assim_growth_vegetative(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''
        S = self.assim_growth_total
        Ds = [self.sink_strength_potential_vegetative,
              self.sink_strength_potential_generative]
        k = self._vegetative_priority

        res = float(parametrized_partitioning(S,Ds,k)[0])

        if res <= 0:
            return 0
        else:
            return res

    def get_assim_growth_generative(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''
        S = self.assim_growth_total

        potential = self.sink_strength_potential_generative

        Ds = [self.sink_strength_potential_vegetative,
              potential]
        k = self._vegetative_priority

        res = float(parametrized_partitioning(S,Ds,k)[1])

        return min(res,potential)

    @property
    def assim_fronds_fraction(self):
        ''' Fraction of assimilates (1) for vegetative growth.

        Returns
        -------
        A float-value of around 0.7
        '''
        if self._palm is None:
            return self._assim_fronds_fraction
        else:
            return self._palm.fronds.sink_strength_potential\
                    /self.sink_strength_potential_vegetative

    @property
    def assim_trunk_fraction(self):
        ''' Fraction of assimilates (1) for vegetative growth.

        Returns
        -------
        A float-value of around 0.1
        '''
        if self._palm is None:
            return self._assim_trunk_fraction
        else:
            return self._palm.trunk.sink_strength_potential\
                    /self.sink_strength_potential_vegetative

    @property
    def assim_roots_fraction(self):
        ''' Fraction of assimilates (1) for vegetative growth.

        Returns
        -------
        A float-value of around 0.1
        '''
        if self._palm is None:
            return self._assim_roots_fraction
        else:
            return self._palm.roots.sink_strength_potential\
                    /self.sink_strength_potential_vegetative

    def get_assim_growth_fronds(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''
        return self.assim_fronds_fraction * self.assim_growth_vegetative

    def get_assim_growth_roots(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''
        return self.assim_roots_fraction * self.assim_growth_vegetative

    def get_assim_growth_trunk(self):
        ''' Assimilates for growth (tonne_CH2O/ha/month). '''
        return self.assim_trunk_fraction * self.assim_growth_vegetative

LatestAssimilates = Assimilates