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

def get_modulo_index(t,anarray):
    ''' Returns t modulo length of the array.

    Example
    -------

    >>> anarray = [1,1,2,3]
    >>> t = 6
    >>> get_modulo_index(t,anarray)
    2

    since len(anarray) = 4 s.t. 6 % 4 -> 2.

    '''
    return int(t%len(anarray))

@add_dumps
class Weather(object):
    ''' Weather related variables.

    The purpose of this object is to fetch weather data
    out of weather data time-series.

    The weather data time-series
        - radiation_series
        - rainfall_series
        - raindays_series
    are object variables with respective by month variables
        - radiation_visible (MJ/m2/day)
        - rainfall (mm/month)
        - raindays (1)

    Furthermore uses a PAR fraction to translate visible radiation intensity
    to PAR intensity and converts to some different units e.g.
        - radiation_visible_per_month (GJ/m2/month)

    Notes
    -----
    The photo-synthetically active radiation is here said to be
    simply a fraction (0.5) of the incident solar radiation.
    Although this is common practice (practically all crop models do so)
    there are reasons to believe that in reality the PAR fraction varies
    somewhat in the 0.4--0.5 range. In case one knows of a good review
    of this topic feel free to contact the author.

    '''

    default_parameters = yaml.load('''
    PAR_fraction:
        value: 0.5
        unit: '1'
        info: 'fraction of PAR in plain sunlight.'
        source: 'Common belief.'
        std_dev: 0.02
    radiation_series:
        value: [15., 15., 15.,
                15., 15., 15.,
                15., 15., 15.,
                15., 15., 15.]
        std_dev: 3
        unit: 'MJ/m**2/day'
        info: 'The visible incident radiation. '
        source: 'Proto-typical values --- made up.'
    rainfall_series:
        value: [120.,120.,120.,
                120.,120.,120.,
                120.,120.,120.,
                120.,120.,120.,]
        std_dev: 100
        unit: 'mm/month'
        info: 'The rainfall over the course of a month.'
        source: 'Proto-typical values --- made up.'
    raindays_series:
        value: [15.,15.,15.,
                15.,15.,15.,
                15.,15.,15.,
                15.,15.,15.,]
        std_dev: 3
        unit: 'days/month'
        info: 'The number of days with rain in a month. Important to the IRHO soil model, see the soil module.'
        source: 'Proto-typical values --- made up.'
    ''')

    variable_units = dict(radiation_visible           = 'MJ/m**2/day',
                          radiation_PAR               = 'MJ/m**2/day',
                          radiation_visible_per_month = 'GJ/m**2/month',
                          radiation_PAR_per_month     = 'GJ/m**2/month',
                          raindays                    = '1/month',
                          rainfall                    = 'mm/month',
                          PAR_fraction                = '1',
                          )

    _name = 'weather'
    _prefix = _name
    _style = 'Basic'
    _version = '1.0.0.1'

    def __init__(self,palm = None):

        self._palm = palm

        self.parameters = deepcopy(self.default_parameters)

        self.radiation_series = np.array(self.parameters['radiation_series']['value'], float)
        self.raindays_series  = np.array(self.parameters['raindays_series']['value'], float)
        self.rainfall_series  = np.array(self.parameters['rainfall_series']['value'], float)

    _PAR_fraction = Parameter('PAR_fraction')

    @property
    def PAR_fraction(self):
        return self._PAR_fraction

    @property
    def _MAP(self):
        ''' Months after planting (month). '''
        if self._palm is None:
            return 0
        else:
            return int(self._palm.MAP)

    @property
    def radiation_visible(self):
        ''' The incident visible radiation (MJ/m**2/day). '''
        month = get_modulo_index(self._MAP,self.radiation_series)
        return float(self.radiation_series[month])

    @property
    def rainfall(self):
        '''The monthly rainfall (mm). '''
        month = get_modulo_index(self._MAP,self.rainfall_series)
        return float(self.rainfall_series[month])

    @property
    def raindays(self):
        '''The number of days with rain in a month (days/month).

        Important to the IRHO soil model, see the soil module.
        '''

        month = get_modulo_index(self._MAP,self.raindays_series)
        return float(self.raindays_series[month])

    @property
    def radiation_visible_per_month(self):
        ''' Visible insolation (GJ/m**2/month). '''

        return 0.001*self.radiation_visible*DAYS_PER_MONTH

    @property
    def radiation_PAR(self):
        ''' The photo-synthetically active radiation (MJ/m**2/day). '''

        return self.PAR_fraction*self.radiation_visible

    @property
    def radiation_PAR_per_month(self):
        ''' The photo-synthetically active radiation (GJ/m**2/month). '''

        return self.PAR_fraction*self.radiation_visible_per_month

LatestWeather = Weather