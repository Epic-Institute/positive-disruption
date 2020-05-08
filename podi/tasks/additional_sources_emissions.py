#!/usr/bin/env python
import pprint
import re

import pandas as pd

from podi import conf


re_scenarios = re.compile(r"^scenario\d+$")


def get_additional_sources_emissions():
    df = pd.read_excel(
        conf.DATA_DIR / "emissions.xlsx",
        skiprows=1,
        index_col=0,
        usecols=lambda x: x not in ["Unnamed: 9", "scenario1.4"],
    )
    baselines = [column for column in df.columns if "baseline" in column]
    scenario_names = [column for column in df.columns if re_scenarios.match(column)]

    for scenario_name in scenario_names:
        scenario_cols = [
            column for column in df.columns if column.startswith(scenario_name)
        ]
        df["baseline_sums"] = sum(df[baseline] for baseline in baselines)
        df[f"{scenario_name}_sums"] = sum(df[scenario] for scenario in scenario_cols)
        df[f"{scenario_name}_results"] = (
            df["baseline_sums"] - df[f"{scenario_name}_sums"]
        )

    return df


if __name__ == "__main__":
    pprint.pprint(get_additional_sources_emissions())
