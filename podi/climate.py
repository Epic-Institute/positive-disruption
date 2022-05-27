#!/usr/bin/env python

import pandas as pd


def climate(emissions_output, data_start_year, proj_end_year):

    # Gases that FAIR climate model takes as input, with associated units
    fair_input_gases = {
        "CO2-fossil": "GtC/yr",
        "CO2-landuse": "GtC/yr",
        "CH4": "Mt/yr",
        "N2O": "MtN2/yr",
        "SOx": "MtS/yr",
        "CO": "Mt/yr",
        "NMVOC": "Mt/yr",
        "NOx": "MtN/yr",
        "BC": "Mt/yr",
        "OC": "Mt/yr",
        "NH3": "Mt/yr",
        "CF4": "kt/yr",
        "C2F6": "kt/yr",
        "C6F14": "kt/yr",
        "HFC23": "kt/yr",
        "HFC32": "kt/yr",
        "HFC43-10": "kt/yr",
        "HFC125": "kt/yr",
        "HFC134a": "kt/yr",
        "HFC143a": "kt/yr",
        "HFC227ea": "kt/yr",
        "HFC245fa": "kt/yr",
        "SF6": "kt/yr",
        "CFC11": "kt/yr",
        "CFC12": "kt/yr",
        "CFC113": "kt/yr",
        "CFC114": "kt/yr",
        "CFC115": "kt/yr",
        "CCl4": "kt/yr",
        "Methyl chloroform": "kt/yr",
        "HCFC22": "kt/yr",
        "HCFC141b": "kt/yr",
        "HCFC142b": "kt/yr",
        "Halon 1211": "kt/yr",
        "Halon 1202": "kt/yr",
        "Halon 1301": "kt/yr",
        "Halon 2401": "kt/yr",
        "CH3Br": "kt/yr",
        "CH3Cl": "kt/yr",
    }

    # Align gas names that are different between FAIR and emissions_output
    # SO2 to SOx

    # Drop dashes
    for gas in [
        "HFC-23",
        "HFC-32",
        "HFC-125",
        "HFC-134a",
        "HFC-143a",
        "HFC-227ea",
        "HFC-245fa",
        "HCFC-141b",
        "HCFC142b",
    ]:
        gas = gas.replace("-", "")
        return gas

    #'HFC-43-10-mee' to 'HFC43-10'

    # Add 'CFC11', 'CFC12', 'CFC113', 'CFC114', 'CFC115', 'CCl4', 'Methyl chloroform', 'HCFC22', 'Halon 1211', 'Halon 1202', 'Halon 1301', 'Halon 2401', 'CH3Br', 'CH3Cl'

    # Drop 'Electricity output' and 'Heat output' to avoid double counting when summing emissions
    emissions_output = emissions_output[
        ~(
            emissions_output.reset_index().flow_category.isin(
                ["Electricity output", "Heat output"]
            )
        ).values
    ]

    return
