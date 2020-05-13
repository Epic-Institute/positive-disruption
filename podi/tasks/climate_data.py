import pandas as pd

from podi import conf


"""TODO: Would be nice to get this working.
def read_climate_data():
    df = pd.read_excel(conf.DATA_DIR / "climate_data.xlsx", header=[2, 3])
    print(df)
    scenarios = []
    for col in df.columns.get_level_values(0):
        if not col.startswith("Unnamed") and col not in scenarios:
            scenarios.append(col)
    # scenarios = list(dict.fromkeys(scenarios))  # Remove duplicates.
    print(scenarios)
    values = []
    for col in df.columns.get_level_values(1):
        if col not in values:
            values.append(col)
    print(values)
    df.columns = df.columns.from_product(
        [scenarios, values], names=["scenario", "value"]
    )
    df = df.set_index(("baseline", "Year"), drop=False)
    df = df.drop("Year", axis=1, level=1)
    return df
"""


def read_climate_data():
    df = pd.read_excel(
        conf.DATA_DIR / "climate_data.xlsx",
        skiprows=3,
        index_col=0,
        usecols=lambda x: not x.startswith("Time."),
    )
    return df
