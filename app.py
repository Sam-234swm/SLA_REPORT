import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="SLA Report", layout="wide")
st.title("📦 SLA Report Dashboard")

def clean_cell(val):
    if pd.isna(val): return val
    return re.sub(r'=\("?([^"]+)"?\)?', r'\1', str(val)).strip()

def highlight_sla(val):
    try:
        val = int(val)
    except:
        return ""
    if val >= 85:
        return 'background-color: #C6EFCE; color: #006100;'
    elif val < 60:
        return 'background-color: #FFC7CE; color: #9C0006;'
    else:
        return 'background-color: #FFEB9C; color: #9C6500;'

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
user_date = st.text_input("Enter Delivery Date (dd/mm/yyyy)", value="01/08/2025")

if uploaded_file and user_date:
    try:
        df_raw = pd.read_csv(uploaded_file, engine="python", on_bad_lines='skip')
        df = df_raw.applymap(clean_cell)

        df['Order Date'] = pd.to_datetime(df['Order Date'], format="%d/%m/%Y %I:%M %p", errors='coerce')
        df['End Time (Actual)'] = pd.to_datetime(df['End Time (Actual)'], format="%d/%m/%Y %I:%M %p", errors='coerce')

        valid_stores = [
            "BLR_kalyan-nagar", "BLR_koramangala", "CH_Periyamet",
            "DEL_malviya-nagar", "HYD_manikonda", "KOL-Topsia",
            "MUM_andheri", "PUN_koregaon-park"
        ]
        df = df[df['Order Dark Store'].isin(valid_stores)]
        df = df[df['Order Status'].str.lower() == "delivered"]

        selected_date = datetime.strptime(user_date, "%d/%m/%Y").date()
        df = df[df['End Time (Actual)'].dt.date == selected_date]

        df['Delivery Type'] = df['Order Date'].apply(
            lambda x: "Quick" if pd.notna(x) and 0 <= x.hour < 15 else "Non Quick"
        )
        df['TAT'] = df['Order Date'].apply(
            lambda x: x.replace(hour=23, minute=59, second=59) if pd.notna(x) and x.hour < 15
            else (x + timedelta(days=1)).replace(hour=23, minute=59, second=59) if pd.notna(x)
            else pd.NaT
        )
        df['SLA Status'] = df.apply(
            lambda row: "SLA Breach" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT']) and row['End Time (Actual)'] > row['TAT']
            else "SLA Met" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT'])
            else "NA",
            axis=1
        )

        summary = df.groupby(['Order Dark Store', 'SLA Status']).size().unstack(fill_value=0)
        summary.columns.name = None
        summary = summary.rename(columns={'SLA Met': 'SLA MET COUNT', 'SLA Breach': 'SLA BREACH COUNT'})

        summary['TOTAL DELIVERED ORDERS'] = summary.sum(axis=1)
        summary['SLA MET%'] = round(summary['SLA MET COUNT'] / summary['TOTAL DELIVERED ORDERS'] * 100).astype(int)
        summary['SLA BREACH%'] = 100 - summary['SLA MET%']

        grand_total = pd.DataFrame(summary.sum(numeric_only=True)).T
        grand_total.index = ['Grand Total']
        grand_total['SLA MET%'] = round(grand_total['SLA MET COUNT'] / grand_total['TOTAL DELIVERED ORDERS'] * 100).astype(int)
        grand_total['SLA BREACH%'] = 100 - grand_total['SLA MET%']

        summary_final = pd.concat([summary, grand_total])

        st.markdown("""
        <style>
        thead tr th {
            background-color: #dce6f1;
            color: black;
            text-align: center;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        styled_summary = summary_final.style \
            .applymap(highlight_sla, subset=["SLA MET%", "SLA BREACH%"]) \
            .format(na_rep='-', precision=0)

        st.markdown("### 📊 SLA Summary Report", unsafe_allow_html=True)
        st.dataframe(styled_summary, use_container_width=True)

        st.markdown("### 📉 SLA Chart")
        labels = summary.index.tolist()
        x = range(len(labels))
        met = summary['SLA MET%']
        breach = summary['SLA BREACH%']

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x, met, label='SLA MET%', color='lightgreen')
        ax.bar(x, breach, bottom=met, label='SLA BREACH%', color='orangered')

        for i in x:
            ax.text(i, met[i] / 2, f"{met[i]}%", ha='center', va='center', fontsize=9)
            ax.text(i, met[i] + breach[i] / 2, f"{breach[i]}%", ha='center', va='center', fontsize=9)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylabel("Percentage")
        ax.set_title("SLA MET% vs SLA BREACH% by Dark Store")
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
