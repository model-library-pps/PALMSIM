import numpy as np

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import os

def smoothen(s, rolling=True, window=3):

    sm = s.astype('float').resample('M').mean()

    if rolling:
        sm = sm.rolling(window,center=True).mean()

    return sm

def make_overview(df, dfo, sname='filename', fdir='plots', window=3):

    plt.figure(figsize=(10,8))

    gs = GridSpec(3, 4)
    ax00 = plt.subplot(gs[0, :-1])
    ax01 = plt.subplot(gs[0, -1])

    ax10 = plt.subplot(gs[1,:-1])
    ax11 = plt.subplot(gs[1,-1])

    ax20 = plt.subplot(gs[2,:-1])
    ax21 = plt.subplot(gs[2,-1])

    cm = 'black'
    co = 'gray'

    ax = ax00

    sm = smoothen(df['generative_FFB_production (t/ha/yr)'],window=window)
    so = smoothen(12*1000*dfo['Y (t/ha/mo)'],window=window)

    sm.loc[:'2019'].plot(ax=ax, label='model', c=cm)
    so.plot(ax=ax, label='observed', c=co)

    ix = so.index

    ax.axhline(sm.mean(), c=cm, ls='dashed')
    ax.axhline(so.mean(), c=co, ls='dashed')

    ax.set_ylabel('FFB (kg/ha/yr)')
    ax.set_xlabel(None)

    ax = ax01

    # try:
    #     compare(sm, so, ax)
    # except:
    #     pass

    ax = ax10

    sm = smoothen(df['generative_bunch_weight (kg)'],window=window)
    so = smoothen(dfo['ABW (kg)'],window=window)

    sm.loc[:'2019'].plot(ax=ax, label='model', c=cm)
    so.plot(ax=ax, label='observed', c=co)
    ax.set_ylabel('ABW (kg)')
    ax.set_xlabel(None)

    ax = ax11

    # try:
    #     compare(sm, so, ax)
    # except:
    #     pass

    ax = ax20

    sm = smoothen(df['generative_bunch_count (1/ha/mo)'],window=window)
    so = smoothen(dfo['BC (1/ha/mo)'],window=window)

    sm.loc[:'2019'].plot(ax=ax, label='model', c=cm)
    so.plot(ax=ax, label='observed', c=co)
    ax.set_ylabel('BC (1/ha/mo)')
    ax.set_xlabel(None)

    ax = ax21

    # try:
    #     compare(sm, so, ax)
    # except:
    #     pass

    plt.tight_layout()

    fp = os.path.join(fdir,sname)

    print('Saving at: {:}.png'.format(fp))
    plt.savefig('{:}.png'.format(fp), dpi=300)

def compare(sm, so, ax=None):

    xs = sm.astype(float).resample('1M').mean().dropna()
    ys = so.astype(float).resample('1M').mean().dropna()

    index = ys.index

    ys = ys[index].values
    xs = xs[index].values

    from scipy.optimize import curve_fit

    f = lambda x, a, b: a*x + b

    coeffs, info = curve_fit(f, xs, ys)

    # SST = Sum(i=1..n) (y_i - y_bar)^2
    # SSReg = Sum(i=1..n) (y_ihat - y_bar)^2
    # Rsquared = SSReg/SST
    # Where I use 'y_bar' for the mean of the y's, and 'y_ihat' to be the fit value for each point.

    yfs = f(xs,*coeffs)
    y_bar = ys.mean()
    SST = ((ys - y_bar)**2).sum()
    SSReg = ((yfs - y_bar)**2).sum()
    Rsquared = SSReg/SST
    print('r**2: ', Rsquared)

    if ax is None:
        fig,ax = plt.subplots()

    ax.scatter(xs,ys, facecolors='none', edgecolors='black')

    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    maxtick = max([xlims[1],ylims[1]])
    mintick = min([xlims[0],ylims[0]])

    ax.set_xlim([mintick,maxtick])
    ax.set_ylim([mintick,maxtick])

    xsm = np.linspace(mintick,maxtick,100)

    ax.plot(xsm, xsm, c='black',ls='dashed')
    ax.plot(xsm, f(xsm, *coeffs), c='black', label='r2: {:3.3}'.format(Rsquared))

    ax.legend()

    ax.set_xlabel('observation')
    ax.set_ylabel('estimate')

    return ax