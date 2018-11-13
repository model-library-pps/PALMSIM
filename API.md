This is a spec of the API of PALMSIM.

Input
-----

Weather variables which determine the simulated growth:

- solar radiation (MJ/m2/day)
- rainfall (mm/month)
- rainday (mm/month)

Output
------

A spreadsheet with all sort of model state/rate variables. Most importantly, per topic:

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