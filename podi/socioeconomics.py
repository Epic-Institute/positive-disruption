#!/usr/bin/env python

from podi.data import etl


def socioeconomics(scenario, data_source):
    socio = etl.etl(data_source)

    pop = socio.loc[slice(None), slice(None), "Population", scenario]

    gdp = socio.loc[slice(None), slice(None), "GDP | MER", scenario]

    return pop, gdp
