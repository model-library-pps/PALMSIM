#!/usr/bin/env python

''' Contains the inflorescence modelling. '''

import yaml
import sys

from copy import deepcopy

from .helpers import add_dumps

from .constants import DEFAULT_PLANTING_DENSITY
from .constants import DAYS_PER_MONTH

from scipy import interpolate

import pandas as pd
import random
import numpy as np

##################
# Helper functions
##################
def mean(ls):
    ''' The mean of a list of floats.

    E.g. mean([1,0,0,1]) -> 0.5.

    '''
    N = len(ls)
    if N == 0:
        # empty list...
        return 0
    else:
        s = sum(ls)
        return ls/N

def make_quadratic_function(x1,x2,A):
    ''' Returns a strictly positive quadratic function.

    We use the fact that "the area below a parabola" is 2/3*height*base.

    Parameters
    ----------
    x1: left x s.t. y = 0
    x2: right x s.t. y = 0
    A: area under parabola

    Returns
    -------
    A quadratic function x -> y.

    '''

    # base width
    W = x2 - x1

    # max height
    h = 1.5*A/W

    # scaling s.t. y = h at x = hw
    hw = .5*(x2-x1)

    def func(x):
        if x <= x1:
            return 0
        elif x >= x2:
            return 0
        else:
            return max(0,-h*(x-x1)*(x-x2)/(hw)**2)

    return func

def make_linear_function(x1,y1,x2,y2):
    ''' Returns a "line" f(x) through (x1,y1) and (x2,y2). '''
    c = (y2-y1)/(x2-x1)
    def f(x):
        return c*(x-x1) + y1
    return f

