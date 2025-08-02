import pandas as pd
import re
from datetime import datetime, timedelta

def clean_cell(val):
    if pd.isna(val): return val
    return re.sub(r'\=\(\"?([^\"]+)\"?\)?', r'\1', str(val)).strip()

def process_sla_data(df, filter_date_str):
    # Step 1: Clean weird Excel-formatted strings
    df = df.applymap(clean_cell)

    # Step 2: Convert to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date'], format="%d/%m/%Y %I:%M %p", errors='coerce')
    df['End Time (Actual)'] = pd.to_datetime(df['End Time (Actual)'], format="%d/%m/%Y %I:%M %p", errors='coerce')

    # Step 3: Filter by valid dark stores
    valid_stores = [
        "BLR_kalyan-nagar", "BLR_koramangala", "CH_Periyamet",
        "DEL_malviya-nagar", "HYD_manikonda", "KOL-Topsia",
        "MUM_andheri", "PUN_koregaon-park"
    ]
    df = df[df['Order Dark Store'].isin(valid_stores)]

    # Step 4: Filter delivered orders
    df = df[df['Order Status'].str.lower() == "delivered"]

    # Step 5: Filter by selected end date
    try:
        filter_date = datetime.strptime(filter_date_str, "%d/%m/%Y").date()
    except ValueError:
        return pd.DataFrame({'Error': ["Invalid date format. Use dd/mm/yyyy"]})

    df = df[df['End Time (Actual)'].dt.date == filter_date]

    if df.empty:
        return pd.DataFrame({'Info': ["No data found for selected date"]})

    # Step 6: Delivery Type
    df['Delivery Type'] = df['Order Date'].apply(
        lambda x: "Quick" if pd.notna(x) and 0 <= x.hour < 15 else "Non Quick"
    )

    # Step 7: TAT calculation
    df['TAT'] = df['Order Date'].apply(
        lambda x: x.replace(hour=23, minute=59, second=59) if pd.notna(x) and x.hour < 15
        else (x + timedelta(days=1)).replace(hour=23, minute=59, second=59) if pd.notna(x)
        else pd.NaT
    )

    # Step 8: SLA Status
    df['SLA Status'] = df.apply(
        lambda row: "SLA Breach" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT']) and row['End Time (Actual)'] > row['TAT']
        else "SLA Met" if pd.notna(row['End Time (Actual)']) and pd.notna(row['TAT'])
        else "NA",
        axis=1
    )

    # Step 9: Summary Table
    summary = df.groupby(['Order Dark Store', 'SLA Status']).size().unstack(fill_value=0)
    summary.columns.name = None
    summary = summary.rename(columns={'SLA Met': 'SLA MET COUNT', 'SLA Breach': 'SLA BREACH COUNT'})

    if 'SLA MET COUNT' not in summary.columns:
        summary['SLA MET COUNT'] = 0
    if 'SLA BREACH COUNT' not in summary.columns:
        summary['SLA BREACH COUNT'] = 0

    summary['TOTAL DELIVERED ORDERS'] = summary['SLA MET COUNT'] + summary['SLA BREACH COUNT']

    summary['SLA MET%'] = summary.apply(
        lambda row: f"{round(row['SLA MET COUNT'] / row['TOTAL DELIVERED ORDERS'] * 100)}%" if row['TOTAL DELIVERED ORDERS'] > 0 else "0%",
        axis=1
    )

    summary['SLA BREACH%'] = summary.apply(
        lambda row: f"{round(row['SLA BREACH COUNT'] / row['TOTAL DELIVERED ORDERS'] * 100)}%" if row['TOTAL DELIVERED ORDERS'] > 0 else "0%",
        axis=1
    )

    # Step 10: Grand Total row
    total_delivered = summary['TOTAL DELIVERED ORDERS'].sum()
    total_met = summary['SLA MET COUNT'].sum()
    total_breach = summary['SLA BREACH COUNT'].sum()

    grand_total = pd.DataFrame({
        'Order Dark Store': ['Grand Total'],
        'SLA MET COUNT': [total_met],
        'SLA BREACH COUNT': [total_breach],
        'TOTAL DELIVERED ORDERS': [total_delivered],
        'SLA MET%': [f"{round(total_met / total_delivered * 100)}%" if total_delivered > 0 else "0%"],
        'SLA BREACH%': [f"{round(total_breach / total_delivered * 100)}%" if total_delivered > 0 else "0%"]
    })

    summary = summary.reset_index()
    summary_final = pd.concat([summary, grand_total], ignore_index=True)

    return summary_final
