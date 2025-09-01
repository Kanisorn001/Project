import streamlit as st
import pandas as pd

st.title("Gold Forecast Dashboard")
df = pd.read_csv("gold_and_macro_data_final.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.set_index("Date")
st.line_chart(df["Gold_Price_USD"])
