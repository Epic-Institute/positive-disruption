import hvplot.pandas
import panel as pn

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

select_scenario = pn.widgets.Select(
    options=df.scenario.unique().tolist(), name="Scenario"
)
select_region = pn.widgets.Select(options=df.region.unique().tolist(), name="Region")
select_sector = pn.widgets.Select(options=df.sector.unique().tolist(), name="Sector")
select_flow_category = pn.widgets.Select(
    options=df.flow_category.unique().tolist(), name="Flow Category"
)


@pn.depends(select_scenario, select_region, select_sector, select_flow_category)
def exp_plot(select_scenario, select_region, select_sector, select_flow_category):
    return (
        df[
            (df.scenario == select_scenario)
            & (df.region == select_region)
            & (df.sector == select_sector)
            & (df.flow_category == select_flow_category)
        ]
        .sort_values(by="year")
        .hvplot(x="year", y="TFC", by=["product_long", "flow_long"])
    )


pn.Column(
    select_scenario, select_region, select_sector, select_flow_category, exp_plot
).embed()
