import streamlit as st

st.set_page_config(layout="wide")

col1, col2, col3, col4 = st.columns(4)

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

with col1:
    kpi_card("Portfolio Value", "₹12,40,000")

with col2:
    kpi_card("1Y Return", "18.4%")

with col3:
    kpi_card("Beta Exposure", "1.12")

with col4:
    kpi_card("VaR (95%)", "₹42,000")