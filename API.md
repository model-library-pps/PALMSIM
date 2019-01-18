This is a spec of the API of PALMSIM.

Input
-----

Site-specific weather data - determines the simulated growth.
In order of importance of accuracy/model sensitivity:

- daily total short-wave radiation (MJ/m2/day)
- daily rainfall (mm/day)
- avg. daily temperature (deg C)
- avg. daily humidity (%)
- avg. daily windspeed (m/s)

Note, temperature, humidity and windspeed are used to estimate the potential evapotranspiration (using the Penman-Monteith combination equation).
In case these variables are relatively constant (varying within +-%5 of the mean), given the nature of the ET estimation, one might get agreeable model result simply taking them as constants.

Output
------

A spreadsheet with model state/rate variables over time (30 years):

- Bunches:
	 - Bunch yield (t DM/ha/month) - also in FM
	 - Bunch counts (1/ha/month)
	 - Bunch weight (kg DM) - also in FM
- Fronds:
	- Frond mass (kg DM/frond) and (t DM/ha)
	- Frond area (m2/frond) and LAI (-)
	- Frond count (1/palm) and (1/ha)
	- Frond production rate (1/palm/month)
	- Plastochron (days/frond) - related off-course
- Trunk:
	- Trunk mass (kg DM/palm) and (t DM/ha)
- Roots:
	- Root mass (kg DM/palm) and (t DM/ha)
- Soil:
	- Soil moisture content (%)