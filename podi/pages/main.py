from dash import html
import dash

dash.register_page(__name__, path="/", title="Main", name="Main")

layout = html.H1("Main Page")
