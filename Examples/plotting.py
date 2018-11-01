import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

global sys
global pd
global np
global plt
global my_plot

plt.rc('font', size=18)
plt.rc('legend', fontsize=14)

import matplotlib
matplotlib.style.use('seaborn-colorblind')

def tsplot(df,c,ax=None,window=12,figsize=(12,4)):
    s = df[c]

    if ax is None:
        f,ax = plt.subplots(figsize=figsize)
    else:
        f = plt.gca()

    ax.plot(s,label='monthly mean')

    s_ = s.rolling(window).mean().shift(-int(0.5*window))
    ax.plot(s_,label='rolling mean (1 yr)'.format(window),color='black')
    ax.legend(fontsize=8)
    ax.set_ylabel(c)

    return f,ax

def add_highlight(ax,x,opacity=0.5,color='orange',label=None):
    ''' Add a fill-between to a graph at location x. '''
    ymin,ymax = ax.get_ylim()
    ax.fill_between(x,ymin,ymax,alpha=opacity,label=label,color=color)
    return ax