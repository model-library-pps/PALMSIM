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
import sys
from scipy import interpolate

import sys

DAYS_PER_MONTH = 30
METERS_PER_HECTARE = 100**2
GAUGE_PLANTING_DENSITY = 138

class Spline(object):
    ''' Piecewise by polynomial spline of order k.

    Parametrized via coordinates [(x0,y0), ..., (xn,yn)].

    Parameters
    ----------
    coords: length>k list of float-2-tuples, e.g. [(0,1),(5,5)]
        The (x,y) coordinates which parametrize the spline.
    k: float
        The order of the polynomials which make up the spline.

    Returns
    -------
    Given a value x, and a spline S, S.calc(x) returns an associated value y.

    Examples
    --------
    Let us define a piece-wise linear (k=1) function -- f: x->y --
    passing through (x,y) coordinates [(0,0),(10,20),(20,20),(30,0)]:

    >>> s = Spline([(0,0),(10,20),(20,20),(30,0)],k=1)
    >>> s
    order: 1
    coords: [(0, 0), (10, 20), (20, 20), (30, 0)]

    To get a x given y e.g. for x = 5:

    >>> y = s.calc(x=5)
    >>> y
    10
    '''

    def __init__(self,coords,k=3):
        ''' 


        '''

        self.coords = coords

        xs = np.array([coord[0] for coord in coords])
        ys = np.array([coord[1] for coord in coords])

        self.xs = xs
        self.ys = ys
        self.k = k
        self.tck = interpolate.splrep(self.xs, self.ys, k = self.k)

    def calc(self,x):
        return float(interpolate.splev(x, self.tck))

    def __repr__(self):
        return 'order: {:}\ncoords: {:}'.format(self.k,self.coords)

class Parameter(object):
    """ Descriptor: gives (dot named) access to self.parameters fields.

    Examples
    --------
    class Fish():
        ''' A fish class. '''
        parameters = {'color':'yellow'}
        color = Parameter('color')

    f = Fish()
    f.color
    >>> 'yellow'
    f.color = 'blue'
    f._parameters
    >>> {'color':'blue'}

    """

    def __init__(self,key):
        self.key = key

    def __get__( self, instance, klass):
        return instance.parameters[self.key]['value']

    def __set__( self, instance, value ):
        instance.parameters[self.key]['value'] = value

def hygienic(decorator):
    ''' Decorator decorator, providies hygiene; preservation of basic attributes.'''
    def new_decorator(obj):
        decorated_obj = decorator(obj)
        decorated_obj.__name__ = obj.__name__
        decorated_obj.__doc__ = obj.__doc__
        decorated_obj.__module__ = obj.__module__
        return decorated_obj
    return new_decorator

@hygienic
def add_dumps(klass):
    ''' Class decorator providing data dump methods (incl. a __repr__). '''

    _attribute_sort_order = ['mass','assim','maint']

    @property
    def _instance_variables(self):
        return [attr for attr in dir(self) if not attr.startswith('_')]

    def to_dict(self):
        ''' Returns a dict of all float-like instance variables.'''

        attributes = self._instance_variables

        units = self.units

        d = {}

        for key in attributes:

            try:
                value = getattr(self,key)
            except:
                print(sys.exc_info[0])
                pass

            if isinstance(value,(float,int)):
                if key in units:
                    unit = units[key]
                    d['{:} ({:})'.format(key,unit)] = value
                else:
                    d[key] = value
            else:
                pass

        return d

    def to_prefixed_dict(self):

        prefix = self._prefix

        dictionary = self.to_dict()

        new_dictionary = {}

        for key,value in dictionary.items():

            if prefix == '':
                new_key = key
            else:
                new_key = prefix + '_' + key

            new_dictionary[new_key] = value

        return new_dictionary

    def print_parameters(self,default=False):
        if default:
            parameters = self.default_parameters
        else:
            parameters = self.parameters
        print(yaml.dump(parameters,default_flow_style=False))

    @property
    def units(self):
        return self.variable_units

    def __repr__(self):

        lines = ['Object: {:}'.format(self._name)]
        lines += ['Version: {:}'.format(self._version)]
        lines += ['']
        lines += ['{:<30.30} {:<9} {:<12}'.format('Property','Value','Unit')]
        lines += [52*'-']

        attributes = self.to_dict()

        for key,value in attributes.items():

            if ' (' in key:
                var,unit = key.split(' (')
                unit = unit[:-1] 
            else:
                var = key
                unit = '?'

            if isinstance(value,(int,float)):
                lines += ['{:<30.30} {:<9.4f} {:<12}'.format(var,value,unit)]
            else:
                pass

        return '\n'.join(lines)

    decorations =  [('_instance_variables',_instance_variables),
                    ('_attribute_sort_order',_attribute_sort_order),
                    ('print_parameters',print_parameters),
                    ('to_prefixed_dict',to_prefixed_dict),
                    ('to_dict',to_dict),
                    ('units',units),]

    decorations_to_add = {k:v for (k,v) in decorations if k not in dir(klass)}
    decorations_to_add['__repr__'] = __repr__

    return type(klass.__name__,
               (klass,),
               decorations_to_add)

def read_yaml(data):
    ''' Reads in a yaml data file either a path or the actual yaml-text.'''
    if isinstance(data,str):

        if data.endswith('.yaml'):
            with open(data,'r') as f:
                _data = yaml.load(f)

        else:
            _data = yaml.load(data)

    else:
        raise ValueError

    return _data

def recursive_dict_printer(d,indent=0):
    '''Prints a nested dict recursively'''
    space = indent*' '
    frmstr = space+'{:}:'
    for k,v in d.items():
        if isinstance(v,dict):
            print(frmstr.format(k))
            recursive_dict_printer(v,indent=indent+4)
        else:
            if isinstance(v,str):
                print(frmstr.format(k),'\'{:}\''.format(v))
            else:
                print(frmstr.format(k),'{:}'.format(v))

import numpy as np