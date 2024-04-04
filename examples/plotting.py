import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import os

import datetime
from datetime import timedelta

def smoothen(s, rolling=True, window=3, fillna=True, min_periods=None, win_type='triang'):
    """ Apply a moving average with windowsize 'window', optionally filling any nans by lin. interpolation.
    
    Notes
    -----
    A 'triangular window-type' is favored over a plain square one since it
    more closely tracks the actual highs-and-lows while being less sensitive to incoming/outgoing
    transients.    
    """

    sm = s.astype('float').resample('M').mean()

    if min_periods is None:
        min_periods = window

    if rolling:
        sm = sm.rolling(window,center=True,min_periods=min_periods,win_type=win_type).mean()

    if fillna:
        sm = sm.interpolate(method='linear',limit=window,limit_direction='both')

    return sm

def gen_avg(s):
    """ Returns a 5 year (60 mo) moving average given a minimum of 3 years (36 mo) of data. """
    sm = smoothen(s,window=60, min_periods=36)

    return sm

def gen_avgs(ss):

    return [gen_avg(s) for s in ss]

def gen_rds(sm, so):
    """ Relative differences to the mean. """

    # model
    s1 = sm

    # observed
    s2 = so

    # indices of observed = shorter signal
    ix2s = s2.index

    # 5 year moving avg
    s1mm = smoothen(sm,window=60, min_periods=36)
    s2mm = smoothen(so,window=60, min_periods=36)
    
    # difference from mean -- anomaly
    s1a = s1 - s1mm
    s2a = s2 - s2mm

    # relative value in % eg signal = 120% of mean value
    s1ra = 100*s1a/s1mm
    s2ra = 100*s2a/s2mm

    s1a = s1a.loc[ix2s]
    s2a = s2a.loc[ix2s]

    s1ra = s1ra.loc[ix2s]
    s2ra = s2ra.loc[ix2s]

    return s1ra, s2ra

cm = 'black'
co = 'gray'

def mytotal(s):
    """ Yearly totals time-series.
    
    Assumes that the input is in (annual) rate units eg (kg/ha/year)
    s.t. the yearly mean is equivalent to the total.

    Places the evaluated total mid-year instead of end of the year
    s.t. the value is properly centered over the corresponding year.
    """
    return pd.Series({datetime.datetime(year=year, month=12, day=31):s.loc[s.index.year == year].mean()
        for year in s.index.year.unique()})

# derive the scatter points from the moving average @ Dec 31st.
HOW = 'maw'

def splot(smp, sm, so, ax, how=HOW):

    smpm, smmm, somm = gen_avgs([smp, sm, so])

    end = so.index[-1]

    smp.loc[:end].plot(ax=ax, label='potential', c=cm, ls='dotted')
    sm.loc[:end].plot(ax=ax, label='water-limited', c=cm)
    
    # evaluate the yearly total by considering the value of the 12-month moving average
    # in january
    if how == 'maw':
        so = so.loc[:end]
        rows = so.index.month == 12
        sox = so.loc[rows].index
        soy = so.loc[rows].values

        ax.scatter(sox, soy, label='observed', c=co)

    # evaluate the yearly total by taking the mean value over each year
    # eg mean yield of 2001 := mean( 2001-01, 2001-02, ..., 2001-12)
    # evaluated at 2001-12-31
    elif how == 'total':

        so = so.loc[:end]
        so = mytotal(so)
        sox = so.index
        soy = so.values

        ax.scatter(sox, soy, label='observed', c=co)

    # line
    else:
        so.loc[:end].plot(ax=ax, label='observed', c=co)
    
    intersection = smmm[sm > smmm].index[0]

    smmm.loc[intersection:end].plot(ax=ax, label='model - moving average', c=cm, ls='dashed')
    somm.loc[:end].plot(ax=ax, label='observed - moving average', c=co, ls='dashed')

    ax.set_xlabel(None)

def rplot(sm, so, ax, how=HOW):

    smr, sor = gen_rds(sm, so)

    smr += 100
    sor += 100

    smr.loc[:'2019'].plot(ax=ax, label='model', c=cm) 

    # evaluate the yearly total by considering the value of the 12-month moving average
    # in january
    if how == 'maw':

        #mid year ~= 2nd July
        rows = sor.index.month == 12
        sox = sor.loc[rows].index
        soy = sor.loc[rows].values

        ax.scatter(sox, soy, label='observed', c=co)

    # evaluate the yearly total by taking the mean value over each year
    # eg mean yield of 2001 := mean( 2001-01, 2001-02, ..., 2001-12)
    # evaluated at 2001-12-31
    elif how == 'total':

        _sor = mytotal(sor)
        sox = _sor.index
        soy = _sor.values

        ax.scatter(sox, soy, label='observed', c=co)

    # line
    else:
        sor.plot(ax=ax, label='observed', c=co)

    sdm = smr.std()
    sdo = sor.std()
    dsd = (smr - sor).std()

    fs = '$\sigma$ (%): $\Delta$Yw: {:2.0f}, $\Delta$Ya: {:2.0f}, $\Delta$Yw-$\Delta$Ya: {:2.0f}'

    ax.set_title(fs.format(sdm, sdo, dsd))

    ax.set_ylim(100-3*dsd,100+3*dsd)

    ax.axhline(0,color='black', ls='dotted')

    ax.fill_between(smr.index,smr+dsd,smr-dsd,color='grey',alpha=0.2)

    #ax.set_title('Anomaly - MAD (observed - model): {:3.0f}%'.format(sd))

    ax.set_ylabel('Anomaly (%)')
    ax.set_xlabel(None)

    return sdm, sdo, dsd

def make_overview(dfyw, dfyp, dfo, filepath='plot.png', window=3, title='placeholder'):

    fig, axes = plt.subplots(3,2,figsize=(12,8))

    info = {}
    info['title'] = title
    info['window'] = window

    ax = axes[0,0]

    smp = smoothen(dfyp['generative_FFB_production (t/ha/yr)'],window=window)
    sm = smoothen(dfyw['generative_FFB_production (t/ha/yr)'],window=window)
    so = smoothen(dfo['Y (kg/ha/yr)'],window=window)

    splot(smp, sm, so, ax)
    
    Yp = float(smp.loc[so.index].mean())
    Ym = float(sm.loc[so.index].mean())
    Yo = float(so.mean())
    rYw = 100*(Yo/Ym)

    info['Avg. Yp'] = round(0.001*Yp,1)
    info['Avg. Yw'] = round(0.001*Ym,1)
    info['Avg. Ya'] = round(0.001*Yo,1)
    info['Avg. Ya/Yw'] = round(rYw,0)
    
    N = len(so)
    xm = sm.index[int(N/10)]
    
    dt = timedelta(days=365)

    ax.hlines(Yp, xm, xm+dt, color=cm, linestyle='dotted')
    ax.hlines(Ym, xm, xm+dt, color=cm, linestyle='dashed')
    ax.hlines(Yo, xm, xm+dt, color=co, linestyle='dashed')
    
    rnd = lambda x: int(round(x, -2))

    # ax.annotate(rnd(Yp), xy=(xm,Yp), xytext=(xm+dt,60000),
    #                             arrowprops=dict(arrowstyle="->",
    #                              connectionstyle="arc3"))

    # ax.annotate(rnd(Ym), xy=(xm,Ym), xytext=(xm+dt,50000),
    #                             arrowprops=dict(arrowstyle="->",
    #                              connectionstyle="arc3"))

    # ax.annotate(rnd(Yo), xy=(xm,Yo), xytext=(xm+dt,10000),
    #                             arrowprops=dict(arrowstyle="->",
    #                              connectionstyle="arc3"))

    fs = 'Yp: {:3.1f}t, Yw: {:3.1f}t, Ya: {:3.1f}t, Ya/Yw: {:3.0f}%'

    ax.set_title(fs.format(0.001*Yp,
                            0.001*Ym,
                            0.001*Yo,
                            rYw))

    ax.set_ylabel('FFB (kg/ha/yr)') 
    ax.set_ylim(0,70000)   

    ax = axes[0,1]

    sdm, sdo, dsd= rplot(sm, so, ax)
    ax.set_ylabel('FFB anomaly (%)')

    info['SD FFB Yw'] = round(sdm,1)
    info['SD FFB Ya'] = round(sdo,1)
    info['SD FFB Yw-Ya'] = round(dsd,1)    
    
    ax = axes[1,0]

    smp = smoothen(dfyp['generative_bunch_weight (kg)'],window=window)
    sm = smoothen(dfyw['generative_bunch_weight (kg)'],window=window)
    so = smoothen(dfo['ABW (kg)'],window=window)

    splot(smp, sm, so, ax)

    ax.set_ylim(0,35)
    ax.set_ylabel('ABW (kg)')
    ax.set_xlabel(None)

    ax = axes[1,1]

    sdm, sdo, dsd = rplot(sm, so, ax)
    ax.set_ylabel('ABW anomaly (%)')

    info['SD ABW Yw'] = round(sdm,1)
    info['SD ABW Ya'] = round(sdo,1)
    info['SD ABW Yw-Ya'] = round(dsd,1) 

    ax = axes[2,0]

    smp = smoothen(dfyp['generative_bunch_count (1/ha/mo)'],window=window)
    sm = smoothen(dfyw['generative_bunch_count (1/ha/mo)'],window=window)
    so = smoothen(dfo['BC (1/ha/mo)'],window=window)

    splot(smp, sm, so, ax)

    ax.set_ylabel('BC (1/ha/mo)')
    ax.set_xlabel(None)
    ax.set_ylim(0,500)

    ax = axes[2,1]

    sdm, sdo, dsd = rplot(sm, so, ax)
    ax.set_ylabel('BC anomaly (%)')

    info['SD BC Yw'] = round(sdm,1)
    info['SD BC Ya'] = round(sdo,1)
    info['SD BC Yw-Ya'] = round(dsd,1) 

    plt.suptitle(title)

    plt.subplots_adjust(hspace=0.3)

    print('\tSaving at: {:}'.format(filepath))
    plt.savefig('{:}'.format(filepath), dpi=200)

    return ax, info

def make_yield_plot(dfyw, dfyp, dfo, filepath='plot.png', window=3, title='placeholder'):

    fig, axes = plt.subplots(2,1,figsize=(6,4))

    cm = 'black'
    co = 'gray'

    info = {}
    info['title'] = title
    info['window'] = window

    ax = axes[0]

    smp = smoothen(dfyp['generative_FFB_production (t/ha/yr)'],window=window)
    sm = smoothen(dfyw['generative_FFB_production (t/ha/yr)'],window=window)
    so = smoothen(dfo['Y (kg/ha/yr)'],window=window)

    splot(smp, sm, so, ax)
    
    Yp = float(smp.loc[so.index].mean())
    Ym = float(sm.loc[so.index].mean())
    Yo = float(so.mean())
    rYw = 100*(Yo/Ym)

    info['Avg. Yp'] = round(0.001*Yp,1)
    info['Avg. Yw'] = round(0.001*Ym,1)
    info['Avg. Ya'] = round(0.001*Yo,1)
    info['Avg. Ya/Yw'] = round(rYw,0)
    
    N = len(so)
    xm = sm.index[int(N/10)]
    
    dt = timedelta(days=365)

    ax.hlines(Yp, xm, xm+dt, color=cm, linestyle='dotted')
    ax.hlines(Ym, xm, xm+dt, color=cm, linestyle='dashed')
    ax.hlines(Yo, xm, xm+dt, color=co, linestyle='dashed')
    
    rnd = lambda x: int(round(x, -2))

    fs = 'Yp: {:3.1f}t, Yw: {:3.1f}t, Ya: {:3.1f}t, Ya/Yw: {:3.0f}%'

    ax.set_title(fs.format(0.001*Yp,
                            0.001*Ym,
                            0.001*Yo,
                            rYw))

    ax.set_ylabel('FFB (kg/ha/yr)') 
    ax.set_ylim(0,70000)   

    ax = axes[1]

    sdm, sdo, dsd= rplot(sm, so, ax)
    ax.set_ylabel('FFB anomaly (%)')

    info['SD FFB Yw'] = round(sdm,1)
    info['SD FFB Ya'] = round(sdo,1)
    info['SD FFB Yw-Ya'] = round(dsd,1)    

    plt.suptitle(title)

    plt.subplots_adjust(hspace=0.4)

    print('\tSaving at: {:}'.format(filepath))
    plt.savefig('{:}'.format(filepath), dpi=200)

    return ax, info

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

def tsplot(df,c,ax=None,window=12,figsize=(12,4),label=True):
    s = df[c]

    if ax is None:
        f,ax = plt.subplots(figsize=figsize)
    else:
        f = plt.gca()

    ax.plot(s,label='monthly mean')

    s_ = s.rolling(window).mean().shift(-int(0.5*window))
    ax.plot(s_,label='rolling mean (1 yr)'.format(window),color='black')
    ax.legend(fontsize=8)
    if label:
        ax.set_ylabel(c)

    return f,ax

def add_highlight(ax,x,alpha=0.5,color='orange',label=None):
    ''' Add a fill-between to a graph at location x. '''
    ymin,ymax = ax.get_ylim()
    ax.fill_between(x,ymin,ymax,alpha=alpha,label=label,color=color)
    return ax