from dash import Dash, html, dcc
import dash

app = Dash(
    __name__,
    use_pages=True,
)

app.layout = html.Div(
    [
        html.Div(
            className="header",
            children=[html.Div("Data Explorer")],
        ),
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
