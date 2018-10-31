
import sys
sys.path.append('..')
from palmsim import PalmField

pf = PalmField()

res = {}
for i in range(120):
    pf.update()
    res[i] = pf.to_dict()

import pandas as pd

df = pd.DataFrame(res).T

cs = pf.organs.females

infl = cs[2]

fs = '{:<60} {:10.4f} {:}'

print(fs.format('pf.assimilates.assim_growth_generative',
                         pf.assimilates.assim_growth_generative,
                        't/mo'))

print(fs.format('pf.organs.assim_growth',pf.organs.assim_growth,'t/mo'))
print(fs.format('sum([c.assim_growth_cohort for c in pf.organs.cohorts])',
                sum([c.assim_growth_cohort for c in pf.organs.cohorts]),
                'kg/mo'))

print(fs.format('infl.assim_growth_cohort',infl.assim_growth_cohort, 'kg/mo'))

print(fs.format('infl.multiplicity',infl.multiplicity,''))

print(fs.format('infl.assim_growth_organ', infl.assim_growth_organ, 'kg/mo'))
print(fs.format('infl.multiplicity * infl.assim_growth_organ',infl.multiplicity * infl.assim_growth_organ,'kg/mo'))

print(fs.format('sum([c.assim_growth for c in infl.components]',
                sum([c.assim_growth for c in infl.components]), 'kg/mo'))
