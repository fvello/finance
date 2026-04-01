import streamlit as st
import pandas as pd
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import get_people, get_payment_methods, get_category_names, get_payment_methods_with_types, update_balance

user = require_auth()

st.title("📋 Expected Payments")

CSV_FOLDER = os.path.join("csv", user, "payments")

people = get_people(user)
payment_methods = get_payment_methods(user)
expense_categories = get_category_names(user)

if not os.path.exists(CSV_FOLDER):
    st.info("No payment entries found. Go to **Expected Payment Input** to add your first payment entry.")
    st.stop()

csv_files = [
    os.path.join(CSV_FOLDER, f)
    for f in os.listdir(CSV_FOLDER)
    if f.endswith(".csv")
]

if not csv_files:
    st.info("No payment entries found. Go to **Expected Payment Input** to add your first payment entry.")
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
    st.warning("No valid payment data found.")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    selected_month = st.selectbox("Filter by Month", options=available_months)
with col2:
    status_filter = st.selectbox("Filter by Status", options=["All", "Pending", "Paid"])

filtered_df = df[df["Month"] == selected_month].copy()

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["Status"] == status_filter]

st.divider()

if filtered_df.empty:
    st.info(f"No payment entries found for {selected_month}")
else:
    total_expected = filtered_df["Value"].sum()
    total_paid = filtered_df[filtered_df["Status"] == "Paid"]["Value"].sum()
    total_pending = filtered_df[filtered_df["Status"] == "Pending"]["Value"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Expected", f"R$ {total_expected:,.2f}")
    col2.metric("Total Paid", f"R$ {total_paid:,.2f}")
    col3.metric("Total Pending", f"R$ {total_pending:,.2f}")
    
    st.divider()
    
    for idx, row in filtered_df.iterrows():
        entry_key = f"{idx}_{row['SourceFile']}"
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
            
            with col1:
                st.write(f"**{row['Date'].strftime('%Y-%m-%d')}**")
            
            with col2:
                st.write(f"{row['Description']}")
                st.caption(f"Payee: {row['Payee']} | Method: {row['Payment_Method']} | Category: {row['Category']}")
            
            with col3:
                st.write(f"R$ {row['Value']:,.2f}")
                if row['Status'] == 'Paid' and pd.notna(row.get('Paid_Date')) and row.get('Paid_Date'):
                    st.caption(f"Paid: {row['Paid_Date']}")
            
            with col4:
                is_paid = st.checkbox(
                    "Paid",
                    value=row['Status'] == 'Paid',
                    key=f"check_{entry_key}"
                )
                
                if is_paid != (row['Status'] == 'Paid'):
                    file_path = row['SourceFile']
                    df_file = pd.read_csv(file_path)
                    
                    row_idx = df_file[
                        (df_file['Date'] == row['Date'].strftime('%Y-%m-%d')) &
                        (df_file['Description'] == row['Description']) &
                        (df_file['Value'] == row['Value'])
                    ].index
                    
                    if len(row_idx) > 0:
                        if is_paid:
                            df_file.loc[row_idx[0], 'Status'] = 'Paid'
                            df_file.loc[row_idx[0], 'Paid_Date'] = datetime.date.today().strftime('%Y-%m-%d')
                            
                            payment_amount = float(row['Value'])
                            payment_description = f"{row['Description']} - {row['Payment_Method']} (to {row['Payee']})"
                            update_balance(user, -payment_amount, payment_description, "expense")
                        else:
                            df_file.loc[row_idx[0], 'Status'] = 'Pending'
                            df_file.loc[row_idx[0], 'Paid_Date'] = ''
                            
                            payment_amount = float(row['Value'])
                            payment_description = f"[REVERSED] {row['Description']} - {row['Payment_Method']} (to {row['Payee']})"
                            update_balance(user, payment_amount, payment_description, "adjustment")
                        
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
                        st.success("Payment entry deleted!")
                        st.rerun()
            
            if st.session_state.get(f"editing_{entry_key}", False):
                with st.form(f"edit_form_{entry_key}"):
                    st.subheader("Edit Payment Entry")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        edit_date = st.date_input("Expected Date", value=row['Date'].date())
                        edit_description = st.text_input("Description", value=row['Description'])
                        edit_value = st.number_input("Value", format="%.2f", min_value=0.0, value=float(row['Value']))
                    
                    with col_b:
                        edit_payee = st.selectbox(
                            "Payee",
                            options=people,
                            index=people.index(row['Payee']) if row['Payee'] in people else 0
                        ) if people else st.text_input("Payee", value=row['Payee'])
                        
                        edit_method = st.selectbox(
                            "Payment Method",
                            options=payment_methods,
                            index=payment_methods.index(row['Payment_Method']) if row['Payment_Method'] in payment_methods else 0
                        ) if payment_methods else st.text_input("Payment Method", value=row['Payment_Method'])
                        
                        edit_category = st.selectbox(
                            "Category",
                            options=expense_categories,
                            index=expense_categories.index(row['Category']) if row['Category'] in expense_categories else 0
                        ) if expense_categories else st.text_input("Category", value=row['Category'])
                    
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
                            df_file.loc[row_idx[0], 'Payee'] = edit_payee
                            df_file.loc[row_idx[0], 'Payment_Method'] = edit_method
                            df_file.loc[row_idx[0], 'Category'] = edit_category
                            
                            df_file.to_csv(file_path, index=False)
                            st.session_state[f"editing_{entry_key}"] = False
                            st.success("Payment entry updated!")
                            st.rerun()
                    
                    if cancel_submitted:
                        st.session_state[f"editing_{entry_key}"] = False
                        st.rerun()
            
            st.divider()
