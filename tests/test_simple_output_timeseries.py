
import sys

sys.path.append('..')

import matplotlib.pyplot as plt

import pandas as pd

from palmsim import PalmField

import os

odir = 'results'

to_plot = ['roots_mass_per_palm',
			'trunk_mass_per_palm',
			'fronds_mass_per_frond',
			'generative_bunch_production',
			'generative_bunch_count',
			'generative_bunch_weight']

pf = PalmField()
pf.weather._radiation_series_mean = 18

res = {}

for i in range(360):

	res[i] = pf.to_dict()
	pf.update()

df = pd.DataFrame(res).T

pks = []

for p in to_plot:

	for k in list(df):

		if p in k:
			pks.append((p,k))

for p, k in pks:

	plt.plot(df[k])
	plt.title(k)
	plt.savefig(os.path.join(odir, '{:}.png'.format(p)))
	plt.close()