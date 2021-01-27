#!/usr/bin/env python

from mdutils.mdutils import MdUtils
from mdutils.tools.Table import Table
from mdutils import Html
from podi.energy_demand import iea_region_list

for i in range(0, len(iea_region_list)):
    mdFile = MdUtils(file_name=iea_region_list[i] + "test.md")

    mdFile.new_header(level=1, title=iea_region_list[i])

    mdFile.new_line()

    mdFile.new_header(level=2, title="Adoption Curves")

    mdFile.insert_code(
        '<iframe id="igraph" scrolling="no" style="border:none" seamless="seamless" src= "demand-baseline-" + iea_region_list[i].replace(" ","") + ".html" height="500" width="150%"></iframe>',
        language="python",
    )

    path = ("demand-pathway-" + (iea_region_list[i]).replace(" ", "") + ".html",)

    mdFile.new_paragraph(
        Html.image(
            path=path,
        )
    )

    mdFile.new_line()
    mdFile.new_header(level=2, title="Energy Supply and Demand")

    mdFile.new_line()
    mdFile.new_header(level=2, title="Emissions")

    mdFile.create_md_file()
