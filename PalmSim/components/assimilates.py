#!/usr/bin/env python

''' Contains the assimilate modelling class. '''

import yaml
import numpy as np

from .helpers import add_dumps

from .constants import DAYS_PER_MONTH

@add_dumps
class Assimilates(object):
    ''' Models the distribution of assimilates.

    Notes
    -----
    To prevent confusion all variable names do start with 'assim'
    otherwise this object would have variables e.g. 'growth_trunk'
    which might not make sense

    Reference
    ---------
    .. Hoffmann, M.P., Castaneda Vera, A., van Wijk, M.T., Giller, K.E., Oberthür,
    T., Donough, C., Whitbread, A.M., (2014)Simulating potential growth and
    yield of oil palm (Elaeis guineensis) with PALMSIM: Model description,
    evaluation and application. Agricultural Systems, 131, 1-10.
    '''

    parameters = yaml.load('''

        vegetative_priority:
            value: .8
            unit: '1'
            info: 'The priority given to assimilates for vegetative growth -- 0: according to sink strength, 1: full priority.'
            source: 'Based on the figure found in Corley, ch. 5, p. 100 (attributed to Squire, 1990) and furthermore Legros et al. 2009.'

    ''')

    variable_units = yaml.load('''

    assim_growth_fronds: 't_CH2O/ha/mo'
    assim_growth_generative: 't_CH2O/ha/mo'
    assim_growth_male: 't_CH2O/ha/mo'
    max_assim_growth_male: 't_CH2O/ha/mo'
    assim_growth_roots: 't_CH2O/ha/mo'
    assim_growth_total: 't_CH2O/ha/mo'
    assim_growth_trunk: 't_CH2O/ha/mo'
    assim_growth_vegetative: 't_CH2O/ha/mo'
    assim_maintenance_female: 't_CH2O/ha/mo'
    assim_maintenance_fronds: 't_CH2O/ha/mo'
    assim_maintenance_generative: 't_CH2O/ha/mo'
    assim_maintenance_male: 't_CH2O/ha/mo'
    assim_maintenance_roots: 't_CH2O/ha/mo'
    assim_maintenance_total: 't_CH2O/ha/mo'
    assim_maintenance_trunk: 't_CH2O/ha/mo'
    assim_maintenance_vegetative: 't_CH2O/ha/mo'
    assim_produced: 't_CH2O/ha/mo'
    potential_sink_strength_vegetative: 't_CH2O/ha/mo'
    assim_veg_growth_fraction_roots: '1'
    assim_veg_growth_fraction_trunk: '1'
    assim_veg_growth_fraction_fronds: '1'

    ''')

    _prefix = 'assimilates'

    def __init__(self,palm=None):
        '''
        Upon calling the set_attributes() method
        the state agrees with the current state
        of the palm (if there is any -- none during prototyping) and its components.
        '''

        self._palm = palm

        self.potential_sink_strength_generative = 0
        self.potential_sink_strength_vegetative = 0

        # only used in testing
        self._assim_veg_growth_fraction_roots_ = 0.1
        self._assim_veg_growth_fraction_trunk_ = 0.1
        self._assim_veg_growth_fraction_fronds_ = 0.8

        # the attributes set by set attributes make up the state.
        self.set_attributes()

    #~~~~~~~~~~

    @property
    def _MAP(self):
        ''' Months after planting (month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    #~~~~~~~~~~

    def update(self):
        ''' Update to the current month.

        Provides a view of the current situation.
        I.e. all state variables are a view of the organs
        and their relative sink strength/growth.
        '''
        self.set_attributes()

    def set_attributes(self):
        ''' Set all the instance variable values. '''

        self.potential_sink_strength_vegetative = self.get_potential_sink_strength_vegetative()
        self.potential_sink_strength_generative = self.get_potential_sink_strength_generative()
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

    #~~~~~~~~~~

    def get_potential_sink_strength_vegetative(self):
        ''' Sink strength (t_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.potential_sink_strength + \
                    self._palm.trunk.potential_sink_strength + \
                    self._palm.roots.potential_sink_strength

    def get_potential_sink_strength_generative(self):
        ''' Potential sink strength (t_CH20/ha/month). '''
        return self.potential_sink_strength_organs

    #~~~~~~~~~~

    @property
    def potential_sink_strength_total(self):
        return self.potential_sink_strength_fronds + \
                self.potential_sink_strength_trunk + \
                self.potential_sink_strength_roots + \
                self.potential_sink_strength_generative

    #~~~~~~~~~~

    @property
    def potential_sink_strength_fronds(self):
        ''' Potential sink strength (t_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.fronds.potential_sink_strength

    @property
    def potential_sink_strength_trunk(self):
        ''' Potential sink strength (t_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.trunk.potential_sink_strength

    @property
    def potential_sink_strength_roots(self):
        ''' Potential sink strength (t_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.roots.potential_sink_strength

    @property
    def potential_sink_strength_organs(self):
        ''' Potential sink strength (t_CH20/ha/month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.organs.potential_sink_strength

    #~~~~~~~~~~

    def get_assim_growth_fronds(self):
        ''' Assimilates for growth (t_CH2O/ha/month). '''
        return self.assim_veg_growth_fraction_fronds * self.assim_growth_vegetative

    def get_assim_growth_roots(self):
        ''' Assimilates for growth (t_CH2O/ha/month). '''
        return self.assim_veg_growth_fraction_roots * self.assim_growth_vegetative

    def get_assim_growth_trunk(self):
        ''' Assimilates for growth (t_CH2O/ha/month). '''
        return self.assim_veg_growth_fraction_trunk * self.assim_growth_vegetative

    #~~~~~~~~~~

    @property
    def assim_veg_growth_fraction_fronds(self):
        ''' Fraction of assimilates (1) for vegetative growth. '''
        if self._palm is None:
            return self._assim_veg_growth_fraction_fronds_
        else:
            return self._palm.fronds.potential_sink_strength\
                    /self.potential_sink_strength_vegetative

    @property
    def assim_veg_growth_fraction_trunk(self):
        ''' Fraction of assimilates (1) for vegetative growth. '''
        if self._palm is None:
            return self._assim_veg_growth_fraction_trunk_
        else:
            return self._palm.trunk.potential_sink_strength\
                    /self.potential_sink_strength_vegetative

    @property
    def assim_veg_growth_fraction_roots(self):
        ''' Fraction of assimilates (1) for vegetative growth. '''
        if self._palm is None:
            return self._assim_veg_growth_fraction_roots_
        else:
            return self._palm.roots.potential_sink_strength\
                    /self.potential_sink_strength_vegetative

    #~~~~~~~~~~

    def get_assim_growth_vegetative(self):
        ''' Assimilates for growth (t_CH2O/ha/month). '''
        S = self.assim_growth_total
        Ds = [self.potential_sink_strength_vegetative,
              self.potential_sink_strength_generative]

        k = self.parameters['vegetative_priority']['value']

        res = float(parametrized_partitioning(S,Ds,k)[0])

        if res <= 0:
            return 0
        else:
            return res

    def get_assim_growth_generative(self):
        ''' Assimilates for growth (t_CH2O/ha/month). '''
        S = self.assim_growth_total

        potential = self.potential_sink_strength_generative

        Ds = [self.potential_sink_strength_vegetative,
              potential]

        k = self.parameters['vegetative_priority']['value']


        res = float(parametrized_partitioning(S,Ds,k)[1])

        return min(res,potential)

    #~~~~~~~~~~

    def get_assim_growth_total(self):

        assim_growth_total = self.assim_produced-self.assim_maintenance_total

        if assim_growth_total >= 0:
            return assim_growth_total
        else:
            return 0

    def get_assim_produced(self):
        if self._palm is None:
            return 0.
        else:
            return self._palm.fronds.assim_produced

    #~~~~~~~~~~

    def get_assim_maintenance_total(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        return self.assim_maintenance_vegetative + self.assim_maintenance_generative

    def get_assim_maintenance_vegetative(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        return self.assim_maintenance_roots \
                + self.assim_maintenance_trunk \
                + self.assim_maintenance_fronds

    def get_assim_maintenance_fronds(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.fronds.maintenance_requirement

    def get_assim_maintenance_generative(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.organs.maintenance_requirement

    def get_assim_maintenance_trunk(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.trunk.maintenance_requirement

    def get_assim_maintenance_roots(self):
        ''' Assimilates for maintenance (t_CH2O/ha/month). '''
        if self._palm is None:
            return 0.
        else:
            return self._palm.roots.maintenance_requirement

    #~~~~~~~~~~

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