#!/usr/bin/env python

''' Provides the interface to the weather data. '''

import yaml
import numpy as np
import pandas as pd

from .helpers import add_dumps
from .constants import DAYS_PER_MONTH

@add_dumps
class Weather(object):
    ''' Weather related logic.

    The instance of this class (singleton) loads the input weather data into memory and makes it easily accessible to the rest of the model.

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
    '''

    parameters = yaml.load('''
    PAR_fraction:
        value: 0.5
        unit: '1'
        info: 'The fraction of PAR in sunlight.'
        source: 'Legacy version - ad hoc.'
    ''')

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

        # Mock-up values - only used
        # if no time-series are supplied.
        self._radiation_series_mean_ = 20
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
    def PAR(self):
        ''' Photo-synthetically active radiation (MJ/m2/day). '''
        c = self.parameters['PAR_fraction']['value']
        return c*self.radiation

    #~~~~~~~~~~~~~~~~~~~

    @property
    def radiation(self):
        ''' Mean monthly visible radiation (MJ/m2/day). '''
        t = self._date_tuple
        s = self.radiation_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.radiation_series_mean

    @radiation.setter
    def radiation(self, value):

        if isinstance(value, float):
            self._radiation_series_mean_ = value
        else:
            raise ValueError

    @property
    def rainfall(self):
        '''Monthly rainfall (mm/mo). '''
        t = self._date_tuple
        s = self.rainfall_series
        if (t and s) and (t in s):
            return s[t]
        else:
            return self.rainfall_series_mean

    @property
    def raindays(self):
        '''Monthly raindays (1). '''
        t = self._date_tuple
        s = self.raindays_series
        if (t and s) and (t in s):
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
        ''' Mean monthly visible radiation (MJ/m2/day) - time-series.

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

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

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

            # to speed up fetching the data, we make a dictionary having the time as keys
            d = {(t.year,t.month,t.day): float(v) for t,v in series.iteritems()}

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

