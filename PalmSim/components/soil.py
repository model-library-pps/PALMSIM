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

@add_dumps
class IRHOSoil(object):
    ''' IRHO* soil water deficit model.

    Describes the state of the soil of the field.
    Soil state variables should be interpreted as
    mean values for the soil in the rooting zone.
    For example, in reality we expect a gradient in the
    soil moisture content but here we consider the 
    mean over the rooting zone.

    A simple soil-water model based on the basis of a
    soil-water budget involving the in- and outflow of
    water into the soil.
    Key concepts:
    - available water (AW) [mm]
    - rainfall (P) [mm/month]
    - evapotranspiration (ET) [mm/month]
    - drainage (D) [mm/month]
    - water holding capacity (WHC) [mm]
    - soil water deficit (SWD) [mm]

    The central state variable is the amount of available water (AW)
    --- available to the plant that is. Which is updated as follows:

        AW(t+dt) = AW(t) + (P - ET - D) * dt

    Here drainage (D) follows from any expected surplus of water
    relative to the soil's water holding capacity (WHC):

    D(t) = max(0,AW(t) + (P - ET) * dt - WHC)

    This sub-model has a recommened time-step of integration of
    a (30-day) month.

    Notes
    -----
    *IRHO: Institut de Reserches pour les Huiles et Oleagineaux.
    --- in 1984 merged with other institutes to form CIRAD.

    This model is described in R.H.V. Corley's book on oil palm ---
    chapter 3.

    IRHO takes the PWP as the critical deficit (CD).

    Reference
    ---------
    .. The Oil Palm, Fifth Edition. R.H.V. Corley. Chapter 3.
    '''

    default_parameters = yaml.load('''
    high_evapotranspiration:
        value: 150
        unit: 'mm/month'
        info: 'The assumed typical evapotranspiration in a palm plantation given a number of raindays per month.'
        source: 'IRHO: Institut de Reserches pour les Huiles et Oleagineaux.'
        error: 0
    low_evapotranspiration:
        value: 120
        unit: 'mm/month'
        info: 'The assumed typical evapotranspiration in a palm plantation given a number of raindays per month.'
        source: 'IRHO: Institut de Reserches pour les Huiles et Oleagineaux.'
        error: 0
    water_holding_capacity:
        value: 400.
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Input: soil characteristic.'
    relative_transpiration_a:
        value: 0.4
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential evapotranspiration versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'
    relative_transpiration_b:
        value: 0.12
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential evapotranspiration versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'
    ''')
    default_initial_values = yaml.load('''
    available_water:
        value: 400
        error: 0
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Initial value- set by user.'
    ''')

    variable_units = dict(available_water                  = 'mm',
                          available_water_change = 'mm/month',
                          drainage                        = 'mm/month',
                          evapotranspiration              = 'mm/month',
                          conversion_efficiency_limiter = '1',
                          water_deficit                   = 'mm',
                          water_contained                 = 'mm',
                          raindays                        = 'days/month',
                          rainfall                        = 'mm/month',
                          critical_deficit_exceedance = 'mm',
                          critical_deficit = 'mm',
                          evapotranspiration_potential = 'mm',
                          moisture_content = '1',
                          relative_transpiration = '1',
                          water_holding_capacity = 'mm',
                          )

    _name = 'soil'
    _prefix = _name
    _style = 'IRHO'
    _version = '1.0.0.1'

    def __init__(self,palm=None):

        self._palm = palm
        self.parameters = deepcopy(self.default_parameters)

        self.initial_values = self.default_initial_values

        self._dt_ = .1

        self.available_water = self.initial_values['available_water']['value']

        # implemented for proto-typing purposes. See associated properties.
        self._raindays = 15
        self._rainfall = 120.

    _high_evapotranspiration = Parameter('high_evapotranspiration')
    _low_evapotranspiration = Parameter('low_evapotranspiration')
    _water_holding_capacity = Parameter('water_holding_capacity')

    @property
    def _weather(self):
        if self._palm is None:
            return None
        else:
            return self._palm.weather

    @property
    def raindays(self):
        ''' Number of "days with rain" (days/month). '''
        if self._weather is None:
            return self._raindays
        else:
            return self._weather.raindays

    @property
    def rainfall(self):
        ''' Rainfall (mm/month). '''
        if self._weather is None:
            return self._rainfall
        else:
            return self._weather.rainfall

    @property
    def water_holding_capacity(self):
        ''' Amount of water available (mm) to the plant.

        Equals the amount of water freed when moving
        from the water holding capacity
        to the permanent wilting point. '''
        return self._water_holding_capacity

    @property
    def _dt(self):
        ''' time step (month) '''
        return self._dt_

    @property
    def evapotranspiration_potential(self):
        ''' Potential Evapotransipiration (ET) rate (mm/month).

        A key assumption made in the IRHO method:
            ET = high if raindays < 10 / month (an arid month)
            ET = low if rainsdays > 10 / month (a humid month)
        '''
        raindays = self.raindays

        if raindays <=10:
            res = self._high_evapotranspiration
        else:
            res = self._low_evapotranspiration

        return res

    @property
    def moisture_content(self):
        ''' The available water : water holding capacity ratio (1). '''
        AW = self.available_water
        AWC = self.water_holding_capacity
        return AW/AWC

    @property
    def relative_transpiration(self):
        ''' The relative transpiration rate (1).
        
        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''
        rel_AW = self.moisture_content

        a = self.parameters['relative_transpiration_a']['value']
        b = self.parameters['relative_transpiration_b']['value']

        # ET reduces with rel. lack of AW
        return 1/(1+np.exp(-(rel_AW-a)/b))

    @property
    def evapotranspiration(self):
        ''' Actual evapotransipiration (ET) rate (mm/month). '''

        return self.relative_transpiration*self.evapotranspiration_potential

    @property
    def drainage(self):
        ''' Drainage rate (mm/month).

        Here taken broadly as any process bringing the
        water level to the water holding capacity:
        run-off, percolation, etc.
        '''

        AW = self.available_water
        P = self.rainfall
        ET = self.evapotranspiration
        AWC = self.water_holding_capacity

        potential_available_water = AW + (P-ET)

        return max(0.,potential_available_water-AWC)

    @property
    def available_water_change(self):
        ''' Rate with which the water held changes (mm/month).

        Follows from the sum of rainfall (P),
        evapotranspiration (ET) and drainage (D):

            d/dt(AW) = P - ET - D
        '''

        P = self.rainfall
        ET = self.evapotranspiration
        D = self.drainage
        return P-ET-D

    @property
    def water_deficit(self):
        ''' The water deficit (mm).

        Follows by subtracting the available water (mm) from the
        the soil water holding capacity (mm).
        '''

        return max(0.,self.water_holding_capacity-self.available_water)

    @property
    def critical_deficit(self):
        ''' The water deficit (mm) at which the plant starts to lose function.

        Notes
        -----
        IRHO assumes water stress sets in when approximately 100% of
        the available water capacity has been tapped. See [1].

        Reference
        ---------
        [1] The Oil Palm, Fifth Edition. R.H.V. Corley. Chapter 3.

        '''
        return self.water_holding_capacity

    @property
    def critical_deficit_exceedance(self):
        ''' The water deficit's exceedance of the critical deficit (mm).

        Note, this signal couples to the plant!
        '''
        return max(0.,self.water_deficit - self.critical_deficit)

    def update(self, dt=1):
        ''' Update 1 month. '''

        steps = int(dt/self._dt)

        for step in range(steps):
            self._update()

    def _update(self):
        ''' Update with a time-step of dt (month). '''

        self.available_water += self.available_water_change*self._dt

class ReySoil(IRHOSoil):
    ''' A twist on the IRHO soil model inspired by the study by Rey et al., 1998.

    The twist consists in taking the critical deficit equal to
    .7 times the available water capacity instead of 1.0 times.
    '''

    _style = 'Rey'
    _version = '1.0.0.1'

    @property
    def critical_deficit(self):
        ''' The water deficit (mm) at which the palm starts to lose function.

        Notes
        -----
        Rey et al. concluded from experiments in the Ivory Coast that
        noticeable water stress sets in when approximately 70% of
        the available water capacity has been tapped.

        Henson et al. found that the crop factor fell below 1 when as little
        as 15% of the available water capacity had been used, indicating
        a much smaller CD.

        Reference
        ---------
        Rey et al., 1998

        '''
        return .7*self.water_holding_capacity

class LegacySoil(IRHOSoil):
    ''' Hoffman's soil model --- a twist on the IRHO model:

    IRHO assumes stress to set on when the available water is zero i.e.
    the critical deficit is assumed to be equal to the available
    water capacity. In other words stress equals time spent
    past the permanent wilting point.

    In this legacy version the soil water deficit (SWD)
    amounts to the lack of available water (AW) relative to zero (mm)
    available water -- not relative to field/water holding capacity (WHC).
    Furthermore, the plant stress is modelled to set on at zero SWD:
    the critical deficit (CD) is taken to be zero.
    Note, these two features counteract each other i.e.:
    The stress sets on when the SWD equals the WHC.

    The choices are somehow a bit un-orthodox.

    Reference
    ---------
    Hoffmann et al, 2014. Simulating potential growth and
    yield of oil palm (Elaeis guineensis) with PALMSIM: Model description,
    evaluation and application. Agricultural Systems, 131, 1-10.

    '''

    _style = 'Legacy'
    _version = '1.0.0.1'

    @property
    def water_deficit(self):
        ''' The soil water deficit in the soil (mm).

        Notes
        -----
        Hoffman/Alba gauge the deficit relative to 0 available water,
        not relative to the water holding capacity.
        '''

        return max(0.,0-self.available_water)

    @property
    def critical_deficit(self):
        ''' The water deficit (mm) at which the palm starts to lose function.

        Notes
        -----
        The Hoffman/Alba soil model assumes water stress sets in when there is
        a "strict deficit": the critical deficit is 0.

        '''

        return 0.

# Aliases
Soil = ReySoil
LatestSoil = ReySoil