import dash
import pandas as pd
from dash import dcc, html

dash.register_page(__name__, path="/AMA", title="AMA", name="AMA")

data_start_year = 1990
data_end_year = 2100

dataset = ["energy_output"]

df = pd.read_parquet(
    "~/positive-disruption/podi/data/" + dataset[0] + ".parquet"
).reset_index()


clst = df.columns[
    (
        ~df.columns.isin(
            f"{i}" for i in range(data_start_year, data_end_year + 1)
        )
    )
    & (~df.columns.isin(["product_short", "flow_short"]))
].tolist()

df.set_index(
    df.columns[
        (
            ~df.columns.isin(
                f"{i}" for i in range(data_start_year, data_end_year + 1)
            )
        )
        & (~df.columns.isin(["product_short", "flow_short"]))
    ].tolist(),
    inplace=True,
)

lst = []
for level in df.index.names:
    lst.append(
        html.Label(
            level.replace("_", " ").replace("long", "").title(),
            className="select-label",
        )
    )
    lst.append(
        html.Div(
            [
                dcc.Dropdown(
                    df.reset_index()[level].unique().tolist(),
                    df.reset_index()[level].unique().tolist(),
                    id=level,
                    multi=True,
                ),
            ],
        )
    )
    lst.append(html.Br())


layout = html.Div(
    children=[
        html.Label("Model Output", className="select-label"),
    ],
)
