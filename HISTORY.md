
History
=======



2.3.4a (2018-11-13)
-------------------

**Improvements**

- HISTORY.md -- the dates might be a bit off (+- 1 month) before March 2018.
- An API spec file API.md

2.3.3a (2018-10-01)
-------------------

**Improvements**

- added an example jupyter notebook on biomass production
- made sure examples 1--7 are up-to-date and run
- started to actively use versioning

2.3.2a (2018-10-31)
----------------

**Improvements**

- refactored the generative sub-module (one file) into a package (multiple files)
- bunch phenology parametrization: start (mo after initiation) and duration of abortion sensitive phases instead of start and stop
- prototype of a calibration tool: knobs and sliders for humans to try and calibrate the model

2.3.1a (2018-03):
-----------------

**Testing**

- Compared predicted vs observed bunch counts for Ghana (2013--2016)
- Overall quite agreeable however
	- N = 1
	- only bunch counts --- bunch weights were off

**Improvements**

- model decrease of evapotranspiration with water stress (sigmoid of stress)
- model decrease of assimilation with water stress (linear via WUE)
- water-stress modelled via soil moisture content (-) instead of soil water deficit (mm)

2.3.0a (2018-02):
-----------------

**Improvements**

Water-stress effects:

- Water-stress (proxy: soil water deficit) decreases the
	- female:male ratio
	- inflorescence "survival" (abortion phase before anthesis)
	- bunch "survival" (abortion phase after anthesis)

2.2.0a (2018-01)
----------------

**Testing**

 - Sensibility test of growth/mass of components: passed for potential production

**Improvements**

- Switch to using relative sink strength to partition assimilates instead of fixed partitioning (trunk catastrophe - kept on growing in v1.0)
- Inflorescences modelled via "bunch components" each having a potential sink strength that changes over time (phenology):
	- stalks
	- mesocarp fibers
	- mesocarp oil
	- kernels

**Bugfixes**

Fixed on-set of bunch growth:

- in previous versions the growth of the first bunches was very unrealistic due to a combination of fixed assimilate partitioning and little maintenance demand: first bunches would "explode" and their maintenance demand would "crash" the palm - see the glitches in the bunch production in A.C. Vera's report.
- fixed by smoothening the bunch production transition from zero inflorescences to N --- using a logistic function.

2.1.0a (2017-12)
--------------

**Improvements**

- Changed the estimate of leaf area from SLA based to YAP based (Gerritsma and Soebagyo, 1998): more accurate.
- Changed the modelling of pruning: via frond count instead of via standing mass.

2.0.0a (2017-11)
-------------------

- Re-implemented PALMSIM: MatLab -> Python
- Direct port - exactly the same behaviour as 1.0

**Improvements**

- Added basic documentation of parameters and model variables (units, references)

1.0b (2014)
----------

- Presumably minor changes by M. Hoffman
- Paper by M. Hoffman and others: Model description, evaluation and application
- Available online (PPS models portal)

pre-1.0 (2010)
---------------

- Conception by A. C. Vera
- MatLab
- functional programming style --- basically a big script

pre-0.1 (2009)
--------------

Media attention:
	- bio-fuels
	- OP
	- perennials
	- rainforts
