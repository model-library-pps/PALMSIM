import sys

sys.path.append('..')

from palmsim.components.trunk import Trunk

def test_potential_growth_rate_spline():

	o = Trunk()

	epsilon = 10**-6

	xys = o.parameters['potential_growth_rates']['value']
	spline = o._potential_growth_rate_spline

	for xy in xys:
		x,y = xy
		delta = abs(spline.calc(x) - y)
		assert  delta < epsilon

def test_growth_when_supplied_with_no_assim():

	o = Trunk()

	# in tonnes... - sufficient
	o._assim_growth_ = 0

	assert o.mass_growth_rate == 0

def test_growth_when_supplied_with_sufficient_assim():

	o = Trunk()

	# in tonnes... - sufficient
	o._assim_growth_ = 1000

	assert o.mass_growth_rate > 0

def test_plain_update():

	o = Trunk()

	o.update()