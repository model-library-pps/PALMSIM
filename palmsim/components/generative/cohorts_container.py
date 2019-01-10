
from ..helpers import add_dumps
from ..helpers import sigmoid

from .cohorts import Indeterminate

import yaml
import numpy as np

@add_dumps
class Cohorts(object):
    """ The interface between the palm and the cohorts.

    Acts like a manager i.e. manages the flow of assimilates
    to the cohorts, handles the initiation of new cohorts,
    deletal of in-active cohorts, etc.

    """

    parameters = yaml.load("""

        soil_moisture_specific_female_fraction_decrease:
            value: 1.5
            unit: '1'
            info: 'Decrease of the female fraction per unit drop of soil moisture content past the threshold.'
            source: 'Calibration.'
            uncertainty: 20%

        female_fraction_decrease_threshold:
            value: .8
            unit: '1'
            info: 'The soil moisture content below which sex ratio response sets in.'
            source: 'Calibration.'
            uncertainty: 20%

        female_fraction_k:
            value: .3

        female_fraction_t0:
            value: 10

        female_fraction_vasym:
            value: .3

        female_fraction_minimum:
            value: 0.1
            unit: '1,YAP'
            info: 'The minimum fraction female --- expected to be a plant characteristic.'
            source: 'Calibration - currently an ad hoc estimate based on L.D. Sparnaaijs thesis: The analysis of bunch production. p 26. figure 5.'
            uncertainty: 20%

        bunch_FM_to_DM_ratio:
            value: 2
            unit: '1'
            info: 'The fresh to dry mass of a bunch.'
            source: 'Calibration - currently an ad hoc estimate based on the information the Oil Palm Monograph by Corley and Tinker, chapter 5 - the figure on bunch component mass over time.'

        onset_time:
            value: 14
            unit: 'month'
            info: 'The time of onset of inflorescence production that leads to actual harvestible bunches in terms of MAP.'
            source: 'Calibration -- hardly reported in the literature thus a contribution.'

        onset_steepness:
            value: .5
            unit: '1/month'
            info: 'The steepness of the onset of inflorescence production -- the time derivative of the onset. I.e. .5 -> in one month the fraction of inflorescences growing goes up by 50%.'
            source: 'Calibration -- hardly reported in the literature thus a contribution.'

        """
    )

    units = yaml.load("""

        assim_growth                    : 'kg_DM/ha/day'
        bunch_production                : 'kg_DM/ha/day'
        count                           : '1/ha'
        count_females                   : '1/ha'
        count_indeterminates            : '1/ha'
        count_males                     : '1/ha'
        EFB_production                  : 'kg_DM/ha/day'
        fraction_initiated              : '1'
        frond_initiation_rate           : '1/palm/day'
        initiation_rate                 : '1/palm/day'
        initial_multiplicity            : '1/cohort'
        maintenance_requirement         : 'kg_CH2O/ha/day'
        mass                            : 'kg_DM/ha'
        mass_females                    : 'kg_DM/ha'
        mass_indeterminates             : 'kg_DM/ha'
        mass_males                      : 'kg_DM/ha'
        max_age                         : 'day'
        mean_age                        : 'day'
        multiplicity                    : '1/ha'
        potential_sink_strength         : 'kg_CH2O/ha/day'
        bunch_weight                    : 'kg_DM'
        bunch_weight_fresh              : 'kg'
        bunch_count                     : '1/ha/day'
        onset_multiplicity_factor       : '1'
        bunch_failure_fraction          : '1'
        inflorescence_abortion_fraction : '1'
        number_of_cohorts               : '1'
        female_fraction                 : '1'
        FFB_production                  : 't/ha/yr'
        PKO_production                  : 'kg_DM/ha/day'
        CPO_production                  : 'kg_DM/ha/day'
        assim_growth_females            : 'kg_CH2O/ha/day'
        assim_growth_indeterminates     : 'kg_CH2O/ha/day'
        assim_growth_males              : 'kg_CH2O/ha/day'
        mesocarp_oil_content            : '1'
        Ic : '1'

    """)

    _prefix = 'generative'

    def __init__(self,palm=None):

        self.cohorts = []
        self._palm = palm

        # rate
        self._assim_growth = 0
        self.assim_growth = 0
        self.potential_sink_strength = 0
        self._initiation_rate = 0

        # pool of cohorts marked for deletion
        self.to_delete = []

    @property
    def _dt(self):
        if self._palm is None:
            return 1
        else:
            return self._palm.dt

    @property
    def Ic(self):
        """ The so-called index of competition.

        After Combres et al., 2013.
        """

        if self.potential_sink_strength == 0:
            res = 1
        else:
            res = self.assim_growth/self.potential_sink_strength

        return res

    @property
    def stress_index(self):
        return self.Ic

    @property
    def _water_deficit(self):
        """ The water deficit - relative to the critical deficit."""
        if self._palm is None:

            return 0
        else:
            return self._palm.soil.critical_deficit_exceedance

    @property
    def _soil_moisture_content(self):
        """ The water deficit - relative to the critical deficit."""
        if self._palm is None:

            return 1
        else:
            return self.Ic #self._palm.soil.moisture_content

    @property
    def _DAP(self):
        """ The palm age in days after planting. """
        if self._palm is None:
            return 0
        else:
            return self._palm.DAP

    @property
    def _MAP(self):
        """ The palm age in months after planting. """
        if self._palm is None:
            return 0
        else:
            return self._palm.MAP

    @property
    def _YAP(self):
        if self._palm is None:
            return 0
        else:
            return self._palm.YAP

    ##############
    # Inter-facing
    ##############
    @property
    def _planting_density(self):
        if self._palm is None:
            return DEFAULT_PLANTING_DENSITY
        else:
            return self._palm.planting_density

    @property
    def frond_initiation_rate(self):
        """ New indeterminate cohorts (1/ha/day). """
        if self._palm is None:
            return 0
        else:
            return float(self._palm.fronds.initiation_rate)

    @property
    def maintenance_requirement(self):
        """ The generative maintenance requirement (kg_CH2O/ha/day). """
        return sum([x.maintenance_requirement*x.multiplicity for x in self.cohorts])

    ###############
    # Sink-strength
    ###############
    def get_potential_sink_strength(self):
        """ The total potential sink strength (kg_CH2O/ha/day). """
        return sum([x.potential_sink_strength*x.multiplicity for x in self.cohorts])

    def get_assim_growth(self):
        """ The assimilates for generative growth. (kg_CH2O/ha/day) """
        if self._palm is None:
            return self._assim_growth
        else:
            return self._palm.assimilates.assim_growth_generative

    ########
    # Update
    ########
    def update(self,dt=1):

        # Calculated in the PalmSim's "assimilates" object.
        self.assim_growth = self.get_assim_growth()

        # Update existing cohorts:
        #   - update each cohort
        #       - mass growth (mass)
        #       - abortion (multiplicity)
        #       - age
        self.update_existing_cohorts(dt=dt)

        # Differentiate and split each
        # "mature" indeterminate cohort to make a
        #   - female cohort
        #   - male cohort
        self.update_sex()

        # Add new indeterminate cohorts
        self.update_new_cohorts(dt=dt)

        # Delete delete-able
        # (metabolically in-active) cohorts:
        #   - Male's past maturity age
        #   - Female's past harvestible age
        #   - Empty cohorts (multiplicity ~= 0)

        self.to_delete = [x for x in self.cohorts if x.is_deletable]

        self.cohorts = [x for x in self.cohorts if not x.is_deletable]

        # Potential/relative SS is independent of RSS
        # Potential determines realized SS thus should be set
        # before calculating realized SS.
        self.potential_sink_strength = self.get_potential_sink_strength()
        self.set_relative_sink_strengths()

    def set_relative_sink_strengths(self):
        """ Sets the relative sink strengh of the cohorts. """

        cohorts = self.cohorts

        for cohort in cohorts:
            cohort.set_relative_sink_strength()

    def update_existing_cohorts(self,dt):
        """ Updates the existing cohorts. """
        for cohort in self.cohorts:
            cohort.update(dt=dt)

    def update_sex(self):
        """ Updates the cohorts by applying sex differentiation. """

        cohorts_ = []

        for cohort in self.cohorts:

            if (cohort.sex == 'indeterminate') \
                    and (cohort.age > cohort.t_differentiation):

                    f = cohort.to_female()
                    m = cohort.to_male()

                    cohorts_.append(f)
                    cohorts_.append(m)

            else:
                cohorts_.append(cohort)

        self.cohorts = cohorts_

    def update_new_cohorts(self,dt=1):
        # introduce new cohorts

        new_cohort = Indeterminate(container=self)
        new_cohort.multiplicity = self.initiation_rate*dt

        self.cohorts.append(new_cohort)

    ################
    # Mass
    ################
    @property
    def mass(self):
        """ The total generative mass (kg_DM/ha). """
        temp = [x.multiplicity*x.mass for x in self.cohorts]
        return sum(temp)

    ##############
    # Cohort Sets
    ##############
    @property
    def _bunches(self):
        return [x for x in self._females if x.is_harvestible]

    @property
    def _females(self):
        """ Female cohorts. """
        return [x for x in self.cohorts if  x.sex == 'female']

    @property
    def _males(self):
        """ Male cohorts. """
        return [x for x in self.cohorts if  x.sex == 'male']

    @property
    def _indeterminates(self):
        """ Indeterminate cohorts. """
        return [x for x in self.cohorts if  x.sex == 'indeterminate']

    ###############
    # Bunch details
    ###############

    @property
    def CPO_production(self):
        """ (kg/ha/day). """
        res = 0
        for bunch in self._bunches:
            res += bunch.multiplicity*bunch.mesocarp_oil.mass

        return res/self._dt

    @property
    def PKO_production(self):
        """ (kg/ha/day). """
        res = 0
        for bunch in self._bunches:
            res += bunch.multiplicity*bunch.kernel.mass

        return res/self._dt

    @property
    def EFB_production(self):
        """ (kg/ha/day). """
        res = 0
        for bunch in self._bunches:
            mass = bunch.stalk.mass + bunch.mesocarp_fibers.mass
            res += bunch.multiplicity*mass

        return res/self._dt

    @property
    def bunch_production(self):
        """ (kg_DM/ha/day). """
        return self.bunch_count*self.bunch_weight

    @property
    def FFB_production(self):
        """ (kg_FM/ha/yr). """

        c = self.parameters['bunch_FM_to_DM_ratio']['value']

        # monthly -> yearly

        return 365*c*self.bunch_production

    @property
    def bunch_count(self):
        """ (1/ha/day). """

        # harvestible number of bunches --- every dt days
        return sum([x.multiplicity for x in self._bunches])/self._dt

    @property
    def bunch_weight(self):
        """(kg_DM/bunch)"""
        if self.bunch_count == 0:
            return 0
        else:
            N = self.bunch_count

            # harvestible mass --- every dt days
            total_mass = sum([x.mass*x.multiplicity for x in self._bunches])

            if N > 0:
                return total_mass/(N*self._dt)
            else:
                return 0

    # @property
    # def bunch_weight_fresh(self):
    #     ratio = self.parameters['bunch_FM_to_DM_ratio']['value']
    #     return ratio*self.bunch_weight

    ##################
    # Abortion details
    ##################

    @property
    def inflorescence_abortion_fraction(self):
        """ The mean of the non-zero values for the female cohorts (1). """
 
        N = len(self._females)
        if N > 0:
            values = [x.inflorescence_abortion_fraction for x in self._females]
            nzvalues = [x for x in values if x > 0]
            M = len(nzvalues)
            if M > 0:
                return sum(nzvalues)/M
            else:
                return 0
        else:
            return 0

    @property
    def bunch_failure_fraction(self):
        """ The mean of the non-zero values for the female cohorts (1). """

        N = len(self._females)
        if N > 0:
            values = [x.bunch_failure_fraction for x in self._females]
            nzvalues = [x for x in values if x > 0]
            M = len(nzvalues)
            if M > 0:
                return sum(nzvalues)/M
            else:
                return 0
        else:
            return 0

    ######################
    # Assimilation details
    ######################

    # @property
    # def assim_growth_females(self):
    #     """ Assimilates for growth (kg_CH2O/cohort/day). """
    #     return sum([x.assim_growth_cohort for x in self._females])

    # @property
    # def assim_growth_males(self):
    #     """ Assimilates for growth (kg_CH2O/cohort/day). """
    #     return sum([x.assim_growth_cohort for x in self._males])

    # @property
    # def assim_growth_indeterminates(self):
    #     """ Assimilates for growth (kg_CH2O/cohort/day). """
    #     return sum([x.assim_growth_cohort for x in self._indeterminates])

    #################
    # Fraction female
    #################
    @property
    def _female_fraction(self):
        """ The female fraction at sex determination (1). """

        t = self._DAP/365

        k = self.parameters['female_fraction_k']['value']
        t0 = self.parameters['female_fraction_t0']['value']
        va = self.parameters['female_fraction_vasym']['value']

        # a decreasing sigmoid

        return (1-va)*1/(1 + np.exp(k*(t-t0))) + va

    @property
    def female_fraction(self):
        """ The female fraction at sex determination (1). """

        coeff = self.parameters['soil_moisture_specific_female_fraction_decrease']['value']
        threshold = self.parameters['female_fraction_decrease_threshold']['value']
        driver = self._soil_moisture_content

        modifier = 1-coeff*max(0,threshold-driver)

        minimum = self.parameters['female_fraction_minimum']['value']

        return self._female_fraction #min(max(minimum,modifier*self._female_fraction),1)

    #############
    # New cohorts
    #############
    def calc_onset_multiplicity(self, MAP, steepness=.5):
        """ Helps model the on-set of inflorescence growth. """
        t0 = self.parameters['onset_time']['value']
        return sigmoid(MAP,t0,steepness)

    @property
    def onset_multiplicity_factor(self):
        """ Helps model the on-set of inflorescence growth (1). """
        MAP = self._MAP
        steepness = self.parameters['onset_steepness']['value']
        return self.calc_onset_multiplicity(MAP, steepness = steepness)

    @property
    def initiation_rate(self):
        """ New indeterminate cohorts (1/ha/day). """
        if self._palm is None:
            return self._initiation_rate
        else:
            return self.frond_initiation_rate*self._planting_density*self.onset_multiplicity_factor

    @property
    def _planting_density(self):
        """ The multiplicity of the cohort at initiation (1). """
        if self._palm is None:
            return 1
        else:
            return self._palm.planting_density

    @property
    def number_of_cohorts(self):
        """ The number of cohorts. """
        return len(self.cohorts)

    @property
    def number_of_inflorescences(self):
        """ The number of inflorescences (1/ha). """
        return sum([x.multiplicity for x in self.cohorts])
