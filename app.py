import pandas as pd
import streamlit as st

st.set_page_config(page_title="Flagship CFO + ERM Dashboard", layout="wide")

def fmt_money(x):
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_000_000:
        return f"{sign}${x/1_000_000:.2f}M"
    if x >= 1_000:
        return f"{sign}${x/1_000:.0f}K"
    return f"{sign}${x:,.0f}"

def fmt_pct(x):
    return f"{x:.1f}%"

@st.cache_data
def load_data():
    q = pd.read_csv("quarterly_financial_position.csv")
    a = pd.read_csv("annual_990_snapshot.csv")
    r = pd.read_csv("risk_register.csv")
    return q, a, r

q, a, r = load_data()

latest_annual = a[a["fiscal_year"] == a["fiscal_year"].max()].iloc[0]
baseline_revenue = q["total_revenue"].sum()
baseline_expenses = q["total_expenses"].sum()
baseline_margin = q["operating_margin"].sum()
baseline_cash_months = (latest_annual["cash_and_short_term_investments"] / baseline_expenses) * 12
baseline_reserve_months = (latest_annual["operating_reserve"] / baseline_expenses) * 12

st.title("Flagship CFO + ERM Dashboard")
st.caption("Synthetic executive dashboard combining quarterly financial position, 990-style annual indicators, and enterprise risk exposure for a mission-driven organization.")

with st.sidebar:
    st.header("Scenario controls")
    donor_dev = st.slider("Donor revenue deviation", -20, 15, -6, 1, format="%d%%")
    program_dev = st.slider("Program revenue deviation", -15, 15, -3, 1, format="%d%%")
    expense_dev = st.slider("Expense deviation", -10, 20, 5, 1, format="%d%%")
    st.divider()
    preset = st.selectbox("Preset", ["Custom", "Base Case", "Soft Stress", "Expense Pressure", "Board Stress Test"])

if preset == "Base Case":
    donor_dev, program_dev, expense_dev = 0, 0, 0
elif preset == "Soft Stress":
    donor_dev, program_dev, expense_dev = -5, -2, 4
elif preset == "Expense Pressure":
    donor_dev, program_dev, expense_dev = -2, 0, 8
elif preset == "Board Stress Test":
    donor_dev, program_dev, expense_dev = -10, -5, 10

scenario = q.copy()
scenario["contributions"] = scenario["contributions"] * (1 + donor_dev / 100)
scenario["program_revenue"] = scenario["program_revenue"] * (1 + program_dev / 100)
scenario["total_revenue"] = scenario["contributions"] + scenario["program_revenue"] + scenario["investment_income"]
scenario["total_expenses"] = scenario["total_expenses"] * (1 + expense_dev / 100)
scenario["operating_margin"] = scenario["total_revenue"] - scenario["total_expenses"]

scenario_revenue = scenario["total_revenue"].sum()
scenario_expenses = scenario["total_expenses"].sum()
scenario_margin = scenario["operating_margin"].sum()
scenario_cash_months = (latest_annual["cash_and_short_term_investments"] / scenario_expenses) * 12
scenario_reserve_months = (latest_annual["operating_reserve"] / scenario_expenses) * 12
total_expected_loss = r["expected_loss"].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Baseline Revenue", fmt_money(baseline_revenue))
m2.metric("Scenario Revenue", fmt_money(scenario_revenue), delta=fmt_money(scenario_revenue - baseline_revenue))
m3.metric("Scenario Expenses", fmt_money(scenario_expenses), delta=fmt_money(scenario_expenses - baseline_expenses))
m4.metric("Scenario Margin", fmt_money(scenario_margin), delta=fmt_money(scenario_margin - baseline_margin))

m5, m6, m7, m8 = st.columns(4)
m5.metric("Cash on Hand", f"{scenario_cash_months:.1f} mo", delta=f"{scenario_cash_months - baseline_cash_months:.1f}")
m6.metric("Reserve Coverage", f"{scenario_reserve_months:.1f} mo", delta=f"{scenario_reserve_months - baseline_reserve_months:.1f}")
m7.metric("Expense Ratio", fmt_pct((scenario_expenses / scenario_revenue) * 100 if scenario_revenue else 0))
m8.metric("Total Expected Loss", fmt_money(total_expected_loss))

st.subheader("Quarterly financial position")
summary = pd.DataFrame({
    "quarter": q["quarter"],
    "baseline_revenue": q["total_revenue"],
    "scenario_revenue": scenario["total_revenue"],
    "baseline_expenses": q["total_expenses"],
    "scenario_expenses": scenario["total_expenses"],
    "baseline_margin": q["operating_margin"],
    "scenario_margin": scenario["operating_margin"],
})
display = summary.copy()
for col in display.columns[1:]:
    display[col] = display[col].map(fmt_money)
st.dataframe(display, use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Revenue vs expense trend")
    trend = scenario.set_index("quarter")[["total_revenue", "total_expenses"]]
    st.line_chart(trend)

with right:
    st.subheader("Quarterly operating margin")
    margins = scenario.set_index("quarter")[["operating_margin"]]
    st.bar_chart(margins)

left2, right2 = st.columns(2)
with left2:
    st.subheader("Top risks by expected loss")
    risk_view = r.sort_values("expected_loss", ascending=False)[["risk_name", "expected_loss"]].set_index("risk_name")
    st.bar_chart(risk_view)

with right2:
    st.subheader("Risk impact by category")
    cat_view = r.groupby("risk_category", as_index=True)["financial_impact"].sum().sort_values(ascending=False)
    st.bar_chart(cat_view)

st.subheader("Executive recommendations")
recommendations = []

if scenario_margin < 0:
    recommendations.append("Operating margin turns negative under the selected scenario. Tighten discretionary spending and sequence hiring or vendor commitments by quarter.")
if donor_dev <= -5:
    recommendations.append("Donor revenue softness is materially affecting the annual position. Prioritize donor retention outreach, board engagement, and pipeline review for top gifts.")
if expense_dev >= 5:
    recommendations.append("Expense growth is outpacing the baseline. Add a monthly variance review and identify fixed versus flexible cost categories before the next budget cycle.")
if scenario_cash_months < 3:
    recommendations.append("Liquidity is thin. Establish a minimum cash threshold and prepare a short-term contingency plan for delayed receipts or unplanned expense events.")
if scenario_reserve_months < 3:
    recommendations.append("Operating reserves fall below a comfortable cushion. Consider a reserve target policy and a board-facing recovery plan.")
if not recommendations:
    recommendations.append("Financial position remains manageable under the selected scenario. Maintain reserve discipline and continue quarterly stress testing with risk owners.")

for rec in recommendations:
    st.markdown(f"- {rec}")

st.subheader("Risk register")
risk_display = r.copy()
risk_display["probability"] = risk_display["probability"].map(lambda x: f"{x:.0%}")
risk_display["financial_impact"] = risk_display["financial_impact"].map(fmt_money)
risk_display["expected_loss"] = risk_display["expected_loss"].map(fmt_money)
st.dataframe(risk_display, use_container_width=True, hide_index=True)

st.subheader("Annual 990-style snapshot")
annual_display = a.copy()
for c in annual_display.columns:
    if c != "fiscal_year":
        annual_display[c] = annual_display[c].map(fmt_money)
st.dataframe(annual_display, use_container_width=True, hide_index=True)