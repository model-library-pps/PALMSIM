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

def gen_avgs(sm, so):

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

    return s1mm, s2mm

def gen_rds(sm, so):

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

def make_overview(df, dfo, sname='filename', fdir='plots', window=3):

    fig, axes = plt.subplots(3,2,figsize=(12,8))

    cm = 'black'
    co = 'gray'

    ax = axes[0,0]

    sm = smoothen(df['generative_FFB_production (t/ha/yr)'],window=window)
    so = smoothen(12*1000*dfo['Y (t/ha/mo)'],window=window)

    def splot(sm, so, ax):

        smmm, somm = gen_avgs(sm, so)

        sm.loc[:'2019'].plot(ax=ax, label='model', c=cm)
        smmm.loc[:'2019'].plot(ax=ax, label='model', c=cm, ls='dashed')
        
        so.plot(ax=ax, label='observed', c=co)
        somm.plot(ax=ax, label='observed', c=co, ls='dashed')

        ax.set_xlabel(None)

    def rplot(sm, so, ax):

        smr, sor = gen_rds(sm, so)

        smr.loc[:'2019'].plot(ax=ax, label='model', c=cm) 
        sor.plot(ax=ax, label='observed', c=co)

        mae = (smr - sor).abs().mean()

        ax.set_ylim(-3*mae,3*mae)

        ax.axhline(0,color='black', ls='dotted')

        ax.fill_between(smr.index,smr+mae,smr-mae,color='grey',alpha=0.5)

        ax.set_title('MAE: {:3.0f}%'.format(mae))

        ax.set_ylabel('anomaly (%)')
        ax.set_xlabel(None)

    splot(sm, so, ax)

    Ym = sm.loc[so.index].mean()
    Yo = so.mean()
    rYw = 100*(1 - Yo/Ym)
    
    N = len(so)
    xm = so.index[int(N/2)]
    xmp = so.index[int(3*N/4)]

    ax.scatter([xm], [Ym], c=cm)
    ax.scatter([xm], [Yo], c=co)

    rnd = lambda x: int(round(x, -3))

    ax.annotate(rnd(Ym), xy=(xm,Ym), xytext=(xmp,1.2*Ym),
                                arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3"))

    ax.annotate(rnd(Yo), xy=(xm,Yo), xytext=(xmp,.6*Yo),
                                arrowprops=dict(arrowstyle="->",
                                 connectionstyle="arc3"))


    ax.set_title('Yw: {:3.0f}%'.format(rYw))

    ax.set_ylabel('FFB (kg/ha/yr)')    

    ax = axes[0,1]

    rplot(sm, so, ax)

    ax = axes[1,0]

    sm = smoothen(df['generative_bunch_weight (kg)'],window=window)
    so = smoothen(dfo['ABW (kg)'],window=window)

    splot(sm, so, ax)

    ax.set_ylabel('ABW (kg)')
    ax.set_xlabel(None)

    ax = axes[1,1]

    rplot(sm, so, ax)

    # try:
    #     compare(sm, so, ax)
    # except:
    #     pass

    ax = axes[2,0]

    sm = smoothen(df['generative_bunch_count (1/ha/mo)'],window=window)
    so = smoothen(dfo['BC (1/ha/mo)'],window=window)

    splot(sm, so, ax)

    ax.set_ylabel('BC (1/ha/mo)')
    ax.set_xlabel(None)

    ax = axes[2,1]

    rplot(sm, so, ax)

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