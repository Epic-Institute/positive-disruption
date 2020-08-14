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

Input Files
=============

The following files, located in podi/data, serve as inputs to the model scripts.


1. afolu.csv
  - Consists of time series of AFOLU data from 2005 to 2100 in 10 year increments.
  - Used in afolu.py to provide data for baseline and pathway projections of AFOLU vector.

2. biofuels.csv
  - Consists of time series of energy consumption data by sector and energy type from 2010 to 2100.
  - Used in energy_demand.py where values are shifted and combined with data on energy efficiency, demand, heat pumps, transport efficiency, and solar thermal.

3. bnef.csv
  - Consists of BNEF data on energy demand and consumption for all countries in a time series from 2012 to 2100.
  - Not currently used in any .py file.

4. cdr.csv
  - Consists of CDR data for baseline and pathway scenarios in time series from 2020 to 2100.
  - Not currently used in model .py files.

5. climate.csv
  - Consists of climate data (CO2 emissions, atm concentration, temp change) in time series from 1900 to 2100.
  - Not currently used in model .py files.

6. electricity.csv
  - Consists of data on electricity generation in time series from 1980 to 2024.
  - Used in energy_supply.py to generate the historical and projected percent of electricity consumption met by given technologies and then to generate projections for the total amount of electricity consumption met by each technology.

7. emissions.csv
  - Consists of data on greenhouse gas emissions in time series from 2010 to 2090.
  - Not currently used in model .py files.

8. emissions_factors.csv
  - Consists of emissions factors for different regions and fuel types in time series from 2010 to 2100.
  - Not currently used in .py files.

9. energy_demand_historical.csv
  - Consists of data on energy demand for different regions and fuels in time series from 2010 to 2040.
  - Used in energy_demand.py where it’s combined with energy_demand_projection.csv and then combined with data on energy efficiency, heat pumps, transport efficiency, solar thermal, and biofuels.

10. energy_demand_projection.csv
  - Consists of data on energy demand for different regions and fuels in time series from 2041 to 2100.
  - Used in energy_demand.py where it’s combined with energy_demand_historical.csv and then combined with data on energy efficiency, heat pumps, transport efficiency, solar thermal, and biofuels.

11. energy_efficiency.csv
  - Consists of data on energy efficiency factors for different regions, sectors, and fuels in time series from 2010 to 2100 for baseline and pathway scenarios.
  - Used in energy_demand.py where it’s combined with data on energy demand, heat pumps, transport efficiency, solar thermal, and biofuels.

12. iea_weo.xlsx
  - Consists of data on energy demand for WEO regions.
  - Used in iea_weo_etl.py where it is transformed into energy_demand_historical.csv.

13. gcam.csv
  - Consists of data on emissions and energy consumption in time series from 2005 to 2100 in ten-year increments.
  - Used in gcam_etl.py, which transforms gcam.csv into appropriate format for use in mode .py files and generates energy_demand_projection_baseline.csv.

14. heat.csv
  - Consists of data on heat generation for buildings and industry by different sources in time series from 2000 to 2015.
  - Used in energy_supply.py to generate projections for heat generation by energy source and sector.

15. heat_pump.csv
  - Consists of data on heat pumps by energy source and sector in time series from 2010 to 2100  for baseline and pathway scenarios.
  - Used in energy_demand.py where it’s combined with data on energy demand, energy efficiency, transport efficiency, solar thermal, and biofuels.

16. metric_categories.csv
  - Consists of table showing relationship between WEO sectors, WEO metrics, and GCAM metrics.
  - Used in gcam_etl.py to index gcam_demand_projections.

17. region_categories.csv
  - Consists of table showing which countries are in which regions (IEA, BNEF, IIASA, R32, CAIT, GCAM).
  - Used in eia_etl.py to set index for electricity_generation.
  - Used in iea_weo_etl.py to create iea_region_list and gcam_region_list used to transform iea_weo.xlsx into energy_demand_historical.csv.

18. socioeconomic.csv
  - Consists of data on GDP, population, and carbon price in time series from 2005 to 2100 in ten-year increments for baseline and pathway scenarios.
  - Used in socioeconomic.py to create data frame socioeconomic.

19. solar_thermal.csv
  - Consists of data on energy generation by different sources and sectors in time series from 2010 to 2100.
  - Used in energy_demand.py where it’s combined with data on energy demand, energy efficiency, transport efficiency, heat pump, and biofuels.

20. transport_efficiency.csv
  - Consists of data on energy demand by different sources and sectors in time series from 2010 to 2100 for baseline and pathways scenarios.
  - Used in energy_demand.py where it’s combined with data on energy demand, energy efficiency, solar thermal, heat pump, and biofuels.


