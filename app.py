import streamlit as st
import pandas as pd
import numpy as np
import openai
import numpy as np

def kpi_card(title, value):
    st.markdown(f"""
        <div style="
            background-color:#F8F9FA;
            padding:20px;
            border-radius:12px;
            text-align:center;
        ">
            <h4 style="margin:0;">{title}</h4>
            <h2 style="margin:0;">{value}</h2>
        </div>
    """, unsafe_allow_html=True)

def winsorize(series, lower=0.05, upper=0.95):
    low = series.quantile(lower)
    high = series.quantile(upper)
    return series.clip(low, high)

def zscore_scaled(series):
    series = winsorize(series)
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(50, index=series.index)
    z = (series - mean) / std
    score = 50 + (z * 15)
    return score.clip(0, 100)

def pillar_icon(score):
    if score >= 75:
        return "🟢"
    elif score >= 65:
        return "🟡"
    elif score >= 50:
        return "🟠"
    else:
        return "🔴"

st.set_page_config(layout="wide")
st.title("📊 Portfolio Dashboard")


st.set_page_config(layout="wide")

st.markdown("## 📊 Smart Portfolio Dashboard")

# ==========================================================
# Create Tabs
# ==========================================================
tab1, tab2, tab3, tab4, tab5, tab10 = st.tabs(["📁 Upload", "📊 Dashboard", "🔎 Detailed View","🧮 Scorecard","✅ Sector Analysis","🧠 Gen AI"])

# ==========================================================
# TAB 1 – FILE UPLOAD
# ==========================================================
with tab1:

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

        # Store in session state
        st.session_state["portfolio_df"] = df

        st.success("File uploaded successfully! Go to Dashboard tab.")

# ==========================================================
# TAB 2 – DASHBOARD
# ==========================================================
with tab2:

    if "portfolio_df" not in st.session_state:
        st.info("Upload file in Tab 1 to view dashboard.")
    else:

        df = st.session_state["portfolio_df"]

        total_invested = df["Invested Amount"].sum()
        total_current = df["Current Value"].sum()
        total_pl = df["P/L"].sum()
        total_return = (total_pl / total_invested) * 100

        prev_day_value = total_current - df["Day P&L"].sum()
        day_change = total_current - prev_day_value
        win_rate = (df["P/L"] > 0).mean() * 100

        # ---------------- Snapshot ----------------
        with st.container(border=True):
            st.subheader("📌 Portfolio Snapshot")

            k0, k1, k2, k3, k4 = st.columns(5)

           # k1.metric("Current Value", f"₹{total_current:,.0f}", f"{day_change:,.0f}")
           # k2.metric("Total Return %", f"{total_return:.2f}%")
           # k3.metric("Total P/L", f"₹{total_pl:,.0f}")
           # k4.metric("Win Rate", f"{win_rate:.1f}%")

            with k0:
                kpi_card("Total Invested", f"₹{total_invested:,.0f}")
            with k1:
                kpi_card("Current Value", f"₹{total_current:,.0f}")
            with k2:
                kpi_card("Total Return %", f"₹{total_return:,.2f}")
            with k3:
                kpi_card("Total P/L", f"₹{total_pl:,.0f}")
            with k4:
                kpi_card("Win Rate", f"{win_rate:.1f}%")


        st.markdown(" ")

        # ---------------- Asset Breakdown ----------------
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

        # ---------------- Portfolio Valuation ----------------
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

        # ---------------- Performance Tables ----------------
        with st.container(border=True):
            st.subheader("📊 Overall Performance")

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

# ==========================================================
# TAB 3 – DETAILED STOCK ANALYZER
# ==========================================================
with tab3:

    if "portfolio_df" not in st.session_state:
        st.info("Upload file in Tab 1 first.")
    else:

        df = st.session_state["portfolio_df"]

        st.subheader("🔎 Stock Performance Analyzer")

        stock_list = sorted(df["Stock Name"].unique())
        selected_stock = st.selectbox("Select Stock", stock_list)

        stock_df = df[df["Stock Name"] == selected_stock].iloc[0]

        with st.container(border=True):

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Return %", f"{stock_df['Return %']:.2f}%")
            c2.metric("Day Change %", f"{stock_df['Day Change %']:.2f}%")
            c3.metric("PE", f"{stock_df['PE TTM Price to Earnings']:.2f}")
            c4.metric("Beta", f"{stock_df['Beta 1Year']:.2f}")

            c5, c6, c7, c8 = st.columns(4)

            c5.metric("ROE", f"{stock_df['ROE Annual %']:.2f}%")
            c6.metric("ROCE", f"{stock_df['ROCE Annual %']:.2f}%")
            c7.metric("Revenue Growth", f"{stock_df['Revenue Growth Annual YoY %']:.2f}%")
            c8.metric("Institutional Holding", f"{stock_df['Institutional holding current Qtr %']:.2f}%")

        st.markdown(" ")

        st.write("### Full Data Snapshot")
        st.dataframe(stock_df)

with tab4:
    if "portfolio_df" not in st.session_state:
        st.info("Upload file in Tab 1 first.")
    else:

        df = st.session_state["portfolio_df"].copy()

        st.subheader("📊 Portfolio Scoring Dashboard")

        # ==================================================
        # 🔎 FILTER BAR
        # ==================================================
        with st.container(border=True):

            f1, f2, f3, f4 = st.columns(4)

            # Stock filter
            stock_filter = f1.multiselect(
                "Stock",
                options=sorted(df["Stock Name"].unique())
            )

            # Sector filter
            sector_filter = f2.multiselect(
                "Sector",
                options=sorted(df["Sector Name"].unique())
            )

            # Asset type
            type_filter = f3.multiselect(
                "Instrument Type",
                options=sorted(df["Asset Type"].unique())
            )

            # Market Cap
            mcap_filter = f4.multiselect(
                "Market Cap",
                options=sorted(df["Mcap Classification"].dropna().unique())
            )

            r1, r2, r3, r4 = st.columns(4)

            price_range = r1.slider(
                "Price Range",
                float(df["Current Price"].min()),
                float(df["Current Price"].max()),
                (float(df["Current Price"].min()),
                 float(df["Current Price"].max()))
            )

            pl_range = r2.slider(
                "Return % Range",
                float(df["Return %"].min()),
                float(df["Return %"].max()),
                (float(df["Return %"].min()),
                 float(df["Return %"].max()))
            )

            pe_range = r3.slider(
                "PE Range",
                float(df["PE TTM Price to Earnings"].min()),
                float(df["PE TTM Price to Earnings"].max()),
                (float(df["PE TTM Price to Earnings"].min()),
                 float(df["PE TTM Price to Earnings"].max()))
            )

            invest_range = r4.slider(
                "Investment Range",
                float(df["Invested Amount"].min()),
                float(df["Invested Amount"].max()),
                (float(df["Invested Amount"].min()),
                 float(df["Invested Amount"].max()))
            )

        # ==================================================
        # APPLY FILTERS
        # ==================================================
        if stock_filter:
            df = df[df["Stock Name"].isin(stock_filter)]

        if sector_filter:
            df = df[df["Sector Name"].isin(sector_filter)]

        if type_filter:
            df = df[df["Asset Type"].isin(type_filter)]

        if mcap_filter:
            df = df[df["Mcap Classification"].isin(mcap_filter)]

        df = df[
            (df["Current Price"].between(price_range[0], price_range[1])) &
            (df["Return %"].between(pl_range[0], pl_range[1])) &
            (df["PE TTM Price to Earnings"].between(pe_range[0], pe_range[1])) &
            (df["Invested Amount"].between(invest_range[0], invest_range[1]))
        ]

        # ==================================================
        # 1️⃣ VALUATION
        # ==================================================
        df["Earnings Yield"] = 1 / df["PE TTM Price to Earnings"].replace(0, np.nan)

        ey_score = zscore_scaled(df["Earnings Yield"])

        df["PE Premium"] = df["PE TTM Price to Earnings"] - df["Sector PE TTM"]
        sector_score = zscore_scaled(-df["PE Premium"])

        peg_score = zscore_scaled(-df["PEG TTM PE to Growth"])

        df["Valuation"] = (
            ey_score * 0.5 +
            sector_score * 0.3 +
            peg_score * 0.2
        )

        # ==================================================
        # 2️⃣ QUALITY
        # ==================================================
        roe_score = zscore_scaled(df["ROE Annual %"])
        roce_score = zscore_scaled(df["ROCE Annual %"])
        pio_score = zscore_scaled(df["Piotroski Score"])
        inst_score = zscore_scaled(df["Institutional holding current Qtr %"])

        df["Quality"] = (
            roe_score * 0.4 +
            roce_score * 0.3 +
            pio_score * 0.2 +
            inst_score * 0.1
        )

        # ==================================================
        # 3️⃣ GROWTH
        # ==================================================
        rev_score = zscore_scaled(df["Revenue Growth Annual YoY %"])
        profit_score = zscore_scaled(df["Net Profit TTM Growth %"])

        df["Growth"] = rev_score * 0.5 + profit_score * 0.5

        df.loc[df["Revenue Growth Annual YoY %"] < 0, "Growth"] *= 0.7
        df.loc[df["Net Profit TTM Growth %"] < 0, "Growth"] *= 0.7

        # ==================================================
        # 4️⃣ RISK
        # ==================================================
        beta_score = zscore_scaled(-df["Beta 1Year"])
        vol_score = zscore_scaled(-df["Standard Deviation 1Year"])

        df["Risk"] = beta_score * 0.5 + vol_score * 0.5

        # ==================================================
        # 5️⃣ MARKET STRENGTH
        # ==================================================
        rel_score = zscore_scaled(df["Relative returns vs Nifty50 year%"])
        momentum_score = zscore_scaled(df["Trendlyne Momentum Score"])

        df["Market"] = rel_score * 0.6 + momentum_score * 0.4

        # ==================================================
        # FINAL SCORE
        # ==================================================
        df["Total Score"] = (
            df["Valuation"] * 0.20 +
            df["Quality"] * 0.25 +
            df["Growth"] * 0.20 +
            df["Risk"] * 0.20 +
            df["Market"] * 0.15
        )

        df["Total Score"] = df["Total Score"].round(1)
        df["Rank"] = df["Total Score"].rank(ascending=False)

        # ==================================================
        # DISPLAY TABLE
        # ==================================================
        st.subheader("📊 Multi-Factor Scoring Dashboard")

        header_cols = st.columns([1.2,1,1,1,1,1,1,1,1,0.8])

        headers = [
            "Stock", "Curr Value", "P/L %",
            "Val", "Qual", "Grow", "Risk", "Mkt", "Total", "Details"
        ]

        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")

        for _, row in df.sort_values("Total Score", ascending=False).iterrows():

            cols = st.columns([1.2,1,1,1,1,1,1,1,1,0.8])

            cols[0].write(row["NSEcode"])
            cols[1].write(f"₹{row['Current Value']:,.0f}")
            cols[2].write(f"{row['Return %']:.2f}%")

            cols[3].write(f"{pillar_icon(row['Valuation'])} {row['Valuation']:.1f}")
            cols[4].write(f"{pillar_icon(row['Quality'])} {row['Quality']:.1f}")
            cols[5].write(f"{pillar_icon(row['Growth'])} {row['Growth']:.1f}")
            cols[6].write(f"{pillar_icon(row['Risk'])} {row['Risk']:.1f}")
            cols[7].write(f"{pillar_icon(row['Market'])} {row['Market']:.1f}")
            cols[8].write(f"{pillar_icon(row['Total Score'])} {row['Total Score']:.1f}")

            if cols[9].button("View", key=f"view_{row['NSEcode']}"):
                st.session_state["selected_stock"] = row["NSEcode"]

        # ==================================================
        # BREAKDOWN SECTION
        # ==================================================
        if "selected_stock" in st.session_state:

            stock_code = st.session_state["selected_stock"]
            stock = df[df["NSEcode"] == stock_code].iloc[0]

            st.markdown("---")
            st.subheader(f"🔎 Detailed Breakdown: {stock_code}")

            with st.container(border=True):

                c1,c2,c3,c4,c5 = st.columns(5)

                c1.metric("Valuation", round(stock["Valuation"],1))
                c2.metric("Quality", round(stock["Quality"],1))
                c3.metric("Growth", round(stock["Growth"],1))
                c4.metric("Risk", round(stock["Risk"],1))
                c5.metric("Market", round(stock["Market"],1))

                st.markdown("---")
                st.write("### Raw Drivers")

                st.write(f"ROE: {stock['ROE Annual %']}%")
                st.write(f"ROCE: {stock['ROCE Annual %']}%")
                st.write(f"Revenue Growth: {stock['Revenue Growth Annual YoY %']}%")
                st.write(f"Net Profit Growth: {stock['Net Profit TTM Growth %']}%")
                st.write(f"Beta: {stock['Beta 1Year']}")
                st.write(f"Std Dev (1Y): {stock['Standard Deviation 1Year']}")
                st.write(f"PE: {stock['PE TTM Price to Earnings']}")
                st.write(f"Sector PE: {stock['Sector PE TTM']}")
                st.write(f"Relative Return: {stock['Relative returns vs Nifty50 year%']}%")
                st.write(f"Momentum: {stock['Trendlyne Momentum Score']}")

with tab5:
        # ==================================================
        # SECTOR VIEW
        # ==================================================
        st.markdown(" ")
        st.subheader("📊 Sector-Level View")

        sector_group = df.groupby("Sector Name").agg(
            Sector_Score=("Score", "mean"),
            Total_Investment=("Invested Amount", "sum"),
            Avg_PE=("PE TTM Price to Earnings", "mean"),
            Avg_Beta=("Beta 1Year", "mean"),
            Avg_ROE=("ROE Annual %", "mean")
        ).reset_index()

        sector_group = sector_group.sort_values("Sector_Score", ascending=False)

        st.dataframe(sector_group, use_container_width=True)

with tab10:

    if "portfolio_df" not in st.session_state:
        st.info("Upload file in Tab 1 first.")
    else:

        df2 = st.session_state["portfolio_df"]

        st.subheader("🧠 AI Stock Research Terminal")

        stock_list2 = sorted(df2["Stock Name"].unique())
        selected_stock2 = st.selectbox("Select Stock", stock_list2,key="ai_stock_select")

        stock2 = df2[df2["Stock Name"] == selected_stock2].iloc[0]

        if st.button("Generate AI Investment Analysis"):

            prompt = f"""
            Analyze this Indian stock from a portfolio perspective.

            Stock: {selected_stock2}

            Metrics:
            PE: {stock2['PE TTM Price to Earnings']}
            Sector PE: {stock2['Sector PE TTM']}
            ROE: {stock2['ROE Annual %']}
            ROCE: {stock2['ROCE Annual %']}
            Revenue Growth: {stock2['Revenue Growth Annual YoY %']}
            Net Profit Growth: {stock2['Net Profit TTM Growth %']}
            Beta: {stock2['Beta 1Year']}
            Institutional Holding: {stock2['Institutional holding current Qtr %']}
            1Y Std Dev: {stock2['Standard Deviation 1Year']}
            Portfolio Return: {stock2['Return %']}

            Provide:
            1. Valuation assessment
            2. Growth quality
            3. Risk profile
            4. Red flags
            5. Investment bias (Accumulate / Hold / Reduce)
            """

            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )

            st.markdown("### 📊 AI Analysis")
            st.write(response.choices[0].message.content)