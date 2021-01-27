#!/usr/bin/env python

from mdutils.mdutils import MdUtils
from mdutils.tools.Table import Table
from mdutils import Html
from podi.energy_demand import iea_region_list

for i in range(0, len(iea_region_list)):
    mdFile = MdUtils(file_name=iea_region_list[i] + ".md")

    mdFile.new_header(level=1, title=iea_region_list[i])
    mdFile.new_line()

    mdFile.new_header(level=2, title="Adoption Curves")

    # region

    path = '"scurves-' + (iea_region_list[i]).replace(" ", "") + '.html"'

    mdFile.write(
        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
    )
    mdFile.write(path)
    mdFile.write(" height='500' width='150%'></iframe>")

    # endregion

    mdFile.new_line()
    mdFile.new_header(level=2, title="Energy Supply and Demand")

    # region

    for j in ["baseline", "pathway"]:
        for k in ["demand", "supply"]:
            path = (
                '"'
                + k
                + "-"
                + j
                + "-"
                + (iea_region_list[i]).replace(" ", "")
                + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")

            mdFile.new_line()

    # endregion

    mdFile.new_line()
    mdFile.new_header(level=2, title="Emissions")

    # region

    for j in ["baseline", "pathway"]:
        for k in ["mwedges", "em1"]:
            path = (
                '"'
                + k
                + "-"
                + j
                + "-"
                + (iea_region_list[i]).replace(" ", "")
                + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")

            mdFile.new_line()

    # endregion

    mdFile.create_md_file()
