import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.title("Positive Disruption")

energy_demand = pd.read_csv("energy_demand_out.csv")

# https://pandas.pydata.org/docs/user_guide/10min.html
energy_demand.stack()

fig = energy_demand

c = (
    alt.Chart(
        fig[
            (fig["IEA Region"] == "World ")
            & (fig["Sector"] == "Buildings")
            & (fig["Scenario"] == "pathway")
        ]
    )
    .mark_area()
    .encode(x="Year", y="gen", color="Metric")
)

"""
st.subheader("Energy Demand")
st.line_chart(energy_demand)

st.subheader("Energy Demand")
st.area_chart(energy_demand)
"""
