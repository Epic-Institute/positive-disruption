# region

import pandas as pd
import numpy as np

# endregion


def results_analysis(
    scenario,
    energy_output,
    afolu_output,
    emissions_output,
    emissions_output_co2e,
    cdr_output,
    data_start_year,
    data_end_year,
    proj_end_year,
):

    ###############################
    # ADOPTION ANALOGS HISTORICAL #
    ###############################

    # region

    analog = pd.read_csv(
        "podi/data/external/CHATTING_SPLICED.csv",
        usecols=["label", "iso3c", "year", "value"],
    )

    labels = [
        "Combine harvesters - threshers in use",
        "Land agricultural land area 1000 ha",
        "Agricultural tractors in use",
        "Total vehicles (OICA)",
        "Aluminum primary production, in metric tons",
        "Land arable land area 1000 ha",
        "ATMs",
        "Air transport, passengers carried",
        "Civil aviation passenger-KM traveled",
        "Civil aviation ton-KM of cargo carried",
        "Households that subscribe to cable",
        "Cellular subscriptions",
        "Personal computers",
        "Electricity from coal (TWH)",
        "Electric power consumption (KWH)",
        "Electricity from gas (TWH)",
        "Electricity from hydro (TWH)",
        "Electricity from nuclear (TWH)",
        "Electricity from oil (TWH)",
        "Electricity from other renewables (TWH)",
        "Electricity from solar (TWH)",
        "Electricity from wind (TWH)",
        "Gross output of electric energy (TWH)",
        "Electricity Generating Capacity, 1000 kilowatts",
        "Fertilizer ammonium nitrate (AN) agricultural use tonnes",
        "Fertilizer ammonium sulphate agricultural use tonnes",
        "Fertilizer diammonium phosphate (DAP) agricultural use tonnes",
        "Fertilizer potassium chloride (muriate of potash) (MOP) agricultural use tonnes",
        "Fertilizer NPK fertilizers agricultural use tonnes",
        "Fertilizer other NP compounds agricultural use tonnes",
        "Fertilizer superphosphates above 35 percent agricultural use tonnes",
        "Fertilizer potassium sulphate (sulphate of potash) (SOP) agricultural use tonnes",
        "Aggregate kg of fertilizer consumed",
        "Fertilizer urea agricultural use tonnes",
        "Land naturally regenerating forest area 1000 ha",
        "Land planted forest area 1000 ha",
        "People with internet access",
        "Area equipped to provide water to crops",
        "Automatic looms",
        "Ordinary and automatic looms",
        "Items mailed or received",
        "% Arable land share in agricultural land",
        "% Irrigated area as a share of cultivated land",
        "Pesticide fungicides and bactericides agricultural use tonnes",
        "Pesticide herbicides agricultural use tonnes",
        "Pesticide insecticides agricultural use tonnes",
        "Pesticide mineral oils agricultural use tonnes",
        "Pesticide other pesticides nes agricultural use tonnes",
        "Pesticide rodenticides agricultural use tonnes",
        "Total metric tons of pesticides in agricultural use",
        "Radios",
        "Geographical/route lengths of line open at the end of the year",
        "Rail lines (total route-km)",
        "Thousands of passenger journeys by railway",
        "Passenger journeys by railway (passenger-km)",
        "Metric tons of freight carried on railways (excluding livestock and passenger baggage)",
        "Freight carried on railways (excluding livestock and passenger baggage) (ton-km)",
        "Length of Paved Road (km)",
        "Secure internet servers",
        "Ships of all kinds",
        "Tonnage of ships of all kinds",
        "Tonnage of sail ships",
        "Tonnage of steam ships",
        "Tonnage of steam and motor ships",
        "Mule spindles",
        "Ring spindles",
        "Steel demand in thousand metric tons",
        "Steel production in thousand metric tons",
        "Stainless steel production",
        "Telegrams",
        "Fixed telephone subscriptions",
        "Television sets",
        "Weight of artificial fibers in spindles",
        "Weight of other fibers in spindles",
        "Weight of synthetic fibers in spindles",
        "Weight of all fibers in spindles",
        "Passenger car vehicles",
        "Passenger cars (BTS)",
        "Commercial vehicles (bus, taxi)",
        "Commercial vehicles (BTS)",
        "Total vehicles (BTS)",
    ]

    def percent_of_max(x):
        xnew = (
            x.value
            / analog[(analog.label == x.label) & (analog.iso3c == x.iso3c)].value.max()
        ) * 100
        x.value = xnew
        return x

    # define function that calculates cumulative distribution function
    def percent_of_total(x):
        xnew = (
            analog[
                (analog.label == x.label)
                & (analog.iso3c == x.iso3c)
                & (analog.year <= x.year)
            ]
            .sum()
            .value
            / analog[(analog.label == x.label) & (analog.iso3c == x.iso3c)].value.sum()
        ) * 100
        x.value = xnew
        return x

    adoption_analog_output_historical = []

    for unit in ["percent of max", "percent of total", "absolute"]:
        if unit == "percent of max":
            analog_output_temp = analog[
                (analog.iso3c == "USA") & (analog.label.isin(labels))
            ].parallel_apply(percent_of_max, axis=1)
            analog_output_temp["unit"] = unit
        elif unit == "percent of total":
            analog_output_temp = analog[
                (analog.iso3c == "USA") & (analog.label.isin(labels))
            ].parallel_apply(percent_of_total, axis=1)
            analog_output_temp["unit"] = unit
        else:
            analog_output_temp = analog[
                (analog.iso3c == "USA") & (analog.label.isin(labels))
            ]
            analog_output_temp["unit"] = unit

        adoption_analog_output_historical = pd.concat(
            [
                pd.DataFrame(adoption_analog_output_historical),
                pd.DataFrame(analog_output_temp),
            ]
        )

    adoption_analog_output_historical.to_csv(
        "podi/data/adoption_analog_output_historical.csv", index=False
    )

    # endregion

    #########################
    #  ADOPTION HISTORICAL  #
    #########################

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
    adoption_output_historical = (
        pd.concat(
            [
                adoption_historical.loc[:, data_start_year : data_end_year - 1],
                pd.concat(
                    [
                        adoption_historical.loc[:, data_end_year],
                        energy_output.groupby(
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

    adoption_output_historical.to_csv("podi/data/adoption_output_historical.csv")

    # endregion

    #########################
    # ADOPTION PROJECTIONS  #
    #########################

    # region

    # Percent of electric power that is renewables
    electricity = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Electric Power"],
            slice(None),
            slice(None),
            [
                "GEOTHERM",
                "HYDRO",
                "SOLARPV",
                "ROOFTOP",
                "SOLARTH",
                "OFFSHORE",
                "ONSHORE",
                "TIDE",
                "NUCLEAR",
            ],
            ["Electricity output"],
        ]
        .groupby(
            [
                "model",
                "scenario",
                "region",
                "sector",
                "product_long",
            ]
        )
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Electric Power"],
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Electricity output"],
                ]
                .groupby(["model", "scenario", "region"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2]]
            ),
            axis=1,
        )
    )

    # Percent of transport energy that is electric or nonelectric renewables
    transport = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Transportation"],
            slice(None),
            slice(None),
            ["ELECTR", "HYDROGEN"],
            slice(None),
            [
                "Road – 2&3-wheel",
                "Road – Buses&Vans",
                "Road – Light-duty vehicles",
                "Road – Trucks",
                "Rail – Heavy-duty",
                "Rail – Light-duty",
                "Transport not elsewhere specified",
                "Domestic navigation",
                "International marine bunkers",
                "Domestic aviation – Long-range",
                "Domestic aviation – Short-range",
                "International aviation bunkers",
                "Non-energy use in transport",
                "Pipeline transport",
                "Losses",
                "Memo: Non-energy use in transport equipment",
            ],
        ]
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Transportation"],
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                    [
                        "Road – 2&3-wheel",
                        "Road – Buses&Vans",
                        "Road – Light-duty vehicles",
                        "Road – Trucks",
                        "Rail – Heavy-duty",
                        "Rail – Light-duty",
                        "Transport not elsewhere specified",
                        "Domestic navigation",
                        "International marine bunkers",
                        "Domestic aviation – Long-range",
                        "Domestic aviation – Short-range",
                        "International aviation bunkers",
                        "Non-energy use in transport",
                        "Pipeline transport",
                        "Losses",
                        "Memo: Non-energy use in transport equipment",
                    ],
                ]
                .groupby(["model", "scenario", "region"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2]]
            ),
            axis=1,
        )
    )

    # Percent of buildings energy that is electric or nonelectric renewables
    buildings = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Commercial", "Residential"],
            slice(None),
            slice(None),
            ["ELECTR", "SOLARTH", "MUNWASTER", "GEOTHERM"],
            slice(None),
            slice(None),
            ["RESIDENT", "COMMPUB"],
        ]
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Commercial", "Residential"],
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                    slice(None),
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
    )
    buildings = (
        buildings.rename(index={"Commercial": "Buildings", "Residential": "Buildings"})
        .groupby(buildings.index.names)
        .sum()
    )

    # Percent of industry energy that is electric or nonelectric renewables
    industry = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Industrial"],
            slice(None),
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Machinery",
                "Non-ferrous metals",
                "Final consumption not elsewhere specified",
                "Food and tobacco",
                "Agriculture/forestry",
                "Non-metallic minerals",
                "Chemical and petrochemical",
                "Iron and steel",
                "Industry not elsewhere specified",
            ],
        ]
        .groupby(["model", "scenario", "region", "sector", "flow_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Industrial"],
                    slice(None),
                    slice(None),
                    slice(None),
                    "Final consumption",
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
        .sort_values(by=[2050], axis=0)
    )

    industry_other = (
        energy_output.loc[
            slice(None),
            slice(None),
            slice(None),
            ["Industrial"],
            slice(None),
            slice(None),
            ["ELECTR", "SOLARTH", "HYDROGEN", "MUNWASTER", "GEOTHERM"],
            "Final consumption",
            [
                "Paper, pulp, and print",
                "Fishing",
                "Wood and wood products",
                "Transport equipment",
                "Textile and leather",
                "Construction",
                "Mining and quarrying",
            ],
        ]
        .groupby(["model", "scenario", "region", "sector"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                energy_output.loc[
                    slice(None),
                    slice(None),
                    slice(None),
                    ["Industrial"],
                    slice(None),
                    slice(None),
                    slice(None),
                    "Final consumption",
                    slice(None),
                ]
                .groupby(["model", "scenario", "region", "sector"])
                .sum()
                .loc[x.name[0], x.name[1], x.name[2], x.name[3]]
            ),
            axis=1,
        )
        .sort_values(by=[2050], axis=0)
    )

    industry_other = pd.concat(
        [industry_other], keys=["Other"], names=["flow_long"]
    ).reorder_levels(["model", "scenario", "region", "sector", "flow_long"])

    industry = pd.concat([industry, industry_other])

    # Percent of agriculture mitigation compared to max extent
    agriculture = (
        afolu_output.loc[slice(None), slice(None), slice(None), ["Agriculture"]]
        .groupby(["model", "scenario", "region", "sector", "product_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                afolu_output.loc[slice(None), slice(None), slice(None), ["Agriculture"]]
                .groupby(["model", "scenario", "region", "sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ).fillna(0),
            axis=1,
        )
    )

    # Percent of forests & wetlands mitigation compared to max extent
    forestswetlands = (
        afolu_output.loc[slice(None), slice(None), slice(None), ["Forests & Wetlands"]]
        .groupby(["model", "scenario", "region", "sector", "product_long"])
        .sum()
        .parallel_apply(
            lambda x: x.divide(
                afolu_output.loc[
                    slice(None), slice(None), slice(None), ["Forests & Wetlands"]
                ]
                .groupby(["model", "scenario", "region", "sector", "product_long"])
                .sum()
                .loc[x.name]
                .max()
            ).fillna(0),
            axis=1,
        )
    )

    # Combine all verticals
    adoption_output_projections = pd.concat(
        [electricity, transport, buildings, industry, agriculture, forestswetlands]
    ).multiply(100)

    adoption_output_projections["unit"] = "% Adoption"
    adoption_output_projections.set_index("unit", append=True, inplace=True)

    adoption_output_projections.to_csv("podi/data/adoption_output_projections.csv")

    # endregion

    ####################
    # EMISSIONS WEDGES #
    ####################

    # region
    emissions_wedges = (
        emissions_output_co2e[
            (emissions_output_co2e.reset_index().scenario == "baseline").values
        ]
        .rename(index={"baseline": scenario}, level=1)
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
                "flow_short",
                "unit",
            ]
        )
        .sum()
        .subtract(
            emissions_output_co2e[
                (emissions_output_co2e.reset_index().scenario == scenario).values
            ]
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
                    "flow_short",
                    "unit",
                ]
            )
            .sum()
        )
    )

    # Add flow_long back into index
    emissions_wedges = emissions_wedges.reset_index()
    emissions_wedges["flow_long"] = "CO2e"

    emissions_wedges = emissions_wedges.set_index(
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

    emissions_wedges.to_csv("podi/data/emissions_wedges.csv")

    # endregion

    #########################################
    #  LOAD & COMPARE TO MODELED EMISSIONS  #
    #########################################

    # region

    # Load historical emissions data from ClimateTRACE
    emissions_historical = pd.concat(
        [
            pd.read_csv(
                "podi/data/ClimateTRACE/climatetrace_emissions_by_subsector_timeseries_interval_year_since_2015_to_2020.csv",
                usecols=["Tonnes Co2e", "country", "sector", "subsector", "start"],
            ),
            pd.read_csv(
                "podi/data/ClimateTRACE/climatetrace_emissions_by_subsector_timeseries_sector_forests_since_2015_to_2020_interval_year.csv",
                usecols=["Tonnes Co2e", "country", "sector", "subsector", "start"],
            ),
        ]
    )

    # Change ISO region names to IEA
    regions = (
        pd.DataFrame(
            pd.read_csv(
                "podi/data/region_categories.csv",
                usecols=["WEB Region", "ISO"],
            ).dropna(axis=0)
        )
        .set_index(["ISO"])
        .rename_axis(index={"ISO": "country"})
    )
    regions["WEB Region"] = (regions["WEB Region"]).str.lower()

    # Add model, scenario, and flow_category indices
    emissions_historical["model"] = "PD22"
    emissions_historical["scenario"] = "baseline"
    emissions_historical["product_category"] = "Emissions"
    emissions_historical["product_short"] = "EM"
    emissions_historical["flow_category"] = "Emissions"
    emissions_historical["flow_long"] = "Emissions"
    emissions_historical["flow_short"] = "EM"
    emissions_historical["unit"] = "MtCO2e"

    # Change unit from t to Mt
    emissions_historical["Tonnes Co2e"] = emissions_historical["Tonnes Co2e"].divide(
        1e6
    )

    # Change 'sector' index to 'product_long' and 'subsector' to 'flow_long' and
    # 'start' to 'year'
    emissions_historical.rename(
        columns={"Tonnes Co2e": "value", "subsector": "product_long", "start": "year"},
        inplace=True,
    )

    # Change 'year' format
    emissions_historical["year"] = (
        emissions_historical["year"].str.split("-", expand=True)[0].values.astype(int)
    )

    # Update Sector index
    def addsector4(x):
        if x["sector"] in ["power"]:
            return "Electric Power"
        elif x["sector"] in ["transport", "maritime"]:
            return "Transportation"
        elif x["sector"] in ["buildings"]:
            return "Buildings"
        elif x["sector"] in ["extraction", "manufacturing", "oil and gas", "waste"]:
            return "Industrial"
        elif x["sector"] in ["agriculture"]:
            return "Agriculture"
        elif x["sector"] in ["forests"]:
            return "Forests & Wetlands"

    emissions_historical["sector"] = emissions_historical.parallel_apply(
        lambda x: addsector4(x), axis=1
    )

    emissions_historical = (
        (
            emissions_historical.reset_index()
            .set_index(["country"])
            .merge(regions, on=["country"])
        )
        .reset_index()
        .set_index(
            [
                "model",
                "scenario",
                "WEB Region",
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
        .rename_axis(index={"WEB Region": "region"})
    ).drop(columns=["country", "index"])

    # Pivot from long to wide
    emissions_historical = emissions_historical.reset_index().pivot(
        index=[
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
        ],
        columns="year",
        values="value",
    )

    # Select data between data_start_year and data_end_year
    emissions_historical.columns = emissions_historical.columns.astype(int)
    emissions_historical = emissions_historical.loc[:, data_start_year:data_end_year]

    # Match modeled (emissions_output_co2e) and observed emissions
    # (emissions_historical) categories across 'model', 'region', 'sector'

    emissions_output_co2e_compare = (
        emissions_output_co2e.rename(
            index={"Residential": "Buildings", "Commercial": "Buildings"}
        )
        .groupby(["model", "region", "sector"])
        .sum()
    )
    emissions_historical_compare = emissions_historical.groupby(
        ["model", "region", "sector"]
    ).sum()

    # Calculate error between modeled and observed
    emissions_error = abs(
        (
            emissions_historical_compare
            - emissions_output_co2e_compare.loc[:, emissions_historical_compare.columns]
        )
        / emissions_historical_compare.loc[:, emissions_historical_compare.columns]
    )

    # Drop observed emissions that are all zero
    emissions_error.replace([np.inf, -np.inf], np.nan, inplace=True)
    emissions_error.dropna(how="all", inplace=True)

    # endregion

    ##############################################
    #  CALCULATE CUMULATIVE EMISSIONS MITIGATED  #
    ##############################################

    # region

    # Calculate cumulative emissions mitigated by 2030
    emissions_output_co2e.loc[:, emissions_output_co2e.columns <= 2030].cumsum(axis=1)

    # Calculate cumulative emissions mitigated by 2050
    emissions_output_co2e.loc[:, emissions_output_co2e.columns <= 2050].cumsum(axis=1)
    

    # endregion

    return
