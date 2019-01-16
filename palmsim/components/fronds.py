#!/usr/bin/env python

''' Contains the frond modelling class. '''

import yaml

from .helpers import add_dumps

from .constants import METERS_PER_HECTARE
from .constants import DAYS_PER_MONTH
from .constants import DEFAULT_PLANTING_DENSITY

import numpy as np

from math import sqrt, exp

@add_dumps
class Fronds(object):
    ''' Models fronds.

    Palm age determines leaf area per frond and frond
    initiation rate.

    Frond count and leaf area per frond determine leaf area index.

    Leaf area index and incoming radiation determine the
    production of assimilates.

    Mass is updated according to
        - mass growth: assimilation
        - mass loss: pruning

    Mass furthermore determines the maintenance requirement.

    References
    ----------
    Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.

    '''

    parameters = yaml.load('''

    specific_maintenance_rachis:
        value: 0.002
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance of the rachis.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                Photosynthese et productivite du palmier a huile en liaison
                avec les facteurs climatiques.
                Tableau II. After Gray, 1969.'
        uncertainty: 5%

    specific_maintenance_leaflets:
        value: 0.0083
        unit: 'g_CH2O/g_DM/day'
        info: 'The specific maintenance of the leaflets.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    Tableau II. Mesures realiseses a La Me.'
        uncertainty: 5%

    conversion_efficiency:
        value: 0.69
        unit: 'g_DM/g_CH2O'
        info: 'The conversion efficiency of the fronds.'
        source: 'Copied from Dufrene, E. and Ochs, R. and Saugier, B., 1990.
                    Photosynthese et productivite du palmier a huile en liaison
                    avec les facteurs climatiques.
                    In turn based on van Kraalingen, D.W.G., 1989.
                    See text below table II and table III.'
        uncertainty: 5%

    fraction_rachis:
        value: 0.75
        unit: '1'
        info: 'Mass of the rachis/frond mass
                not clear if frond mass includes/excludes petiole.'
        source: '?'
        uncertainty: 5%

    fraction_leaflets:
        value: 0.25
        unit: '1'
        info: 'Mass of the leaflets/frond mass
                not clear if frond mass includes/excludes petiole.'
        source: '?'
        uncertainty: 5%

    specific_leaf_area:
        value: 3.1
        unit: 'm**2/kg_DM'
        info: 'The specific leaf area. Not used, only for checking.'
        source: 'Presumably derived by dividing reported leaf area/
                    leaf mass found in the paper by Corley, R.H.V.
                    and Gray, B.S. and Ng, S.K., 1971:
                    Productivity of the oil palm in Malaysia.'
        uncertainty: 10%

    LUE:
        value: 3.8
        unit: 'g_CH2O/MJ'
        info: 'The light use efficiency.'
        source: 'Based on a more detailed hourly light-response
                    model (copied from SUCROS) using oil palm LR measurements by Breure, Gerritsma.'
        uncertainty: 10%

    k:
        value: 0.33
        unit: '1'
        info: 'The canopy light extinction coefficient.'
        source: 'Based on the thesis by Gerritsma, W., 1988.'
        uncertainty: 5%

    leaf_area_a:
        value: 12.13
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    leaf_area_b:
        value: 2.47
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    leaf_area_c:
        value: 0.36
        unit: 'm**2'
        info: 'Parametrizes leaf area (Gompertz curve: a*exp(-b*exp(-c*t)))as a function of years after planting.'
        source: 'Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of
                    oil palm in indonesia.
                    Table 1, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_a:
        value: 25
        unit: '1/palm/year'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Calibration, initially based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_b:
        value: 1.6
        unit: '1'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Calibration, initially based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_c:
        value: 0.3
        unit: '1/year'
        info: 'Parametrizes the frond initiation rate (exponential decay with age: a*(1+b*exp(-c*(t)) )as a function of years after planting.'
        source: 'Calibration, initially based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    initiation_rate_max:
        value: 50
        unit: '1/year'
        info: 'The upper limit on the frond initiation rate.'
        source: 'Roughly based on Gerritsma, W. and Soebagyo, F.X., 1998.
                    An analysis of the growth of leaf area of oil palm in indonesia.
                    Table 3, experiment 1, 143 palms/ha density.'
        uncertainty: 5%

    potential_growth_rate:
        value: 4
        unit: 'kg_DM/palm/month'
        info: 'The potential growth rate'
        source: 'Based on Corley et al., 1971.'
        uncertainty: 5%

    asymptotic_photosynthesis_rate:
        value: 600
        unit: 'ug_CO2/m2/s'
        info: 'Co-determines the light response (g CH2O/m2/s) curve, the maximum value.'
        source: 'Gerritsma, W., 1988. 
                Light interception, leaf photosynthesis
                and sink-source relations in Oil Palm'

    initial_light_efficiency:
        value: 9
        unit: 'ug_CO2/J'
        info: 'Co-determines the light response (g CH2O/MJ) curve, the slope.'
        source: 'Gerritsma, W., 1988. 
                Light interception, leaf photosynthesis
                and sink-source relations in Oil Palm'

    ''')

    initial_values = yaml.load('''
    mass:
        value: 30
        uncertainty: 0
        unit: 'kg_DM/plant'
        info: 'Frond mass at 0 MAP.'
        source: 'Based on Corley, 1971.'
    count:
        value: 30
        uncertainty: 0
        unit: 'count/plant'
        info: 'Frond count at 0 MAP.'
        source: 'Based on Woittiez, L. et al. 2017, and Advances in Oil Palm Research Volume 1, 2000. p. 27.'
    ''')

    units = yaml.load('''

        assim_growth                   : 'kg_CH2O/ha/day'
        assim_produced                 : 'kg_CH2O/ha/day'
        count                          : '1/ha'
        count_per_palm                 : '1/palm'
        fraction_intercepted           : '1'
        intercepted_solar_energy       : 'GJ/ha/day'
        total_leaf_area                : 'm2/ha'
        leaf_area_index                : '1'
        maintenance_requirement        : 'kg_CH2O/ha/day'
        mass                           : 'kg_DM/ha'
        mass_change_rate               : 'kg_DM/ha/day'
        mass_change_rate_yearly        : 'kg_DM/ha/year'
        mass_change_rate_per_palm      : 'kg_DM/palm/year'
        mass_growth_rate               : 'kg_DM/ha/day'
        mass_loss_rate                 : 'kg_DM/ha/day'
        mean_leaf_area                 : 'm2/frond'
        plastochron                    : 'day'
        leaf_area_per_palm             : 'm2'
        initiation_rate                : '1/palm/day'
        intercepted_PAR                : 'GJ/ha/day'
        specific_leaf_area             : 'cm2/g_DM'
        prune_rate                     : 'kg_DM/ha/day'
        mass_per_palm                  : 'kg/palm'
        mass_per_frond                 : 'kg/frond'
        count_change_rate              : '1/ha/day'
        count_growth_rate              : '1/ha/day'
        count_loss_rate                : '1/ha/day'
        LUE                            : 'g_CH2O/MJ PAR'
        potential_growth_rate          : 'kg_DM/ha/day'
        potential_growth_rate_per_palm : 'kg_DM/palm/year'
        potential_sink_strength        : 'kg_CH2O/ha/day'
        prune_rate                     : '1/ha/day'
        prune_rate_mass                : 'kg_DM/ha/day'
        prune_rate_rachis_mass         : 'kg_DM/ha/day'
        prune_rate_leaflets_mass       : 'kg_DM/ha/day'

    ''')

    _prefix = 'fronds'

    def __init__(self,palm=None):

        self._palm = palm

        # convert from kg/plant -> t/ha
        mass_per_palm = self.initial_values['mass']['value']
        self.mass  = self._planting_density*mass_per_palm

        # convert from 1/plant -> 1/ha
        count_per_palm = self.initial_values['count']['value']
        self.count = self._planting_density*count_per_palm

        # for testing only
        self._PAR_ = 500
        self._assim_growth_ = 0

    #~~~~~~~~~~~~~~~~

    @property
    def _planting_density(self):
        ''' The planting density (1/ha). '''
        if self._palm is None:
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.management.planting_density

    @property
    def _MAP(self):
        ''' Months after planting; Palm age (month). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    @property
    def _DAP(self):
        ''' Days after planting; Palm age (days). '''
        if self._palm is None:
            return 0
        else:
            return self._palm.DAP

    @property
    def _PAR(self):
        ''' Radiation (PAR) (MJ/m2/day). '''

        if self._palm is None:
            return self._PAR_
        else:
            return self._palm.weather.PAR

    @property
    def _relative_transpiration_rate(self):
        ''' Evapotranspiration (mm/month).

        Note, we consider the evaporation (soil)
        to be negligible (closed canopy).'''

        if self._palm is None:
            return 1
        else:
            return self._palm.soil.relative_transpiration_rate

    @property
    def prune_rate_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        if self._palm is None:
            return 0
        else:
            # prune me!
            return self._palm.management.prune_rate_mass

    @property
    def prune_rate_rachis_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        c = self.parameters['fraction_rachis']['value']

        return c*self.prune_rate_mass

    @property
    def prune_rate_leaflets_mass(self):
        ''' Prune rate (kg_DM/ha/day). '''

        c = self.parameters['fraction_leaflets']['value']

        return c*self.prune_rate_mass

    #~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        ''' Update state by dt days.'''
        self._update(dt=dt)

    def _update(self,dt=1):
        ''' Update state by dt days. '''
        self._update_mass(dt=dt)
        self._update_count(dt=dt)

    def _update_mass(self,dt=1):
        ''' Update the mass (t_DM/ha) by dt days. '''

        self.mass += self.mass_change_rate*dt

        assert self.mass >= 0

    def _update_count(self,dt=1):
        ''' Update the count (1/ha) by dt days. '''
        self.count += self.count_change_rate*dt

        assert self.count >= 0

    #~~~~~~~~~~~~~~~~

    @property
    def mass_change_rate(self):
        ''' Mass change rate (kg_DM/ha/day). '''
        return self.mass_growth_rate - self.mass_loss_rate

    @property
    def mass_growth_rate(self):
        ''' Mass growth rate (kg_DM/ha/day). '''

        c = self.parameters['conversion_efficiency']['value']

        return c*self.assim_growth

    @property
    def mass_loss_rate(self):
        ''' Mass loss rate (kg_DM/ha/day).

        Due to pruning. See also the management sub-model's
        prune variables.
        '''
        return self.prune_rate_mass

    @property
    def mass_change_rate_yearly(self):
        ''' Mass change rate (kg_DM/ha/year). '''

        return 365*self.mass_change_rate

    @property
    def potential_growth_realization(self):
        ''' Actual growth : potential growth (1). '''

        return self.mass_growth_rate/self.potential_growth_rate

    #~~~~~~~~~~~~~~~~

    @property
    def count_change_rate(self):
        ''' Fround count change rate (1/ha/day).

        The difference between growth and loss.
        See associated growth and loss rate properties.
        '''
        return self.count_growth_rate - self.count_loss_rate

    @property
    def count_growth_rate(self):
        ''' Fround count growth rate (1/ha/day). '''
        return self.initiation_rate*self._planting_density

    @property
    def initiation_rate(self):

        ''' The frond initiation_rate/count growth rate (1/palm/day).

        Uses a fit to field observations; a Gompertz function

        R = (1/365)*a*(1+b*exp(-c*(t/12))

        R the frond initiation_rate rate (1/palm/month)
        t year after planting
        a the asymptotic rate (1/palm/year)
        b the initial relative offset from the asymptote (1)
        c the typical time scale (year)

        Is based on:

            Gerritsma, W. and Soebagyo, F.X., 1998.
            An analysis of the growth of leaf area of oil palm in indonesia.
            Table 3, experiment 1, 143 palms/ha density.

        '''

        a = self.parameters['initiation_rate_a']['value']
        b = self.parameters['initiation_rate_b']['value']
        c = self.parameters['initiation_rate_c']['value']

        cap = self.parameters['initiation_rate_max']['value']

        # YAP
        t = self._DAP/365

        # (1/year/palm)
        yearly_naive = a*(1+b*np.exp(-c*(t)))

        yearly = min(cap,yearly_naive)

        # (1/day/palm)
        daily = yearly/365

        return float(daily)

    @property
    def count_loss_rate(self):
        ''' Fround count loss rate (1/ha/day).

        Determined strictly by the pruning regime.
        '''
        return self.prune_rate

    @property
    def prune_rate(self):
        ''' Frond prune rate (1/ha/day).

        Determined strictly by the pruning regime.
        '''
        if self._palm is None:
            return 0
        else:
            return self._palm.management.prune_rate

    @property
    def plastochron(self):
        ''' Days between consecutive frond initiation (days). '''
        return 1/self.initiation_rate

    @property
    def count_per_palm(self):
        return self.count/self._planting_density

    #~~~~~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        ''' Maintenance requirement equals that for rachis plus leaflets. '''
        return self._maintenance_rachis + self._maintenance_leaflets

    @property
    def _maintenance_rachis(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance_rachis']['value']

        return c * self._mass_rachis

    @property
    def _maintenance_leaflets(self):
        ''' Maintenance requirement (kg_CH2O/ha/day). '''

        c = self.parameters['specific_maintenance_leaflets']['value']

        return c * self._mass_leaflets

    #~~~~~~~~~~~~~~~~

    @property
    def potential_sink_strength(self):
        ''' Potential sink strength (kg_CH2O/ha/day)'''

        c = self.parameters['conversion_efficiency']['value']

        return self.potential_growth_rate/c

    @property
    def potential_growth_rate_per_palm(self):
        ''' Potential growth rate (kg_DM/palm/year). '''

        monthly_rate = self.parameters['potential_growth_rate']['value']

        yearly_rate = 12 * monthly_rate

        return yearly_rate

    @property
    def potential_growth_rate(self):
        ''' Potential growth rate (kg_DM/ha/day) '''

        yearly_rate = self.potential_growth_rate_per_palm

        c = (1/365)

        return c * yearly_rate * self._planting_density

    @property
    def assim_growth(self):
        ''' Assimilates for growth (kg_CH2O/ha/day). '''

        if self._palm is None:
            return self._assim_growth_
        else:
            return self._palm.assimilates.assim_growth_fronds

    #~~~~~~~~~~~~~~~~

    @property
    def leaf_area_index(self):
        ''' The LAI (total leaf area/ total ground area). '''

        # 0.0001 ha/m2

        return 0.0001*self.total_leaf_area

    @property
    def total_leaf_area(self):
        ''' The total leaf area (m2). '''
        return self.mean_leaf_area*self.count

    @property
    def mean_leaf_area(self):
        ''' Leaf area per leaf.

        Based on the following paper:

        Gerritsma, W. and Soebagyo, F.X., 1998.
        An analysis of the growth of leaf area of oil palm in indonesia.

        See Fig. 1 and Table 1.
        '''

        # YAP
        t = self._DAP/365

        a = self.parameters['leaf_area_a']['value'] # 12 +- 1
        b = self.parameters['leaf_area_b']['value'] # 2.47 +- 0.1
        c = self.parameters['leaf_area_c']['value'] # 0.36 +- 0.04

        return a*np.exp(-b*np.exp(-c*(t)))

    @property
    def leaf_area_per_palm(self):
        ''' Calculates the leaf area per palm (m2/palm). '''
        return self.total_leaf_area/self._planting_density

    @property
    def specific_leaf_area(self):
        ''' Specific leaf area (m2 leaf/kg leaf). '''

        c = self.parameters['fraction_leaflets']['value']

        leaflet_mass_per_frond = c*self.mass_per_frond

        return self.mean_leaf_area/leaflet_mass_per_frond

    #~~~~~~~~~~~~

    @property
    def assim_produced2(self):
        ''' Assimilates produced (kg_CH2O/day/ha). '''

        # g_CH2O/MJ -> kg_CH2O/GJ
        LUE = self.LUE

        # (GJ/ha/day)
        intercepted_PAR = self.intercepted_PAR

        rT = self._relative_transpiration_rate

        return rT * LUE * intercepted_PAR

    @property
    def assim_produced(self):
        ''' Assimilates produced (kg_CH2O/day/ha). '''

        rT = self._relative_transpiration_rate

        return rT*self.total_gross_assimilation

    @property
    def LUE(self):
        ''' The light-use efficiency (g_CH2O/MJ). '''
        return self.parameters['LUE']['value']

    @property
    def LUE2(self):
        ''' The light-use efficiency (g_CH2O/MJ). '''

        # the factor 0.1 comes from conversion:
        # Unit GA: kg/ha/day -> 1000 g/ha/day
        # Unit PAR MJ/m2/day -> 10000 MJ/ha/day
        # -> GA/PAR in g/MJ = 1000/10000 * GA [kg/ha/day]/PAR[MJ/m2/day]

        return 0.1*self.total_gross_assimilation/self._PAR

    @property
    def total_gross_assimilation(self):
        """ (kg_CH2O/ha/day) """

        return self.calc_total_gross_assimilation()

    def calc_light_response(self,I):    
        """
        Calculates a photosynthesis rate (ug_CH2O/m2/s).

        Parameters
        ----------
        I: float, light (PAR) intensity (J/m2/s)
        Fm: float, asymptotic photosynthesis rate (ug_CO2/m2/s)
        Eff: float, initial light efficiency (ug_CO2/J)

        Returns
        -------
        photosynthesis rate (ug_CH2O/m2/s)

        References
        ----------
            Goudriaan, J. and van Laar, H.H, 1994.
            Modelling Potential Crop Growth Processes
            Textbook with exercises

        """

        Fm = self.parameters['asymptotic_photosynthesis_rate']['value']
        Eff = self.parameters['initial_light_efficiency']['value']
        
        # molecular mass ratio
        c = 30/44 # CH2O : CO2
        
        return c * Fm * (1 - exp(-Eff*I/Fm))

    def _calc_fraction_diffuse(self, hour=12):

        parent = self._palm

        if parent is None:
            return self._fraction_diffuse_
        else:
            return parent.weather.calc_fraction_diffuse(hour=12)

    def _calc_sine_solar_height(self, hour):

        parent = self._palm

        if parent is None:
            return self._sine_solar_height_
        else:
            return parent.weather.calc_sine_solar_height(hour)

    def _calc_PAR(self, hour):

        parent = self._palm

        if parent is None:
            return self._light_intensity_
        else:
            return parent.weather.calc_PAR(hour)

    @property
    def _hour_of_dawn(self):

        parent = self._palm

        if parent is None:
            return self._hour_of_dawn_
        else:
            return parent.weather.hour_of_dawn

    @property
    def _hour_of_dusk(self):

        parent = self._palm

        if parent is None:
            return self._hour_of_dusk_
        else:
            return parent.weather.hour_of_dusk

    def calc_total_gross_assimilation(self):
        """ Calculates the daily total gross assimilation rate (kg_CH2O/ha/day).
        
        Note, should be of the order 100--500 kg/ha/day.
        """
        
        h0 = self._hour_of_dawn
        h1 = self._hour_of_dusk

        daylength = h1 - h0

        assert daylength >= 0

        # the time-step of integration (hour)
        # gaussian weights
        xgs = [0.047, 0.231, 0.5, 0.769, 0.953]
        wgs = [0.118,0.239,0.284,0.239,0.12]

        # kg_CH2O/ha/day
        total = 0

        for xg,wg in zip(xgs,wgs):

            hour = h0 + xg*daylength

            rate = self.calc_gross_assimilation(hour=hour)

            dtotal = 3600 * 10**-9 * 10**4 * rate * wg * daylength

            total += dtotal

        return total

    def calc_gross_assimilation(self, hour=12, SCP=0.2, KDF=0.33, verbose=False):
        """ Calculates the gross assimilation rate (ug_CH2O/m2/s).

        After the SUCROS97 implementation.

        Determined via a weighted sum (gaussian integral)
        of the photosynthesis rate
        --via the light response curve--
        at different heights in the canopy.

        Simpliying assumptions:
        - Light intensity and flux described by an exponential light-extinction curve
        - The leaves have random angles

        Parameters
        ----------
        I: photo-syntetically active radiation (irridiance) (J/m2/s)
        LAI: leaf area index (m2 leaf/m2 soil)
        fDF: fraction diffuse light (1)
        SCP: Scattering coefficient of leaves for PAR; fraction un-absorbed PAR (1)
        KDF: Extinction coefficient diffuse flux leaves (1)
        SINB: Sine of the light-angle b (1)

        Reference
        ---------
        Explanation:
            Goudriaan, J. and van Laar, H.H, 1994.
            Modelling Potential Crop Growth Processes
            Textbook with exercises
        SUCROS code:
            Van Laar, H.H and Goudriaan, J. and Van Keulen, H., 1994.
            SUCROS97: Simulation of crop growth for
            potential and water-limited production situations

        """

        LAI = self.leaf_area_index 

        SINB = self._calc_sine_solar_height(hour)

        fDF = self._calc_fraction_diffuse(hour)

        I = self._calc_PAR(hour)

        # the intensity of the portion of diffuse light (J/m2/s)
        PARDF = I*fDF

        # the intensity of the portion of direct light (J/m2/s) 
        PARDR = I*(1-fDF)

        # gaussian weights
        xgs = [0.047,0.231,0.5,0.769,0.953]
        wgs = [0.118,0.239,0.284,0.239,0.12]

        # Goal here is to estimate how the light intensity
        # decreases throughout the (uniform) canopy.
        # It turns out that we can best assume the light intensity
        # decreases exponentially the more canopy is above ones head.

        # We start by considering
        # SQV: a light extinction coeff for horizontal opague leaves ~ .9
        SQV = sqrt(1-SCP)
        
        # from which we derive
        
        # REFH: a light reflection coeff for horizontal opaque leaves ~.05
        # REFS: a light reflection coeff for spherical opaque leaves ~.05
        REFH = (1-SQV)/(1+SQV)
        REFS = REFH*2/(1+2*SINB)

        # next we derive a 
        # CLUSTF: cluster coeff ~.4
        # to try and take into account that leaves may be clustered i.e.
        # less extinction for the same amount of leaves
        CLUSTF = KDF / (0.8*SQV)

        if verbose: print('CLUSTF',CLUSTF)
        
        # this cluster coeff is used to estimate the final
        # KBL: extinction coeff spherical black leaves ~.4
        # KDRT: extinction coeff spherical 'opaque' leaves ~.3
        # These 'opaque leaves' are our model leaves
        # for which we take into account first order reflection/transmission
        # in the exponential light decrease.
        KBL = (0.5/SINB) * CLUSTF
        KDRT = KBL * SQV

        # KBL is used to estimate the direct light intensity
        # at a certain depth.
        # KDRT is used to estimate the total light intensity ''
        # By comparing the two light intensities we also estimate
        # the diffuse light intensity at a certain depth,
        # which is the difference.

        # this will hold our result, the gross assimilation (ug_CH20/ha/s)
        AGROS = 0

        if verbose: print('SCP',SCP)
        if verbose: print('REFH',REFH)
        if verbose: print('REFS',REFS)
        if verbose: print('KDF',KDF)
        if verbose: print('KDRT',KDRT)
        if verbose: print('KBL',KBL)

        # now let us integrate our light response over the canopy depth
        # using a Gaussian quadrature
        for xg,wg in zip(xgs,wgs):

            # leaf area above the point the evaluate the light response
            # eg .1
            L = xg*LAI

            if verbose: print('--------------')
            if verbose: print('L',L)

            # the absorbed fluxes - our exponential decrease
            
            # the flux of diffuse light
            VISDF = (1-REFH)*PARDF*KDF*exp(-KDF*L)

            # the total flux of absorbed direct light - involves first order scattering
            VIST = (1-REFS)*PARDR*KDRT*exp(-KDRT*L)

            # the flux of direct light directly hitting any leaves
            VISD = (1-SCP)*PARDR*KBL*exp(-KBL*L)

            if verbose: print('VISDF', VISDF)
            if verbose: print('VISTOT', VIST)
            if verbose: print('VISD', VISD)

            # absorbed flux for shaded leaves:
            # diffuse light originating from the incoming diffuse light plus
            # diffuse light originating from the scattered direct light.
            # This estimate of the scattered direct light is arguable the most
            # difficult part to wrap your mind around.
            VISSHD = VISDF + (VIST - VISD)

            # the assimilation rate of the shaded leaves at depth L
            ASHD = self.calc_light_response(VISSHD)

            if verbose: print('VISSHD',VISSHD)
            if verbose: print('\tASHD',ASHD)
            if verbose: print('\tLUESH',ASHD/VISSHD)

            # the light use efficiency of the shaded leaves
            LUESHD = ASHD/VISSHD

            # absorbed flux of direct light: the non-scattering fraction
            # of the light, adjusted for the sun angle (lower angle -> less intense)
            VISPP = (1-SCP) * PARDR / SINB

            # effective assimilation sunlight
            VISSUN = VISSHD + VISPP
            if verbose: print('\tVISSUN',VISSUN)

            # the assimilation rate of the sun-lit leaves at depth L
            ASUN = 0

            # now, since our leaves are randomly oriented
            # we evaluate the effective assimilation rate
            # for the directly lit leaves by effectively
            # averaging over
            # the distribution of absorbed direct-light 
            for xg_,wg_ in zip(xgs,wgs):

                VISSUN = VISSHD + VISPP*xg_

                AS_ = self.calc_light_response(VISSUN)

                ASUN += AS_*wg_

            if verbose: print('\tASUN',ASUN)
            if verbose: print('\tLUESUN',ASUN/VISSUN)

            # the light use efficiency of the sun-lit leaves
            LUESUN = ASUN/VISSUN

            # the fraction of sun-lit leaves
            FSLLA = CLUSTF * exp(-KBL*L)

            if verbose: print('FSLLA',FSLLA)
            if verbose: print('\tELUE',(VISSHD*LUESHD + VISD*LUESUN)/(VISSHD+VISD))

            # the total assimilation rate (ug_CH20/m2/s) at depth L
            AGL = FSLLA * ASUN + (1-FSLLA) * ASHD

            if verbose: print('AGL',AGL)

            # we add the result to the accumulator
            # the assimilation rate canopy average (ug_CH20/m2/s)
            AGROS += wg*AGL

        if verbose: print('AGROS',AGROS)

        # so far we have not been multiplying each layers
        # photosynthesis by the representative amount of leaf area
        # in the layer ie we did
        # AGROS += wg*AGL instead of AGROS += LAI*wg*AGL
        # accordingly, sticking to the style of the SUCROS implementation
        # we multiply by the LAI, in the end.

        return AGROS*LAI

    @property
    def intercepted_PAR(self):
        ''' The intercepted radiation (PAR) (GJ/ha/day). '''

        # (MJ/m2/day)
        PAR = self._PAR

        # 9 MJ/m2/day --> ~ 9*10000/1000 = 90 GJ/ha/day
        # 1 MJ/m2 = 10 GJ/ha

        c = 10

        # (1)
        fraction_intercepted = self.fraction_intercepted

        return c * fraction_intercepted * PAR

    @property
    def fraction_intercepted(self):
        ''' The fraction of PAR intercepted (1).

        Uses the Lambert-Beer estimate.
        '''

        LAI = self.leaf_area_index

        k = self.parameters['k']['value']

        return (1 - np.exp(-k*LAI))

    #~~~~~~~~~~~~

    @property
    def _mass_rachis(self):
        ''' The mass of the rachis (t_DM/ha). '''

        c = self.parameters['fraction_rachis']['value']

        return c * self.mass

    @property
    def _mass_leaflets(self):
        ''' The mass of the leaflets (t_DM/ha). '''

        c = self.parameters['fraction_leaflets']['value']

        return c * self.mass

    @property
    def mass_per_palm(self):
        ''' Frond mass per palm (kg_DM/palm). '''
        return self.mass / self._planting_density

    @property
    def mass_change_rate_per_palm(self):
        ''' Mass change rate (kg_DM/palm/year). '''
        return (1/self._planting_density)*self.mass_change_rate_yearly

    @property
    def mass_per_frond(self):
        ''' Mass per frond (kg_DM/frond). '''
        return self.mass / self.count

