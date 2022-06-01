import hvplot.pandas
import panel as pn

############
#  ENERGY  #
############

# region

df = energy_output.droplevel(
    ["model", "product_category", "product_short", "flow_short", "unit"]
)
df = pd.melt(
    df.reset_index(),
    id_vars=[
        "scenario",
        "region",
        "sector",
        "product_long",
        "flow_category",
        "flow_long",
    ],
    var_name="year",
    value_name="TFC",
)

df = df[(df.scenario == "pathway") & (df.year < 2021)]

select_region = pn.widgets.Select(options=df.region.unique().tolist(), name="Region")
select_sector = pn.widgets.Select(options=df.sector.unique().tolist(), name="Sector")


@pn.depends(select_region, select_sector)
def exp_plot(select_region, select_sector):
    return (
        df[(df.region == select_region) & (df.sector == select_sector)]
        .sort_values(by="year")
        .hvplot(x="year", y="TFC", by=["flow_long"])
    )


pn.Column(select_region, select_sector, exp_plot).embed()

# endregion

###########
#  AFOLU  #
###########

# region

df = afolu_output.droplevel(
    ["model", "product_category", "product_short", "flow_short", "unit"]
)
df = pd.melt(
    df.reset_index(),
    id_vars=[
        "scenario",
        "region",
        "sector",
        "product_long",
        "flow_category",
        "flow_long",
    ],
    var_name="year",
    value_name="TFC",
)

df = df[(df.scenario == "pathway")]


select_region = pn.widgets.Select(options=df.region.unique().tolist(), name="Region")
select_sector = pn.widgets.Select(options=df.sector.unique().tolist(), name="Sector")


@pn.depends(select_region, select_sector)
def exp_plot(select_region, select_sector):
    return (
        df[(df.region == select_region) & (df.sector == select_sector)]
        .sort_values(by="year")
        .hvplot(x="year", y="TFC", by=["product_long"])
    )


pn.Column(select_region, select_sector, exp_plot).embed()

# endregion

##############
#  ADOPTION  #
##############

# region

df = analysis_output.droplevel(
    ["model", "product_category", "product_short", "flow_short", "unit"]
)
df = pd.melt(
    df.reset_index(),
    id_vars=[
        "scenario",
        "region",
        "sector",
        "product_long",
        "flow_category",
        "flow_long",
    ],
    var_name="year",
    value_name="TFC",
)

df = df[(df.scenario == "pathway") & (df.year < 2021)]

select_region = pn.widgets.Select(options=df.region.unique().tolist(), name="Region")
select_sector = pn.widgets.Select(options=df.sector.unique().tolist(), name="Sector")
select_product = pn.widgets.Select(options=df.product.unique().tolist(), name="Product")


@pn.depends(select_region, select_sector, select_product)
def exp_plot(select_region, select_sector, select_product):
    return (
        df[
            (df.region == select_region)
            & (df.sector == select_sector)
            & (df.product == select_product)
        ]
        .sort_values(by="year")
        .hvplot(x="year", y="TFC", by=["flow_long"])
    )


pn.Column(select_region, select_sector, select_product, exp_plot).embed()

# endregion
