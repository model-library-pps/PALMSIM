
import sys

sys.path.append('..')

from palmsim import PalmField

filepath = 'results/units.txt'

pf = PalmField()

lines = []

missingUnits = []

for submodel in pf.components:

	p = submodel._prefix

	mlines = submodel.__repr__().splitlines()

	vs = [x for x in dir(submodel) if not x.startswith('_') and isinstance(getattr(submodel,x), float)]

	for k in vs:

		if k not in submodel.units:
			missingUnits.append('\t- {:} {:}'.format(p,k))

		else:

			u = submodel.units[k]

			if '?' in u:
				missingUnits.append('\t- {:} {:}'.format(p,k))


	lines.append('')
	lines.extend(mlines)

uLines = missingUnits

olines = []
olines.append('Has no units:')
olines.extend(['\t'+x for x in uLines])
olines.extend(lines)

text = '\n'.join(olines)

with open(filepath, 'w') as f:
	f.write(text)