#!/usr/bin/env python

'''
Provides the Weather class which fetches each months weather data
for associated time-series.
'''

import yaml
import numpy as np
import pandas as pd

from .helpers import add_dumps
from .constants import DAYS_PER_MONTH

@add_dumps
class Weather(object):
    ''' Weather related logic.

    The instance of this class (singleton design pattern)
    fetches each months weather (variable values)
    out of weather-data-time-series.

    Time-series slots:
    - radiation_series
    - rainfall_series
    - raindays_series

    Associated looked-up values:
    - radiation (GJ/m2/mo)
    - rainfall (mm/mo)
    - raindays (1/mo)

    Note, a PAR fraction* is used to translate visible radiation (input)
    to PAR intensity.

    *Although this is common practice for crop models
    there are reasons to believe that in reality the PAR fraction varies
    non-trivially in the 0.4--0.5 range [no ref atm].
    '''

    parameters = yaml.load('''
    PAR_fraction:
        value: 0.5
        unit: '1'
        info: 'The fraction of PAR in sunlight.'
        source: 'Legacy version - ad hoc.'
    ''')

    units = {'PAR': 'MJ/m**2/day',
            'PAR_monthly': 'TJ/ha/mo',
            'radiation': 'MJ/m**2/day',
            'radiation_monthly': 'TJ/ha/mo',
            'radiation_series_mean': 'MJ/m**2/day',
            'raindays': '1/mo',
            'raindays_series_mean': '1/mo',
            'rainfall': 'mm/mo',
            'rainfall_series_mean': 'mm/mo',}

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

        # Mock-up values - only used
        # if no time-series are supplied.
        self._radiation_series_mean_ = 12
        self._raindays_series_mean_ = 14
        self._rainfall_series_mean_ = 150

    @property
    def _date_tuple(self):
        if self._palm:
            return self._palm.date_tuple
        else:
            return None

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation_monthly(self):
        ''' Visible radiation (TJ/ha/mo). '''

        # I_m [TJ/ha/mo] : I_d [MJ/m**2/day] =
        # 10^-6 [TJ/MJ] * 10^4 [m**2/ha] * 30 [days/mo] = ~0.3

        return 0.01*DAYS_PER_MONTH*self.radiation

    @property
    def PAR(self):
        ''' Photo-synthetically active radiation (MJ/m**2/day). '''
        c = self.parameters['PAR_fraction']['value']
        return c*self.radiation

    @property
    def PAR_monthly(self):
        ''' Photo-synthetically active radiation (TJ/ha/mo). '''
        c = self.parameters['PAR_fraction']['value']
        return c*self.radiation_monthly

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation(self):
        ''' Mean monthly visible radiation (MJ/m**2/day). '''
        t = self._date_tuple
        s = self.radiation_series
        if t and s:
            return s[t]
        else:
            return self.radiation_series_mean

    @property
    def rainfall(self):
        '''Monthly rainfall (mm/mo). '''
        t = self._date_tuple
        s = self.rainfall_series
        if t and s:
            return s[t]
        else:
            return self.rainfall_series_mean

    @property
    def raindays(self):
        '''Monthly raindays (1). '''
        t = self._date_tuple
        s = self.raindays_series
        if t and s:
            return s[t]
        else:
            return self.raindays_series_mean

    #~~~~~~~~~~~~~~~~~~~

    @property
    def rainfall_series(self):
        '''Monthly rainfall (mm/mo) time-series.

        A dict with a (year,month)-tuple keys and float values.
        '''
        return self._rainfall_series

    @property
    def radiation_series(self):
        ''' Mean monthly visible radiation (MJ/m**2/day) - time-series.

        A dict with a (year,month)-tuple keys and float values.
        '''
        return self._radiation_series

    @property
    def raindays_series(self):
        '''Monthly raindays (1) - time-series.

        A dict with a (year,month)-tuple keys and float values.
        '''
        return self._raindays_series

    #~~~~~~~~~~~~~~~~~~~

    @rainfall_series.setter
    def rainfall_series(self,series):
        ''' Sets the monthly rainfall time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 120

        Furthermore, sets the all-time mean rainfall -
        used by default in case of missing values.
        '''

        if series is None:

            self._rainfall_series = None
            self._rainfall_series_mean = None

        elif isinstance(series, pd.Series):

            d = {(k.year,k.month):v for k,v in series.iteritems()}

            self._rainfall_series = d
            self._rainfall_series_mean = float(series.mean())

        else:

            print(type(rseries))
            raise ValueError('Input a time-series.')

    @radiation_series.setter
    def radiation_series(self,series):
        ''' Sets the monthly radiation time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean radiation -
        used by default in case of missing values.
        '''

        if series is None:

            self._radiation_series = None
            self._radiation_series_mean = None

        elif isinstance(series, pd.Series):

            d = {(k.year,k.month):v for k,v in series.iteritems()}

            self._radiation_series = d
            self._radiation_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    @raindays_series.setter
    def raindays_series(self,series):
        ''' Sets the monthly raindays time-series variable.

        Expects a date-time indexed time-series e.g.
        2007-01-01 00:00:00 - 12

        Furthermore, sets the all-time mean number of raindays -
        used by default in case of missing values.
        '''

        if series is None:

            self._raindays_series = None
            self._raindays_series_mean = None

        elif isinstance(series, pd.Series):

            d = {(k.year,k.month):v for k,v in series.iteritems()}

            self._raindays_series = d
            self._raindays_series_mean = float(series.mean())

        else:

            print(type(series))
            raise ValueError('Input a time-series.')

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation_series_mean(self):
        ''' The all-time mean of the mean-monthly radiation (MJ/m2/day). '''
        if self._radiation_series_mean:
            return self._radiation_series_mean
        else:
            return self._radiation_series_mean_

    @property
    def rainfall_series_mean(self):
        ''' The all-time mean of the monthly rainfall (mm/mo). '''
        if self._rainfall_series_mean:
            return self._rainfall_series_mean
        else:
            return self._rainfall_series_mean_

    @property
    def raindays_series_mean(self):
        ''' The all-time mean of the monthly raindays (1/mo). '''
        if self._raindays_series_mean:
            return self._raindays_series_mean
        else:
            return self._raindays_series_mean_

