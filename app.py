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

# ---- Sidebar filters ------------------------------------------------------
st.sidebar.header("Filters")
emirates = st.sidebar.multiselect("Emirate", sorted(df["Emirate"].unique()))
stores = st.sidebar.multiselect(
    "Store location",
    sorted(df[df["Emirate"].isin(emirates)]["Store_Name"].unique() if emirates else df["Store_Name"].unique()),
)
cats = st.sidebar.multiselect("Category", sorted(df["Category"].unique()))
measure = st.sidebar.radio("Measure", ["Units sold", "Net sales (AED)"])
col = "Units_Sold" if measure == "Units sold" else "Net_Sales_AED"

f = df.copy()
if emirates:
    f = f[f["Emirate"].isin(emirates)]
if stores:
    f = f[f["Store_Name"].isin(stores)]
if cats:
    f = f[f["Category"].isin(cats)]

# ---- Header and KPIs ------------------------------------------------------
st.title("LuLu sales dashboard")
st.caption(f"{f['Month'].min()} to {f['Month'].max()} · {len(f):,} transactions in view")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Units sold", f"{f['Units_Sold'].sum():,}")
k2.metric("Net sales (AED)", f"{f['Net_Sales_AED'].sum():,.0f}")
k3.metric("Transactions", f"{len(f):,}")
k4.metric("Avg units / transaction", f"{f['Units_Sold'].mean():.1f}" if len(f) else "0")

# ---- Charts ---------------------------------------------------------------
cat_scale = alt.Scale(domain=list(CAT_COLORS), range=list(CAT_COLORS.values()))
c1, c2 = st.columns(2)

with c1:
    st.subheader("Monthly trend by category")
    monthly = f.groupby(["Month_Label", "Category"], as_index=False)[col].sum()
    st.altair_chart(
        alt.Chart(monthly).mark_bar().encode(
            x=alt.X("Month_Label:N", sort=month_order, title=None),
            y=alt.Y(f"{col}:Q", title=measure),
            color=alt.Color("Category:N", scale=cat_scale),
            tooltip=["Month_Label", "Category", alt.Tooltip(f"{col}:Q", format=",.0f")],
        ).properties(height=300),
        width="stretch",
    )

with c2:
    st.subheader("By emirate")
    em = f.groupby("Emirate", as_index=False)[col].sum()
    st.altair_chart(
        alt.Chart(em).mark_bar().encode(
            y=alt.Y("Emirate:N", sort="-x", title=None),
            x=alt.X(f"{col}:Q", title=measure),
            color=alt.Color("Emirate:N", scale=alt.Scale(range=EMIRATE_COLORS), legend=None),
            tooltip=["Emirate", alt.Tooltip(f"{col}:Q", format=",.0f")],
        ).properties(height=300),
        width="stretch",
    )

st.subheader("Top 8 items")
top = (
    f.groupby(["Sub_Category", "Category"], as_index=False)[col].sum().nlargest(8, col)
)
st.altair_chart(
    alt.Chart(top).mark_bar().encode(
        y=alt.Y("Sub_Category:N", sort="-x", title=None),
        x=alt.X(f"{col}:Q", title=measure),
        color=alt.Color("Category:N", scale=cat_scale),
        tooltip=["Sub_Category", "Category", alt.Tooltip(f"{col}:Q", format=",.0f")],
    ).properties(height=260),
    width="stretch",
)

# ---- Pivot: months as columns --------------------------------------------
st.subheader("Monthly breakdown")
views = {
    "Item": "Sub_Category",
    "Category": "Category",
    "Emirate": "Emirate",
    "Store location": "Store_Name",
}
view = st.radio("Group rows by", list(views), horizontal=True)

pivot = (
    f.pivot_table(index=views[view], columns="Month_Label", values=col, aggfunc="sum", fill_value=0)
    .reindex(columns=[m for m in month_order if m in f["Month_Label"].unique()])
)
pivot["Total"] = pivot.sum(axis=1)
pivot = pivot.sort_values("Total", ascending=False)
pivot.loc["Total"] = pivot.sum()

vmax = pivot.drop(columns="Total").drop(index="Total").to_numpy().max() if len(pivot) > 1 else 0
month_cols = [c for c in pivot.columns if c != "Total"]
styled = (
    pivot.style.map(lambda v: heat(v, vmax), subset=(pivot.index[:-1], month_cols))
    .set_properties(subset=["Total"], **{"font-weight": "bold"})
    .format("{:,.0f}")
)
st.dataframe(styled, width="stretch", height=min(650, 40 + 35 * len(pivot)))

st.download_button(
    "Download this table (CSV)", pivot.to_csv().encode("utf-8"), "lulu_monthly_breakdown.csv", "text/csv"
)
