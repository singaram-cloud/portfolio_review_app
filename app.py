import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ---------------- HEADER ----------------
header_col1, header_col2 = st.columns([3,1])

with header_col1:
    st.markdown("## 📊 Smart Portfolio Dashboard")

with header_col2:
    uploaded_file = st.file_uploader("Upload File", type=["xlsx"], label_visibility="collapsed")

st.markdown("---")

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

    prev_day_value = total_current - df["Day P&L"].sum()
    day_change = total_current - prev_day_value

    win_rate = (df["P/L"] > 0).mean() * 100

    # ============================================================
    # 📌 SECTION 1: PORTFOLIO SNAPSHOT (BORDERED)
    # ============================================================

    with st.container(border=True):
        st.subheader("📌 Portfolio Snapshot")

        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Current Value", f"₹{total_current:,.0f}", f"{day_change:,.0f}")
        k2.metric("Total Return %", f"{total_return:.2f}%")
        k3.metric("Total P/L", f"₹{total_pl:,.0f}")
        k4.metric("Win Rate", f"{win_rate:.1f}%")

    st.markdown(" ")

    # ============================================================
    # 📊 SECTION 2: ASSET BREAKDOWN (BORDERED)
    # ============================================================

    with st.container(border=True):
        st.subheader("📊 Asset Breakdown")

        asset_summary = df.groupby("Asset Type").agg(
            Invested=("Invested Amount", "sum"),
            Current=("Current Value", "sum"),
            PnL=("P/L", "sum")
        ).reset_index()

        cols = st.columns(len(asset_summary))

        for i, row in asset_summary.iterrows():
            ret = (row["PnL"] / row["Invested"]) * 100 if row["Invested"] != 0 else 0
            cols[i].metric(
                row["Asset Type"],
                f"₹{row['Current']:,.0f}",
                f"{ret:.2f}%"
            )

    st.markdown(" ")

    # ============================================================
    # 📈 SECTION 3: PORTFOLIO VALUATION METRICS (BORDERED)
    # ============================================================

    with st.container(border=True):
        st.subheader("📈 Portfolio Valuation Metrics")

        weighted_pe = np.average(
            df["PE TTM Price to Earnings"].replace(0, np.nan).fillna(0),
            weights=df["Current Value"]
        )

        weighted_pb = np.average(
            df["Price to Book Value Adjusted"].replace(0, np.nan).fillna(0),
            weights=df["Current Value"]
        )

        weighted_beta = np.average(
            df["Beta 1Year"].fillna(1),
            weights=df["Current Value"]
        )

        weighted_roe = np.average(
            df["ROE Annual %"].fillna(0),
            weights=df["Current Value"]
        )

        weighted_roce = np.average(
            df["ROCE Annual %"].fillna(0),
            weights=df["Current Value"]
        )

        v1, v2, v3, v4, v5 = st.columns(5)

        v1.metric("Portfolio PE", f"{weighted_pe:.2f}")
        v2.metric("Portfolio PB", f"{weighted_pb:.2f}")
        v3.metric("Portfolio Beta", f"{weighted_beta:.2f}")
        v4.metric("Portfolio ROE", f"{weighted_roe:.2f}%")
        v5.metric("Portfolio ROCE", f"{weighted_roce:.2f}%")

    st.markdown(" ")

    # ============================================================
    # 📊 SECTION 4: PERFORMANCE TABLES
    # ============================================================

    with st.container(border=True):
        st.subheader("📊 Overall Performance (Since Purchase)")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔥 Top 5 Profit % Stocks")
            top_profit = df.sort_values("Return %", ascending=False).head(5)
            st.dataframe(top_profit[["Stock Name", "Return %", "P/L"]])

        with col2:
            st.markdown("#### ❌ Top 5 Loss % Stocks")
            top_loss = df.sort_values("Return %").head(5)
            st.dataframe(top_loss[["Stock Name", "Return %", "P/L"]])

    st.markdown(" ")

    # ============================================================
    # 📊 SECTION 5: TODAY PERFORMANCE
    # ============================================================

    with st.container(border=True):
        st.subheader("📅 Today's Performance")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("#### 🚀 Top 5 Gainers Today")
            today_profit = df.sort_values("Day Change %", ascending=False).head(5)
            st.dataframe(today_profit[["Stock Name", "Day Change %", "Day P&L"]])

        with col4:
            st.markdown("#### 🔻 Top 5 Losers Today")
            today_loss = df.sort_values("Day Change %").head(5)
            st.dataframe(today_loss[["Stock Name", "Day Change %", "Day P&L"]])

else:
    st.info("Upload portfolio file to view dashboard.")