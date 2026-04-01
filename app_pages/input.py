import streamlit as st
import pandas as pd
import datetime
import os
from auth import require_auth
from settings import get_people_with_user, get_payment_methods, get_category_names, get_payment_methods_with_types, update_balance, get_income_sources

user = require_auth()

st.title("📝 Input")

people = get_people_with_user(user)
payment_methods = get_payment_methods(user)
expense_categories = get_category_names(user)
income_sources = get_income_sources(user)

if not people:
    st.warning("⚠️ You need to set up People first. Go to **Settings** to configure them.")
    st.stop()

if "entry_type" not in st.session_state:
    st.session_state.entry_type = "Expense"

def on_entry_type_change():
    st.session_state.entry_type = st.session_state.entry_type_select

st.selectbox(
    "Entry Type",
    ["Expense", "Income"],
    key="entry_type_select",
    on_change=on_entry_type_change
)

entry_type = st.session_state.entry_type

today = datetime.date.today()

def get_invoice_month(date):
    if date.day >= 20:
        invoice_date = date + pd.DateOffset(months=1)
    else:
        invoice_date = date
    return invoice_date.strftime("%Y-%m")

with st.form("entry_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        entry_date = st.date_input("Date")
        description = st.text_input("Description")
        value = st.number_input("Value", format="%.2f", min_value=0.0)
        person = st.selectbox("Person", people)
    
    with col2:
        if entry_type == "Expense":
            card = st.selectbox("Payment Method", payment_methods if payment_methods else [""])
            category = st.selectbox(
                "Category",
                expense_categories if expense_categories else [""],
                index=0
            )
            parcelas = st.number_input("Parcelas", step=1, min_value=1, format="%d")
        else:
            source = st.selectbox("Income Source", income_sources if income_sources else [""])
    
    submitted = st.form_submit_button("Add Entry")

if submitted:
    if not description:
        st.error("Please provide a description")
    elif value <= 0:
        st.error("Value must be greater than 0")
    else:
        is_expected = entry_date > today
        
        if entry_type == "Expense":
            if not payment_methods:
                st.error("⚠️ You need to set up Payment Methods first. Go to **Settings** to configure them.")
            elif not expense_categories:
                st.error("⚠️ No expense categories found. Go to **Settings** to configure them.")
            else:
                parcelas_int = int(parcelas)
                installment_value = round(value / parcelas_int, 2)
                
                if is_expected:
                    CSV_FOLDER = os.path.join("csv", user, "payments")
                    os.makedirs(CSV_FOLDER, exist_ok=True)
                    
                    for i in range(parcelas_int):
                        installment_date = pd.Timestamp(entry_date) + pd.DateOffset(months=i)
                        invoice_month = get_invoice_month(installment_date)
                        FILE_NAME = os.path.join(CSV_FOLDER, f"{invoice_month}.csv")
                        
                        if os.path.exists(FILE_NAME):
                            df = pd.read_csv(FILE_NAME)
                        else:
                            df = pd.DataFrame(
                                columns=["Date", "Description", "Value", "Payee", "Payment_Method", "Category", "Status", "Paid_Date"]
                            )
                        
                        new_row = pd.DataFrame(
                            [[
                                installment_date.date(),
                                f"{description} ({i+1}/{parcelas_int})" if parcelas_int > 1 else description,
                                installment_value,
                                person,
                                card,
                                category,
                                "Pending",
                                ""
                            ]],
                            columns=["Date", "Description", "Value", "Payee", "Payment_Method", "Category", "Status", "Paid_Date"]
                        )
                        
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(FILE_NAME, index=False)
                    
                    st.success(f"Expected payment added! ({parcelas_int} installment{'s' if parcelas_int > 1 else ''})")
                
                else:
                    CSV_FOLDER = os.path.join("csv", user)
                    os.makedirs(CSV_FOLDER, exist_ok=True)
                    
                    for i in range(parcelas_int):
                        installment_date = pd.Timestamp(entry_date) + pd.DateOffset(months=i)
                        invoice_month = get_invoice_month(installment_date)
                        FILE_NAME = os.path.join(CSV_FOLDER, f"{invoice_month}.csv")
                        
                        if os.path.exists(FILE_NAME):
                            df = pd.read_csv(FILE_NAME)
                        else:
                            df = pd.DataFrame(
                                columns=["Date", "Description", "Value", "Person", "Card", "Category", "Parcelas"]
                            )
                        
                        if "Category" not in df.columns:
                            df["Category"] = "General/Daily"
                        
                        new_row = pd.DataFrame(
                            [[
                                installment_date.date(),
                                f"{description} ({i+1}/{parcelas_int})" if parcelas_int > 1 else description,
                                installment_value,
                                person,
                                card,
                                category,
                                parcelas_int
                            ]],
                            columns=["Date", "Description", "Value", "Person", "Card", "Category", "Parcelas"]
                        )
                        
                        df = pd.concat([df, new_row], ignore_index=True)
                        df.to_csv(FILE_NAME, index=False)
                    
                    payment_methods_with_types = get_payment_methods_with_types(user)
                    method_type = next(
                        (pm["type"] for pm in payment_methods_with_types if pm["name"] == card),
                        "credit"
                    )
                    
                    if method_type == "immediate":
                        total_amount = round(value, 2)
                        update_balance(user, -total_amount, f"{description} - {card}", "expense")
                    
                    st.success(f"Expense added! ({parcelas_int} installment{'s' if parcelas_int > 1 else ''})")
                
                st.rerun()
        
        else:
            if not income_sources:
                st.error("⚠️ You need to set up Income Sources first. Go to **Settings** to configure them.")
            else:
                invoice_month = get_invoice_month(pd.Timestamp(entry_date))
                
                if is_expected:
                    CSV_FOLDER = os.path.join("csv", user, "income")
                    os.makedirs(CSV_FOLDER, exist_ok=True)
                    FILE_NAME = os.path.join(CSV_FOLDER, f"{invoice_month}.csv")
                    
                    if os.path.exists(FILE_NAME):
                        df = pd.read_csv(FILE_NAME)
                    else:
                        df = pd.DataFrame(
                            columns=["Date", "Description", "Value", "Payer", "Source", "Status", "Received_Date"]
                        )
                    
                    new_row = pd.DataFrame(
                        [[
                            entry_date,
                            description,
                            value,
                            person,
                            source,
                            "Pending",
                            ""
                        ]],
                        columns=["Date", "Description", "Value", "Payer", "Source", "Status", "Received_Date"]
                    )
                    
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(FILE_NAME, index=False)
                    
                    st.success("Expected income added!")
                
                else:
                    CSV_FOLDER = os.path.join("csv", user)
                    os.makedirs(CSV_FOLDER, exist_ok=True)
                    FILE_NAME = os.path.join(CSV_FOLDER, f"{invoice_month}.csv")
                    
                    if os.path.exists(FILE_NAME):
                        df = pd.read_csv(FILE_NAME)
                    else:
                        df = pd.DataFrame(
                            columns=["Date", "Description", "Value", "Person", "Card", "Category", "Parcelas", "Type", "Source"]
                        )
                    
                    for col in ["Type", "Source"]:
                        if col not in df.columns:
                            df[col] = ""
                    
                    new_row = pd.DataFrame(
                        [[
                            entry_date,
                            description,
                            value,
                            person,
                            "",
                            "",
                            1,
                            "Income",
                            source
                        ]],
                        columns=["Date", "Description", "Value", "Person", "Card", "Category", "Parcelas", "Type", "Source"]
                    )
                    
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(FILE_NAME, index=False)
                    
                    update_balance(user, value, f"{description} - {source}", "income")
                    
                    st.success("Income added!")
                
                st.rerun()
