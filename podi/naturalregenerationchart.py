
    # region

    scenario = scenario
    model = "PD22"

    fig = (
        emissions_afolu.loc[model]
        .groupby(["region","scenario", "sector", "product_long", "flow_long"])
        .sum()
        .T
    )
    fig.index.name = "year"
    fig.reset_index(inplace=True)
    fig2 = pd.melt(
        fig,
        id_vars="year",
        var_name=["region","scenario", "sector", "product_long", "flow_long"],
        value_name="Emissions",
    )

    for gas in ["CO2"]:
        for scenario in fig2["scenario"].unique():
            fig = go.Figure()
            for region in fig2[(fig2['year']==2050) & (fig2['product_long']=='Natural Regeneration')].sort_values("Emissions", ascending=True)["region"].unique():
                for sector in ['Forests & Wetlands']:
                    for product_long in ['Natural Regeneration']:
                        fig.add_trace(
                            go.Scatter(
                                name=region,
                                line=dict(
                                    width=0.5,
                                    color=np.concatenate(
                                        (
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                            px.colors.qualitative.Dark24,
                                        )
                                    )[
                                        fig2["region"]
                                        .unique()
                                        .tolist()
                                        .index(region)
                                    ],
                                ),
                                x=fig2["year"].unique(),
                                y=fig2[(fig2["region"] == region) &
                                    (fig2["scenario"] == scenario)
                                    & (fig2["sector"] == sector)
                                    & (fig2["product_long"] == product_long)
                                    & (fig2["flow_long"] == gas)
                                ]["Emissions"],
                                fill="tonexty",
                                stackgroup="one",
                            )
                        )

            fig.update_layout(
                title={
                    "text": "Emissions, "
                    + "World, "
                    + gas
                    + ", "
                    + str(sector).capitalize()
                    + ", "
                    + str(scenario).capitalize(),
                    "xanchor": "center",
                    "x": 0.5,
                    "y": 0.9,
                },
                yaxis={"title": "Mt " + gas},
                legend=dict(font=dict(size=8)),
            )

            if show_figs is True:
                fig.show()

            if save_figs is True:
                                pio.write_html(
                                    fig,
                                    file=(
                                        "./charts/emissions-NaturalRegeneration"
                                        + "-"
                                        + str(scenario)
                                        + ".html"
                                    ).replace(" ", ""),
                                    auto_open=False,
                                )

    # endregion

