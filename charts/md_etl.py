from mdutils.mdutils import MdUtils

region_dict = {
    "World ": "",
    "US ": "",
    "BRAZIL ": "",
    "EU ": "",
    "SAFR ": "",
    "EURASIA ": "",
    "RUS ": "",
    "CHINA ": "",
    "INDIA ": "",
    "JPN ": "",
    "ASEAN ": "",
    "AdvancedECO ": "",
    "DevelopingECO ": "",
    " OECD ": "Australia, Austria, Belgium, Canada, Chile, Czech Republic, Denmark, Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Ireland, Israel, Italy, Japan, Korea, Luxembourg, Mexico, Netherlands, New Zealand, Norway, Poland, Portugal, Slovak Republic, Slovenia, Spain, Sweden, Switzerland, Turkey, United Kingdom, United States",
    "NonOECD ": "All countries not included in OECD regional grouping.",
    "NAM ": "Canada, Mexico, United States",
    "ASIAPAC ": "Southeast Asia regional grouping, Australia, Bangladesh, China, Chinese Taipei, India, Japan, Korea, Democratic People’s Republic of Korea, Mongolia, Nepal, New Zealand, Pakistan, Sri Lanka, Afghanistan, Bhutan, Cook Islands, Fiji, French Polynesia, Kiribati, the Lao People’s Democratic Republic, Macau (China), Maldives, New Caledonia, Palau, Papua New Guinea, Samoa, Solomon Islands, Timor-Leste, Tonga, Vanuatu",
    "CSAM ": "Argentina, Bolivia, Bolivarian Republic of Venezuela, Brazil, Chile, Colombia, Costa Rica, Cuba, Curaçao, Dominican Republic, Ecuador, El Salvador, Guatemala, Haiti, Honduras, Jamaica, Nicaragua, Panama, Paraguay, Peru, Suriname, Trinidad and Tobago, Uruguay, Antigua and Barbuda, Aruba, Bahamas, Barbados, Belize, Bermuda, Bonaire, British Virgin Islands, Cayman Islands, Dominica, Falkland Islands (Malvinas), French Guiana, Grenada, Guadeloupe, Guyana, Martinique, Montserrat, Saba, Saint Eustatius, Saint Kitts and Nevis, Saint Lucia, Saint Vincent and the Grenadines, Saint Maarten, Turks and Caicos Islands",
    "EUR ": "European Union regional grouping, Albania, Belarus, Bosnia and Herzegovina, Gibraltar, Iceland, Israel, Kosovo, Montenegro, Norway, Serbia, Switzerland, the Former Yugoslav Republic of Macedonia, Republic of Moldova, Turkey, Ukraine",
    "AFRICA ": "Algeria, Egypt, Libya, Morocco, Tunisia, Angola, Benin, Botswana, Cameroon, Republic of the Congo, Côte d\’Ivoire, Democratic Republic of the Congo, Eritrea, Ethiopia, Gabon, Ghana, Kenya, Mauritius, Mozambique, Namibia, Niger, Nigeria, Senegal, South Africa, South Sudan, Sudan, United Republic of Tanzania, Togo, Zambia, Zimbabwe, Burkina Faso, Burundi, Cabo Verde, Central African Republic, Chad, Comoros, Djibouti, Equatorial Guinea, Gambia, Guinea, Guinea-Bissau, Lesotho, Liberia, Madagascar, Malawi, Mali, Mauritania, Réunion, Rwanda, Sao Tome and Principe, Seychelles, Sierra Leone, Somalia, Swaziland, Uganda, Western Sahara",
    "ME ": "Bahrain, Islamic Republic of Iran, Iraq, Jordan, Kuwait, Lebanon, Oman, Qatar, Saudi Arabia, Syrian Arab Republic, United Arab Emirates, Yemen",
}

for i in range(0, len(region_list)):

    ###################
    # MAP & COUNTRIES #
    ###################

    # region

    mdFile = MdUtils(file_name="md-" + region_list[i].replace(" ", "") + ".md")

    mdFile.new_header(level=1, title=region_list[i]).replace(" ", "")
    mdFile.new_line()

    mdFile.write("![](../region%20maps/")
    mdFile.write(region_list[i].replace(" ", ""))
    mdFile.write(".png)")

    # mdFile.write(region_dict[region_list[i]])

    mdFile.new_line()
    mdFile.new_line()

    # endregion

    ########################
    # ENERGY SUPPLY/DEMAND #
    ########################
    """
    # region

    mdFile.new_line()
    mdFile.new_header(level=2, title="Energy Supply and Demand")

    for j in ["baseline", "pathway"]:
        for k in ["demand", "supply", "supply2"]:
            path = (
                '"' + k + "-" + j + "-" + (region_list[i]).replace(" ", "") + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")
            mdFile.new_line()

    # endregion
    """
    #############
    # EMISSIONS #
    #############

    # region

    mdFile.new_line()
    mdFile.new_header(level=2, title="Emissions")

    for j in ["pathway"]:
        for k in ["em2"]:
            path = (
                '"' + k + "-" + j + "-" + (region_list[i]).replace(" ", "") + '.html"'
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
                    + (region_list[i]).replace(" ", "")
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
                    + (region_list[i]).replace(" ", "")
                    + "-"
                    + sector
                    + '.html"'
                ).replace(" ", "")
                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")

                mdFile.new_line()

    """
    if region_list[i] == "World ":
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
                    + (region_list[i]).replace(" ", "")
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
            + (region_list[i]).replace(" ", "")
            + '.html"'
        )

        mdFile.write(
            "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
        )
        mdFile.write(path)
        mdFile.write(" height='500' width='150%'></iframe>")

        mdFile.new_line()

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
                + (region_list[i]).replace(" ", "")
                + '.html"'
            )

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")

            mdFile.new_line()

    if region_list[i] == "World ":
        for sub in ["emsubind"]:
            path = '"' + sub + "-" + "pathway" + '.html"'

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
                '"' + k + "-" + j + "-" + (region_list[i]).replace(" ", "") + '.html"'
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
        path = '"scurves-' + (region_list[i]).replace(" ", "") + "-" + j + '.html"'

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

    mdFile.new_line()
    mdFile.new_header(level=2, title="Subvector Adoption Curves")
    """
    for j in ["pathway"]:
        for k in [
            "Industry",
            "Regenerative Agriculture",
            "Forests & Wetlands",
        ]:
            path = (
                '"scurvessub-' + region_list[i] + "-" + k + "-" + j + '.html"'
            ).replace(" ", "")

            mdFile.write(
                "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
            )
            mdFile.write(path)
            mdFile.write(" height='500' width='150%'></iframe>")
            mdFile.new_line()
    """
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
                    + region_list[i]
                    + "-"
                    + k
                    + "-"
                    + j
                    + "-"
                    + subvector
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
                    + region_list[i]
                    + "-"
                    + k
                    + "-"
                    + j
                    + "-"
                    + subvector
                    + '.html"'
                ).replace(" ", "")

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")
                mdFile.new_line()

    # endregion

    ###########
    # CLIMATE #
    ###########

    # region

    if region_list[i] == "World ":
        mdFile.new_line()
        mdFile.new_header(level=2, title="Climate")

        if region_list[i] == "World ":
            for k in ["co2conc", "ghgconc", "forcing", "temp"]:
                path = '"' + k + "-" + (region_list[i]).replace(" ", "") + '.html"'

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")

                mdFile.new_line()

    # endregion

    mdFile.create_md_file()

for scen in [
    "daulp",
    "dauwe",
    "daura",
    "daufw",
    "dauncs",
    "dauffi",
    "dauncsffi",
    "dauncsffiet",
]:

    for i in range(0, len(region_list)):

        ###################
        # MAP & COUNTRIES #
        ###################

        # region

        mdFile = MdUtils(
            file_name="md-" + region_list[i].replace(" ", "") + "-" + scen + ".md"
        )

        mdFile.new_header(level=1, title=region_list[i]).replace(" ", "")
        mdFile.new_line()

        mdFile.write("![](../region%20maps/")
        mdFile.write(region_list[i].replace(" ", ""))
        mdFile.write(".png)")

        # mdFile.write(region_dict[region_list[i]])

        mdFile.new_line()
        mdFile.new_line()

        # endregion

        ########################
        # ENERGY SUPPLY/DEMAND #
        ########################
        """
        # region

        mdFile.new_line()
        mdFile.new_header(level=2, title="Energy Supply and Demand")

        for j in ["baseline", "pathway"]:
            for k in ["demand", "supply", "supply2"]:
                path = (
                    '"' + k + "-" + j + "-" + (region_list[i]).replace(" ", "") + '.html"'
                )

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")
                mdFile.new_line()

        # endregion
        """
        #############
        # EMISSIONS #
        #############

        # region

        mdFile.new_line()
        mdFile.new_header(level=2, title="Emissions")

        for j in ["pathway"]:
            """
            for k in ["em2"]:
                path = (
                    '"'
                    + k
                    + "-"
                    + j
                    + "-"
                    + (region_list[i]).replace(" ", "")
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
                        + (region_list[i]).replace(" ", "")
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
            """
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
                        + (region_list[i]).replace(" ", "")
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
        """
        if region_list[i] == "World ":
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
                        + (region_list[i]).replace(" ", "")
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
                + (region_list[i]).replace(" ", "")
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
                    + (region_list[i]).replace(" ", "")
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
        """
        if region_list[i] == "World ":
            for sub in ["emsubind"]:
                path = '"' + sub + "-" + "pathway" + "-" + scen + '.html"'

                mdFile.write(
                    "<iframe id='igraph' scrolling='no' style='border:none' seamless='seamless' src= "
                )
                mdFile.write(path)
                mdFile.write(" height='500' width='150%'></iframe>")

                mdFile.new_line()
        """
        """
        for j in ["pathway"]:
            for k in ["ei"]:
                path = (
                    '"' + k + "-" + j + "-" + (region_list[i]).replace(" ", "") + '.html"'
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
                + (region_list[i]).replace(" ", "")
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
        """
        # region

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
                    + region_list[i]
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
                        + region_list[i]
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
                        + region_list[i]
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

        # endregion
        """
        ###########
        # CLIMATE #
        ###########

        # region

        if region_list[i] == "World ":
            mdFile.new_line()
            mdFile.new_header(level=2, title="Climate")

            if region_list[i] == "World ":
                for k in ["co2conc", "ghgconc", "forcing", "temp"]:
                    path = (
                        '"'
                        + k
                        + "-"
                        + (region_list[i]).replace(" ", "")
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
