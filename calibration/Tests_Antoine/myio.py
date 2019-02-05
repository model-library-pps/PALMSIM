
import numpy as np
import pandas as pd
import os

def read_in_weather_data(fp):
    """ Reads in our weather data. 
    
    Tries to correct for any in-correct values.
    I.e. negative values for precipitation.
    """
    
    # "fix" the header of our weather file
    nfpath = harmonize_weather_file(fp)
    
    # read in the data
    dfw = pd.read_csv(nfpath, sep='\t', skiprows=2)
    dfw = dfw.drop([0],axis=0)
    dfw = dfw.astype('float')
    
    # set a datetime-like index
    dfw.index = compose_date(dfw['Year'], days=dfw['DOY'])
    dfw = dfw.sort_index()
    dfw = dfw.drop(['Year','DOY'], axis=1)

    # try and correct in-correct values
    bad = dfw['Precip'] < 0
    dfw.loc[bad, 'Precip'] = 0
    
    return dfw

def harmonize_weather_file(fpath):
    """ Corrects the header in our tsv-like files. 
    
    Swaps the spaces in lines 2 and 3 to tabs.
    Why? S.t. we can read in the files as a plain tsv.
    """

    with open(fpath, 'r') as f:
        text = f.read()
    
    lines = text.splitlines()
    
    lines[2] = lines[2].replace(' ','\t')
    lines[3] = lines[3].replace(' ','\t')
    
    fname, ext = os.path.splitext(fpath)
    
    nfname = fname + '-e'
    
    nfpath = nfname + ext
    
    text = '\n'.join(lines)
    
    with open(nfpath, 'w') as f:
        f.write(text)
    
    return nfpath

def compose_date(years, months=1, days=1, weeks=None, hours=None, minutes=None,
                 seconds=None, milliseconds=None, microseconds=None, nanoseconds=None):
    """ Makes a datetime-like series by joining associated series of years, months, etc. """
    
    years = np.asarray(years) - 1970
    months = np.asarray(months) - 1
    days = np.asarray(days) - 1
    types = ('<M8[Y]', '<m8[M]', '<m8[D]', '<m8[W]', '<m8[h]',
             '<m8[m]', '<m8[s]', '<m8[ms]', '<m8[us]', '<m8[ns]')
    vals = (years, months, days, weeks, hours, minutes, seconds,
            milliseconds, microseconds, nanoseconds)
    return sum(np.asarray(v, dtype=t) for t, v in zip(types, vals)
               if v is not None)