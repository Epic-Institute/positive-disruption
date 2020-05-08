#!/usr/bin/env python
import collections
import pprint

import pandas as pd

from podi import conf


def get_emissions_curves():
    df = pd.read_csv(conf.DATA_DIR / "emissions_curves.csv")
    df = df.set_index(["Subvector", "Scenario", "Year"])
    data = collections.defaultdict(lambda: collections.defaultdict(list))

    for index, row in df.iterrows():
        data[index[0]][index[1]].append(row["Value"])

    baselines = [scenarios.pop("Baseline") for scenarios in data.values()]
    baseline_sums = list(map(sum, zip(*baselines)))

    scenario_values = collections.defaultdict(list)
    for scenarios in data.values():
        for scenario, values in scenarios.items():
            scenario_values[scenario].append(values)

    scenario_sums = {}
    for scenario, values in scenario_values.items():
        scenario_sums[scenario] = list(map(sum, zip(*values)))

    results = collections.defaultdict(list)
    for scenario, sums in scenario_sums.items():
        for baseline_sum, scenario_sum in zip(baseline_sums, sums):
            results[scenario].append(scenario_sum - baseline_sum)

    return {
        "baseline_sums": baseline_sums,
        "scenario_sums": scenario_sums,
        "emissions_mitigated": results,
    }


if __name__ == "__main__":
    pprint.pprint(get_emissions_curves())
