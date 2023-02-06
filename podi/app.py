from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import dash

app = Dash(
    __name__,
    use_pages=True,
)


app.layout = html.Div(
    [
        html.Meta(
            charSet="utf-8",
        ),
        html.Meta(
            name="description",
            content="",
        ),
        html.Meta(
            name="viewport",
            content="width=device-width, initial-scale=1.0",
        ),
        html.Title("Data Explorer"),
        html.Link(rel="preconnect", href="https://fonts.googleapis.com"),
        html.Link(rel="preconnect", href="https://fonts.gstatic.com"),
        html.Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:ital,wght@0,200;0,300;0,400;0,600;0,700;0,900;1,200;1,300;1,400;1,600;1,700;1,900&family=Josefin+Sans:wght@100;200;300;400;500;600;700&display=swap",
        ),
        html.Link(rel="stylesheet", href="css/bootstrap.min.css"),
        html.Link(rel="stylesheet", href="css/homepage.css"),
        html.Meta(name="twitter:card", content="summary_large_image"),
        html.Meta(name="twitter:title", content="Positive Disruption Data Explorer"),
        html.Meta(
            name="twitter:description",
            content="The Positive Disruption model examines how adoption of low- and no-carbon technologies and practices can be expected to grow over the next 30 years.",
        ),
        html.Meta(
            name="twitter:image",
            content="https://epic-institute.github.io/data-explorer/img/social-twitter.png",
        ),
        # make a header
        html.Div(
            [
                html.Div(
                    id="mobile-popup",
                    children=[
                        html.Div(
                            id="mobile-logo",
                            className="row",
                            children=[
                                html.A(
                                    href="https://epicinstitute.org/",
                                    target="_blank",
                                    children=[
                                        html.Img(
                                            src=app.get_asset_url("img/epic-logo.png")
                                        )
                                    ],
                                )
                            ],
                        ),
                        html.Div(
                            id="mobile-title",
                            className="row",
                            children=[html.Span("Data Explorer")],
                        ),
                        html.Div(
                            id="mobile-text",
                            className="row",
                            children=[
                                html.P(
                                    "Visit on a larger screen \n to explore the data"
                                )
                            ],
                        ),
                    ],
                )
            ]
        ),
        html.Div(
            className="row",
            id="data-explorer",
            children=[
                html.Div(
                    className="row header",
                    children=[
                        html.Div(
                            [
                                html.A(
                                    html.Img(
                                        src=app.get_asset_url("img/epic-logo.png")
                                    ),
                                    href="https://epicinstitute.org/",
                                    target="_blank",
                                )
                            ],
                            className="col-2 icon-col",
                        ),
                        html.Div(
                            [html.Span("Data Explorer")],
                            className="col-8 title",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    html.A(
                                        "github",
                                        href="https://github.com/Epic-Institute/data-explorer",
                                        target="_blank",
                                    ),
                                    className="header-item",
                                )
                            ],
                            className="col-1",
                        ),
                        html.Div(
                            className="col-1",
                            children=[
                                html.Div(
                                    id="dropdown-about",
                                    children=[
                                        html.Span(
                                            "about",
                                            id="about-button",
                                            className="header-item",
                                        ),
                                        html.Div(
                                            id="about-details",
                                            children=[
                                                dbc.Tooltip(
                                                    children=[
                                                        html.P(
                                                            "Positive Disruption Data Explorer",
                                                            className="about-subtitle",
                                                        ),
                                                        html.P(
                                                            "The Data Explorer is a web-based tool that allows for easy navigation through the Positive Disruption model results to examine how adoption of low- and no-carbon technologies and practices in the energy, agriculture, and land-use sectors can be expected to grow over the next 30 years, and the effect they will have on the process of reversing climate change."
                                                        ),
                                                    ],
                                                    target="about-button",
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(className="row ei-border-bottom"),
                # Filters
                html.Div(
                    className="row filters",
                    children=[
                        html.Div(
                            className="col-12",
                            children=[
                                html.Div(
                                    className="row select",
                                    children=[
                                        html.Div(
                                            className="col-4 select-output",
                                            children=[
                                                html.Span(
                                                    "Positive Disruption model output",
                                                    className="select-label",
                                                ),
                                                html.Div(
                                                    dcc.Dropdown(
                                                        [
                                                            "AFOLU",
                                                            "Energy",
                                                            "Climate",
                                                            "Emissions",
                                                            "Energy",
                                                            "Results Analysis",
                                                            "Energy Balances",
                                                        ]
                                                    ),
                                                    className="buttons",
                                                    id="buttons-vector",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="col-3 select-country",
                                            children=[
                                                html.Span(
                                                    "Region", className="select-label"
                                                ),
                                                html.Div(
                                                    className="dropdown",
                                                    id="dropdown-region",
                                                    children=[
                                                        html.Div(
                                                            className="dropbtn",
                                                            id="dropbtn-region",
                                                        ),
                                                        html.Div(
                                                            className="dropdown-content",
                                                            id="regions-search",
                                                            children=[
                                                                dcc.Input(
                                                                    type="text",
                                                                    id="search-box",
                                                                    placeholder="Search...",
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(
                                                            id="regions-menu",
                                                            className="dropdown-content",
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="col-2 select-scenario",
                                            children=[
                                                html.Span(
                                                    "Scenario", className="select-label"
                                                ),
                                                html.Div(
                                                    className="buttons",
                                                    id="buttons-scenario",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="col-3 select-scenario",
                                            children=[
                                                html.Span(
                                                    "Date", className="select-label"
                                                ),
                                                html.Div(
                                                    className="buttons",
                                                    id="time-slider",
                                                ),
                                            ],
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                ),
                html.Div(className="row ei-border-bottom"),
                # Results
                html.Div(
                    className="row outputs",
                    children=[
                        html.Div(
                            className="col-4",
                            id="region-details",
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Span(id="region-flag"),
                                        html.Span(id="region-name"),
                                    ],
                                ),
                                html.Div(className="row cia-indicators"),
                            ],
                        ),
                        html.Div(
                            className="col-8",
                            id="chart-options-container",
                            children=[
                                html.Div(
                                    id="chart-options",
                                    children=[
                                        html.Span(
                                            "Chart Type",
                                            className="select-label",
                                            id="select-chart",
                                        ),
                                        html.Div(id="chart-types"),
                                        html.Div(
                                            id="filters-col",
                                            children=[
                                                html.Div(
                                                    "Graph options",
                                                    id="show-filters",
                                                    className="select-label",
                                                ),
                                                html.Div(id="graph-filters"),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(className="row", id="chart"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # original
        html.Div(
            children=html.Div(
                [
                    html.Div(dcc.Link(f"{page['name']}", href=page["relative_path"]))
                    for page in dash.page_registry.values()
                ]
            )
        ),
        html.Br(),
        html.Br(),
        dash.page_container,
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True)
