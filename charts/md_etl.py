from mdutils.mdutils import MdUtils
import pandas as pd

scenario = "pathway"
regions = pd.read_fwf("podi/data/IEA/Regions.txt").rename(columns={"REGION": "Region"})

for scen in ["dau"]:

    for region in regions:

        ###################
        # MAP & COUNTRIES #
        ###################

        # region

        mdFile = MdUtils(
            file_name="md-" + regions[region].replace(" ", "") + "-" + scen + ".md"
        )

        mdFile.new_header(level=1, title=regions[region]).replace(" ", "")
        mdFile.new_line()

        mdFile.write("![](../region%20maps/")
        mdFile.write(regions[region].replace(" ", ""))
        mdFile.write(".png)")

        # mdFile.write(region_dict[regions[region]])

        mdFile.new_line()
        mdFile.new_line()

        # endregion

        ########################
        # ENERGY SUPPLY/DEMAND #
        ########################

        # region
        """
        mdFile.new_line()
        mdFile.new_header(level=2, title="Energy Supply and Demand")

        for j in ["baseline", "pathway"]:
            for k in ["demand", "supply", "supply2"]:
                path = (
                    '"' + k + "-" + j + "-" + (regions[region]).replace(" ", "") + '.html"'
                )

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")
                mdFile.new_line()
        """
        # endregion

        #############
        # EMISSIONS #
        #############

        # region

        mdFile.new_line()
        mdFile.new_header(level=2, title="Emissions")

        for j in ["pathway"]:
            if scen == "dau":
                for k in ["em2"]:
                    path = (
                        '"'
                        + k
                        + "-"
                        + j
                        + "-"
                        + (regions[region]).replace(" ", "")
                        + "-"
                        + scen
                        + '.html"'
                    )
                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")

                    mdFile.new_line()

            """
            for m in ["em3", "em4"]:
                for n in [
                    "Electricity",
                    "Transport",
                    "Buildings",
                    "Industry",
                    "Regenerative Agriculture",
                    "Forests & Wetlands",
                ]:
                    path = (
                        '"'
                        + m
                        + "-"
                        + j
                        + "-"
                        + (regions[region]).replace(" ", "")
                        + "-"
                        + n
                        + '.html"'
                    )
                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")

                    mdFile.new_line()
            """
            if scen == "dau":
                for m in ["emsub"]:
                    for sector in [
                        "Industry",
                        "Regenerative Agriculture",
                        "Forests & Wetlands",
                    ]:
                        path = (
                            '"'
                            + m
                            + "-"
                            + scenario
                            + "-"
                            + (regions[region]).replace(" ", "")
                            + "-"
                            + sector
                            + "-"
                            + scen
                            + '.html"'
                        ).replace(" ", "")
                        mdFile.write(
                            "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                        )
                        mdFile.write(path)
                        mdFile.write(" height='500' width='150%'></iframe>")

                        mdFile.new_line()
        """
        if regions[region] == "World ":
            for j in ["ncsbar"]:
                for year in ["2050"]:
                    path = (
                        '"'
                        + j
                        + "-"
                        + "pathway"
                        + "-"
                        + year
                        + "-"
                        + (regions[region]).replace(" ", "")
                        + '.html"'
                    )

                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")

                    mdFile.new_line()
        """
        for k in ["mwedges"]:
            path = (
                '"'
                + k
                + "-"
                + "pathway"
                + "-"
                + (regions[region]).replace(" ", "")
                + "-"
                + scen
                + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")

            mdFile.new_line()
        if scen == "dau":
            for j in ["em1"]:
                for k in ["2030", "2050"]:
                    path = (
                        '"'
                        + j
                        + "-"
                        + "pathway"
                        + "-"
                        + k
                        + "-"
                        + (regions[region]).replace(" ", "")
                        + "-"
                        + scen
                        + '.html"'
                    )

                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")

                    mdFile.new_line()

        if regions[region] == "World ":
            for sub in ["emsubind"]:
                path = '"' + sub + "-" + "pathway" + "-" + scen + '.html"'

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")

                mdFile.new_line()

        """
        for j in ["pathway"]:
            for k in ["ei"]:
                path = (
                    '"' + k + "-" + j + "-" + (regions[region]).replace(" ", "") + '.html"'
                )
                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")

                mdFile.new_line()
        """
        # endregion

        ###################
        # ADOPTION CURVES #
        ###################

        # region

        mdFile.new_line()
        mdFile.new_header(level=2, title="Adoption Curves")

        for j in ["pathway"]:
            path = (
                '"scurves-'
                + (regions[region]).replace(" ", "")
                + "-"
                + j
                + "-"
                + scen
                + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")
            mdFile.new_line()

        # endregion

        #############################
        # SUBVECTOR ADOPTION CURVES #
        #############################

        # region
        """
        mdFile.new_line()
        mdFile.new_header(level=2, title="Subvector Adoption Curves")

        for j in ["pathway"]:
            for k in [
                "Industry",
                "Regenerative Agriculture",
                "Forests & Wetlands",
            ]:
                path = (
                    '"scurvessub-'
                    + regions[region]
                    + "-"
                    + k
                    + "-"
                    + j
                    + "-"
                    + "scen"
                    + '.html"'
                ).replace(" ", "")

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")
                mdFile.new_line()

        for j in ["pathway"]:
            for k in [
                "Regenerative Agriculture",
            ]:
                for subvector in [
                    "Biochar",
                    "Cropland Soil Health",
                    "Improved Rice",
                    "Nitrogen Fertilizer Management",
                    "Optimal Intensity",
                    "Silvopasture",
                    "Trees in Croplands",
                ]:
                    path = (
                        '"scurvessubafolu-'
                        + regions[region]
                        + "-"
                        + k
                        + "-"
                        + j
                        + "-"
                        + subvector
                        + "-"
                        + scen
                        + '.html"'
                    ).replace(" ", "")

                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")
                    mdFile.new_line()

            for k in [
                "Forests & Wetlands",
            ]:
                for subvector in [
                    "Coastal Restoration",
                    "Improved Forest Mgmt",
                    "Natural Regeneration",
                    "Peat Restoration",
                ]:
                    path = (
                        '"scurvessubafolu-'
                        + regions[region]
                        + "-"
                        + k
                        + "-"
                        + j
                        + "-"
                        + subvector
                        + "-"
                        + scen
                        + '.html"'
                    ).replace(" ", "")

                    mdFile.write(
                        "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                    )
                    mdFile.write(path)
                    mdFile.write(" height='500' width='150%'></iframe>")
                    mdFile.new_line()
        """
        # endregion

        ###########
        # CLIMATE #
        ###########

        # region

        if regions[region] == "World ":
            mdFile.new_line()
            mdFile.new_header(level=2, title="Climate")

            if regions[region] == "World ":
                for k in ["co2conc", "ghgconc", "forcing", "temp"]:
                    path = (
                        '"'
                        + k
                        + "-"
                        + (regions[region]).replace(" ", "")
                        + "-"
                        + scen
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
