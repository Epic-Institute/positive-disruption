###################
Positive Disruption
###################

Prerequisites
=============

1. `Python 3.8 <http://www.python.org/>`_
2. `pipenv <https://pipenv.pypa.io/>`_

Installation
============

1. Run ``pipenv install``.

That's it.

Usage
=====

TODO: There's not really any user-facing way to run anything yet.

1. Run ``pipenv shell``.
2. While in the virtual environment you can run scripts.

Developing
==========

1. Run ``pipenv install --dev``.
2. Run ``pipenv shell`` to get into the virtual environment.

Make sure to run tests and linters before committing: ``make all``

TODO: Run linters automatically.


Primer
==========

The model has 7 components:

1. socioeconomic
2. energy_demand
3. energy_supply
4. afolu
5. emissions
6. results_analysis
7. charts

These components are run sequentially through main.py, and are meant to compare two scenarios (a 'baseline' and a 'pathway'). The characteristics of baseline and pathway scenarios are determined by their input .csv/.xlsx data files, and can be changed to explore different scenarios. 

'etl' scripts in the data folder are used to format input datafiles from the format in which they are recieved into a format that can be interpreted by the model.


1. socioeconomic
==========
- Population
- GDP



2. energy_demand
==========
- Takes historical energy demand, projected energy demand, and applies reductions based on measures such as energy efficiency, shift of heat demand to electricity via heat pumps, transport efficiency, shift from fuels to electricity via electric vehicles, solar thermal energy, and biofuels.

3. energy_supply
==========
- Takes energy demand estimates, and estimates the technology mix of energy supply. Historical adoption rates and estimated saturation points are used to fit a logistics curve to future adoption.


4. afolu
==========
- 


5. emissions
==========
- Takes energy supply technology mix and emissions factors to estimate energy emissions. These are added to afolu emissions and additional emissions sources from non-energy processes to arrive at a total emission estimate.


6. results_analysis
==========
- 


7. charts
==========
- Produces charts of results