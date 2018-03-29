import matplotlib.pyplot as plt

import matplotlib
matplotlib.style.use('seaborn-colorblind')
matplotlib.rc('font',family='Times New Roman')

class Plotter():

        default_recipe = '''
        *weather_PAR_monthly

        *soil_critical_deficit_exceedance
        *soil_available_water_change

        ++mass_total
        +trunk_mass
        +roots_mass
        +fronds_mass
        +female_mass_total
        +male_mass_total

        ++assim_growth_total
        +assim_growth_trunk
        +assim_growth_roots
        +assim_growth_fronds
        +assim_growth_female
        +assim_growth_male

        assim_growth_trunk
        assim_growth_roots
        assim_growth_fronds
        assim_growth_female
        assim_growth_male

        ++assim_maintenance_total
        +assim_maintenance_trunk
        +assim_maintenance_roots
        +assim_maintenance_fronds
        +assim_maintenance_female
        +assim_maintenance_male

        assim_maintenance_total
        assim_maintenance_trunk
        assim_maintenance_roots
        assim_maintenance_fronds
        assim_maintenance_female
        assim_maintenance_male

        female_harvest
        male_harvest

        ++assim_produced
        +assim_maintenance_total
        +assim_growth_total

        *fronds_mass
        *management_goal_mass_fronds

        *indeterminate_female_fraction

        *indeterminate_new_organs

        *female_abortion_fraction_month_00
        *female_abortion_fraction_month_03
        *female_abortion_fraction_month_06
        *female_abortion_fraction_month_09
        *female_abortion_fraction_month_12

        *female_mass_month_03
        *female_mass_month_06
        *female_mass_month_09
        *female_mass_month_12
        *female_mass_month_15
        *female_mass_month_18
        *female_mass_month_21
        '''

        def __init__(self,df,units=None):

            self.df = df
            self.units = units
            self.recipe = self.default_recipe
            self.xlim = None

        def show(self):
            df = self.df
            recipes = get_subrecipes(self.recipe)

            units = self.units

            f,axes = plt.subplots(len(recipes),1,figsize=(12,2*len(recipes)))

            for recipe,ax in zip(recipes,axes):

                columns = recipe['columns']
                unit = units[columns[0]]

                if recipe['how'] == 'stacked':
                    df[columns].plot.area(ax=ax,).legend(loc='center left', bbox_to_anchor=(1, 0.5))
                elif recipe['how'] == 'line':
                    df[columns].plot.line(ax=ax,).legend(loc='center left', bbox_to_anchor=(1, 0.5))
                elif recipe['how'] == 'stacknormalized':
                    norm = df[recipe['normalizer']]
                    (df[columns].divide(norm,axis=0)).plot.area(ax=ax,).legend(loc='center left', bbox_to_anchor=(1, 0.5))
                    unit = '1'
                else:
                    pass

                if units is None:
                    pass
                else:
                    ax.set_ylabel(unit)

                if self.xlim is None:
                    pass
                else:
                    ax.set_xlim(self.xlim)

            plt.tight_layout()

def get_subrecipes(source):
    ''' A plotting micro-language interpreter.

    In case we want to plot multiple variables
    per axes and use either stacked/line plots.

    Examples
    --------
    recipe:

    a

    *b
    *c

    ->

    -{how: stacked,columns:[a]}
    -{how: line,columns:[b,c]}

    '''

    def Recipe(how='stacked'):
        return dict(how=how,columns=[])

    recipes = []

    instructions = source.strip().split('\n')

    recipe = Recipe()

    for instruction in instructions:
        instruction = instruction.strip()
        if instruction == '':
            recipes.append(recipe)
            recipe = Recipe()
        elif instruction.startswith('*'):
            recipe['how'] = 'line'
            recipe['columns'] += [instruction[1:]]
        elif instruction.startswith('++'):
            recipe['how'] = 'stacknormalized'
            recipe['normalizer'] = instruction[2:]
        elif instruction.startswith('+'):
            recipe['columns'] += [instruction[1:]]
        else:
            recipe['how'] = 'stacked'
            recipe['columns'] += [instruction]

    recipes.append(recipe)
    return recipes

def cook_recipe(recipe):
    recipes = get_subrecipes(recipe)
    f,axes = plt.subplots(len(recipes),1,figsize=(12,2*len(recipes)))
    print(12,2*len(recipes))
    for recipe,ax in zip(recipes,axes):

        columns = recipe['columns']

        if recipe['how'] == 'stacked':
            df[columns].plot.area(ax=ax,).legend(loc='center left', bbox_to_anchor=(1, 0.5))
        elif recipe['how'] == 'line':
            df[columns].plot.line(ax=ax,).legend(loc='center left', bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
