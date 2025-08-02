import streamlit as st
import pandas as pd
from utils.sla_logic import process_sla_data

st.set_page_config(page_title="SLA Report", layout="wide")
st.title("📦 SLA Performance Report")

uploaded_file = st.file_uploader("Upload ERP CSV File", type=["csv"])
filter_date = st.date_input("Select End Time (Actual) Date")

if uploaded_file and filter_date:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8", engine="python")
        result = process_sla_data(df, filter_date.strftime("%d/%m/%Y"))

        st.success("✅ Report Generated")
        st.dataframe(result)

        st.markdown("### 📊 SLA MET vs BREACH% (Chart coming soon...)")

    except Exception as e:
        st.error(f"❌ Error: {e}")
