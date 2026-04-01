import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import load_user_settings, save_user_settings, has_settings, auto_categorize_payment_method

user = require_auth()

st.title("⚙️ Settings")

is_new_user = not has_settings(user)

if is_new_user:
    st.info("👋 Welcome! Before you start, set up your People, Payment Methods, Income Sources, and Expense Categories below. These will be used when adding transactions.")
    st.divider()

settings = load_user_settings(user)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("People (Pessoas)")
    st.caption("Add the people who will make purchases")
    
    people = settings.get("people", [])
    
    if not people:
        st.write("_No people added yet_")
    
    for i, person in enumerate(people):
        c1, c2 = st.columns([4, 1])
        with c1:
            new_name = st.text_input(f"Person {i+1}", person, key=f"person_{i}", label_visibility="collapsed")
            if new_name != person:
                people[i] = new_name
        with c2:
            if st.button("🗑️", key=f"del_person_{i}"):
                people.pop(i)
                settings["people"] = people
                save_user_settings(user, settings)
                st.rerun()
    
    new_person = st.text_input("Add Person", key="new_person", placeholder="Type name and press Add")
    if st.button("Add Person"):
        if new_person and new_person not in people:
            people.append(new_person)
            settings["people"] = people
            save_user_settings(user, settings)
            st.rerun()

with col2:
    st.subheader("Payment Methods (Cartões)")
    st.caption("Add your cards and payment options")
    
    payment_methods_raw = settings.get("payment_methods", [])
    
    if payment_methods_raw and isinstance(payment_methods_raw[0], str):
        payment_methods = [{"name": pm, "type": auto_categorize_payment_method(pm)} for pm in payment_methods_raw]
    else:
        payment_methods = payment_methods_raw if payment_methods_raw else []
    
    if not payment_methods:
        st.write("_No payment methods added yet_")
    
    for i, method in enumerate(payment_methods):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            new_name = st.text_input(f"Method {i+1}", method.get("name", method) if isinstance(method, dict) else method, 
                                     key=f"method_{i}", label_visibility="collapsed")
        with c2:
            current_type = method.get("type", "credit") if isinstance(method, dict) else "credit"
            new_type = st.selectbox(
                "Type",
                options=["immediate", "credit"],
                index=0 if current_type == "immediate" else 1,
                key=f"method_type_{i}",
                label_visibility="collapsed"
            )
        with c3:
            if st.button("🗑️", key=f"del_method_{i}"):
                payment_methods.pop(i)
                settings["payment_methods"] = payment_methods
                save_user_settings(user, settings)
                st.rerun()
        
        if isinstance(payment_methods[i], dict):
            payment_methods[i]["name"] = new_name
            payment_methods[i]["type"] = new_type
        else:
            payment_methods[i] = {"name": new_name, "type": new_type}
    
    new_method_name = st.text_input("Add Payment Method", key="new_method", placeholder="e.g., Nubank, Cash")
    col_new_type, col_add = st.columns([2, 1])
    with col_new_type:
        new_method_type = st.selectbox(
            "Type",
            options=["immediate", "credit"],
            key="new_method_type",
            label_visibility="collapsed"
        )
    with col_add:
        if st.button("Add", key="add_method_btn"):
            if new_method_name:
                exists = any(
                    (pm.get("name", pm) if isinstance(pm, dict) else pm) == new_method_name 
                    for pm in payment_methods
                )
                if not exists:
                    payment_methods.append({"name": new_method_name, "type": new_method_type})
                    settings["payment_methods"] = payment_methods
                    save_user_settings(user, settings)
                    st.rerun()


with col3:
    st.subheader("Income Sources")
    st.caption("Add sources of income")
    
    income_sources = settings.get("income_sources", [])
    
    if not income_sources:
        st.write("_No income sources added yet_")
    
    for i, source in enumerate(income_sources):
        c1, c2 = st.columns([4, 1])
        with c1:
            new_name = st.text_input(f"Source {i+1}", source, key=f"source_{i}", label_visibility="collapsed")
            if new_name != source:
                income_sources[i] = new_name
        with c2:
            if st.button("🗑️", key=f"del_source_{i}"):
                income_sources.pop(i)
                settings["income_sources"] = income_sources
                save_user_settings(user, settings)
                st.rerun()
    
    new_source = st.text_input("Add Income Source", key="new_source", placeholder="e.g., Salary, Freelance")
    if st.button("Add Source"):
        if new_source and new_source not in income_sources:
            income_sources.append(new_source)
            settings["income_sources"] = income_sources
            save_user_settings(user, settings)
            st.rerun()

with col4:
    st.subheader("Expense Categories")
    st.caption("Categorize your expenses")
    
    expense_categories = settings.get("expense_categories", [])
    
    if not expense_categories:
        from settings import DEFAULT_EXPENSE_CATEGORIES
        expense_categories = DEFAULT_EXPENSE_CATEGORIES
    
    for i, category in enumerate(expense_categories):
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1:
            cat_icon = st.text_input(f"Icon {i+1}", category.get("icon", "📦"), key=f"cat_icon_{i}", label_visibility="collapsed", max_chars=2)
        with c2:
            cat_name = st.text_input(f"Category {i+1}", category.get("name", ""), key=f"cat_name_{i}", label_visibility="collapsed")
        with c3:
            if st.button("🗑️", key=f"del_cat_{i}"):
                expense_categories.pop(i)
                settings["expense_categories"] = expense_categories
                save_user_settings(user, settings)
                st.rerun()
        
        if isinstance(expense_categories[i], dict):
            expense_categories[i]["icon"] = cat_icon
            expense_categories[i]["name"] = cat_name
        else:
            expense_categories[i] = {"icon": cat_icon, "name": cat_name}
    
    col_new_cat_icon, col_new_cat_name, col_add = st.columns([1, 3, 1])
    with col_new_cat_icon:
        new_cat_icon = st.text_input("Icon", key="new_cat_icon", placeholder="📦", max_chars=2, label_visibility="collapsed")
    with col_new_cat_name:
        new_cat_name = st.text_input("Category Name", key="new_cat_name", placeholder="Category name", label_visibility="collapsed")
    with col_add:
        if st.button("Add", key="add_cat_btn"):
            if new_cat_name:
                exists = any(
                    (cat.get("name", cat) if isinstance(cat, dict) else cat) == new_cat_name 
                    for cat in expense_categories
                )
                if not exists:
                    expense_categories.append({"icon": new_cat_icon if new_cat_icon else "📦", "name": new_cat_name})
                    settings["expense_categories"] = expense_categories
                    save_user_settings(user, settings)
                    st.rerun()

st.divider()

if st.button("Save All Changes", type="primary"):
    settings["people"] = people
    settings["payment_methods"] = payment_methods
    settings["income_sources"] = income_sources
    settings["expense_categories"] = expense_categories
    save_user_settings(user, settings)
    st.success("Settings saved!")

st.caption("Note: Removing a person, payment method, income source, or category from settings does not delete existing transaction data.")
