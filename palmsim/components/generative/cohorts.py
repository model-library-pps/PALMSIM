
from ..helpers import add_dumps

from .bunch_components import Stalk, MesocarpOil, MesocarpFibers, Kernels

import yaml

@add_dumps
class Cohort(object):
    """ The general model for inflorescence cohorts.

    A cohort is represented by a "mean" inflorescence,
    and a multiplicity denoting the number of
    inflorescences in the cohort.

    Concrete sub-classes: Indeterminate, Male, Female.

    Key Properties:
        age : months after initiation
        t_differentiation : -
        mass : mass of the mean inflorescence
        multiplicity : number of inflorescences in cohort

    """

    units = yaml.load("""

        age                             : 'day'
        t_differentiation               : 'day'
        assim_growth_cohort             : 'kg_CH2O/cohort/day'
        assim_growth_organ              : 'kg_CH2O/organ/day'
        female_fraction                 : '1'
        maintenance_requirement         : 'kg_CH2O/organ/day'
        mass                            : 'kg_DM'
        potential_mass                  : 'kg_DM'
        mass_growth_rate                : 'kg_DM/day'
        mass_growth_rate_potential      : 'kg_DM/day'
        multiplicity                    : '1/cohort'
        potential_sink_strength         : 'kg_CH2O/organ/day'
        relative_sink_strength          : '1'
        abortion_fraction               : '1'
        bunch_failure_fraction          : '1'
        is_deletable                    : 'bool'
        has_flowered                    : 'bool'
        inflorescence_abortion_fraction : '1'
        is_harvestible                  : 'bool'
        mesocarp_oil_content            : '1'
        relative_sink_strength          : '1'
        should_trigger_flowering        : 'bool'
        Ic                              : '1'

    """)

    _name = 'Cohort'

    @property
    def _MAP(self):
        """ The palm age in months after planting (month). """
        if self._container is None:
            return 0
        else:
            if self._container._palm is None:
                return 0
            else:
                return self._container._palm.MAP

#~~~~~~~~~~~~~~~~

    @property
    def potential_sink_strength(self):
        """ The potential sink strength (kg_CH2O/inflorescence/day). """
        return sum([x.potential_sink_strength for x in self.components])

    def get_relative_sink_strength(self):
        """ Sink strength relative to other organs (1), a partitioning fraction. """

        if self._container is None:
            # assume it is the only one - only used in testing
            return 1

        else:
            cohort_sink_strength = self.multiplicity*self.potential_sink_strength

            total_sink_strength = self._container.potential_sink_strength

            if total_sink_strength == 0:
                return 0
            else:

                # relative sink strength of each cohort
                res = cohort_sink_strength/total_sink_strength
                return res

    @property
    def assim_growth_cohort(self):
        """ Assimilates for growth (kg_CH20/cohort organs/month). """

        if self._container is None:
            # only used in testing
            return self.potential_sink_strength*self.multiplicity

        else:
            assim_growth_generative = self._container.assim_growth

            return self.relative_sink_strength*assim_growth_generative

    @property
    def assim_growth_organ(self):
        """ Assimilates for growth (kg_CH20/organ/month). """

        if self.multiplicity > 0:
            return self.assim_growth_cohort/self.multiplicity
        else:
            return 0

    @property
    def Ic(self):
        """ The so-called index of competition.

        After Combres et al., 2013.
        """
        PSS = self.potential_sink_strength
        if PSS > 0:
            return self.assim_growth_organ/PSS
        else:
            return 0

#~~~~~~~~~~~~~~~~

    @property
    def potential_mass(self):
        """ The potential mass (kg_DM). """

        # TEMP
        return 1 + (1/12)*self._MAP

    @property
    def mass(self):
        """ The mass (kg_DM). """
        return sum([x.mass for x in self.components])

    @property
    def mass_growth_rate(self):
        """ The mass growth rate (kg_DM/day). """
        return sum([x.mass_growth_rate for x in self.components])

    @property
    def mass_growth_rate_potential(self):
        """ The mass growth rate (kg_DM/day). """
        return sum([x.mass_growth_rate_potential for x in self.components])

#~~~~~~~~~~~~~~~~

    @property
    def maintenance_requirement(self):
        """ The maintenance requirement (kg_CH2O/day). """
        return sum([x.maintenance_requirement for x in self.components])

#~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        """ Update the cohort by dt days. """
        self._update(dt=dt)

    def set_relative_sink_strength(self):
        """ Set the relative sink strength. """
        res = self.get_relative_sink_strength()
        self.relative_sink_strength = res

    def _update(self,dt=1):
        """ Update the cohort by dt days.

        Note
        ----
        We assume abortion fraction is "small"
        s.t. we can use 1-N*epsilon ~= (1-epsilon)**N.
        E.g. 1.01**10 = 1.105 ~= 1 + 10*0.01
        """

        # 1. update the representative bunch components

        # in updating the mass
        # the bunch components will ask
        # the cohort how much assimilates are available
        # for growth given their current age
        for component in self.components:
            component.update_mass(dt=dt)

        # only after the mass growth has been applied
        # we increment the age - namely
        # the sink strength is a function of age
        for component in self.components:
            component.update_age(dt=dt)

        # 2. apply the abortion fractions
        survival_fraction = max(0, (1-self.abortion_fraction*dt))
        self.multiplicity *= survival_fraction

        # 3. increment age
        self.age += dt

#~~~~~~~~~~~~~~~~

    def to_comprehensive_dict(self):
        """ Returns a dict containing comprehensive info. """
        d = self.to_dict()
        for component in self.components:
            d.update(component.to_dict(prefixed=True))
        return d

    @property
    def abortion_fraction(self):
        """ The abortion fraction (1/month). """
        return self._abortion_fraction

#~~~~~~~~~~~~~~~~

class Indeterminate(Cohort):
    """ Models a cohort of indeterminate inflorescences. """

    parameters = yaml.load("""

        t_differentiation:
            value: 210
            unit: 'days'
            info: 'The number of days until sex differentiation.'
            source: 'Calibration - initially based on Adam et al., see fig 3.'

        abortion_fraction:
            value: 0
            unit: '1/day'
            info: 'Monthly aborted fraction before (!) sex differentiation.'
            source: 'Estimated to be insignificantly small - note, not mentioned in Adam et al. 2011.'
        """)

    _prefix = 'indeterminate'
    sex = 'indeterminate'

    def __init__(self,container=None):

        # the container keeps track of the cohorts
        self._container = container

        # components - here only a stalk
        self.stalk = Stalk(self)

        # state
        self.multiplicity = 1

        # in days after frond initiation
        self.age = 0

        # rate
        self.relative_sink_strength = 0

        # param
        self._abortion_fraction = self.parameters['abortion_fraction']['value']
        self.t_differentiation = self.parameters['t_differentiation']['value']

        # only used in testing
        self._female_fraction = 0.9

    @property
    def should_differentiate(self):
        """ Should the indeterminate differentiate? (bool). """
        return self.age >= self.t_differentiation

    @property
    def components(self):
        """ The sub-organs. """
        return [self.stalk]

    @property
    def female_fraction(self):
        """ Fraction female at sex determination (1). """

        if self._container is None:
            return self._female_fraction

        else:
            return self._container.female_fraction

    def to_male(self):
        """ Returns the associated male inflorescence cohort after sex determination.

        Conceptually converts the indeterminate to a male inflorescence.
        """

        cohort = Male(self._container)

        cohort.stalk = self.stalk.copy()
        cohort.stalk._cohort = cohort
        cohort.components = [cohort.stalk]
        cohort.age = self.age

        # fractionality
        f = 1 - self.female_fraction

        # Pass on cohort multiplicity/relative sink strength
        cohort.multiplicity = f*self.multiplicity
        cohort.relative_sink_strength = f*self.relative_sink_strength

        return cohort

    def to_female(self):
        """ Returns the associated female inflorescence cohort after sex determination.

        Conceptually converts the indeterminate to a female inflorescence.
        """

        cohort = Female(self._container)

        # Pass on cohort mean organ state/components
        cohort.stalk = self.stalk.copy()
        cohort.stalk._cohort = cohort
        cohort.components = [cohort.stalk]
        cohort.age = self.age

        # fractionality
        f = self.female_fraction

        # Pass on cohort multiplicity/relative sink strength
        cohort.multiplicity = f*self.multiplicity
        cohort.relative_sink_strength = f*self.relative_sink_strength

        return cohort

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool)

        Any indeterminate cohort should be deleted
        after sex determination - continues its life
        as a male and female cohort.
        """
        return self.age > self.t_differentiation

class Female(Cohort):

    _prefix = 'female'

    parameters = yaml.load("""

        inflorescence_abortion_fraction:
            value: 0.0016
            unit: '1/day'
            info: 'Base-line aborted fraction during inflorescence abortion.'
            source: 'Based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 62.'

        inflorescence_abortion_t0:
            value: -90
            unit: 'day'
            info: 'The start of the period in which inflorescence abortion occurs relative to the time of anthesis.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        inflorescence_abortion_dt:
            value: 30
            unit: 'day'
            info: 'The duration of the period in which inflorescence abortion occurs.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        bunch_failure_fraction:
            value: 0.0033
            unit: '1/day'
            info: 'Base-line aborted fraction during bunch abortion.'
            source: 'Based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 62.'

        bunch_failure_t0:
            value: 60
            unit: 'day'
            info: 'The start of the period in which bunch failure occurs relative to the time of anthesis.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        bunch_failure_dt:
            value: 30
            unit: 'day'
            info: 'The duration of the period in which bunch failure occurs.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        t_anthesis:
            value: 990
            unit: 'day'
            info: 'The age at which the anthesis takes place in terms of months after frond initiation.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'

        water_stress_bunch_failure_increase:
            value: .8
            unit: '1'
            info: 'The increase in bunch failure given an increase in water stress (coeff. of proportionality).'
            source: 'Calibration:: less sensitive than sex ratio and bunch failure.'

        water_stress_bunch_failure_threshold:
            value: .6
            unit: '1'
            info: 'Moisture content below which bunch failure response sets in.'
            source: 'Calibration:: less sensitive than sex ratio and infloresence abortion.'

        water_stress_inflorescence_abortion_increase:
            value: 1.0
            unit: '1'
            info: 'The increase in inflorescence abortion given an increase in water stress (coeff. of proportionality).'
            source: 'Calibration:: less sensitive than sex ratio, more sensitive than bunch failure.'

        water_stress_inflorescence_abortion_threshold:
            value: .4
            unit: '1'
            info: 'Moisture content below which inflorescence abortion response sets in.'
            source: 'Calibration:: less sensitive than sex ratio, more sensitive than bunch failure.'

        t_maturity:
            value: 1200
            unit: 'day'
            info: 'The age at which the fruit is harvestible.'
            source: 'Calibration - initially based on Adam et al. 2011, see fig 3.'
            """)

    sex = 'female'
    def __init__(self,container=None):

        self._container = container

        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # state
        self.multiplicity = 1

        # in days after frond initiation
        self.age = 0

        self.has_flowered = False

        # rate
        self.relative_sink_strength = 0

        # param

        self.t_anthesis = self.parameters['t_anthesis']['value']
        self.t_maturity = self.parameters['t_maturity']['value']

        self._inflorescence_abortion_t0 = self.parameters['inflorescence_abortion_t0']['value']
        self._inflorescence_abortion_dt = self.parameters['inflorescence_abortion_dt']['value']

        self._bunch_failure_t0 = self.parameters['bunch_failure_t0']['value']
        self._bunch_failure_dt = self.parameters['bunch_failure_dt']['value']

        # proto-typical value
        self._water_deficit_ = 0
        self._soil_moisture_content_ = 1

#~~~~~~~~~~~~~~~~

    def update(self,dt=1):
        """ Update the cohort by dt days. """

        self._update(dt=dt)

        if self.should_trigger_flowering:
            self.set_fruit()

    @property
    def _water_deficit(self):
        if self._container is None:

            return self._water_deficit_
        else:
            return self._container._water_deficit

    @property
    def _soil_moisture_content(self):
        if self._container is None:
            return self._soil_moisture_content_
        else:
            return self._container._soil_moisture_content

    @property
    def abortion_fraction(self):
        """ The monthly abortion fraction (1/month). """
        return self.inflorescence_abortion_fraction + self.bunch_failure_fraction

    @property
    def inflorescence_abortion_fraction(self):
        """ The monthly abortion fraction (1/month).

        Here we derive it's value.

        """

        t = self.age - self.t_anthesis

        t0 = self._inflorescence_abortion_t0
        dt = self._inflorescence_abortion_dt
        t1 = t0 + dt

        if (t >= t0) and (t < t1):
            return self._inflorescence_abortion_fraction
        else:
            return 0

    @property
    def _inflorescence_abortion_fraction(self):
        """ The monthly abortion fraction (1/month).

        Here we derive it's value.
        """

        base = self.parameters['inflorescence_abortion_fraction']['value']

        t0 = self._inflorescence_abortion_t0
        dt = self._inflorescence_abortion_dt
        t1 = t0 + dt

        timespan =  t1-t0

        driver = self._soil_moisture_content
        threshold = self.parameters['water_stress_inflorescence_abortion_threshold']['value']
        slope = self.parameters['water_stress_inflorescence_abortion_increase']['value']

        # onset when driver < threshold
        modifier = slope*max(0,threshold-driver)

        return (base + modifier)/timespan

    @property
    def bunch_failure_fraction(self):

        t = self.age - self.t_anthesis

        t0 = self._bunch_failure_t0
        dt = self._bunch_failure_dt
        t1 = t0 + dt

        if (t >= t0) and (t < t1):
            return self._bunch_failure_fraction
        else:
            return 0

    @property
    def _bunch_failure_fraction(self):

        base = self.parameters['bunch_failure_fraction']['value']

        t0 = self._bunch_failure_t0
        dt = self._bunch_failure_dt
        t1 = t0 + dt

        timespan = t1 - t0

        driver = self._soil_moisture_content
        threshold = self.parameters['water_stress_bunch_failure_threshold']['value']
        slope = self.parameters['water_stress_bunch_failure_increase']['value']

        # onset when driver < threshold
        modifier = slope*max(0,threshold-driver)

        return (base + modifier)/timespan

    def set_fruit(self):
        self.mesocarp_oil = MesocarpOil(self)
        self.mesocarp_fibers = MesocarpFibers(self)
        self.kernel = Kernels(self)
        self.components = [self.stalk,
                            self.mesocarp_fibers,
                            self.mesocarp_oil,
                            self.kernel]
        self.has_flowered = True

    @property
    def should_trigger_flowering(self):
        """ A boolean indicating whether "set_fruit" should be triggered. """
        return self.age > self.t_anthesis and not self.has_flowered

    @property
    def is_harvestible(self):
        """ Indicates whether this cohort is harvestible. """
        return self.age >= self.t_maturity

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool) - (metabolically inactive) """
        return self.age > self.t_maturity

    @property
    def mesocarp_oil_content(self):
        """ Mesocarp oil content (DM/DM). """
        if self.has_flowered:
            return self.mesocarp_oil.mass/self.mass
        else:
            return 0

class Male(Cohort):
    _name = 'male'
    _version = '0.0'

    parameters = yaml.load("""

        t_anthesis:
            value: 990
            unit: 'day'
            info: 'The age at which the anthesis takes place in terms of months after frond initiation.'
            source: 'Adam et al. 2011, see fig 3.'

            """)

    sex = 'male'

    def __init__(self, container=None):

        self._container = container

        # components
        self.stalk = Stalk(self)
        self.components = [self.stalk]

        # state

        # in practice the initial values will be set
        # upon sex determination via the associated indeterminate cohort
        # see "Indeterminate.to_male"

        self.multiplicity = 1

        # in days after frond initiation
        self.age = 0

        self.has_flowered = False

        self.relative_sink_strength = 0

        # param
        self.t_anthesis = self.parameters['t_anthesis']['value']

        # we do not model abortion of male inflorescences
        # and thus keep it at a value of zero.
        self._abortion_fraction = 0

    @property
    def is_deletable(self):
        """ When to delete this cohort? (bool) - (metabolically inactive) """
        return self.age > self.t_anthesis