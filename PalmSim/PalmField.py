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
__credits__ = ["M. Slingerland","W. Hekman", "G. van de Ven", "M. Hoffman", "A. Castaneda-Vera", "L. Woittiez", "T. Rhebergen"]
__license__ = "Copyleft,see http://models.pps.wur.nl/content/licence_agreement"
__version__ = "1.0.0.1"
__maintainer__ = "Willem Hekman"
__email__ = "willem.hekman@wur.nl"
__status__ = "Development"

##################
# Import Libraries
##################

import yaml
import os
import sys

from copy import deepcopy

import numpy as np
import pandas as pd

from components.helpers import add_dumps
from components.helpers import METERS_PER_HECTARE
from components.helpers import DAYS_PER_MONTH
from components.helpers import GAUGE_PLANTING_DENSITY

from components.fronds import Fronds
from components.trunk  import Trunk
from components.roots  import Roots
from components.generative        import Organs
from components.assimilates       import Assimilates
from components.management        import Management
from components.soil              import Soil
from components.weather           import Weather
from components.generative        import Indeterminate,Male,Female
from components.generative        import Stalk,MesocarpFibers,MesocarpOil,Kernel

MODULE_FILEPATH = sys.modules[__name__].__file__
MODULE_DIR = os.path.dirname(MODULE_FILEPATH)

CLASSES = [Fronds,
            Trunk,
            Roots,
            Organs,
            Assimilates,
            Management,
            Soil,
            Weather,
            Indeterminate,
            Male,
            Female,
            Stalk,
            MesocarpFibers,
            MesocarpOil,
            Kernel]

def make_parameter_file(filename='settings.yaml'):
    ''' Makes the settings file (settings.yaml) based on the defaults. '''

    config_dict = {}

    for kls in CLASSES:
        config_dict[kls._name] = kls.default_parameters

    preamble = 'INFO\n\n'

    preamble += 'Number of parameters per sub-model'
    preamble += '\n------------------------------'

    for kls in config_dict:
        params = config_dict[kls]
        preamble += '\n{:<20} {:}'.format(kls,len(params))

    dump = yaml.dump(config_dict,default_flow_style=False)

    preamble = '\n'.join(['# ' + x for x in preamble.splitlines()])

    config_text = preamble + '\n\n# Parameters per sub-model:\n\n' + dump

    filepath = os.path.join(MODULE_DIR,filename)

    with open(filepath,'w') as f:
        f.write(config_text)

def set_parameters(settings = None):
    ''' Sets the parameters of all sub-models. '''
    if settings is None:
        return False
    else:

        for kls in CLASSES:

            params = settings[kls._name]

            kls.default_parameters = params

SETTINGS_FILENAME = 'settings.yaml'

def load_parameters(SETTINGS_FILENAME):

    SETTINGS = None

    if SETTINGS_FILENAME in os.listdir(MODULE_DIR):

        filepath = os.path.join(MODULE_DIR,SETTINGS_FILENAME)

        with open(filepath,'r') as f:
            SETTINGS_TEXT = f.read()
            SETTINGS = yaml.load(SETTINGS_TEXT)

        set_parameters(SETTINGS)

load_parameters(SETTINGS_FILENAME)

class PalmField():
    ''' The main PalmSim class, models a field of oil palms.

    Here a field of palms is modelled by the underlying
    components (sub-models):

            - fronds
            - trunks
            - roots
            - assimilates
            - fruits

            - weather
            - soil
            - management

    The model of the palm field follows from
    these sub-models.

    Given a palm field "pf"

        pf = PalmField()

    we have e.g. access to the fronds sub-model via

        pf.fronds

    For a list of all instance variables

        pf.instance_variables

    See the "getting started" below.

    Notes
    -----
    All the interesting stuff --- the actual model implementation ---
    can be found in the sub-models; this class is a so-called
    "container class":

    This role of this class is to link and manage the sub-models.
    Note, we at any time have access to the sub-models.
    For means of development we can even run the sub-models
    by themselves, standalone.

    In our opinion this is a good design of the implementation.

    Getting Started
    ---------------

    Given a palm field "pf"

        pf = PalmField()

    we have e.g. access to the fronds sub-model via

        pf.fronds

    the weather sub-model via

        pf.weather

    For a list of all the components that can be accessed
    in such a way simply access

        pf.components

    Running the command

        pf

    by itself displays a neat list of all the model
    variables. Similarly for a component e.g.

        pf.fronds

    For a list of all instance variables

        pf.instance_variables

    To update the palm field one time-step (one month)

        pf.update()

    optionally we can update by a fractional amount
    using the dt key-word argument.

        pf.update(dt=0.5)

    To retrieve all the exposed component variables

        pf.to_dict()

    To instantiate a palm field at a certain year and time
    e.g. the 1st of January 2017

        pf = PalmField(year_of_planting = 2017, month_of_planting = 0)

    note we can aswell interchange the order of arguments since
    we are using key-word arguments and we count the months zero-based

        pf = PalmField(month_of_planting = 0, year_of_planting = 2017)

    '''

    variable_units = dict(age              = 'month',
                        dt                   = 'month',
                        harvest              = 'tonne_DM/ha/month',
                        harvest_yearly       = 'tonne_DM/ha/year',
                        mass_fronds          = 'tonne_DM/ha',
                        mass_roots           = 'tonne_DM/ha',
                        mass_trunk           = 'tonne_DM/ha',
                        month                = 'month',
                        planting_density     = '1/ha',
                        assim_synth_total    = 'ton_CH2O/ha/month',
                        trunk_mass_per_palm  = 'kg_DM/palm',
                        roots_mass_per_palm  = 'kg_DM/palm',
                        fronds_mass_per_palm = 'kg_DM/palm',
                        mass_generative      = 'tonne_DM/ha',
                        mass_vegetative      = 'tonne_DM/ha',
                        yield_DM             = 'tonne_DM/ha/month',
                        )

    _name = 'palm'
    _prefix = ''
    _version = '1.0.0.1'

    default_parameters = {}

    def __init__(self,
                    version = 'modern',
                    verbose = True,
                    settings = None,
                    year_of_planting = 2017,
                    month_of_planting = 0,
                    dt = 1):

        # for convenience sake time is kept in the palm
        self.MAP = 0
        self._month = 0

        self._year_of_planting = year_of_planting
        self._month_of_planting = month_of_planting
        self._dt = dt

        self.parameters = deepcopy(self.default_parameters)

        # Bind the drivers
        self.weather    = Weather(self)
        self.soil       = Soil(self)
        self.management = Management(self)

        # Bind the parts/components
        self.fronds      = Fronds(self)
        self.roots       = Roots(self)
        self.trunk       = Trunk(self)
        self.organs      = Organs(self)
        self.assimilates  = Assimilates(self)

        self.components = [self.fronds,
                            self.roots,
                            self.trunk,
                            self.organs,
                            self.assimilates,
                            self.weather,
                            self.soil,
                            self.management,
                            ]

        # one of the few non-trivial instance variables
        self.planting_density = self.management.planting_density

        self.units = self.get_units()

    @property
    def month(self):
        ''' The current month. '''
        return self._month%12

    @property
    def year(self):
        ''' The current year. '''
        return self._year_of_planting+int(self._month//12)

    @property
    def date(self):
        ''' The date (yyyy-mm-dd). '''
        return '{:}-{:}-1'.format(self.year,self.month+1)

    #########################
    # Mass: alternative units
    #########################

    @property
    def mass_total(self):
        ''' The mass of all the palms together (t DM/ha). '''
        return self.mass_vegetative + self.mass_generative

    @property
    def mass_vegetative(self):
        ''' The mass of all the vegetative parts together (t DM/ha). '''
        return self.fronds.mass + self.trunk.mass + self.roots.mass

    @property
    def yield_DM(self):
        ''' The dry-matter bunch yield (t DM/ha/month). '''
        return self.organs.bunch_production

    @property
    def mass_generative(self):
        ''' The mass of all the generative organs (t DM/ha). '''
        return self.organs.mass

    @property
    def trunk_mass_per_palm(self):
        ''' The mean mass of the palm trunks (kg). '''
        return 1000*self.trunk.mass/self.planting_density

    @property
    def roots_mass_per_palm(self):
        ''' The mean mass of the palm roots (kg). '''
        return 1000*self.roots.mass/self.planting_density

    @property
    def fronds_mass_per_palm(self):
        ''' The mean mass of the palm fronds (kg). '''
        return 1000*self.fronds.mass/self.planting_density

    def update(self,N_months = None, dt=1):
        ''' update N_months (30 day) months '''

        if N_months is None:
            N_steps = 1
        else:
            N_steps  = int(N_months/dt)

        for step in range(N_steps):
            self._update(dt=dt)

        return self

    def _update(self,dt):
        '''Update a dt * 30 day month'''

        self.MAP += dt
        self._month += dt

        self.soil.update(dt=dt)
        self.assimilates.update()

        self.management.update()
        self.fronds.update(dt=dt)
        self.trunk.update(dt=dt)
        self.roots.update(dt=dt)

        self.organs.update(dt=dt)

    def run(self,duration=360,dt=1):

        if (1%dt) != 0:
            raise ValueError

        N_steps = duration / dt
        if N_steps%1 != 0:
            raise ValueError

        N_steps = int(N_steps)

        res = {}

        units = self.units

        for step in range(N_steps):

            self._update(dt=dt)
            values = self.to_dict()
            res[self.MAP] = values

        df = pd.DataFrame(res).T

        df.index = pd.to_datetime(df['date'])

        df = df.apply(pd.to_numeric, errors='ignore')

        df.columns = [my_replace(s) for s in df.columns]

        df['yield FM yearly (tonne FM/year)'] = df['organs yield FM yearly (tonne FM/year)']
        return df

    ########
    # output
    ########

    @property
    def instance_variables(self):
        ''' The list of instance variables. '''
        return [attr for attr in dir(self) if not attr.startswith('_')]

    def _to_dict(self):
        ''' Returns a dictionary of direct float-like instance variables. '''

        attributes = self.instance_variables

        units = self.units

        d = {}

        for key in attributes:

            try:
                value = getattr(self,key)
            except:
                print(sys.exc_info[0])
                pass

            if isinstance(value,(float,int,str)):
                d[key] = value

            elif isinstance(value,np.ndarray):
                pass

            else:
                pass

        return d

    def to_prefixed_dict(self, hide_attr=True):
        ''' Output the variable values to a dictionary.

        Here the keys have prefixes to distinguish between
        the different sub-models. E.g.

           trunk_mass
        fronds_mass

        '''

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

    def to_dict(self,hide_attr = True):
        ''' Output the variable values to a dictionary. '''

        d = self._to_dict()

        for component in self.components:

            d.update(component.to_prefixed_dict())

        return d

    def get_units(self):
        ''' Get the associated units. '''

        res = {**self.variable_units}

        for component in self.components:

            for original_key in component.units:

                if component._prefix == '':
                    key = original_key
                else:
                    key = component._prefix +'_'+ original_key

                res[key] = component.units[original_key]

        return res

def my_replace(s):
    ''' Replace some sub-strings in a string.

        '_' -> ' '
        'tonne_DM' -> 't'

        >>> my_replace('alfa_beta')
        'alfa beta'
    '''
    s = s.replace('tonne_CH2O','t')
    s = s.replace('tonne_DM','t')
    s = s.replace('_',' ')
    return s