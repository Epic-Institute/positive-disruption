# Model Overview

The Positive Disruption model has 6 main components:

1. energy_demand
2. energy_supply
3. afolu
4. emissions
5. results_analysis
6. charts

These components are run sequentially through main.py, and are meant to compare two scenarios (a 'baseline' and a 'pathway'). The characteristics of baseline and pathway scenarios are determined by their input .csv/.xlsx data files, and can be changed to explore different scenarios. 

'etl' scripts in the data folder are used to format input datafiles from the format in which they are recieved into a format that can be interpreted by the model.


1. energy_demand

  Takes historical energy demand, projected energy demand, and applies reductions based on measures such as energy efficiency, shift of heat demand to electricity via heat pumps, transport efficiency, shift from fuels to electricity via electric vehicles, solar thermal energy, and biofuels.

2. energy_supply

  Takes energy demand estimates, and estimates the technology mix of energy supply. Historical adoption rates and estimated saturation points are used to fit a logistics curve to future adoption.


3. afolu

  Takes historical emissions from agriculture and land use sectors, and subtracts from this the estimated mitigation from adoption of new technologies and practices in the AFOLU sector.


4. emissions

  Takes energy supply technology mix and emissions factors to estimate energy emissions. These are added to afolu emissions and additional emissions sources from non-energy processes to arrive at a total emission estimate.


5. results_analysis

  Estimates adoption rates for each vector and subvector.


7. charts

  Produces charts of results.


<br/><br/>


# Input Files

iamc_data.csv is required to run the model, it can be downloaded [here](https://drive.google.com/file/d/1YxMrXCssIwUmpR-YkA559x03yo2qDywf/view?usp=sharing). Place the file in podi/data


# Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
       ├── __init__.py    <- Makes src a Python module
       │
       ├── data           <- Scripts to download or generate data
       │   └── make_dataset.py
       │
       ├── features       <- Scripts to turn raw data into features for modeling
       │   └── build_features.py
       │
       ├── models         <- Scripts to train models and then use trained models to make
       │   │                 predictions
       │   ├── predict_model.py
       │   └── train_model.py
       │
       └── visualization  <- Scripts to create exploratory and results oriented visualizations
          └── visualize.py   
<p></p>
