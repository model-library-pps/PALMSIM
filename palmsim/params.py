


from .components.fronds import Fronds
from .components.trunk  import Trunk
from .components.roots  import Roots
from .components.generative        import Organs
from .components.assimilates       import Assimilates
from .components.management        import Management
from .components.soil              import Soil
from .components.weather           import Weather
from .components.generative        import Indeterminate,Male,Female
from .components.generative        import Stalk,MesocarpFibers,MesocarpOil,Kernel

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

def get_parameters_config():
    ''' Get the default parameters of the model. '''
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

    return config_text

def save_parameters_config(filename='settings.yaml'):
    ''' Makes the settings file (settings.yaml) based on the defaults. '''

    config_text = get_default_parameters()

    filepath = os.path.join(MODULE_DIR,filename)

    with open(filepath,'w') as f:
        f.write(yaml.dump(config_text,default_flow_style=False))

    return config_text

def get_default_parameters():
    ''' Gets the parameters of all sub-models.

    Returns
    -------
    A nested-dictionary of parameters per sub-model.
    '''
    config_dict = {}

    for kls in CLASSES:
        config_dict[kls._name] = kls.default_parameters

    return config_dict

def set_parameters(settings = None):
    ''' Sets the parameters of all sub-models.

    Input
    -----
    settings: dict
        A nested-dictionary of parameters per sub-model.

    '''
    if settings is None:
        return False
    else:
        print('Setting settings...')
        for kls in CLASSES:

            params = settings[kls._name]

            kls.default_parameters = params

SETTINGS_FILENAME = 'settings.yaml'

def load_parameters(SETTINGS_FILENAME):

    SETTINGS = None

    print('Trying to load settings from file...')

    if SETTINGS_FILENAME in os.listdir(MODULE_DIR):

        filepath = os.path.join(MODULE_DIR,SETTINGS_FILENAME)

        with open(filepath,'r') as f:
            SETTINGS_TEXT = f.read()
            SETTINGS = yaml.load(SETTINGS_TEXT)

        set_parameters(SETTINGS)

#load_parameters(SETTINGS_FILENAME)