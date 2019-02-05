#!/usr/bin/env python

''' Provides the soil-water balance models. '''

import yaml
import numpy as np

from .helpers import add_dumps

class PTF(object):
    """ Translates a soil texture string to volumetric water contents; a PTF.
    
    Implements the translation rules of [1], uses a Van Genuchten methodology.
    
    Examples
    --------
    
    ptf = PTF('Sand')
    
    Fetch shaping parameter (1/kPa)
    
    >>> ptf.alpha
    0.38
    
    Fetch plant available water content (m3/m3)
    
    >>> ptf.PAWC
    0.2
    
    References
    ----------
    [1] Hodnett, Martin & Tomasella, Javier. (2002).
        Marked differences between van Genuchten soil water-retention
        parameters for temperate and tropical soils:
        A new water-retention pedo-transfer functions developed for tropical soils.
        Geoderma. 108. 155-180. 10.1016/S0016-7061(02)00105-2. 

    """
    
    parameter_library = yaml.load("""
    
    sand:
        alpha: 0.380
        n: 2.474
        saturated_moisture_content: 0.410
        residual_moisture_content: 0.037
    loamy sand:
        alpha: 0.837
        n: 1.672
        saturated_moisture_content: 0.438
        residual_moisture_content: 0.062
    sandy loam:
        alpha: 0.396
        n: 1.553
        saturated_moisture_content: 0.461
        residual_moisture_content: 0.111
    loam:
        alpha: 0.246
        n: 1.461
        saturated_moisture_content: 0.521
        residual_moisture_content: 0.155
    silty loam:
        alpha: 0.191
        n: 1.644
        saturated_moisture_content: 0.601
        residual_moisture_content: 0.223
    sandy clay loam:
        alpha: 0.644
        n: 1.535
        saturated_moisture_content: 0.413
        residual_moisture_content: 0.149
    clay loam:
        alpha:  0.392
        n: 1.437
        saturated_moisture_content: 0.519
        residual_moisture_content: 0.226
    silty clay loam:
        alpha: 0.298
        n: 1.513
        saturated_moisture_content: 0.586
        residual_moisture_content: 0.267
    silty clay:
        alpha:  0.258
        n: 1.466
        saturated_moisture_content: 0.570
        residual_moisture_content: 0.278
    sandy clay:
        alpha:  0.509
        n: 1.396
        saturated_moisture_content: 0.460
        residual_moisture_content: 0.199
    clay:
        alpha: 0.463
        n: 1.514
        saturated_moisture_content: 0.546
        residual_moisture_content: 0.267
    
    """    
    )
    
    def __init__(self, texture_class = 'sand'):
        
        self.texture_class = texture_class
    
    @property
    def options(self):
        return list(self.parameter_library)
    
    @property
    def parameters(self):
        """ Parameters (dict) associated with a certain texture class. """
        key = self.texture_class
        library = self.parameter_library
        
        return library[key]
        
    @property
    def alpha(self):
        """  (1/kPa) """
        return self.parameters['alpha']
    
    @property
    def n(self):
        """ (1) """
        return self.parameters['n']
    
    @property
    def m(self):
        """ (1) """
        return 1. - 1./self.n
    
    @property
    def saturated_moisture_content(self):
        """ (m3/m3) """
        return self.parameters['saturated_moisture_content']
    
    @property
    def residual_moisture_content(self):
        """ (m3/m3) """
        return self.parameters['residual_moisture_content']
    
    def calc_water_content(self, pressure):
        """ Returns the volumetric water content at a certain suction pressure (m3/m3) """
        
        a = self.alpha
        n = self.n
        
        sat = self.saturated_moisture_content
        res = self.residual_moisture_content
        
        m = 1. - 1./n
        
        num = sat-res
        denum = (1 + (a * pressure)**n)**m
        
        water_content = res + num/denum
        
        return water_content
    
    @property
    def water_content_FC(self):
        """ the volumetric water content (m3/m3) at -33 kPa  """
        
        # reference pressures - matrix potential (kPa)
        P_ref = 10
            
        return self.calc_water_content(pressure=P_ref)
    
    @property
    def water_content_PWP(self):
        """ the volumetric water content (m3/m3) at -1500 kPa  """
        
        # reference pressures - matrix potential (kPa)
        P_ref = 1500
            
        return self.calc_water_content(pressure=P_ref)
    
    @property
    def plant_available_water_content(self):
        """ The plant available volumetric water content (m3/m3).
        
        Defined as the difference in water content at
        field capacity (-33 kPa) and at the permanent wilting point (-1500 kPa).
        """
        
        return self.water_content_FC - self.water_content_PWP

@add_dumps
class SoilMixin(object):
    ''' '''

    parameters = yaml.load('''

    water_holding_capacity:
        value: 500.
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Input: soil/root characteristic.'

    high_ET:
        value: 5
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given <= 10 raindays per month - little rain == much sun == much ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    low_ET:
        value: 4
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given > 10 raindays per month - much rain == little sun == little ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    relative_transpiration_rate_x0:
        value: 0.2
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'

    relative_transpiration_rate_b:
        value: 0.1
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'
    ''')

    initial_values = yaml.load('''

    available_water:
        value: 300
        error: 0
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Initial value - set by user.'

    ''')

    units = yaml.load('''

        available_water                   : 'mm'
        drainage                          : 'mm/day'
        conversion_efficiency_limiter     : '1'
        water_deficit                     : 'mm'
        water_contained                   : 'mm'
        rainfall                          : 'mm/day'
        critical_deficit_exceedance       : 'mm'
        critical_deficit                  : 'mm'
        ET_monthly_potential              : 'mm'
        moisture_content                  : '1'
        relative_transpiration_rate       : '1'
        water_holding_capacity            : 'mm'
        available_water_change_rate       : 'mm/day'
        evapotranspiration                : 'mm/day'
        evapotranspiration_potential      : 'mm/day'

    ''')

    _prefix = 'soil'

    def __init__(self,palm=None):

        self._palm = palm

        self.available_water = self.initial_values['available_water']['value']

        # implemented for proto-typing purposes. See associated properties.
        self._rainfall_ = 120

    #~~~~~~~~~~~~~~~~

    @property
    def _weather(self):
        ''' A reference to the weather. '''
        if self._palm is None:
            return None
        else:
            return self._palm.weather

    @property
    def rainfall(self):
        ''' Rainfall (mm/day). '''
        if self._weather is None:
            return self._rainfall_
        else:
            return self._weather.rainfall

    #~~~~~~~~~~~~~~~~

    @property
    def water_holding_capacity(self):
        '''The water holding capacity of the soil.

        The amount of water freed when moving
        from the water holding capacity
        to the permanent wilting point.
        '''

        c = self.parameters['water_holding_capacity']['value']

        return c

    @property
    def moisture_content(self):
        ''' The available water : water holding capacity ratio (1). '''
        AW = self.available_water
        AWC = self.water_holding_capacity
        
        return AW/AWC

    #~~~~~~~~~~~~~~~~

    def update(self, dt=1):
        ''' Update by dt days. '''

        for i in range(dt):
            self._update(dt=1)
            
    def _update(self, dt=1):
        ''' Update by dt days. '''

        self.available_water += self.available_water_change_rate*dt

        assert self.available_water >= 0

    #~~~~~~~~~~~~~~~~

    @property
    def available_water_change_rate(self):
        ''' Rate with which the water held changes (mm/day).

        Follows from the sum of rainfall_monthly (P),
        ET_monthly (ET) and drainage_monthly (D):

            d/dt(AW) = P - ET - D
        '''

        P = self.rainfall
        ET = self.evapotranspiration
        D = self.drainage

        return P-ET-D

    #~~~~~~~~~~~~~~~~

    @property
    def evapotranspiration(self):
        ''' Actual evapotransipiration (ET) rate (mm/day). '''
        return self.relative_transpiration_rate*self.evapotranspiration_potential

    @property
    def relative_transpiration_rate(self):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''

        rel_AW = self.moisture_content

        return self.calc_relative_transpiration_rate(rel_AW)

    def calc_relative_transpiration_rate(self, rel_AW):
        ''' The relative transpiration rate (1).

        A value of 1 corresponds to potential transpiration.
        A (extreme) value of 0 corresponds to no transpiration.
        '''
        
        a = self.parameters['relative_transpiration_rate_x0']['value']
        b = self.parameters['relative_transpiration_rate_b']['value']

        # ET reduces with rel. lack of AW
        return 1/(1+np.exp(-(rel_AW-a)/b))

    @property
    def drainage(self):
        ''' Drainage rate (mm/day).

        Here taken broadly as any process bringing the
        water level to the water holding capacity:
        run-off, percolation, etc.
        '''

        AW = self.available_water
        P = self.rainfall
        ET = self.evapotranspiration

        AW_potential = AW + (P-ET)

        AWC = self.water_holding_capacity

        # any AW > AWC := drainage
        D_potential = AW_potential - AWC

        # D >= 0
        return max(0., D_potential)

    #~~~~~~~~~~~~

    @property
    def water_deficit(self):
        ''' The water deficit (mm).

        Follows by subtracting the available water (mm) from the
        the soil water holding capacity (mm).
        '''

        return max(0.,self.water_holding_capacity-self.available_water)

@add_dumps
class IRHOSoil(SoilMixin):
    ''' IRHO* soil water deficit model.

    Describes the state of the soil of the field.
    Soil state variables should be thought of as
    mean values for the soil in the rooting zone.

    A simple soil-water model based on the basis of a
    soil-water budget involving the in- and outflow of
    water into the soil.

    Key concepts:
    - available water (AW) [mm]
    - rainfall_monthly (P) [mm/month]
    - ET_monthly (ET) [mm/month]
    - drainage_monthly (D) [mm/month]
    - water holding capacity (WHC) [mm]
    - soil water deficit (SWD) [mm]

    The central state variable is the amount of available water (AW)
    --- available to the plant that is. Which is updated as follows:

        AW(t+dt) = AW(t) + (P - ET - D) * dt

    Here drainage_monthly (D) follows from any expected surplus of water
    relative to the soil's water holding capacity (WHC):

    D(t) = max(0,AW(t) + (P - ET) * dt - WHC)

    This sub-model is compatible with daily time-steps.

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

    parameters = yaml.load('''

    water_holding_capacity:
        value: 500.
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Input: soil/root characteristic.'

    high_ET:
        value: 5
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given <= 10 raindays per month - little rain == much sun == much ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    low_ET:
        value: 4
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given > 10 raindays per month - much rain == little sun == little ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    relative_transpiration_rate_x0:
        value: 0.2
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'

    relative_transpiration_rate_b:
        value: 0.1
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'
    ''')

    initial_values = yaml.load('''

    available_water:
        value: 300
        error: 0
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Initial value - set by user.'

    ''')

    units = yaml.load('''

        available_water                   : 'mm'
        drainage                          : 'mm/day'
        conversion_efficiency_limiter     : '1'
        water_deficit                     : 'mm'
        water_contained                   : 'mm'
        raindays                          : 'days/month'
        rainfall                          : 'mm/day'
        critical_deficit_exceedance       : 'mm'
        critical_deficit                  : 'mm'
        ET_monthly_potential              : 'mm'
        moisture_content                  : '1'
        relative_transpiration_rate       : '1'
        water_holding_capacity            : 'mm'
        available_water_change_rate       : 'mm/day'
        evapotranspiration                : 'mm/day'
        evapotranspiration_potential      : 'mm/day'

    ''')

    _prefix = 'soil'

    def __init__(self,palm=None):

        self._palm = palm

        self.available_water = self.initial_values['available_water']['value']

        # implemented for proto-typing purposes. See associated properties.
        self._raindays_ = 15
        self._rainfall_ = 120

    @property
    def raindays(self):
        ''' Number of "days with rain" (days/month). '''
        if self._weather is None:
            return self._raindays_
        else:
            return self._weather.raindays

    @property
    def evapotranspiration_potential(self):
        ''' The potential evapotransipiration (ET) rate (mm/day).

        A key assumption made in the IRHO method:
            ET = high if raindays <= 10 / month (a sunny/arid month)
            ET = low if raindays > 10 / month (a cloudy/humid month)
        '''

        raindays = self.raindays

        if raindays <=10:
            return self.parameters['high_ET']['value']
        else:
            return self.parameters['low_ET']['value']

        return res

@add_dumps
class PenmanSoil(SoilMixin):
    ''' '''

    parameters = yaml.load('''

    water_holding_capacity:
        value: 500.
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Input: soil/root characteristic.'

    high_ET:
        value: 5
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given <= 10 raindays per month - little rain == much sun == much ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    low_ET:
        value: 4
        unit: 'mm/day'
        info: 'The assumed typical ET_monthly in a palm plantation given > 10 raindays per month - much rain == little sun == little ET.'
        source: 'Based on Surre (1968) - IRHO: Les besoins en eau du palmier huile'
        error: 0

    relative_transpiration_rate_x0:
        value: 0.5
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'

    relative_transpiration_rate_b:
        value: 0.15
        unit: '1'
        info: 'Shapes the sigmoid (1/(1+exp(-(x-a)/b))) relation between actual to potential ET_monthly versus soil water content.'
        source: 'Based on the relation given in Combres et al. 2013 which refers to the PhD thesis by E. Dufrene (1989).'
    ''')

    initial_values = yaml.load('''

    available_water:
        value: 300
        error: 0
        unit: 'mm'
        info: 'Working definition: The difference between rooting zone water content at field capacity (pF 2) and permanent wilting point (pF 4.2).'
        source: 'Initial value - set by user.'

    ''')

    units = yaml.load('''

        available_water                   : 'mm'
        drainage                          : 'mm/day'
        conversion_efficiency_limiter     : '1'
        water_deficit                     : 'mm'
        water_contained                   : 'mm'
        raindays                          : 'days/month'
        rainfall                          : 'mm/day'
        critical_deficit_exceedance       : 'mm'
        critical_deficit                  : 'mm'
        ET_monthly_potential              : 'mm'
        moisture_content                  : '1'
        relative_transpiration_rate       : '1'
        water_holding_capacity            : 'mm'
        available_water_change_rate       : 'mm/day'
        evapotranspiration                : 'mm/day'
        evapotranspiration_potential      : 'mm/day'

    ''')

    _prefix = 'soil'

    @property
    def evapotranspiration_potential(self):
        """ . """
    
        parent = self._weather
    
        if parent is None:
            return 0
        else:
            return parent.ET_potential


Soil = PenmanSoil

