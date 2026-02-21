import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Portfolio Dashboard")

uploaded_file = st.file_uploader("Upload Portfolio Excel File", type=["xlsx"])

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Calculations
    df["Current Value"] = df["Quantity"] * df["Current Price"]
    df["P/L"] = df["Current Value"] - df["Invested Amount"]
    df["Return %"] = (df["P/L"] / df["Invested Amount"]) * 100

    total_invested = df["Invested Amount"].sum()
    total_current_value = df["Current Value"].sum()
    total_profit_loss = df["P/L"].sum()
    total_return_pct = (total_profit_loss / total_invested) * 100

    # ---------------- KPI SECTION ----------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Invested", f"₹{total_invested:,.0f}")
    col2.metric("Current Value", f"₹{total_current_value:,.0f}")
    col3.metric("Profit / Loss", f"₹{total_profit_loss:,.0f}")
    col4.metric("Return %", f"{total_return_pct:.2f}%")

    st.markdown("---")

    # ---------------- SECTOR ALLOCATION ----------------
    st.subheader("Sector Allocation")

    sector_allocation = df.groupby("Sector Name")["Current Value"].sum()

    fig1, ax1 = plt.subplots()
    ax1.pie(sector_allocation, labels=sector_allocation.index, autopct='%1.1f%%')
    ax1.axis('equal')
    st.pyplot(fig1)

    st.markdown("---")

    # ---------------- TOP GAINERS / LOSERS ----------------
    col5, col6 = st.columns(2)

    top_gainers = df.sort_values("P/L", ascending=False).head(5)
    top_losers = df.sort_values("P/L").head(5)

    with col5:
        st.subheader("Top 5 Gainers")
        st.dataframe(top_gainers[["Stock Name", "P/L", "Return %"]])

    with col6:
        st.subheader("Top 5 Losers")
        st.dataframe(top_losers[["Stock Name", "P/L", "Return %"]])

    st.markdown("---")

    # ---------------- RETURN DISTRIBUTION ----------------
    st.subheader("Return Distribution")

    fig2, ax2 = plt.subplots()
    ax2.hist(df["Return %"].dropna(), bins=20)
    ax2.set_xlabel("Return %")
    ax2.set_ylabel("Number of Stocks")
    st.pyplot(fig2)

else:
    st.info("Upload an Excel file to generate dashboard.")