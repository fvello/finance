import streamlit as st
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import get_people, get_payment_methods, get_category_names

user = require_auth()

st.title("💳 Invoice Summary")

CSV_FOLDER = os.path.join("csv", user)

people_settings = get_people(user)
payment_settings = get_payment_methods(user)
category_settings = get_category_names(user)

csv_files = sorted(
    [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
)

if not csv_files:
    st.warning("No invoices found.")
    st.stop()

selected_invoice = st.selectbox(
    "Select Invoice",
    csv_files
)

file_path = os.path.join(CSV_FOLDER, selected_invoice)

df = pd.read_csv(file_path)

df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

df = df.dropna(subset=["Value"])


data_people = list(df["Person"].dropna().unique()) if "Person" in df.columns else []
data_cards = list(df["Card"].dropna().unique()) if "Card" in df.columns else []
data_categories = list(df["Category"].dropna().unique()) if "Category" in df.columns else []

all_people = sorted(set(people_settings + data_people))
all_cards = sorted(set(payment_settings + data_cards))
all_categories = sorted(set(category_settings + data_categories))

col1, col2, col3 = st.columns(3)

with col1:
    persons = st.multiselect(
        "Person",
        all_people,
        default=all_people
    )

with col2:
    cards = st.multiselect(
        "Card",
        all_cards,
        default=all_cards
    )

with col3:
    if all_categories:
        categories = st.multiselect(
            "Category",
            all_categories,
            default=all_categories
        )
    else:
        categories = []

if "Category" in df.columns and categories:
    filtered_df = df[
        (df["Person"].isin(persons)) &
        (df["Card"].isin(cards)) &
        (df["Category"].isin(categories))
    ]
else:
    filtered_df = df[
        (df["Person"].isin(persons)) &
        (df["Card"].isin(cards))
    ]


# =========================
# TOTALS
# =========================

st.subheader("Invoice by Card")

card_totals = filtered_df.groupby("Card")["Value"].sum().reset_index()

st.dataframe(card_totals)

total = card_totals["Value"].sum()

st.metric(
    "Total Invoice",
    f"R$ {total:,.2f}"
)


# =========================
# SHOW PURCHASES
# =========================

st.subheader("Purchases")

st.dataframe(filtered_df)