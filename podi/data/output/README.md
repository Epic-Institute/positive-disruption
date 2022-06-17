# Files

afolu_output: AFOLU results, in units of land area (Mha) and tree volume (m3)

emissions_output: All emissions from energy, AFOLU, and additional sources. Units are Mt of the gas listed in flow_long (and if flow_long does not list a gas, it's CO2) 

emissions_output_co2e: Same as emissions_output, but all values have been converted to units CO2e

emissions_wedges: emissions_output_co2e 'baseline' results subtracted from emissions_output_co2e 'pathway' results. This represents the difference in emissions for each region/product/flow.

energy_ouput: energy results, in units TJ