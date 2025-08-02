import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.sla_logic import process_sla_data  # already working
import io

# 📌 File upload
st.title("📦 SLA Report with Chart")
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
filter_date = st.date_input("Select End Date")

if uploaded_file and filter_date:
    # Read and process
    df = pd.read_csv(uploaded_file)
    summary_df = process_sla_data(df, filter_date)

    st.subheader("📊 SLA Summary Table")
    st.dataframe(summary_df)

    # 📌 Remove 'Grand Total' row for the chart
    chart_df = summary_df[summary_df['Order Dark Store'] != 'Grand Total']

    # 📌 Bar Chart: SLA MET% vs SLA BREACH%
    st.subheader("📉 SLA MET% vs SLA BREACH% by Dark Store")

    labels = chart_df['Order Dark Store']
    met = chart_df['SLA MET%'].str.rstrip('%').astype(int)
    breach = chart_df['SLA BREACH%'].str.rstrip('%').astype(int)
    x = range(len(labels))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, met, label='SLA MET%', color='lightgreen')
    ax.bar(x, breach, bottom=met, label='SLA BREACH%', color='orangered')

    # 📌 Annotate %
    for i in x:
        ax.text(i, met[i] / 2, f"{met[i]}%", ha='center', va='center', fontsize=9)
        ax.text(i, met[i] + breach[i] / 2, f"{breach[i]}%", ha='center', va='center', fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel("Percentage")
    ax.set_title("SLA MET% vs SLA BREACH%")
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    st.pyplot(fig)
