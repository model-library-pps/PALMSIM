import sys

sys.path.append('..')

from palmsim.components.weather import Weather

w = Weather()

def test_default_rainfall_mean():
	assert w.rainfall_series_mean == w._rainfall_series_mean_

def test_default_radiation_mean():
	assert w.radiation_series_mean == w._radiation_series_mean_

def test_default_raindays_mean():
	assert w.raindays_series_mean == w._raindays_series_mean_