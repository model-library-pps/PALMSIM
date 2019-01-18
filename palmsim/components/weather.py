#!/usr/bin/env python

""" Provides the interface to the weather data. """

import yaml
import numpy as np
import pandas as pd

from .helpers import add_dumps

from math import exp, sin, cos, sqrt, pi, acos, asin

PI = pi

SECONDS_PER_DAY = 24*60*60

def rad(deg):
    """ Convert from degrees to radials. """
    return 2*PI*(deg/360)

@add_dumps
class Weather(object):
    """ Weather related logic.

    The instance of this class (singleton) loads the input weather data into memory and
    calculates derived quantities.

    Time-series:
    - radiation_series
    - rainfall_series
    - raindays_series

    Associated looked-up values:
    - radiation (MJ/m2/day)
    - rainfall (mm/day)
    - rainday (1)

    Note, a PAR fraction* is used to translate visible radiation (input)
    to PAR intensity.

    *Although this is common practice for crop models
    there are reasons to believe that in reality the PAR fraction varies
    non-trivially in the 0.4--0.5 range [missing reference].
    """

    parameters = yaml.load("""
    PAR_fraction:
        value: 0.5
        unit: '1'
        info: 'The fraction of PAR in sunlight.'
        source: 'The 2004 book by Goudriaan and Van Laar, chapter 3.'

    solar_constant:
        value: 1367
        unit: 'J/m2/s'
        info: 'The incoming visible radiation,
                midday, above, the equator, at the edge of the atmosphere.
                Used to estimate the instantaneous radiation (J/m2/s)
                from the daily total radiation (MJ/m2/day).'
        source: 'The 2004 book by Goudriaan and Van Laar, chapter 3.'

    sigma:
        value: 5.668E-8
        unit: '?'
        info: 'Constant in the Stefan-Boltzmann equation.'
        source: '[0] - setpmd.for'

    psychrometer_coefficient:
        value: 0.067
        unit: 'kPa/degC'
        source: ''

    latent_heat_water:
        value: 2.454
        unit: 'MJ/kg'
        source: ''

    density_dry_air:
        value: 1.224
        unit: 'kg/m3'
        source: ''

    heat_capacity_dry_air:
        value: 1013
        unit: 'J/kg/degC'
        source: ''

    albedo:
        value: 0.14
        unit: '1'
        info: 'Albedo of a twelve year old oil palm'
        source: 'Meijide et al. 2017, Controls of water and energy fluxes
                 in oil palm plantations: environmental variables and oil palm age'

    """)

    units = {'PAR'                   : 'MJ/m2/day',
             'PAR_monthly'           : 'TJ/ha/mo',
             'radiation'             : 'MJ/m2/day',
             'radiation_monthly'     : 'TJ/ha/mo',
             'radiation_series_mean' : 'MJ/m2/day',
             'raindays'              : '1/mo',
             'raindays_series_mean'  : '1/mo',
             'rainfall'              : 'mm/day',
             'rainfall_series_mean'  : 'mm/day',}

    _prefix = 'weather'

    def __init__(self,palm = None):

        self._palm = palm

        self.radiation_series = None
        self.raindays_series  = None
        self.rainfall_series  = None

        # Mean values - used
        # at times if no time-series data is available.
        self._radiation_series_mean = None
        self._raindays_series_mean = None
        self._rainfall_series_mean = None

        # Mock-up values - only used in prototyping/testing
        self._radiation_series_mean_ = 20
        self._raindays_series_mean_ = 14
        self._rainfall_series_mean_ = 150
        self._latitude_ = 0
        self._DOY_ = 1

        self.update()
        
    def set_sine_solar_height(self):
        self.sine_solar_height_mean = self.calc_sine_solar_height_mean()
        self.sine_solar_height_amplitude = self.calc_sine_solar_height_amplitude()

    def _set_DOY(self):

        self._DOY = self._get_DOY()

    def update(self):

        self._set_DOY()
        self.set_sine_solar_height()
        
    @property
    def _date_tuple(self):
        if self._palm:
            return self._palm.date_tuple
        else:
            return None

    #~~~~~~~~~~~~~~~~~~~

    @property
    def PAR(self):
        """ Photo-synthetically active radiation (MJ/m2/day). """
        c = self.parameters['PAR_fraction']['value']
        return c*self.radiation

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation(self):
        """ Mean monthly visible radiation (MJ/m2/day). """
        t = self._date_tuple
        s = self.radiation_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.radiation_series_mean

    @radiation.setter
    def radiation(self, value):

        if isinstance(value, (int, float)):
            self._radiation_series_mean_ = value
        else:
            raise ValueError

    @property
    def rainfall(self):
        """Monthly rainfall (mm/mo). """
        t = self._date_tuple
        s = self.rainfall_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.rainfall_series_mean

    @property
    def raindays(self):
        """Monthly raindays (1). """
        t = self._date_tuple
        s = self.raindays_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.raindays_series_mean

    #~~~~~~~~~~~~~~~~~~~

    @property
    def rainfall_series(self):
        """Monthly rainfall (mm/mo) time-series.

        A dict with a (year,month)-tuple keys and float values.
        """
        return self._rainfall_series

    @property
    def radiation_series(self):
        """ Mean monthly visible radiation (MJ/m2/day) - time-series.

        A dict with a (year,month)-tuple keys and float values.
        """
        return self._radiation_series

    @property
    def raindays_series(self):
        """Monthly raindays (1) - time-series.

        A dict with a (year,month)-tuple keys and float values.
        """
        return self._raindays_series

    #~~~~~~~~~~~~~~~~~~~

    @rainfall_series.setter
    def rainfall_series(self,series):
        """ Sets the monthly rainfall time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 120

        Furthermore, sets the all-time mean rainfall -
        used by default in case of missing values.
        """

        if series is None:

            self._rainfall_series = None
            self._rainfall_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._rainfall_series = d
            self._rainfall_series_mean = float(series.mean())

        else:

            print(type(rseries))
            raise ValueError('Input a time-series.')

    @radiation_series.setter
    def radiation_series(self,series):
        """ Sets the monthly radiation time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean radiation -
        used by default in case of missing values.
        """

        if series is None:

            self._radiation_series = None
            self._radiation_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._radiation_series = d
            self._radiation_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @raindays_series.setter
    def raindays_series(self,series):
        """ Sets the monthly raindays time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean number of raindays -
        used by default in case of missing values.
        """

        if series is None:

            self._raindays_series = None
            self._raindays_series_mean = None

        elif isinstance(series, pd.Series):

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

            self._raindays_series = d
            self._raindays_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation_series_mean(self):
        """ The all-time mean of the mean-monthly radiation (MJ/m2/day). """
        if self._radiation_series_mean:
            return self._radiation_series_mean
        else:
            return self._radiation_series_mean_

    @property
    def rainfall_series_mean(self):
        """ The all-time mean of the monthly rainfall (mm/mo). """
        if self._rainfall_series_mean:
            return self._rainfall_series_mean
        else:
            return self._rainfall_series_mean_

    @property
    def raindays_series_mean(self):
        """ The all-time mean of the monthly raindays (1/mo). """
        if self._raindays_series_mean:
            return self._raindays_series_mean
        else:
            return self._raindays_series_mean_

    @property
    def temperature(self):
        """ Average daily temperature 2 m above earth surface (degC). """
    
        return 28

    @property
    def relative_humidity(self):
        """ (1) """
    
        return .86

    @property
    def windspeed(self):
        """ (m/s) """
    
        return 1

    #---------------------------

    def _get_DOY(self):
        """ . """
    
        parent = self._palm
    
        if parent is None:
            return self._DOY_
        else:
            return parent.DOY

    @property
    def _latitude(self):
        """ . """
    
        parent = self._palm
    
        if parent is None:
            return self._latitude_
        else:
            return parent.latitude

    @property
    def radiation_extraterrestrial_daily(self):
        """ The solar irridiance just outside the atmosphere (MJ/m2/day).
        
        See page 31 of the 2004 book by Goudriaan and Van Laar, equation 3.7.
        """

        d = self.daylength
        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        # reference solar irridiance
        S0 = self.parameters['solar_constant']['value']

        # daily integral of sine solar height
        int_sine_solar_height = a*d + (24*b/PI) * cos( (PI/2) * (d/12 -1) )
        
        # J -> MJ, hrs -> secs
        return 10**-6 * 3600 * S0 * int_sine_solar_height

    def calc_radiation_extraterrestrial(self, hour=12):
        """ The solar irridiance just outside the atmosphere (J/m2/s), at a given hour. 
        
        Based on the book by Goudriaan and Van Laar, 2004, on crop modelling p.29, c3.2.
        
        The output should be somewhere between 0--1367 J/m2/s.
        
        """

        def rad(deg):
            """ Convert from degrees to radials. """
            return 2*PI*(deg/360)

        # reference solar irridiance
        S0 = self.parameters['solar_constant']['value']

        sinb = self.calc_sine_solar_height(hour)

        day = self._DOY

        # the last factor takes into account the
        # earths eccentric trajectory around the sun :)
        S = S0 * sinb * (1 + 0.033*cos(2*PI*(day - 10/365)))

        assert S >= 0
        assert S <= S0

        return S

    def calc_PAR(self, hour=12):

        T = self.transmission_factor

        I0 = self.calc_radiation_extraterrestrial(hour=hour)

        c = self.parameters['PAR_fraction']['value']

        return c*T*I0

    def calc_sine_solar_height_mean(self):

        day = self._DOY
        gamma = self._latitude

        # tilt of the earth
        tilt = 23.45

        singamma = sin(rad(gamma))
        cosgamma = cos(rad(gamma))

        sindelta = -sin(rad(tilt))*cos(2*PI*(day+10)/365)
        cosdelta = sqrt(1-sindelta**2)

        # the mean sine of the solar height [-1,1] - given the day, latitude
        # the height at 6AM and 6PM.
        # for the Netherlands varies from -.31 (Dec 21st) to .31 (June 21st)
        a = singamma*sindelta

        assert a <= 1
        assert a >= -1

        return a

    def calc_sine_solar_height_amplitude(self):

        day = self._DOY
        gamma = self._latitude

        # tilt of the earth
        tilt = 23.45

        singamma = sin(rad(gamma))
        cosgamma = cos(rad(gamma))

        sindelta = -sin(rad(tilt))*cos(2*PI*(day+10)/365)
        cosdelta = sqrt(1-sindelta**2)

        # the amplitude - idem [0,1]
        # for the Netherlands varies very little, approx equal to .6.
        b = cosgamma*cosdelta

        assert b >= 0
        assert b <= 1

        return b

    @property
    def daylength(self):
        res =  self.hour_of_dusk - self.hour_of_dawn
        
        assert res >= 0
        
        return res

    @property
    def hour_of_dusk(self):

        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude 

        return 12*(2-acos(a/b)/PI)

    @property
    def hour_of_dawn(self):

        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude 

        return 12*(acos(a/b)/PI)

    def calc_sine_solar_height(self, hour=12):

        a = self.sine_solar_height_mean
        b = self.sine_solar_height_amplitude

        # the height of the sun
        sinb = a + b*cos(2*PI*(hour-12)/24)

        if sinb < 0:
            sinb = 0

        return sinb

    def calc_fraction_diffuse_lower_limit(self,hour=12):
        """ A lower limit on the fraction of diffuse light (1).
        
        Source: [0] - totasc.
        """


        sinb = self.calc_sine_solar_height(hour)

        if sinb > 0:
            return 0.15 + 0.85 * (1 - exp(-0.1/sinb))
        else:
            return 0

    def calc_fraction_diffuse(self, hour=12):
        """ The fraction of diffuse light at a certain hour (1). """
        return max(self.fraction_diffuse, self.calc_fraction_diffuse_lower_limit(hour=hour))

    @property
    def fraction_diffuse(self):
        """ The daily average fraction of diffuse light (1).
        
        Uses some emperical relation. Source: [0] - totasc.for
        """

        f = self.transmission_factor
        
        if f < 0.22:
            res =  1.
        elif f >= 0.22 and f < 0.35:
            res = 1.-6.4*(f-0.22)**2
        else:
            res = 1.47-1.66*f

        assert res <= 1
        assert res >= 0

        return res

    @property
    def transmission_factor(self):
        """ (1) """

        I = self.radiation
        Iext = self.radiation_extraterrestrial_daily

        return I/Iext

    @property
    def canopy_net_radiation_capture(self):
        """ The net radiation received by the canopy surface (J/m2/day). """

        albedo = self.parameters['albedo']['value']
        
        # short and longwave
        I_sun = self.radiation

        # longwave
        I_sky = self.radiation_longwave_sky_daily
        I_earth = self._radiation_longwave_earth_daily

        return (1-albedo)*I_sun + I_sky - I_earth

    @property
    def ET_potential(self):
        """ (mm/day).
        
        Calculated as prescribed by the FAO.
        """

        u = self.windspeed
        Rn = self.canopy_net_radiation_capture
        VPD = self.vapour_pressure_deficit
        T = self.temperature

        c_psy = self.parameters['psychrometer_coefficient']['value']
        slope = self.saturated_vapour_pressure_slope

        num = 0.408*slope*Rn + c_psy * (900/(T+273)) * u * VPD
        denum = (slope + c_psy*(1+0.32*u))

        ET = num/denum

        return ET

    @property
    def _radiation_longwave_earth(self):
        """ The (long-wave) radiation given off by the earth (J/m2/s). """

        T_avg = self.temperature

        sigma = self.parameters['sigma']['value']

        # 0 deg C -> Kelvin
        T0 = 273.16

        T = T_avg + T0

        # Stefan-Boltzmann
        I = sigma*T**4

        return I

    @property
    def _radiation_longwave_earth_daily(self):
        """ The (long-wave) radiation given off by the earth (MJ/m2/day). """

        I = self._radiation_longwave_earth

        # seconds per day
        SPD = SECONDS_PER_DAY

        return 10**-6 * SPD * I

    @property
    def _radiation_longwave_sky(self):
        """ The (long-wave) radiation given off by the sky (J/m2/s).
        
        Involves the use of an adapted Swinbank formula - see p. 7 of
        https://library.wur.nl/WebQuery/wurpubs/fulltext/4413
        
        """

        # note, should be in the range [0,a0]
        a = self.transmission_factor
        T_avg = self.temperature
        I_earth = self._radiation_longwave_earth

        # reference transmission factor -- clear skies
        a0 = 0.7

        # The estimated radiation given off by the sky in case
        # it was a perfect black-body radiator (balance)
        I_sky_BB = I_earth 

        # Swinbank constant - see the original paper by Swinbank, 1963.
        c = 5.31E-13

        # 0 deg C -> Kelvin
        T0 = 273.16
        T = T_avg + T0

        # Adapted Swinbank formula:
        # a linear combination via a of the clear-skies Swinbank estimate
        # and the black-body sky estimate

        radiation_longwave_sky = (a/a0) * c * T**6 + ((a0 - a)/a0) * I_sky_BB

        # a = 0 -> I_sky_BB
        # a = a0 -> Swinbank
        return radiation_longwave_sky

    @property
    def radiation_longwave_sky_daily(self):
        """ The (long-wave) radiation given off by the sky (MJ/m2/day). """

        I = self._radiation_longwave_sky

        # seconds per day
        SPD = SECONDS_PER_DAY

        return 10**-6 * SPD * I



    @property
    def vapour_pressure_early_morning(self):
        """ . """

        VPref = self.saturated_vapour_pressure
        rH = self.relative_humidity

        return rH*VPref

    @property
    def vapour_pressure_deficit(self):
        """ (kPA) """

        VPa = self.vapour_pressure_early_morning
        VPref = self.saturated_vapour_pressure

        return VPref - VPa

    @property
    def saturated_vapour_pressure(self):
        """ The satured vapour pressure (kPa).
        
         Is derived from the (daily average) temperature (deg C).

         Adopted from the Fortran SUBROUTINE SVPS1 v1.0 (1991),
         can be found in the CASE2 source-code.
        """

        # deg C
        T = self.temperature

        VPS = 0.1*6.10588*exp(17.32491*T/(T+238.102))
        
        return VPS

    @property
    def saturated_vapour_pressure_slope(self):
        """ The change of the satured vapour pressure with temperature (kPa/C).

         Is derived from the (daily average) temperature (deg C).

         Adopted from the Fortran SUBROUTINE SVPS1 v1.0 (1991),
         can be found in the CASE2 source-code.       
        """

        # deg C
        T = self.temperature
        VPS = self.saturated_vapour_pressure

        slope = 238.102*17.32491*VPS/(T+238.102)**2
        
        return slope