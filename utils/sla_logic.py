import pandas as pd

valid_stores = [
    "BLR_kalyan-nagar", "BLR_koramangala", "CH_Periyamet",
    "DEL_malviya-nagar", "HYD_manikonda", "KOL-Topsia",
    "MUM_andheri", "PUN_koregaon-park"
]

def process_sla_data(df, filter_date):
    df.columns = df.columns.str.strip()
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce', dayfirst=True)
    df['End Time (Actual)'] = pd.to_datetime(df['End Time (Actual)'], errors='coerce', dayfirst=True)
    df = df[df['Order Dark Store'].isin(valid_stores)]
    df = df[df['Order Status'] == 'Delivered']
    df = df[df['End Time (Actual)'].dt.strftime('%d/%m/%Y') == filter_date]
    df['Delivery Type'] = df['Order Date'].apply(lambda x: 'Quick' if 0 <= x.hour < 15 else 'Non Quick')
    df['TAT'] = df['Order Date'].apply(lambda x: x.replace(hour=23, minute=59, second=59) if x.hour < 15 else (x + pd.Timedelta(days=1)).replace(hour=23, minute=59, second=59))
    df['SLA STATUS'] = df.apply(lambda row: 'SLA Breach' if row['End Time (Actual)'] > row['TAT'] else 'SLA Met', axis=1)
    summary = df.groupby('Order Dark Store')['SLA STATUS'].value_counts().unstack(fill_value=0).reset_index()
    summary['TOTAL DELIVERED'] = summary['SLA Met'] + summary['SLA Breach']
    summary['SLA MET%'] = (summary['SLA Met'] / summary['TOTAL DELIVERED'] * 100).round(0).astype(str) + '%'
    summary['SLA BREACH%'] = (summary['SLA Breach'] / summary['TOTAL DELIVERED'] * 100).round(0).astype(str) + '%'
    return summary
