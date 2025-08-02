import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="SLA Report", layout="wide")
st.title("📊 SLA MET vs BREACH Report")

def clean_cell(val):
    if pd.isna(val): return val
    return re.sub(r'=\("?([^"]+)"?\)?', r'\1', str(val)).strip()

# Upload CSV
uploaded_file = st.file_uploader("Upload SLA Report CSV File", type=["csv"])

# Select Date
selected_date = st.date_input("Select Delivery Date (End Time)", format="DD/MM/YYYY")

if uploaded_file and selected_date:
    # Read and clean file
    try:
        df_raw = pd.read_csv(uploaded_file, encoding="utf-8", engine="python", on_bad_lines="skip")
        df = df_raw.applymap(clean_cell)

        # Parse datetime
        df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d/%m/%Y %I:%M %p", errors="coerce")
        df["End Time (Actual)"] = pd.to_datetime(df["End Time (Actual)"], format="%d/%m/%Y %I:%M %p", errors="coerce")

        # Filter valid stores
        valid_stores = [
            "BLR_kalyan-nagar", "BLR_koramangala", "CH_Periyamet",
            "DEL_malviya-nagar", "HYD_manikonda", "KOL-Topsia",
            "MUM_andheri", "PUN_koregaon-park"
        ]
        df = df[df["Order Dark Store"].isin(valid_stores)]

        # Filter for delivered orders on selected date
        df = df[df["Order Status"].str.lower() == "delivered"]
        df = df[df["End Time (Actual)"].dt.date == selected_date]

        # Delivery Type
        df['Delivery Type'] = df['Order Date'].apply(
            lambda x: "Quick" if pd.notna(x) and 0 <= x.hour < 15 else "Non Quick"
        )

        # TAT Calculation
        df['TAT'] = df['Order Date'].apply(
            lambda x: x.replace(hour=23, minute=59, second=59) if pd.notna(x) and x.hour < 15
            else (x + timedelta(days=1)).replace(hour=23, minute=59, second=59) if pd.notna(x)
            else pd.NaT
        )

        # SLA Status
        df['SLA Status'] = df.apply(
            lambda row: "SLA Breach" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT']) and row['End Time (Actual)'] > row['TAT']
            else "SLA Met" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT'])
            else "NA",
            axis=1
        )

        # Summary Table
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

        final_summary = pd.concat([summary, grand_total]).reset_index().rename(columns={'index': 'Order Dark Store'})

        # Display Table
        st.dataframe(final_summary)

        # Plot
        st.subheader("📉 SLA % Chart")

        chart_data = final_summary[final_summary["Order Dark Store"] != "Grand Total"]
        x = chart_data["Order Dark Store"]
        met = chart_data["SLA MET%"]
        breach = chart_data["SLA BREACH%"]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x, met, label="SLA MET%", color="lightgreen")
        ax.bar(x, breach, bottom=met, label="SLA BREACH%", color="orangered")

        for i in range(len(x)):
            ax.text(i, met.iloc[i] / 2, f"{met.iloc[i]}%", ha="center", va="center", fontsize=9)
            ax.text(i, met.iloc[i] + breach.iloc[i] / 2, f"{breach.iloc[i]}%", ha="center", va="center", fontsize=9)

        ax.set_ylabel("Percentage")
        ax.set_title("SLA MET% vs SLA BREACH% by Dark Store")
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(x, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.6)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
