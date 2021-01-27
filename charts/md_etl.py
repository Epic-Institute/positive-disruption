#!/usr/bin/env python

from mdutils.mdutils import MdUtils
from mdutils.tools.Table import Table
from mdutils import Html
from podi.energy_demand import iea_region_list

for i in range(0, len(iea_region_list)):
    mdFile = MdUtils(file_name=iea_region_list[i] + ".md")

    mdFile.new_header(level=1, title="[Region]")
    mdFile.new_line()

    mdFile.new_line()

    text_list = [
        "Vector",
        "Adoption Metric",
        "Grid",
        "TFC met by renewables",
        "Transport",
        "Transport TFC met by electricity and renewables",
        "Buildings",
        "Buildings TFC met by electricity & renewable heat",
        "Industry",
        "Industry TFC met by electricity & renewable heat",
        "Regenerative Agriculture",
        "Mha under Regenerative Agriculture",
        "Forests and Wetlands",
        "Mha of at-risk Forests/Wetlands preserved",
        "CDR",
        "GtCO2 removed via CDR",
    ]

    mdFile.new_table(columns=2, rows=8, text=text_list, text_align="center")

    mdFile.new_line()
    mdFile.new_header(level=3, title="Adoption Curves")

    mdFile.new_line()
    mdFile.new_header(level=3, title="Energy Supply and Demand")

    mdFile.new_line()
    mdFile.new_header(level=3, title="Emissions")

    mdfile.create_md_file()
