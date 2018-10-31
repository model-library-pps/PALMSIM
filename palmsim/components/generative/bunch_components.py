
from ..helpers import add_dumps
from ..constants import DAYS_PER_MONTH

import yaml

def make_quadratic_function(x1,x2,A):
    """ Returns a strictly positive quadratic function.

    We use the fact that "the area below a parabola" is 2/3*height*base.

    Parameters
    ----------
    x1: left x s.t. y = 0
    x2: right x s.t. y = 0
    A: area under parabola

    Returns
    -------
    A quadratic function x -> y.

    """

    # base width
    W = x2 - x1

    # max height - derived analytically
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
    """ Returns a linear function f(x) through (x1,y1) and (x2,y2). """
    c = (y2-y1)/(x2-x1)
    def f(x):
        return c*(x-x1) + y1
    return f

@add_dumps
class BunchComponent(object):

    """ A general model for bunch components. for  (e.g. stalk).

    Key components:

        potential_mass          : the potential mass.
        potential_sink_strength : potential sink strength.
        relative_sink_strength  : sink strength relative to sibling sub-organs.
        _cohort                  : reference to the parent organ (the cohort).

    Notes
    -----
    Each bunch component is associated with an inflorescence cohort.

    The potential sink strength is modelled as a function of age -
    parametrized via a start time/end time of growth and a potential mass.

    This potential sink strength determines the relative sink strength
    and thus the realised sink strength (assimilates for growth),
    and so the mass growth rate.

    """

    parameters = yaml.load("""

        specific_maintenance:
            value: 0.0005
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'

        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'

        """)

    units = yaml.load("""

        mass                             : 'kg_DM'
        potential_mass                   : 'kg_DM'
        age                              : 'month'
        assim_growth                     : 'kg_CH2O/month'
        conversion_efficiency            : 'g_DM/g_CH2O'
        specific_maintenance_requirement : 'tonne_CH2O/tonne_DM/day'
        maintenance_requirement          : 'kg_CH2O/month'
        mass_growth_rate                 : 'kg_DM/month'
        mass_growth_rate_potential       : 'kg_DM/month'
        relative_sink_strength           : '1'
        potential_sink_strength          : 'kg_CH2O/month'

    """)

    def __init__(self, cohort = None, potential_mass = None):
        """ Initialization.

        Each bunch component is associated with a cohort
        via the "_cohort" property.
        """

        self._cohort = cohort

        if potential_mass is None:
            self.potential_mass = self.get_potential_mass()
        else:
            self.potential_mass = potential_mass

        self._potential_growth_function = \
            make_quadratic_function(self.parameters['t_growth_start']['value'],
                                      self.parameters['t_growth_end']['value'],
                                      self.potential_mass,
                                      )

        # state
        self.mass = 0
        self.age = 0

        # driving rate variable
        self.potential_sink_strength = self.get_potential_sink_strength()

        # dummy variable for proto-typing
        self._assim_growth = 0

#~~~~~~~~~~~~~~~~

    def get_potential_mass(self):
        """ A linear function of palm age.

        Parametrized via y0 the potential mass
        for the first fruits (x0) and y1 the
        potential mass at the end of a typical
        field life-time (x1) -- 30 years after planting:

        y = (y1-y0)/(x1-x0)*(x-x0) + y0 .

        """

        if 'potential_mass_t0' in self.parameters:

            y0 = self.parameters['potential_mass_t0']['value']

        else:
            print(self.__class__.__name__)
            print(list(self.parameters))

        if self._cohort is None:
            return y1
        else:
            MAP = self._cohort._MAP
            y1 = self.parameters['potential_mass_t1']['value']

            # here hard-coded..
            MAP0 = 0
            MAP1 = 360

            # a linear interpolation
            c = (y1-y0)/(MAP1-MAP0)

            res = c*(MAP-MAP0) + y0

            if res < y0:
                return y0
            else:
                return res

#~~~~~~~~~~~~~~~~

    def get_potential_sink_strength(self):
        """ Potential sink strength (kg CH2O/month).

        Follows from the potential mass growth rate and the
        conversion efficiency.
        """
        c = self.parameters['conversion_efficiency']['value']

        return self.mass_growth_rate_potential/c

    @property
    def mass_growth_rate_potential(self):
        """ The potential mass growth rate (kg DM/month).

        Is a function of palm age.
        """
        return self._potential_growth_function(self.age)

    @property
    def relative_sink_strength(self):
        """ The sink strength relative to the other elements (1). """
        if self._cohort is None:
            # assume it is stand-alone
            return 1
        else:
            if self._cohort.potential_sink_strength > 0:
                return self.potential_sink_strength / \
                        self._cohort.potential_sink_strength
            else:
                return 0

    @property
    def assim_growth(self):
        """ The realised sink strength (kg CH2O/month). """
        if self._cohort is None:
            # assume proto-typing
            return self._assim_growth
        else:
            # total assim inflow per representative mean organ
            total = self._cohort.assim_growth_organ
            return self.relative_sink_strength * total

#~~~~~~~~~~~~~~~~

    @property
    def mass_growth_rate(self):
        """ The realised mass growth rate (kg DM/month). """

        c = self.parameters['conversion_efficiency']['value']

        res = c*self.assim_growth
        cap = self.mass_growth_rate_potential
        #return res
        return min(cap,res)

#~~~~~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        """ The maintenance resp. requirement (kg CH2O/month). """

        c = self.parameters['specific_maintenance']['value']

        return DAYS_PER_MONTH*c*self.mass

#~~~~~~~~~~~~~~~~

    # Note, updating is managed by the associated cohort.
    # -- the relative sink strength of each bunch component
    # depends on that of the other bunch components;
    # the calculation of the relative sink strength
    # must be done in a synchronized manner

    def update_mass(self,dt=1):
        """ Update the mass by a month. """
        self.mass += self.mass_growth_rate*dt

    def update_age(self,dt=1):
        """ Update the age by a month and set the potential sink strength. """
        self.age += dt
        self.potential_sink_strength = self.get_potential_sink_strength()

#~~~~~~~~~~~~~~~~

    def copy(self):
        """ Makes a copy of a bunch component.

        This is used in the "sex determination" stage where a
        single indeterminate cohort is split in a male and female cohort:
        we make a copies of the bunch component(s) (the stalk)
        and assign these to the associated male and female cohort.

        """

        # the constructor makes a new bunch component of the same type.
        constructor = type(self)

        # make sure to pass the potential mass which was set at inflorescence initiation
        duplicate = constructor(potential_mass = self.potential_mass)

        # carry over state (of basic types e.g. float so straightforward to do so)
        duplicate.mass = self.mass
        duplicate.age = self.age

        # re-set the potential sink strength
        duplicate.potential_sink_strength = duplicate.get_potential_sink_strength()

        return duplicate

#~~~~~~~~~~~~~~~~

    @property
    def cohort_age(self):
        """ The age of the owning cohort. """
        if self._cohort is None:
            return 0
        else:
            return self._cohort.age

#~~~~~~~~~~~~~~~~

class Stalk(BunchComponent):
    """ Models an inflorescence's stalk."""

    _prefix = 'stalk'

    parameters = yaml.load("""

        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%

        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%

        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, in months after leaf initiation.'
            source: 'Based on Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        t_growth_end:
            value: 33
            unit: 'month'
            info: 'The end of potential growth, in months after leaf initiation.'
            source: 'Based on Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        potential_mass_t0:
            value: .5
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        potential_mass_t1:
            value: 5
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        """)

class MesocarpFibers(BunchComponent):
    """ Models an inflorescence's mesocarp fibers."""

    _prefix = 'mesocarp_fibers'

    parameters = yaml.load("""

        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%

        conversion_efficiency:
            value: 0.69
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%

        t_growth_start:
            value: 0
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        t_growth_end:
            value: 5
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        potential_mass_t0:
            value: 2
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        potential_mass_t1:
            value: 20
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%
        """)

class MesocarpOil(BunchComponent):
    """ Models an inflorescence's mesocarp oil. """

    _prefix = 'mesocarp_oil'

    parameters = yaml.load("""
        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%

        conversion_efficiency:
            value: 0.42
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%

        t_growth_start:
            value: 3
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        t_growth_end:
            value: 5
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        potential_mass_t0:
            value: 3
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        potential_mass_t1:
            value: 30
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        """)

class Kernels(BunchComponent):
    """ Models an inflorescence's kernels."""

    _prefix = 'kernel'

    parameters = yaml.load("""

        specific_maintenance:
            value: 0.0022
            unit: 'tonne_CH2O/tonne_DM/day'
            info: 'The specific maintenance.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. Table II.'
            uncertainty: 5%

        conversion_efficiency:
            value: 0.42
            unit: 'g_DM/g_CH2O'
            info: 'The conversion efficiency.'
            source: 'Based on Dufrene, E. and Ochs, R. and Saugier, B., 1990. Photosynthese et productivite du palmier a huile en liaison avec les facteurs climatiques. In turn based on van Kraalingen, D.W.G., 1989. See text below table II and table III.'
            uncertainty: 5%

        t_growth_start:
            value: 2
            unit: 'month'
            info: 'The start of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        t_growth_end:
            value: 6
            unit: 'month'
            info: 'The end of potential growth, relative to anthesis.'
            source: 'Based on Corley, Ch.5. See fig 5.7. and Adam et al. 2011, see fig 3.'
            uncertainty: 5%

        potential_mass_t0:
            value: .5
            unit: 'kg'
            info: 'The potential mass for a "young" palm (age <= 3 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        potential_mass_t1:
            value: 5
            unit: 'kg'
            info: 'The potential mass for a "mature" palm ( age > 15 YAP).'
            source: 'Based on Corley, Ch.5. See fig 5.7.'
            uncertainty: 5%

        """)
