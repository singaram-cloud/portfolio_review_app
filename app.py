import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Smart Portfolio Dashboard")

uploaded_file = st.file_uploader("Upload Portfolio Excel File", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # ---------------- Asset Classification ----------------
    def classify_asset(row):
        nse = str(row["NSEcode"])
        name = str(row["Stock Name"]).upper()

        if nse.startswith("F000"):
            return "Mutual Fund"
        elif "ETF" in name:
            return "ETF"
        else:
            return "Equity"

    df["Asset Type"] = df.apply(classify_asset, axis=1)

    # ---------------- Core Calculations ----------------
    df["Current Value"] = df["Quantity"] * df["Current Price"]
    df["P/L"] = df["Current Value"] - df["Invested Amount"]
    df["Return %"] = (df["P/L"] / df["Invested Amount"]) * 100

    total_invested = df["Invested Amount"].sum()
    total_current = df["Current Value"].sum()
    total_pl = df["P/L"].sum()
    total_return = (total_pl / total_invested) * 100

    win_rate = (df["P/L"] > 0).mean() * 100
    weighted_beta = np.average(df["Beta 1Year"].fillna(1), weights=df["Current Value"])
    avg_roe = df["ROE Annual %"].mean()

    # ---------------- KPI SECTION ----------------
    st.subheader("📌 Portfolio Health")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Invested", f"₹{total_invested:,.0f}")
    c2.metric("Current Value", f"₹{total_current:,.0f}")
    c3.metric("Return %", f"{total_return:.2f}%")
    c4.metric("Win Rate", f"{win_rate:.1f}%")
    c5.metric("Portfolio Beta", f"{weighted_beta:.2f}")

    st.markdown("---")

    # ---------------- Allocation Section ----------------
    st.subheader("📊 Allocation Overview")

    col1, col2 = st.columns(2)

    with col1:
        asset_alloc = df.groupby("Asset Type")["Current Value"].sum()
        fig1, ax1 = plt.subplots()
        ax1.pie(asset_alloc, labels=asset_alloc.index, autopct='%1.1f%%')
        ax1.axis('equal')
        st.pyplot(fig1)

    with col2:
        sector_alloc = df.groupby("Sector Name")["Current Value"].sum().sort_values(ascending=False).head(8)
        fig2, ax2 = plt.subplots()
        ax2.bar(sector_alloc.index, sector_alloc.values)
        ax2.set_xticklabels(sector_alloc.index, rotation=45)
        st.pyplot(fig2)

    st.markdown("---")

    # ---------------- Risk Section ----------------
    st.subheader("⚠ Risk Indicators")

    high_beta = df.sort_values("Beta 1Year", ascending=False).head(5)
    high_vol = df.sort_values("Standard Deviation 1Year", ascending=False).head(5)

    col3, col4 = st.columns(2)

    with col3:
        st.write("Top 5 High Beta Stocks")
        st.dataframe(high_beta[["Stock Name", "Beta 1Year", "Return %"]])

    with col4:
        st.write("Top 5 High Volatility Stocks")
        st.dataframe(high_vol[["Stock Name", "Standard Deviation 1Year", "Return %"]])

    st.markdown("---")

    # ---------------- Quality Section ----------------
    st.subheader("🏆 Quality & Value Signals")

    quality = df[(df["ROE Annual %"] > 20) & (df["Revenue Growth Annual YoY %"] > 10)]
    value = df[(df["PE TTM Price to Earnings"] < df["Sector PE TTM"]) & (df["ROE Annual %"] > 15)]

    col5, col6 = st.columns(2)

    with col5:
        st.write("High ROE + High Growth")
        st.dataframe(quality[["Stock Name", "ROE Annual %", "Revenue Growth Annual YoY %"]].head(5))

    with col6:
        st.write("Value Picks (Low PE vs Sector)")
        st.dataframe(value[["Stock Name", "PE TTM Price to Earnings", "Sector PE TTM"]].head(5))

else:
    st.info("Upload an Excel file to generate smart dashboard.")