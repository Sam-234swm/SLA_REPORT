import streamlit as st
import pandas as pd
from sla_logic import process_sla_data  # Make sure file is named sla_logic.py

st.set_page_config(page_title="📊 SLA Report", layout="wide")
st.title("📦 SLA Report Generator")

uploaded_file = st.file_uploader("Upload ERP CSV File", type=["csv"])
date_filter = st.date_input("Select a delivery date to filter")

if uploaded_file and date_filter:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8', engine='python', error_bad_lines=False)
        result = process_sla_data(df, date_filter.strftime("%d/%m/%Y"))

        st.success("✅ Processed SLA report")
        st.dataframe(result)

        # Optional bar chart
        st.subheader("📈 SLA Met vs SLA Breach by Dark Store")
        chart_df = result[result["Order Dark Store"] != "Grand Total"]
        chart_df["SLA MET %"] = chart_df["SLA MET%"].str.replace('%', '').astype(float)
        chart_df["SLA BREACH %"] = chart_df["SLA BREACH%"].str.replace('%', '').astype(float)

        st.bar_chart(chart_df.set_index("Order Dark Store")[["SLA MET %", "SLA BREACH %"]])

    except Exception as e:
        st.error(f"❌ Error: {e}")
