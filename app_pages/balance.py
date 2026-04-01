import streamlit as st
import pandas as pd
import os
import sys
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import (
    get_balance,
    get_balance_history,
    update_balance,
    get_credit_payment_methods,
    get_immediate_payment_methods,
    get_expense_categories,
    get_credit_card_payments_total,
    get_credit_card_payments_total_by_card,
    update_card_payment_status,
)

user = require_auth()

st.set_page_config(layout="wide")

current_balance = get_balance(user)
balance_history = get_balance_history(user, limit=100)
credit_methods = get_credit_payment_methods(user)
immediate_methods = get_immediate_payment_methods(user)

CSV_FOLDER = os.path.join("csv", user)
INCOME_FOLDER = os.path.join("csv", user, "income")
PAYMENT_FOLDER = os.path.join("csv", user, "payments")

current_month = datetime.date.today().strftime("%Y-%m")
current_month_file = os.path.join(CSV_FOLDER, f"{current_month}.csv")

credit_cards_breakdown = {}
immediate_breakdown = {}
credit_to_pay = 0.0
month_spending_immediate = 0.0
month_spending_credit = 0.0
df = None

if os.path.exists(current_month_file):
    df = pd.read_csv(current_month_file)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Value"])
    
    if "Card" in df.columns:
        credit_expenses = df[df["Card"].isin(credit_methods)]
        credit_to_pay_raw = credit_expenses["Value"].sum()
        paid_credit_total = get_credit_card_payments_total(user, current_month)
        credit_to_pay = max(0.0, credit_to_pay_raw - paid_credit_total)
        
        for card in credit_methods:
            card_total = credit_expenses[credit_expenses["Card"] == card]["Value"].sum()
            card_paid = get_credit_card_payments_total_by_card(user, card, current_month)
            card_unpaid = max(0.0, card_total - card_paid)
            if card_total > 0 or card_paid > 0:
                credit_cards_breakdown[card] = card_unpaid
        
        immediate_expenses = df[df["Card"].isin(immediate_methods)]
        month_spending_immediate = immediate_expenses["Value"].sum()
        month_spending_credit = credit_to_pay_raw
        
        for method in immediate_methods:
            method_total = immediate_expenses[immediate_expenses["Card"] == method]["Value"].sum()
            if method_total > 0:
                immediate_breakdown[method] = method_total

month_income = 0.0
pending_income = 0.0
pending_incomes_list = []

if os.path.exists(INCOME_FOLDER):
    income_files = [
        os.path.join(INCOME_FOLDER, f)
        for f in os.listdir(INCOME_FOLDER)
        if f.endswith(".csv")
    ]
    
    if income_files:
        all_income_data = []
        for file in income_files:
            inc_df = pd.read_csv(file)
            all_income_data.append(inc_df)
        
        income_df = pd.concat(all_income_data, ignore_index=True)
        
        if "Date" in income_df.columns:
            income_df["Date"] = pd.to_datetime(income_df["Date"], errors="coerce")
            income_df["Month"] = income_df["Date"].dt.strftime("%Y-%m")
            
            current_month_income = income_df[income_df["Month"] == current_month]
            received_income = current_month_income[current_month_income["Status"] == "Received"]["Value"].sum()
            month_income = received_income
            
            pending_income_df = income_df[income_df["Status"] == "Pending"].copy()
            pending_income = pending_income_df["Value"].sum()
            
            if not pending_income_df.empty:
                pending_income_df = pending_income_df.sort_values("Date")
                for idx, row in pending_income_df.head(5).iterrows():
                    pending_incomes_list.append({
                        "date": row["Date"].strftime("%Y-%m-%d"),
                        "description": row["Description"],
                        "value": row["Value"],
                        "payer": row.get("Payer", "N/A")
                    })

pending_payment = 0.0
pending_payments_list = []

if os.path.exists(PAYMENT_FOLDER):
    payment_files = [
        os.path.join(PAYMENT_FOLDER, f)
        for f in os.listdir(PAYMENT_FOLDER)
        if f.endswith(".csv")
    ]
    
    if payment_files:
        all_payment_data = []
        for file in payment_files:
            pay_df = pd.read_csv(file)
            all_payment_data.append(pay_df)
        
        payment_df = pd.concat(all_payment_data, ignore_index=True)
        
        if "Date" in payment_df.columns:
            payment_df["Date"] = pd.to_datetime(payment_df["Date"], errors="coerce")
            payment_df["Month"] = payment_df["Date"].dt.strftime("%Y-%m")
            
            pending_payment_df = payment_df[payment_df["Status"] == "Pending"].copy()
            pending_payment = pending_payment_df["Value"].sum()
            
            if not pending_payment_df.empty:
                pending_payment_df = pending_payment_df.sort_values("Date")
                for idx, row in pending_payment_df.head(5).iterrows():
                    pending_payments_list.append({
                        "date": row["Date"].strftime("%Y-%m-%d"),
                        "description": row["Description"],
                        "value": row["Value"],
                        "payee": row.get("Payee", "N/A")
                    })

net_worth = current_balance - credit_to_pay
net_pending = pending_income - pending_payment
total_spending = month_spending_immediate + month_spending_credit
savings = month_income - total_spending

expense_categories = get_expense_categories(user)
category_breakdown = {}

if os.path.exists(current_month_file):
    if "Category" in df.columns:
        for category in expense_categories:
            cat_name = category["name"]
            cat_total = df[df["Category"] == cat_name]["Value"].sum()
            if cat_total > 0:
                category_breakdown[cat_name] = {
                    "icon": category["icon"],
                    "total": cat_total
                }

# ===== HEADER WITH MAIN BALANCE =====
col_balance, col_net, col_credit = st.columns([2, 1.5, 1.5])

with col_balance:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 1rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">💰 Current Balance</div>
        <div style="font-size: 2.2rem; font-weight: bold;">R$ {current_balance:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_net:
    st.markdown(f"""
    <div style="background: {'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' if net_worth >= 0 else 'linear-gradient(135deg, #eb3349 0%, #f45c43 100%)'}; 
                padding: 1.5rem; border-radius: 1rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">💵 Net Worth</div>
        <div style="font-size: 1.8rem; font-weight: bold;">R$ {net_worth:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_credit:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 1.5rem; border-radius: 1rem; color: white;">
        <div style="font-size: 0.9rem; opacity: 0.9;">💳 Credit to Pay</div>
        <div style="font-size: 1.8rem; font-weight: bold;">R$ {credit_to_pay:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

if current_balance < 0:
    st.error("⚠️ Your balance is negative! Consider adding funds.")
elif current_balance < 100:
    st.warning("⚠️ Your balance is running low!")

st.markdown("")

# ===== PENDING SUMMARY =====
st.markdown("#### 📊 Pending Overview")
col_pending1, col_pending2, col_pending3 = st.columns(3)

with col_pending1:
    st.metric("📥 Pending Income", f"R$ {pending_income:,.2f}")

with col_pending2:
    st.metric("💸 Pending Payments", f"R$ {pending_payment:,.2f}")

with col_pending3:
    st.metric("📈 Net Pending", f"R$ {net_pending:,.2f}", 
            delta=f"+R$ {net_pending:,.2f}" if net_pending >= 0 else f"R$ {net_pending:,.2f}")

st.markdown("---")

# ===== MAIN CONTENT: TWO COLUMNS =====
col_main_left, col_main_right = st.columns([1, 1])

with col_main_left:
    # Monthly Summary
    st.markdown("#### 📅 Monthly Summary")
    
    col_sum1, col_sum2 = st.columns(2)
    with col_sum1:
        st.metric("💰 Income Received", f"R$ {month_income:,.2f}")
    with col_sum2:
        st.metric("💸 Total Spent", f"R$ {total_spending:,.2f}")

    st.markdown("")
    
    # Category Breakdown
    if category_breakdown:
        st.markdown("#### 📂 Expenses by Category")
        sorted_categories = sorted(category_breakdown.items(), key=lambda x: x[1]["total"], reverse=True)
        
        for cat_name, cat_data in sorted_categories[:6]:
            cat_total = cat_data["total"]
            cat_icon = cat_data["icon"]
            percent = (cat_total / total_spending * 100) if total_spending > 0 else 0
            
            st.markdown(f"**{cat_icon} {cat_name}**")
            st.progress(min(percent / 100, 1.0))
            col_cat_val, col_cat_pct = st.columns([3, 1])
            with col_cat_val:
                st.caption(f"R$ {cat_total:,.2f}")
            with col_cat_pct:
                st.caption(f"{percent:.1f}%")

with col_main_right:
    # Pending Lists
    col_pend_left, col_pend_right = st.columns([1, 1])
    
    with col_pend_left:
        st.markdown("#### 📥 Expected Income")
        if not pending_incomes_list:
            st.info("No pending income")
        else:
            for income in pending_incomes_list[:4]:
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 0.7rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid #3b82f6;">
                    <div style="font-size: 0.8rem; color: #666;">{income['date']}</div>
                    <div style="font-weight: 600; color: #666;">{income['description']}</div>
                    <div style="font-size: 0.8rem; color: #059669;">R$ {income['value']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
    
    with col_pend_right:
        st.markdown("#### 💸 Expected Payments")
        if not pending_payments_list:
            st.info("No pending payments")
        else:
            for payment in pending_payments_list[:4]:
                st.markdown(f"""
                <div style="background: #fef2f2; padding: 0.7rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid #ef4444;">
                    <div style="font-size: 0.8rem; color: #666;">{payment['date']}</div>
                    <div style="font-weight: 600; color: #666;">{payment['description']}</div>
                    <div style="font-size: 0.8rem; color: #dc2626;">R$ {payment['value']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")

# ===== PAYMENT METHODS BREAKDOWN =====
st.markdown("#### 💳 Payment Methods This Month")

col_pay_left, col_pay_right = st.columns([1, 1])

with col_pay_left:
    st.markdown("**🏦 Credit Cards**")
    if not credit_cards_breakdown:
        st.caption("No credit card expenses")
    else:
        for card_name, card_total in credit_cards_breakdown.items():
            col_card, col_val, col_pay = st.columns([2, 1.5, 1])
            with col_card:
                st.markdown(f"• {card_name}")
            with col_val:
                st.markdown(f"**R$ {card_total:,.2f}**")
            with col_pay:
                if card_total > 0:
                    with st.popover("💵 Pay"):
                        pay_card_amount = st.number_input(
                            "Amount",
                            format="%.2f",
                            min_value=0.01,
                            max_value=float(card_total),
                            value=float(card_total),
                            key=f"pay_{card_name.replace(' ', '_')}"
                        )
                        if st.button("Confirm", key=f"btn_{card_name.replace(' ', '_')}", type="primary"):
                            if pay_card_amount > 0:
                                desc = f"Credit card payment - {card_name}"
                                update_balance(user, -pay_card_amount, desc, "expense")
                                update_card_payment_status(user, card_name, pay_card_amount)
                                st.success(f"Paid R$ {pay_card_amount:,.2f}!")
                                st.rerun()
                else:
                    st.caption("✅ Paid")

with col_pay_right:
    st.markdown("**💸 Immediate Payments**")
    if not immediate_breakdown:
        st.caption("No immediate payment expenses")
    else:
        for method_name, method_total in immediate_breakdown.items():
            col_meth, col_mval = st.columns([2, 2])
            with col_meth:
                st.markdown(f"• {method_name}")
            with col_mval:
                st.markdown(f"**R$ {method_total:,.2f}**")

# Pay All Credit Cards
if credit_to_pay > 0:
    st.markdown("")
    with st.expander("💳 Pay All Credit Cards"):
        with st.form("pay_all_credit_form"):
            st.info(f"Total credit debt: R$ {credit_to_pay:,.2f}")
            pay_amount = st.number_input(
                "Amount to Pay",
                format="%.2f",
                min_value=0.01,
                max_value=float(credit_to_pay),
                value=float(credit_to_pay)
            )
            pay_description = st.text_input("Description", value="Credit card payment - All")
            pay_submitted = st.form_submit_button("Pay All", type="primary")
            
            if pay_submitted and pay_amount > 0:
                desc = pay_description if pay_description else "Credit card payment - All"
                update_balance(user, -pay_amount, desc, "expense")
                update_card_payment_status(user, "All", pay_amount, desc)
                st.success(f"Paid R$ {pay_amount:,.2f}!")
                st.rerun()

st.markdown("---")

# ===== QUICK ACTIONS & TRANSACTIONS =====
col_actions, col_history = st.columns([1, 1])

with col_actions:
    with st.expander("⚙️ Quick Actions", expanded=False):
        col_action1, col_action2, col_action3 = st.columns(3)

        with col_action1:
            with st.form("add_money_form"):
                st.markdown("**➕ Add Money**")
                add_amount = st.number_input("Amount", format="%.2f", min_value=0.01, key="add_amt")
                add_description = st.text_input("Description", placeholder="e.g., ATM withdrawal", key="add_desc")
                add_submitted = st.form_submit_button("Add", type="primary")
                
                if add_submitted and add_amount > 0:
                    desc = add_description if add_description else "Manual addition"
                    update_balance(user, add_amount, desc, "adjustment")
                    st.success(f"Added R$ {add_amount:,.2f}!")
                    st.rerun()

        with col_action2:
            with st.form("remove_money_form"):
                st.markdown("**➖ Remove Money**")
                remove_amount = st.number_input("Amount", format="%.2f", min_value=0.01, key="remove_amt")
                remove_description = st.text_input("Description", placeholder="e.g., Cash out", key="remove_desc")
                remove_submitted = st.form_submit_button("Remove")
                
                if remove_submitted and remove_amount > 0:
                    desc = remove_description if remove_description else "Manual removal"
                    update_balance(user, -remove_amount, desc, "adjustment")
                    st.success(f"Removed R$ {remove_amount:,.2f}!")
                    st.rerun()

        with col_action3:
            with st.form("set_balance_form"):
                st.markdown("**🔄 Set Balance**")
                set_amount = st.number_input("Amount", format="%.2f", min_value=0.0, key="set_amt")
                set_description = st.text_input("Description", placeholder="Optional", key="set_desc")
                set_submitted = st.form_submit_button("Set")
                
                if set_submitted:
                    difference = set_amount - current_balance
                    if difference != 0:
                        desc = set_description if set_description else f"Balance set to R$ {set_amount:,.2f}"
                        update_balance(user, difference, desc, "adjustment")
                        st.success(f"Balance set to R$ {set_amount:,.2f}!")
                        st.rerun()

with col_history:
    with st.expander("📜 Recent Transactions", expanded=False):
        if not balance_history:
            st.info("No transactions yet.")
        else:
            for transaction in balance_history[:8]:
                amount = transaction.get("amount", 0)
                type_emoji = {"income": "💰", "expense": "💸", "adjustment": "⚙️"}.get(transaction.get('type'), '📝')
                
                st.markdown(f"""
                <div style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 600;">{transaction.get('description', 'N/A')}</span>
                        <span style="color: {'#059669' if amount >= 0 else '#dc2626'}; font-weight: bold;">
                            {'+' if amount >= 0 else ''}R$ {amount:,.2f}
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; color: #666;">
                        {transaction.get('date', 'N/A')} • {type_emoji} {transaction.get('type', 'N/A').title()}
                    </div>
                </div>
                """, unsafe_allow_html=True)
