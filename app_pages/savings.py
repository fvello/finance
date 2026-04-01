import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth
from settings import (
    get_savings_data, add_savings_account, add_asset_to_account,
    update_asset_balance, update_asset, delete_asset, delete_savings_account,
    get_crypto_prices, get_exchange_rates, CRYPTO_OPTIONS, CURRENCY_OPTIONS, POPULAR_STOCKS
)

user = require_auth()

st.set_page_config(page_title="Savings", page_icon="🪙", layout="wide")

if "crypto_prices" not in st.session_state:
    st.session_state.crypto_prices = {}
if "crypto_prices_loaded" not in st.session_state:
    st.session_state.crypto_prices_loaded = False
if "exchange_rates" not in st.session_state:
    st.session_state.exchange_rates = {}
if "exchange_rates_loaded" not in st.session_state:
    st.session_state.exchange_rates_loaded = False

def load_crypto_prices():
    if not st.session_state.crypto_prices_loaded:
        with st.spinner("Loading crypto prices..."):
            st.session_state.crypto_prices = get_crypto_prices()
            st.session_state.crypto_prices_loaded = True

def load_exchange_rates():
    if not st.session_state.exchange_rates_loaded:
        with st.spinner("Loading exchange rates..."):
            st.session_state.exchange_rates = get_exchange_rates()
            st.session_state.exchange_rates_loaded = True

def convert_to_brl(amount, currency):
    rates = st.session_state.exchange_rates
    if not rates:
        load_exchange_rates()
        rates = st.session_state.exchange_rates
    rate = rates.get(currency, 1.0)
    return amount * rate

def format_currency(amount, currency):
    symbols = {"BRL": "R$", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CHF": "CHF", "CAD": "C$", "AUD": "A$"}
    symbol = symbols.get(currency, currency)
    return f"{symbol} {amount:,.2f}"

st.title("🪙 Savings Accounts")

savings_data = get_savings_data(user)
accounts = savings_data.get("accounts", [])

has_crypto = any(
    asset.get("type") == "crypto"
    for acc in accounts
    for asset in acc.get("assets", [])
)

has_foreign_currency = any(
    asset.get("type") == "currency" and asset.get("currency") != "BRL"
    for acc in accounts
    for asset in acc.get("assets", [])
)

if has_crypto:
    load_crypto_prices()
if has_foreign_currency:
    load_exchange_rates()

total_brl = 0
for account in accounts:
    for asset in account.get("assets", []):
        if asset.get("type") == "crypto":
            price = st.session_state.crypto_prices.get(asset.get("symbol", ""), {}).get("brl", 0)
            total_brl += asset.get("amount", 0) * price
        elif asset.get("type") == "currency":
            total_brl += convert_to_brl(asset.get("balance", 0), asset.get("currency", "BRL"))
        elif asset.get("type") == "stock":
            total_brl += convert_to_brl(asset.get("quantity", 0) * asset.get("buy_price", 0), asset.get("currency", "USD"))

st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 1.5rem; border-radius: 1rem; color: white; margin-bottom: 1rem;">
    <div style="font-size: 0.9rem; opacity: 0.9;">💰 Total Savings (in BRL)</div>
    <div style="font-size: 2.2rem; font-weight: bold;">R$ {total_brl:,.2f}</div>
</div>
""", unsafe_allow_html=True)

with st.expander("➕ Add New Account", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Account Name", placeholder="e.g., Main Bank", key="new_acc_name")
    with col2:
        new_type = st.selectbox("Account Type", ["bank", "investment", "crypto"], key="new_acc_type")
    
    if st.button("Create Account", type="primary"):
        if new_name:
            add_savings_account(user, new_name, new_type)
            st.success(f"Account '{new_name}' created!")
            st.rerun()
        else:
            st.error("Please enter an account name")

if not accounts:
    st.info("No savings accounts yet. Add one above to get started!")
    st.stop()

st.markdown("---")

def render_add_asset_form(account, account_type):
    acc_id = account["id"]
    
    if account_type == "bank":
        st.markdown("**Add Currency**")
        col1, col2 = st.columns(2)
        with col1:
            currency = st.selectbox("Currency", CURRENCY_OPTIONS, key=f"add_cur_{acc_id}")
        with col2:
            initial = st.number_input("Initial Balance", min_value=0.0, format="%.2f", key=f"add_init_{acc_id}")
        
        if st.button("Add Currency", key=f"btn_add_cur_{acc_id}"):
            existing = [a for a in account.get("assets", []) if a.get("type") == "currency" and a.get("currency") == currency]
            if existing:
                st.error(f"{currency} already exists in this account")
            else:
                add_asset_to_account(user, acc_id, "currency", currency=currency, initial_balance=initial)
                st.success(f"Added {currency}")
                st.rerun()
    
    elif account_type == "investment":
        st.markdown("**Add Stock/Asset**")
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            stock_symbol = st.text_input("Symbol", placeholder="e.g., AAPL", key=f"add_sym_{acc_id}").upper()
        with col2:
            quantity = st.number_input("Quantity", min_value=0.0, format="%.2f", key=f"add_qty_{acc_id}")
        with col3:
            buy_price = st.number_input("Buy Price", min_value=0.0, format="%.2f", key=f"add_price_{acc_id}")
        with col4:
            stock_currency = st.selectbox("Currency", ["USD", "BRL", "EUR"], key=f"add_stock_cur_{acc_id}")
        
        if st.button("Add Stock", key=f"btn_add_stock_{acc_id}"):
            if stock_symbol and quantity > 0:
                add_asset_to_account(user, acc_id, "stock", symbol=stock_symbol, quantity=quantity, buy_price=buy_price, currency=stock_currency)
                st.success(f"Added {stock_symbol}")
                st.rerun()
            else:
                st.error("Symbol and quantity required")
    
    elif account_type == "crypto":
        st.markdown("**Add Cryptocurrency**")
        crypto_options = list(CRYPTO_OPTIONS.keys())
        crypto_labels = [f"{CRYPTO_OPTIONS[c]['name']} ({CRYPTO_OPTIONS[c]['symbol']})" for c in crypto_options]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_idx = st.selectbox("Cryptocurrency", range(len(crypto_options)), format_func=lambda i: crypto_labels[i], key=f"add_crypto_sel_{acc_id}")
            selected_crypto = crypto_options[selected_idx]
        with col2:
            crypto_amount = st.number_input("Amount", min_value=0.0, format="%.8f", key=f"add_crypto_amt_{acc_id}")
        
        if st.button("Add Crypto", key=f"btn_add_crypto_{acc_id}"):
            existing = [a for a in account.get("assets", []) if a.get("type") == "crypto" and a.get("symbol") == selected_crypto]
            if existing:
                st.error(f"{CRYPTO_OPTIONS[selected_crypto]['symbol']} already exists in this account")
            else:
                add_asset_to_account(user, acc_id, "crypto", symbol=selected_crypto, initial_amount=crypto_amount)
                st.success(f"Added {CRYPTO_OPTIONS[selected_crypto]['name']}")
                st.rerun()

def render_asset(account, asset, account_type):
    asset_id = asset["id"]
    acc_id = account["id"]
    
    if asset.get("type") == "currency":
        currency = asset.get("currency", "BRL")
        balance = asset.get("balance", 0)
        balance_brl = convert_to_brl(balance, currency)
        
        col_info, col_actions = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{currency}**: {format_currency(balance, currency)}")
            if currency != "BRL":
                st.caption(f"~ R$ {balance_brl:,.2f}")
        
        with col_actions:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("➕", key=f"dep_{asset_id}", help="Deposit"):
                    st.session_state[f"show_dep_{asset_id}"] = True
                    st.session_state[f"show_wit_{asset_id}"] = False
            with c2:
                if st.button("➖", key=f"wit_{asset_id}", help="Withdraw"):
                    st.session_state[f"show_wit_{asset_id}"] = True
                    st.session_state[f"show_dep_{asset_id}"] = False
            with c3:
                if st.button("🗑️", key=f"del_asset_{asset_id}", help="Remove"):
                    st.session_state[f"confirm_del_asset_{asset_id}"] = True
    
    elif asset.get("type") == "crypto":
        symbol = asset.get("symbol", "")
        amount = asset.get("amount", 0)
        crypto_info = CRYPTO_OPTIONS.get(symbol, {"name": symbol, "symbol": "?"})
        price = st.session_state.crypto_prices.get(symbol, {}).get("brl", 0)
        value_brl = amount * price
        
        col_info, col_actions = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{crypto_info['name']} ({crypto_info['symbol']})**")
            st.markdown(f"Amount: **{amount:.8f}** {crypto_info['symbol']}")
            st.caption(f"Price: R$ {price:,.2f} | Value: R$ {value_brl:,.2f}")
        
        with col_actions:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("➕", key=f"dep_{asset_id}", help="Deposit"):
                    st.session_state[f"show_dep_{asset_id}"] = True
                    st.session_state[f"show_wit_{asset_id}"] = False
            with c2:
                if st.button("➖", key=f"wit_{asset_id}", help="Withdraw"):
                    st.session_state[f"show_wit_{asset_id}"] = True
                    st.session_state[f"show_dep_{asset_id}"] = False
            with c3:
                if st.button("🗑️", key=f"del_asset_{asset_id}", help="Remove"):
                    st.session_state[f"confirm_del_asset_{asset_id}"] = True
    
    elif asset.get("type") == "stock":
        symbol = asset.get("symbol", "")
        quantity = asset.get("quantity", 0)
        buy_price = asset.get("buy_price", 0)
        stock_currency = asset.get("currency", "USD")
        total_value = quantity * buy_price
        total_brl_stock = convert_to_brl(total_value, stock_currency)
        
        col_info, col_actions = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{symbol}**: {quantity:.2f} shares @ {format_currency(buy_price, stock_currency)}")
            st.caption(f"Total: {format_currency(total_value, stock_currency)} (~ R$ {total_brl_stock:,.2f})")
        
        with col_actions:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("➕", key=f"dep_{asset_id}", help="Buy More"):
                    st.session_state[f"show_buy_{asset_id}"] = True
                    st.session_state[f"show_sell_{asset_id}"] = False
            with c2:
                if st.button("➖", key=f"wit_{asset_id}", help="Sell"):
                    st.session_state[f"show_sell_{asset_id}"] = True
                    st.session_state[f"show_buy_{asset_id}"] = False
            with c3:
                if st.button("🗑️", key=f"del_asset_{asset_id}", help="Remove"):
                    st.session_state[f"confirm_del_asset_{asset_id}"] = True
    
    if st.session_state.get(f"show_dep_{asset_id}"):
        with st.form(f"dep_form_{asset_id}"):
            if asset.get("type") == "crypto":
                amt = st.number_input("Amount", min_value=0.00000001, format="%.8f", key=f"dep_amt_{asset_id}")
            else:
                amt = st.number_input("Amount", min_value=0.01, format="%.2f", key=f"dep_amt_{asset_id}")
            desc = st.text_input("Description", value="Deposit", key=f"dep_desc_{asset_id}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Confirm", type="primary"):
                    update_asset_balance(user, acc_id, asset_id, amt, desc or "Deposit")
                    st.session_state[f"show_dep_{asset_id}"] = False
                    st.rerun()
            with c2:
                if st.form_submit_button("Cancel"):
                    st.session_state[f"show_dep_{asset_id}"] = False
                    st.rerun()
    
    if st.session_state.get(f"show_wit_{asset_id}"):
        with st.form(f"wit_form_{asset_id}"):
            if asset.get("type") == "crypto":
                max_val = float(asset.get("amount", 0))
                amt = st.number_input("Amount", min_value=0.00000001, max_value=max_val if max_val > 0 else 0.00000001, format="%.8f", key=f"wit_amt_{asset_id}")
            else:
                max_val = float(asset.get("balance", 0))
                amt = st.number_input("Amount", min_value=0.01, max_value=max_val if max_val > 0 else 0.01, format="%.2f", key=f"wit_amt_{asset_id}")
            desc = st.text_input("Description", value="Withdrawal", key=f"wit_desc_{asset_id}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Confirm"):
                    update_asset_balance(user, acc_id, asset_id, -amt, desc or "Withdrawal")
                    st.session_state[f"show_wit_{asset_id}"] = False
                    st.rerun()
            with c2:
                if st.form_submit_button("Cancel"):
                    st.session_state[f"show_wit_{asset_id}"] = False
                    st.rerun()
    
    if st.session_state.get(f"show_buy_{asset_id}"):
        with st.form(f"buy_form_{asset_id}"):
            qty = st.number_input("Quantity to buy", min_value=0.01, format="%.2f", key=f"buy_qty_{asset_id}")
            new_price = st.number_input("Price per share", min_value=0.01, format="%.2f", value=asset.get("buy_price", 0), key=f"buy_price_{asset_id}")
            desc = st.text_input("Description", value="Bought shares", key=f"buy_desc_{asset_id}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Confirm", type="primary"):
                    update_asset_balance(user, acc_id, asset_id, qty, desc or "Bought shares")
                    update_asset(user, acc_id, asset_id, buy_price=new_price)
                    st.session_state[f"show_buy_{asset_id}"] = False
                    st.rerun()
            with c2:
                if st.form_submit_button("Cancel"):
                    st.session_state[f"show_buy_{asset_id}"] = False
                    st.rerun()
    
    if st.session_state.get(f"show_sell_{asset_id}"):
        with st.form(f"sell_form_{asset_id}"):
            max_qty = float(asset.get("quantity", 0))
            qty = st.number_input("Quantity to sell", min_value=0.01, max_value=max_qty if max_qty > 0 else 0.01, format="%.2f", key=f"sell_qty_{asset_id}")
            desc = st.text_input("Description", value="Sold shares", key=f"sell_desc_{asset_id}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Confirm"):
                    update_asset_balance(user, acc_id, asset_id, -qty, desc or "Sold shares")
                    st.session_state[f"show_sell_{asset_id}"] = False
                    st.rerun()
            with c2:
                if st.form_submit_button("Cancel"):
                    st.session_state[f"show_sell_{asset_id}"] = False
                    st.rerun()
    
    if st.session_state.get(f"confirm_del_asset_{asset_id}"):
        st.warning("Delete this asset?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", key=f"confirm_del_asset_yes_{asset_id}"):
                delete_asset(user, acc_id, asset_id)
                st.session_state[f"confirm_del_asset_{asset_id}"] = False
                st.rerun()
        with c2:
            if st.button("Cancel", key=f"confirm_del_asset_no_{asset_id}"):
                st.session_state[f"confirm_del_asset_{asset_id}"] = False
                st.rerun()
    
    with st.expander("📜 History"):
        transactions = asset.get("transactions", [])
        if not transactions:
            st.caption("No transactions")
        else:
            for tx in transactions[:8]:
                amount = tx.get("amount", 0)
                color = "#059669" if amount >= 0 else "#dc2626"
                sign = "+" if amount >= 0 else ""
                amt_str = f"{sign}{amount:.8f}" if asset.get("type") == "crypto" else f"{sign}{amount:,.2f}"
                bal_after = tx.get("balance_after", 0)
                bal_str = f"{bal_after:.8f}" if asset.get("type") == "crypto" else f"{bal_after:,.2f}"
                st.markdown(f"""
                <div style="padding: 0.3rem 0; border-bottom: 1px solid #eee;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{tx.get('description', 'N/A')}</span>
                        <span style="color: {color}; font-weight: bold;">{amt_str}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #666;">{tx.get('date', 'N/A')} | Balance: {bal_str}</div>
                </div>
                """, unsafe_allow_html=True)

bank_accounts = [acc for acc in accounts if acc["type"] == "bank"]
investment_accounts = [acc for acc in accounts if acc["type"] == "investment"]
crypto_accounts = [acc for acc in accounts if acc["type"] == "crypto"]

def render_account_card(account):
    acc_id = account["id"]
    account_type = account["type"]
    
    icon_map = {"bank": "🏦", "investment": "📈", "crypto": "₿"}
    bg_map = {
        "bank": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "investment": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "crypto": "linear-gradient(135deg, #f7931a 0%, #ffab40 100%)"
    }
    
    account_total_brl = 0
    for asset in account.get("assets", []):
        if asset.get("type") == "crypto":
            price = st.session_state.crypto_prices.get(asset.get("symbol", ""), {}).get("brl", 0)
            account_total_brl += asset.get("amount", 0) * price
        elif asset.get("type") == "currency":
            account_total_brl += convert_to_brl(asset.get("balance", 0), asset.get("currency", "BRL"))
        elif asset.get("type") == "stock":
            account_total_brl += convert_to_brl(asset.get("quantity", 0) * asset.get("buy_price", 0), asset.get("currency", "USD"))
    
    st.markdown(f"""
    <div style="background: {bg_map[account_type]}; padding: 1rem; border-radius: 0.8rem; color: white; margin-bottom: 0.5rem;">
        <div style="font-size: 1.2rem; font-weight: bold;">{icon_map[account_type]} {account['name']}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">Total: R$ {account_total_brl:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    assets = account.get("assets", [])
    if assets:
        for asset in assets:
            render_asset(account, asset, account_type)
    else:
        st.caption("No assets yet")
    
    with st.expander(f"➕ Add {'Currency' if account_type == 'bank' else ('Stock' if account_type == 'investment' else 'Crypto')}"):
        render_add_asset_form(account, account_type)
    
    if st.button("🗑️ Delete Account", key=f"del_acc_{acc_id}"):
        st.session_state[f"confirm_del_acc_{acc_id}"] = True
    
    if st.session_state.get(f"confirm_del_acc_{acc_id}"):
        st.warning(f"Delete '{account['name']}' and all its assets?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Yes, delete", key=f"confirm_del_acc_yes_{acc_id}"):
                delete_savings_account(user, acc_id)
                st.session_state[f"confirm_del_acc_{acc_id}"] = False
                st.rerun()
        with c2:
            if st.button("Cancel", key=f"confirm_del_acc_no_{acc_id}"):
                st.session_state[f"confirm_del_acc_{acc_id}"] = False
                st.rerun()
    
    st.markdown("---")

if bank_accounts:
    st.markdown("### 🏦 Bank Accounts")
    for acc in bank_accounts:
        render_account_card(acc)

if investment_accounts:
    st.markdown("### 📈 Investments")
    for acc in investment_accounts:
        render_account_card(acc)

if crypto_accounts:
    st.markdown("### ₿ Cryptocurrency")
    if st.button("🔄 Refresh Crypto Prices"):
        st.session_state.crypto_prices_loaded = False
        st.rerun()
    for acc in crypto_accounts:
        render_account_card(acc)
