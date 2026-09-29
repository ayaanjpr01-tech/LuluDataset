"""LuLu sales dashboard (Streamlit) with a multi-colour scheme.

Run:
    pip install streamlit pandas altair
    streamlit run app.py

Keep lulu_sales_data.csv in the same folder as this file.
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="LuLu Sales Dashboard", page_icon="🛒", layout="wide")

CSV = Path(__file__).parent / "lulu_sales_data.csv"

# ---- Multi-colour palette -------------------------------------------------
CAT_COLORS = {
    "Fresh": "#2BB673",
    "Grocery": "#F5A623",
    "Fashion": "#E8438A",
    "Electronics": "#2F80ED",
    "Home Decor": "#9B51E0",
    "Furniture": "#EB5757",
}
EMIRATE_COLORS = ["#2F80ED", "#2BB673", "#F5A623", "#E8438A", "#9B51E0", "#EB5757", "#17B6C8"]
# Heat-map stops for the pivot table: cool teal -> yellow -> orange -> magenta
HEAT = [(0.0, (232, 247, 244)), (0.35, (255, 236, 153)), (0.7, (255, 168, 90)), (1.0, (214, 51, 132))]

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem;}
    h1 {background: linear-gradient(90deg,#2BB673,#2F80ED,#9B51E0,#E8438A,#F5A623);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    div[data-testid="stMetric"] {border-radius: 10px; padding: 12px 16px; border-left: 6px solid;}
    div[data-testid="stMetric"]:nth-of-type(1) {border-color:#2BB673;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["Month_Label"] = pd.to_datetime(df["Month"] + "-01").dt.strftime("%b %y")
    return df


def heat(v, vmax):
    if pd.isna(v) or v == 0 or vmax == 0:
        return ""
    t = min(v / vmax, 1.0)
    for (a, ca), (b, cb) in zip(HEAT, HEAT[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            r, g, bl = (round(x + (y - x) * f) for x, y in zip(ca, cb))
            lum = 0.299 * r + 0.587 * g + 0.114 * bl
            return f"background-color: rgb({r},{g},{bl}); color: {'#fff' if lum < 140 else '#222'}"
    return ""


df = load()
month_order = df.sort_values("Month")["Month_Label"].unique().tolist()

# ----
