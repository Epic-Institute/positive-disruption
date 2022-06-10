import hvplot.pandas
import panel as pn
from plotly import graph_objects as go
from bokeh.resources import INLINE, CDN

############
#  ENERGY  #
############

# region


def _energy_chart():
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

    select_region = pn.widgets.Select(
        options=df.region.unique().tolist(), name="Region"
    )
    select_sector = pn.widgets.Select(
        options=df.sector.unique().tolist(), name="Sector"
    )

    @pn.depends(select_region, select_sector)
    def exp_plot(select_region, select_sector):
        return (
            df[(df.region == select_region) & (df.sector == select_sector)]
            .sort_values(by="year")
            .hvplot(x="year", y="TFC", by=["flow_long"])
        )

    return pn.Column(
        pn.Row(pn.pane.Markdown("##Energy Output")),
        select_region,
        select_sector,
        exp_plot,
    )


app = _energy_chart()
app.save("./charts/energy_chart.html", resources=CDN)


# endregion
