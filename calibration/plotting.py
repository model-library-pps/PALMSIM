import numpy as np

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import os

def smoothen(s, rolling=True, window=3, fillna=True, min_periods=None, win_type='triang'):

    sm = s.astype('float').resample('M').mean()

    if min_periods is None:
        min_periods = window

    if rolling:
        sm = sm.rolling(window,center=True,min_periods=min_periods,win_type=win_type).mean()

    if fillna:
        sm = sm.interpolate(method='linear',limit=window, limit_direction='both')

    return sm

def gen_avg(s):

    sm = smoothen(s,window=60, min_periods=36)

    return sm


def gen_avgs(ss):

    return [gen_avg(s) for s in ss]

def gen_rds(sm, so):
    """ Relative differences to the mean. """

    s1 = sm
    s2 = so

    ix0 = s1.index.get_loc(s2.index[0])
    ix1 = s1.index.get_loc(s2.index[-1])

    ix2s = s2.index

    nx = 1

    ix0e = ix0 - nx
    ix1e = ix1 + nx

    s1mm = smoothen(sm,window=60, min_periods=36)
    s2mm = smoothen(so,window=60, min_periods=36)
    
    t0 = s1.index[0]

    s1a = s1 - s1mm
    s2a = s2 - s2mm

    s1ra = 100*s1a/s1mm
    s2ra = 100*s2a/s2mm

    s1a = s1a.loc[ix2s]
    s2a = s2a.loc[ix2s]

    s1ra = s1ra.loc[ix2s]
    s2ra = s2ra.loc[ix2s]

    return s1ra, s2ra

def make_overview(dfyw, dfyp, dfo, sname='filename', fdir='plots', window=3, title='placeholder'):

    fig, axes = plt.subplots(3,2,figsize=(12,8))

    cm = 'black'
    co = 'gray'

    info = {}
    info['title'] = title
    info['window'] = window

    def splot(smp, sm, so, ax):

        smpm, smmm, somm = gen_avgs([smp, sm, so])

        end = so.index[-1]

        smp.loc[:end].plot(ax=ax, label='potential', c=cm, ls='dotted')
        sm.loc[:end].plot(ax=ax, label='water-limited', c=cm)
        so.loc[:end].plot(ax=ax, label='observed', c=co)
        
        smmm.loc[:end].plot(ax=ax, label='model - moving average', c=cm, ls='dashed')
        somm.loc[:end].plot(ax=ax, label='observed - moving average', c=co, ls='dashed')

        ax.set_xlabel(None)

    def rplot(sm, so, ax):

        smr, sor = gen_rds(sm, so)

        smr += 100
        sor += 100

        smr.loc[:'2019'].plot(ax=ax, label='model', c=cm) 
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

    ax = axes[0,0]

    smp = smoothen(dfyp['generative_FFB_production (t/ha/yr)'],window=window)
    sm = smoothen(dfyw['generative_FFB_production (t/ha/yr)'],window=window)
    so = smoothen(dfo['Y (kg/ha/yr)'],window=window)

    splot(smp, sm, so, ax)
    
    Yp = smp.loc[so.index].mean()
    Ym = sm.loc[so.index].mean()
    Yo = so.mean()
    rYw = 100*(Yo/Ym)

    info['Avg. Yp'] = round(0.001*Yp,1)
    info['Avg. Yw'] = round(0.001*Ym,1)
    info['Avg. Ya'] = round(0.001*Yo,1)
    info['Avg. Ya/Yw'] = round(rYw,0)
    
    N = len(so)
    xm = so.index[int(N/2)]
    xmp = so.index[int(3*N/4)]

    ax.scatter([xm], [Ym], c=cm)
    ax.scatter([xm], [Yo], c=co)

    rnd = lambda x: int(round(x, -2))

    ax.annotate(rnd(Yp), xy=(xm,Yp), xytext=(xmp,60000),
                                arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3"))

    ax.annotate(rnd(Ym), xy=(xm,Ym), xytext=(xmp,50000),
                                arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3"))

    ax.annotate(rnd(Yo), xy=(xm,Yo), xytext=(xmp,20000),
                                arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3"))

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

    fp = os.path.join(fdir,sname)

    print('\tSaving at: {:}.png'.format(fp))
    plt.savefig('{:}.png'.format(fp), dpi=300)

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