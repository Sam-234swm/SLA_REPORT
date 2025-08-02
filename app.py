import streamlit as st
import pandas as pd
from sla_logic import process_sla_data  # Make sure file is named sla_logic.py

st.set_page_config(page_title="📊 SLA Report", layout="wide")
st.title("📦 SLA Report Generator")

uploaded_file = st.file_uploader("Upload ERP CSV File", type=["csv"])
date_filter = st.date_input("Select a delivery date to filter")

if uploaded_file is not None and date_filter:
    df = pd.read_csv(uploaded_file, encoding="utf-8", engine="python", on_bad_lines="skip")
    date_str = date_filter.strftime("%d/%m/%Y")
    try:
        final_df = process_sla_data(df, date_str)
        st.success("SLA Report Generated!")
        st.dataframe(final_df)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
