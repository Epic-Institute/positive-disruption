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
