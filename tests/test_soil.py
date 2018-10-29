import sys

sys.path.append('..')

from palmsim.components.soil import Soil

def test_equilibrium_if_ET_equals_RF():

	o = Soil()

	ET = o.evapotranspiration

	o._rainfall_ = ET

	assert o.available_water_change_rate == 0

def test_water_gain_if_much_rain():

	o = Soil()

	o._rainfall_ = 400

	assert o.available_water_change_rate > 0

def test_water_loss_if_no_rain():

	o = Soil()

	o._rainfall_ = 0

	assert o.available_water_change_rate < 0