#!/usr/bin/env python

# region

import pandas as pd

# endregion


def results_analysis(
    energy_output,
    afolu_output,
    emissions_output,
    cdr_output,
    climate_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ##############
    #  ADOPTION  #
    ##############

    # region

    # Load historical adoption data
    index = [
        "model",
        "scenario",
        "region",
        "sector",
        "product_category",
        "product_long",
        "product_short",
        "flow_category",
        "flow_long",
        "flow_short",
        "unit",
    ]

    adoption_historical = (
        pd.DataFrame(pd.read_csv("podi/data/adoption_historical.csv"))
        .set_index(index)
        .dropna(axis=0, how="all")
    )
    adoption_historical.columns = adoption_historical.columns.astype(int)

    # Project future growth based on percentage growth of energy demand
    adoption_output = (
        pd.concat(
            [
                adoption_historical.loc[:, data_start_year : data_end_year - 1],
                pd.concat(
                    [
                        adoption_historical.loc[:, data_end_year],
                        energy_output.droplevel(["hydrogen", "flexible", "nonenergy"])
                        .groupby(
                            [
                                "model",
                                "scenario",
                                "region",
                                "sector",
                                "product_category",
                                "product_long",
                                "product_short",
                                "flow_category",
                                "flow_long",
                                "flow_short",
                                "unit",
                            ]
                        )
                        .sum()
                        .loc[:, data_end_year:]
                        .pct_change(axis=1)
                        .dropna(axis=1, how="all")
                        .add(1)
                        .clip(upper=2),
                    ],
                    axis=1,
                ).cumprod(axis=1),
            ],
            axis=1,
        )
        .replace(np.inf, 0)
        .replace(-np.inf, 0)
    )

    # endregion

    ########
    # NDCs #
    ########

    # region

    em_mit_ndc = []

    for i in range(0, len(region_list)):
        if region_list[i] in [
            "World ",
            "US ",
            "EUR ",
            "SAFR ",
            "RUS ",
            "JPN ",
            "CHINA ",
            "BRAZIL ",
            "INDIA ",
        ]:
            em_ndc = (
                pd.read_csv("podi/data/emissions_ndcs.csv")
                .set_index(["region"])
                .loc[region_list[i]]
            )

            em_ndc = pd.DataFrame(
                (
                    em_baseline.loc[region_list[i]].sum().loc[[2025, 2030, 2050]] / 1000
                ).values
                - (em_ndc).values
            ).rename(index={0: 2025, 1: 2030, 2: 2050}, columns={0: "em_mit"})

            em_ndc["region"] = region_list[i]
        else:
            em_ndc = []

        em_mit_ndc = pd.DataFrame(em_mit_ndc).append(em_ndc)

    # endregion

    #################
    #  SAVE OUTPUT  #
    #################

    # region

    adoption_output.to_csv("podi/data/adoption_output.csv")

    analysis_output.to_csv("podi/data/analysis_output.csv")

    # endregion

    return
