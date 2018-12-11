#!/usr/bin/env python

''' Contains the helper functions/classes. '''

import yaml
import sys

import traceback

import numpy as np

from scipy import interpolate

import sys

def sigmoid(x,x0,k):
    """ A sigmoid f(x).

    Properties:

        f(x0) = 0
        f'(x0) = k
        f(-inf) = 0
        f(+inf) = 1

    """
    return 1/(1+np.exp(-k*(x-x0)))

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
    ''' Add data dump functionality to a class.

    Most importantly adds the "to_dict" method which
    when called on an object puts the objects state/rate variables
    in a dictionary.

    '''

    @property
    def _variables(self):
        return [attr for attr in dir(self) if not attr.startswith('_')]

    def to_dict(self, prefixed = False):
        ''' Returns a dict of all float-like instance variables.'''

        attributes = self._variables
        units = self.units

        d = {}

        for key in attributes:

            try:
                value = getattr(self, key)
            except Exception as e:
                print(traceback.format_exc())

            if isinstance(value,(float,int)):
                if key in units:
                    unit = units[key]
                    d['{:} ({:})'.format(key,unit)] = value
                else:
                    d['{:} ({:})'.format(key,'?')] = value
            else:
                pass

        if prefixed:

            prefix = self._prefix

            d = {'{:}_{:}'.format(prefix,k):v for k,v in d.items()}

        return d

    def print_parameters(self,default=False):
        if default:
            parameters = self.default_parameters
        else:
            parameters = self.parameters
        print(yaml.dump(parameters,default_flow_style=False))

    def __repr__(self):

        lines = ['Object: {:}'.format(self.__class__.__name__)]
        lines += ['']
        lines += ['{:<40.40} {:>9} {:<12}'.format('Property','Value','Unit')]
        lines += [62*'-']

        attributes = self.to_dict()

        for key,value in attributes.items():

            if ' (' in key:
                var,unit = key.split(' (')
                unit = unit[:-1]
            else:
                var = key
                unit = '?'

            if isinstance(value,(int,float)):
                lines += ['{:<40.40} {:>9.3f}  {:<12}'.format(var,value,unit)]
            else:
                pass

        return '\n'.join(lines)


    decorations =  [('_variables',_variables),
                    ('print_parameters',print_parameters),
                    ('to_dict',to_dict)]

    decorations_to_add = {k:v for (k,v) in decorations if k not in dir(klass)}
    decorations_to_add['__repr__'] = __repr__

    return type(klass.__name__,
               (klass,),
               decorations_to_add)


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