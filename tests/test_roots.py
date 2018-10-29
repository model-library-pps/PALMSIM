import sys

sys.path.append('..')

from palmsim.components.roots import Roots

def test_growth_when_supplied_with_no_assim():

	o = Roots()

	# in tonnes... - sufficient
	o._assim_growth_ = 0

	assert o.mass_growth_rate == 0

def test_growth_when_supplied_with_sufficient_assim():

	o = Roots()

	# in tonnes... - sufficient
	o._assim_growth_ = 1000

	assert o.mass_growth_rate > 0

def test_plain_update():

	o = Roots()

	o.update()