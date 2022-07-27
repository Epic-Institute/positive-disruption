# Model Workflow
```mermaid
graph LR
   A[Configuration files]--> G[main.py]
   B[Historical Data] --> G
   G --> I[Output files]
   I-->J[Output dataviz]
   I-->O[Data Explorer]
```

# Electricity Flow Chart

```mermaid
graph LR
   A[Combustible Fuels]--> G[Gross Production]
   B[Hydro] --> G
   C[Geothermal]--> G
   D[Nuclear]--> G
   E[Solar]--> G
   F[Tide, Wave or Ocean] --> G
   G --> I[Net Production]
   I-->J[Heat Pumps & Electric Boilers]
   I-->O[Transmission & Distribution Losses]
   I-->M[Total Consumption]
   I-->K[Storage]-->G
   G--> H[Own Use]
```

# Heat Flow Chart

```mermaid
graph LR
    A[Combustible Fuels]--> G[Gross Production]
    B[Nuclear] --> G
    C[Geothermal]--> G
    E[Solar]--> G
    F[Electric Boilers] --> G
    Z[Heat Pumps] --> G
    Other[Other] --> G
    G --> I[Net Production]
    I-->O[Transmission & Distribution Losses]
    I-->M[Total Consumption]
    I-->K[Storage]-->G
    G--> H[Own Use]
```

# Project Organization

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data`
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
