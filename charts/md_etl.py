#!/usr/bin/env python

from mdutils.mdutils import MdUtils
from podi.energy_demand import iea_region_list

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

for i in range(0, len(iea_region_list)):
    mdFile = MdUtils(file_name=iea_region_list[i].replace(" ", "") + ".md")

    mdFile.new_header(level=1, title=iea_region_list[i]).replace(" ", "")
    mdFile.new_line()

    mdFile.write("![](../region%20maps/")
    mdFile.write(iea_region_list[i].replace(" ", ""))
    mdFile.write(".png)")
    mdFile.new_line()
    mdFile.new_line()

    mdFile.write(region_dict[iea_region_list[i]])
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

    for k in ["em2"]:
        path = (
            '"'
            + k
            + "-"
            + "baseline"
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

    for k in ["mwedges", "em1"]:
        path = (
            '"'
            + k
            + "-"
            + "pathway"
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
