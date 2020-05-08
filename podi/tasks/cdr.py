import pprint

import pandas as pd

from podi import conf

from . import additional_sources_emissions, emissions_curves


def run_cdr():
    additional_emissions = (
        additional_sources_emissions.get_additional_sources_emissions()
    )
    pprint.pprint(additional_emissions)
    emission_curves = emissions_curves.get_emissions_curves()
    cdr_df = pd.read_excel(conf.DATA_DIR / "cdr.xlsx", index_col=0, usecols=[0, 1])
    cdr_df["baseline emissions [MtCO2e]"] = (
        emission_curves["baseline_sums"] + additional_emissions["baseline_sums"]
    )
    cdr_df["baseline CDR [MtCO2]"] = (
        cdr_df["baseline emissions [MtCO2e]"] - cdr_df["target emissions [MtCO2e]"]
    )

    # Workaround, we only have one scenario in additional_emissions right now.
    emission_curves["scenario_sums"].pop("scenario2")

    for scenario_name, scenario_sums in emission_curves["scenario_sums"].items():
        cdr_df[f"{scenario_name} emissions [MtCO2e]"] = (
            scenario_sums + additional_emissions[f"{scenario_name}_results"]
        )
        cdr_df[f"{scenario_name} CDR [MtCO2]"] = (
            cdr_df[f"{scenario_name} emissions [MtCO2e]"]
            - cdr_df["target emissions [MtCO2e]"]
        )

    pprint.pprint(cdr_df)
