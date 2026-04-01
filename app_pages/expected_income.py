import streamlit as st
import pandas as pd
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import get_income_sources, get_people, update_balance

user = require_auth()

st.title("📋 Expected Income")

CSV_FOLDER = os.path.join("csv", user, "income")

income_sources = get_income_sources(user)
people = get_people(user)

if not os.path.exists(CSV_FOLDER):
    st.info("No income entries found. Go to **Income Input** to add your first income entry.")
    st.stop()

csv_files = [
    os.path.join(CSV_FOLDER, f)
    for f in os.listdir(CSV_FOLDER)
    if f.endswith(".csv")
]

if not csv_files:
    st.info("No income entries found. Go to **Income Input** to add your first income entry.")
    st.stop()

all_data = []
for file in csv_files:
    df = pd.read_csv(file)
    df["SourceFile"] = file
    all_data.append(df)

df = pd.concat(all_data, ignore_index=True)

if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("Date", ascending=False)

df["Month"] = df["Date"].dt.strftime("%Y-%m")

available_months = sorted(df["Month"].dropna().unique(), reverse=True)

if not available_months:
    st.warning("No valid income data found.")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    selected_month = st.selectbox("Filter by Month", options=available_months)
with col2:
    status_filter = st.selectbox("Filter by Status", options=["All", "Pending", "Received"])

filtered_df = df[df["Month"] == selected_month].copy()

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["Status"] == status_filter]

st.divider()

if filtered_df.empty:
    st.info(f"No income entries found for {selected_month}")
else:
    total_expected = filtered_df["Value"].sum()
    total_received = filtered_df[filtered_df["Status"] == "Received"]["Value"].sum()
    total_pending = filtered_df[filtered_df["Status"] == "Pending"]["Value"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Expected", f"${total_expected:,.2f}")
    col2.metric("Total Received", f"${total_received:,.2f}")
    col3.metric("Total Pending", f"${total_pending:,.2f}")
    
    st.divider()
    
    for idx, row in filtered_df.iterrows():
        entry_key = f"{idx}_{row['SourceFile']}"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            
            with col1:
                st.write(f"**{row['Date'].strftime('%Y-%m-%d')}**")
            
            with col2:
                st.write(f"{row['Description']}")
                st.caption(f"Source: {row['Source']} | Payer: {row['Payer']}")
            
            with col3:
                st.write(f"${row['Value']:,.2f}")
                if row['Status'] == 'Received' and pd.notna(row.get('Received_Date')) and row.get('Received_Date'):
                    st.caption(f"Received: {row['Received_Date']}")
            
            with col4:
                is_received = st.checkbox(
                    "Received",
                    value=row['Status'] == 'Received',
                    key=f"check_{entry_key}"
                )
                
                if is_received != (row['Status'] == 'Received'):
                    file_path = row['SourceFile']
                    df_file = pd.read_csv(file_path)
                    
                    row_idx = df_file[
                        (df_file['Date'] == row['Date'].strftime('%Y-%m-%d')) &
                        (df_file['Description'] == row['Description']) &
                        (df_file['Value'] == row['Value'])
                    ].index
                    
                    if len(row_idx) > 0:
                        if is_received:
                            df_file.loc[row_idx[0], 'Status'] = 'Received'
                            df_file.loc[row_idx[0], 'Received_Date'] = datetime.date.today().strftime('%Y-%m-%d')
                            
                            income_amount = float(row['Value'])
                            income_description = f"{row['Description']} - {row['Source']} (from {row['Payer']})"
                            update_balance(user, income_amount, income_description, "income")
                        else:
                            df_file.loc[row_idx[0], 'Status'] = 'Pending'
                            df_file.loc[row_idx[0], 'Received_Date'] = ''
                            
                            income_amount = float(row['Value'])
                            income_description = f"[REVERSED] {row['Description']} - {row['Source']} (from {row['Payer']})"
                            update_balance(user, -income_amount, income_description, "adjustment")
                        
                        df_file.to_csv(file_path, index=False)
                        st.rerun()
            
            col_edit, col_delete, col_space = st.columns([1, 1, 6])
            
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_btn_{entry_key}"):
                    st.session_state[f"editing_{entry_key}"] = True
            
            with col_delete:
                if st.button("🗑️ Delete", key=f"del_btn_{entry_key}"):
                    file_path = row['SourceFile']
                    df_file = pd.read_csv(file_path)
                    
                    row_idx = df_file[
                        (df_file['Date'] == row['Date'].strftime('%Y-%m-%d')) &
                        (df_file['Description'] == row['Description']) &
                        (df_file['Value'] == row['Value'])
                    ].index
                    
                    if len(row_idx) > 0:
                        df_file = df_file.drop(row_idx[0])
                        df_file.to_csv(file_path, index=False)
                        st.success("Income entry deleted!")
                        st.rerun()
            
            if st.session_state.get(f"editing_{entry_key}", False):
                with st.form(f"edit_form_{entry_key}"):
                    st.subheader("Edit Income Entry")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        edit_date = st.date_input("Expected Date", value=row['Date'].date())
                        edit_description = st.text_input("Description", value=row['Description'])
                        edit_value = st.number_input("Value", format="%.2f", min_value=0.0, value=float(row['Value']))
                    
                    with col_b:
                        edit_payer = st.selectbox(
                            "Payer",
                            options=people,
                            index=people.index(row['Payer']) if row['Payer'] in people else 0
                        ) if people else st.text_input("Payer", value=row['Payer'])
                        
                        edit_source = st.selectbox(
                            "Income Source",
                            options=income_sources,
                            index=income_sources.index(row['Source']) if row['Source'] in income_sources else 0
                        ) if income_sources else st.text_input("Source", value=row['Source'])
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        save_submitted = st.form_submit_button("💾 Save Changes", type="primary")
                    
                    with col_cancel:
                        cancel_submitted = st.form_submit_button("❌ Cancel")
                    
                    if save_submitted:
                        file_path = row['SourceFile']
                        df_file = pd.read_csv(file_path)
                        
                        row_idx = df_file[
                            (df_file['Date'] == row['Date'].strftime('%Y-%m-%d')) &
                            (df_file['Description'] == row['Description']) &
                            (df_file['Value'] == row['Value'])
                        ].index
                        
                        if len(row_idx) > 0:
                            df_file.loc[row_idx[0], 'Date'] = edit_date.strftime('%Y-%m-%d')
                            df_file.loc[row_idx[0], 'Description'] = edit_description
                            df_file.loc[row_idx[0], 'Value'] = edit_value
                            df_file.loc[row_idx[0], 'Payer'] = edit_payer
                            df_file.loc[row_idx[0], 'Source'] = edit_source
                            
                            df_file.to_csv(file_path, index=False)
                            st.session_state[f"editing_{entry_key}"] = False
                            st.success("Income entry updated!")
                            st.rerun()
                    
                    if cancel_submitted:
                        st.session_state[f"editing_{entry_key}"] = False
                        st.rerun()
            
            st.divider()
