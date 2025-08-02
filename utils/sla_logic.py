import pandas as pd
from datetime import datetime

def process_sla_data(df, date_filter_str):
    # Step 1: Fix date format
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce', dayfirst=True)
    df['End Time (Actual)'] = pd.to_datetime(df['End Time (Actual)'], errors='coerce', dayfirst=True)

    # Step 2: Filter dark stores
    valid_stores = [
        "BLR_kalyan-nagar", "BLR_koramangala", "CH_Periyamet",
        "DEL_malviya-nagar", "HYD_manikonda", "KOL-Topsia",
        "MUM_andheri", "PUN_koregaon-park"
    ]
    df = df[df['Order Dark Store'].isin(valid_stores)]

    # Step 3: Filter by Order Status
    df = df[df['Order Status'].str.lower() == "delivered"]

    # Step 4: Filter by End Time (Actual) date
    date_filter = pd.to_datetime(date_filter_str, dayfirst=True)
    df = df[df['End Time (Actual)'].dt.date == date_filter.date()]

    # Step 5: Add computed columns
    df['Delivery Type'] = df['Order Date'].apply(
        lambda x: "Quick" if x.hour >= 0 and x.hour < 15 else "Non Quick"
    )

    df['TAT'] = df['Order Date'].apply(
        lambda x: datetime.combine(x.date(), datetime.max.time()) if x.hour < 15
        else datetime.combine(x.date(), datetime.max.time()) + pd.Timedelta(days=1)
    )

    df['SLA STATUS'] = df.apply(
        lambda row: "SLA Breach" if row['End Time (Actual)'] > row['TAT'] else "SLA Met", axis=1
    )

    # Summary Table: Grouped by Dark Store
    summary = df.groupby('Order Dark Store')['SLA STATUS'].value_counts().unstack(fill_value=0).reset_index()

    summary['TOTAL DELIVERED ORDERS'] = summary.get('SLA Met', 0) + summary.get('SLA Breach', 0)
    summary['SLA MET%'] = round(summary.get('SLA Met', 0) / summary['TOTAL DELIVERED ORDERS'] * 100).astype(str) + '%'
    summary['SLA BREACH%'] = round(summary.get('SLA Breach', 0) / summary['TOTAL DELIVERED ORDERS'] * 100).astype(str) + '%'

    summary.rename(columns={
        'SLA Met': 'SLA MET COUNT',
        'SLA Breach': 'SLA BREACH COUNT'
    }, inplace=True)

    # Add Grand Total row
    total_row = pd.DataFrame({
        'Order Dark Store': ['Grand Total'],
        'SLA MET COUNT': [summary['SLA MET COUNT'].sum()],
        'SLA BREACH COUNT': [summary['SLA BREACH COUNT'].sum()],
        'TOTAL DELIVERED ORDERS': [summary['TOTAL DELIVERED ORDERS'].sum()],
        'SLA MET%': [str(round(summary['SLA MET COUNT'].sum() / summary['TOTAL DELIVERED ORDERS'].sum() * 100)) + '%'],
        'SLA BREACH%': [str(round(summary['SLA BREACH COUNT'].sum() / summary['TOTAL DELIVERED ORDERS'].sum() * 100)) + '%']
    })

    final_result = pd.concat([summary, total_row], ignore_index=True)
    return final_result
