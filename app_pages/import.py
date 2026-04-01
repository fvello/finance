import streamlit as st
import pandas as pd
import datetime
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth

user = require_auth()

st.title("Import CSV (Append to Database)")

CSV_FOLDER = os.path.join("csv", user)
os.makedirs(CSV_FOLDER, exist_ok=True)

today = datetime.date.today()
FILE_NAME = os.path.join(CSV_FOLDER, today.strftime("%Y-%m") + ".csv")


REQUIRED_COLUMNS = ["Date", "Description", "Value", "Person", "Card", "Parcelas"]
uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        new_df = pd.read_csv(uploaded_file)

        st.subheader("Preview of Uploaded File")
        st.dataframe(new_df)

        # ---- VALIDATE COLUMNS ----
        if not all(col in new_df.columns for col in REQUIRED_COLUMNS):
            st.error(f"CSV must contain columns: {REQUIRED_COLUMNS}")
            st.stop()

        if st.button("Import CSV"):

            # Load existing database or create new one
            if os.path.exists(FILE_NAME):
                existing_df = pd.read_csv(FILE_NAME)
            else:
                existing_df = pd.DataFrame(columns=REQUIRED_COLUMNS)

            # Append
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)

            # Save
            combined_df.to_csv(FILE_NAME, index=False)

            st.success("Data successfully appended to database!")

    except Exception as e:
        st.error(f"Error reading file: {e}")