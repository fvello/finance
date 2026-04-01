import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import get_people, get_payment_methods, get_income_sources, get_expense_categories

user = require_auth()

st.title("📊 Financial Analytics")

CSV_FOLDER = os.path.join("csv", user)
INCOME_FOLDER = os.path.join("csv", user, "income")

people_settings = get_people(user)
payment_settings = get_payment_methods(user)
income_settings = get_income_sources(user)
category_settings = get_expense_categories(user)

category_names = [cat["name"] for cat in category_settings]

csv_files = [
    os.path.join(CSV_FOLDER, f)
    for f in os.listdir(CSV_FOLDER)
    if f.endswith(".csv")
]

if not csv_files:
    st.warning("No database files found.")
    st.stop()

all_data = []

for file in csv_files:
    df_file = pd.read_csv(file)

    if "Date" in df_file.columns:
        df_file["Date"] = pd.to_datetime(df_file["Date"], errors="coerce")

    df_file["SourceFile"] = file

    all_data.append(df_file)

df = pd.concat(all_data, ignore_index=True)

df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
df = df.dropna(subset=["Value"])

df["Month"] = df["Date"].dt.strftime("%Y-%m")

data_people = list(df["Person"].dropna().unique()) if "Person" in df.columns else []
data_cards = list(df["Card"].dropna().unique()) if "Card" in df.columns else []
data_categories = list(df["Category"].dropna().unique()) if "Category" in df.columns else []

all_people = sorted(set(people_settings + data_people))
all_cards = sorted(set(payment_settings + data_cards))
all_categories = sorted(set(category_names + data_categories))

col1, col2, col3 = st.columns(3)

with col1:
    selected_persons = st.multiselect(
        "Filter by Person",
        options=all_people,
        default=all_people
    )

with col2:
    selected_cards = st.multiselect(
        "Filter by Card",
        options=all_cards,
        default=all_cards
    )

with col3:
    if all_categories:
        selected_categories = st.multiselect(
            "Filter by Category",
            options=all_categories,
            default=all_categories
        )
    else:
        selected_categories = []

if "Category" in df.columns and selected_categories:
    filtered_df = df[
        (df["Person"].isin(selected_persons)) &
        (df["Card"].isin(selected_cards)) &
        (df["Category"].isin(selected_categories))
    ]
else:
    filtered_df = df[
        (df["Person"].isin(selected_persons)) &
        (df["Card"].isin(selected_cards))
    ]

income_df = None
if os.path.exists(INCOME_FOLDER):
    income_files = [
        os.path.join(INCOME_FOLDER, f)
        for f in os.listdir(INCOME_FOLDER)
        if f.endswith(".csv")
    ]
    
    if income_files:
        income_data = []
        for file in income_files:
            inc_df = pd.read_csv(file)
            income_data.append(inc_df)
        
        income_df = pd.concat(income_data, ignore_index=True)
        
        if "Date" in income_df.columns:
            income_df["Date"] = pd.to_datetime(income_df["Date"], errors="coerce")
        
        income_df["Value"] = pd.to_numeric(income_df["Value"], errors="coerce")
        income_df = income_df.dropna(subset=["Value"])
        income_df["Month"] = income_df["Date"].dt.strftime("%Y-%m")

if income_df is not None:
    st.subheader("💰 Income vs Expenses Overview")
    
    expenses_by_month = filtered_df.groupby("Month")["Value"].sum().reset_index()
    expenses_by_month.columns = ["Month", "Expenses"]
    
    income_by_month = income_df.groupby("Month")["Value"].sum().reset_index()
    income_by_month.columns = ["Month", "Income"]
    
    comparison_df = pd.merge(expenses_by_month, income_by_month, on="Month", how="outer").fillna(0)
    comparison_df["Net"] = comparison_df["Income"] - comparison_df["Expenses"]
    
    col1, col2, col3 = st.columns(3)
    total_income = comparison_df["Income"].sum()
    total_expenses = comparison_df["Expenses"].sum()
    total_net = total_income - total_expenses
    
    col1.metric("Total Income", f"${total_income:,.2f}")
    col2.metric("Total Expenses", f"${total_expenses:,.2f}")
    col3.metric("Net Balance", f"${total_net:,.2f}", delta=f"${total_net:,.2f}")
    
    st.divider()
    
    comparison_long = comparison_df.melt(id_vars=["Month"], value_vars=["Income", "Expenses"],
                                         var_name="Type", value_name="Amount")
    
    fig_comparison = px.bar(
        comparison_long,
        x="Month",
        y="Amount",
        color="Type",
        barmode="group",
        title="Income vs Expenses by Month"
    )
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    st.divider()
    
    st.subheader("📈 Income by Source")
    
    income_by_source = income_df.groupby("Source")["Value"].sum().reset_index()
    
    fig_income_source = px.pie(
        income_by_source,
        names="Source",
        values="Value",
        hole=0.4,
        title="Income Distribution by Source"
    )
    st.plotly_chart(fig_income_source, use_container_width=True)
    
    st.divider()
    
    if "Payer" in income_df.columns:
        st.subheader("👥 Income by Payer")
        
        income_by_payer = income_df.groupby("Payer")["Value"].sum().reset_index()
        
        fig_income_payer = px.pie(
            income_by_payer,
            names="Payer",
            values="Value",
            hole=0.4,
            title="Income Distribution by Payer"
        )
        st.plotly_chart(fig_income_payer, use_container_width=True)
        
        st.divider()

# =========================
# MONTHLY SPENDING
# =========================

st.subheader("Spending by Month")

month_group = filtered_df.groupby("Month")["Value"].sum().reset_index()

fig_month = px.bar(
    month_group,
    x="Month",
    y="Value"
)

st.plotly_chart(fig_month, use_container_width=True)

# =========================
# PIE BY PERSON
# =========================

st.subheader("Spending by Person")

person_group = filtered_df.groupby("Person")["Value"].sum().reset_index()

fig_person = px.pie(
    person_group,
    names="Person",
    values="Value",
    hole=0.4
)

st.plotly_chart(fig_person, use_container_width=True)

# =========================
# PIE BY CARD
# =========================

st.subheader("Spending by Card")

card_group = filtered_df.groupby("Card")["Value"].sum().reset_index()

fig_card = px.pie(
    card_group,
    names="Card",
    values="Value",
    hole=0.4
)

st.plotly_chart(fig_card, use_container_width=True)

# =========================
# PIE BY CATEGORY
# =========================

if "Category" in filtered_df.columns:
    st.subheader("Spending by Category")
    
    category_group = filtered_df.groupby("Category")["Value"].sum().reset_index()
    
    fig_category = px.pie(
        category_group,
        names="Category",
        values="Value",
        hole=0.4
    )
    
    st.plotly_chart(fig_category, use_container_width=True)