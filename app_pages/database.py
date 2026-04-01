import streamlit as st
import pandas as pd
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import get_people, get_payment_methods, get_people_with_user

user = require_auth()

st.title("Database")

CSV_FOLDER = os.path.join("csv", user)
os.makedirs(CSV_FOLDER, exist_ok=True)

people_settings = get_people_with_user(user)
payment_settings = get_payment_methods(user)

today = datetime.date.today()
FILE_NAME = os.path.join(CSV_FOLDER, today.strftime("%Y-%m") + ".csv")

if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    st.warning("No data found yet.")
    st.stop()

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)

if st.button("Save Changes"):
    edited_df.to_csv(FILE_NAME, index=False)
    st.success("Changes saved!")

data_people = list(edited_df["Person"].dropna().unique()) if "Person" in edited_df.columns else []
data_cards = list(edited_df["Card"].dropna().unique()) if "Card" in edited_df.columns else []

person_options = ["All"] + sorted(set(people_settings + data_people))
card_options = ["All"] + sorted(set(payment_settings + data_cards))

person_selected = st.selectbox("Select Person", person_options)
card_selected = st.selectbox("Select Card", card_options)

filtered_df = edited_df.copy()

if person_selected != "All":
    filtered_df = filtered_df[filtered_df["Person"] == person_selected]

if card_selected != "All":
    filtered_df = filtered_df[filtered_df["Card"] == card_selected]

total = filtered_df["Value"].sum()

st.metric("Filtered Total", f"R$ {total:,.2f}")

csv = edited_df.to_csv(index=False).encode("utf-8")