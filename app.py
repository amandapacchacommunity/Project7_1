import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

def fmt(x):
    if x >= 1_000_000:
        return f"${x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:,.0f}"

q = pd.read_csv("quarterly_financial_position.csv")
r = pd.read_csv("risk_register.csv")

baseline_rev = q["total_revenue"].sum()
baseline_margin = q["operating_margin"].sum()

st.title("CFO + ERM Dashboard")

st.header("Board Summary")
st.write("Margin:", fmt(baseline_margin))
st.write("Top Risk:", r.sort_values("expected_loss",ascending=False).iloc[0]["risk_name"])
st.write("Total Risk Exposure:", fmt(r["expected_loss"].sum()))

st.subheader("Revenue vs Expense")
st.caption("Analyst view: divergence signals structural issues")
st.line_chart(q.set_index("quarter")[["total_revenue","total_expenses"]])

st.subheader("Margin by Quarter")
st.caption("Analyst view: negative margins indicate pressure periods")
st.bar_chart(q.set_index("quarter")[["operating_margin"]])

st.subheader("Risk by Timing")
st.caption("Analyst view: links risk to financial impact timing")
timing = r.groupby("timing")["expected_loss"].sum()
st.bar_chart(timing)

st.subheader("Key Ratios")
margin_pct = baseline_margin / baseline_rev * 100
st.write(f"Operating Margin: {margin_pct:.1f}%")
