import streamlit as st
import pandas as pd
import numpy as np
import openai


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

st.set_page_config(layout="wide")
st.title("📊 Portfolio Dashboard")


st.set_page_config(layout="wide")

st.markdown("## 📊 Smart Portfolio Dashboard")

# ==========================================================
# Create Tabs
# ==========================================================
tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload", "📊 Dashboard", "🔎 Detailed View","Gen AI"])

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

        df2 = st.session_state["portfolio_df"]

        st.subheader("🧠 AI Stock Research Terminal")

        stock_list2 = sorted(df2["Stock Name"].unique())
        selected_stock2 = st.selectbox("Select Stock", stock_list2)

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