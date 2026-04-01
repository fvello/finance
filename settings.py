import json
import os
import datetime

def get_settings_path(user):
    return os.path.join("csv", user, "settings.json")

def load_user_settings(user):
    settings_path = get_settings_path(user)
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            return json.load(f)
    return {"people": [], "payment_methods": [], "income_sources": []}

def save_user_settings(user, settings):
    settings_path = get_settings_path(user)
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

def get_people(user):
    settings = load_user_settings(user)
    return settings.get("people", [])

def get_people_with_user(user):
    import yaml
    from yaml.loader import SafeLoader
    
    auth_path = "auth.yaml"
    user_display = user
    if os.path.exists(auth_path):
        with open(auth_path) as f:
            auth_config = yaml.load(f, Loader=SafeLoader)
        if user in auth_config.get("credentials", {}).get("usernames", {}):
            user_display = auth_config["credentials"]["usernames"][user].get("name", user)
    
    people = get_people(user)
    if user_display not in people:
        return [user_display] + people
    return people

def get_payment_methods(user):
    settings = load_user_settings(user)
    payment_methods = settings.get("payment_methods", [])
    
    if payment_methods and isinstance(payment_methods[0], dict):
        return [pm["name"] for pm in payment_methods]
    return payment_methods

def get_income_sources(user):
    settings = load_user_settings(user)
    return settings.get("income_sources", [])

def get_payment_methods_with_types(user):
    settings = load_user_settings(user)
    payment_methods = settings.get("payment_methods", [])
    
    if payment_methods and isinstance(payment_methods[0], dict):
        return payment_methods
    
    return [{"name": pm, "type": auto_categorize_payment_method(pm)} for pm in payment_methods]

def auto_categorize_payment_method(method_name):
    method_lower = method_name.lower()
    
    immediate_keywords = ["dinheiro", "cash", "pix", "debit", "débito", "débit"]
    credit_keywords = ["credit", "crédito", "créd", "card", "cartão", "nubank", "azul", "itau", "bradesco", "santander", "bb"]
    
    for keyword in immediate_keywords:
        if keyword in method_lower:
            return "immediate"
    
    for keyword in credit_keywords:
        if keyword in method_lower:
            return "credit"
    
    return "credit"

def get_immediate_payment_methods(user):
    methods_with_types = get_payment_methods_with_types(user)
    return [pm["name"] for pm in methods_with_types if pm["type"] == "immediate"]

def get_credit_payment_methods(user):
    methods_with_types = get_payment_methods_with_types(user)
    return [pm["name"] for pm in methods_with_types if pm["type"] == "credit"]

def get_balance_path(user):
    return os.path.join("csv", user, "balance.json")

def get_balance(user):
    balance_path = get_balance_path(user)
    if os.path.exists(balance_path):
        with open(balance_path, "r") as f:
            data = json.load(f)
            return data.get("current_balance", 0.0)
    return 0.0

def get_balance_data(user):
    balance_path = get_balance_path(user)
    if os.path.exists(balance_path):
        with open(balance_path, "r") as f:
            return json.load(f)
    return {"current_balance": 0.0, "transactions": []}

def update_balance(user, amount, description, transaction_type):
    balance_path = get_balance_path(user)
    os.makedirs(os.path.dirname(balance_path), exist_ok=True)
    
    if os.path.exists(balance_path):
        with open(balance_path, "r") as f:
            data = json.load(f)
    else:
        data = {"current_balance": 0.0, "transactions": []}
    
    current_balance = data["current_balance"]
    new_balance = round(current_balance + amount, 2)
    
    transaction = {
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "description": description,
        "amount": round(amount, 2),
        "type": transaction_type,
        "balance_after": new_balance
    }
    
    data["transactions"].insert(0, transaction)
    data["current_balance"] = new_balance
    
    with open(balance_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return new_balance

def get_balance_history(user, limit=100):
    data = get_balance_data(user)
    return data.get("transactions", [])[:limit]

def has_settings(user):
    settings_path = get_settings_path(user)
    return os.path.exists(settings_path)

DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "General/Daily", "icon": "🛒"},
    {"name": "Subscription/Recurring", "icon": "📺"},
    {"name": "Loan Payment", "icon": "💰"},
    {"name": "Housing", "icon": "🏠"},
    {"name": "Transportation", "icon": "🚗"},
    {"name": "Food", "icon": "🍔"},
    {"name": "Entertainment", "icon": "🎮"},
    {"name": "Other", "icon": "✨"}
]

def get_expense_categories(user):
    settings = load_user_settings(user)
    categories = settings.get("expense_categories", DEFAULT_EXPENSE_CATEGORIES)
    
    if not categories:
        return DEFAULT_EXPENSE_CATEGORIES
    
    return categories

def get_category_names(user):
    categories = get_expense_categories(user)
    return [cat["name"] for cat in categories]

import uuid

CURRENCY_OPTIONS = ["BRL", "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]

CRYPTO_OPTIONS = {
    "bitcoin": {"name": "Bitcoin", "symbol": "BTC"},
    "ethereum": {"name": "Ethereum", "symbol": "ETH"},
    "solana": {"name": "Solana", "symbol": "SOL"},
    "cardano": {"name": "Cardano", "symbol": "ADA"},
    "ripple": {"name": "XRP", "symbol": "XRP"},
    "polkadot": {"name": "Polkadot", "symbol": "DOT"},
    "dogecoin": {"name": "Dogecoin", "symbol": "DOGE"},
    "litecoin": {"name": "Litecoin", "symbol": "LTC"},
    "binancecoin": {"name": "BNB", "symbol": "BNB"},
    "chainlink": {"name": "Chainlink", "symbol": "LINK"},
    "avalanche-2": {"name": "Avalanche", "symbol": "AVAX"},
    "polygon": {"name": "Polygon", "symbol": "MATIC"},
    "uniswap": {"name": "Uniswap", "symbol": "UNI"},
    "stellar": {"name": "Stellar", "symbol": "XLM"},
    "cosmos": {"name": "Cosmos", "symbol": "ATOM"}
}

POPULAR_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD", "NFLX", "DIS", "V", "JPM", "WMT", "PG", "MA"]

def get_savings_path(user):
    return os.path.join("csv", user, "savings.json")

def get_savings_data(user):
    savings_path = get_savings_path(user)
    if os.path.exists(savings_path):
        with open(savings_path, "r") as f:
            data = json.load(f)
        data = migrate_savings_data(data)
        return data
    return {"accounts": [], "version": 2}

def migrate_savings_data(data):
    if data.get("version", 1) >= 2:
        return data
    
    migrated = {"accounts": [], "version": 2}
    
    for account in data.get("accounts", []):
        new_account = {
            "id": account.get("id", str(uuid.uuid4())),
            "name": account.get("name", "Account"),
            "type": account.get("type", "bank"),
            "assets": []
        }
        
        if account.get("type") == "crypto":
            if account.get("crypto_symbol") and account.get("crypto_amount", 0) > 0:
                new_account["assets"].append({
                    "id": str(uuid.uuid4()),
                    "type": "crypto",
                    "symbol": account["crypto_symbol"],
                    "amount": account.get("crypto_amount", 0),
                    "transactions": account.get("transactions", [])
                })
        else:
            balance = account.get("balance", 0)
            if balance > 0 or account.get("transactions"):
                new_account["assets"].append({
                    "id": str(uuid.uuid4()),
                    "type": "currency",
                    "currency": account.get("currency", "BRL"),
                    "balance": balance,
                    "transactions": account.get("transactions", [])
                })
        
        migrated["accounts"].append(new_account)
    
    return migrated

def save_savings_data(user, data):
    savings_path = get_savings_path(user)
    os.makedirs(os.path.dirname(savings_path), exist_ok=True)
    data["version"] = 2
    with open(savings_path, "w") as f:
        json.dump(data, f, indent=2)

def add_savings_account(user, name, account_type):
    data = get_savings_data(user)
    account = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": account_type,
        "assets": []
    }
    data["accounts"].append(account)
    save_savings_data(user, data)
    return account

def get_account_by_id(user, account_id):
    data = get_savings_data(user)
    for account in data["accounts"]:
        if account["id"] == account_id:
            return account, data
    return None, data

def add_asset_to_account(user, account_id, asset_type, **kwargs):
    data = get_savings_data(user)
    asset = None
    for account in data["accounts"]:
        if account["id"] == account_id:
            asset = {
                "id": str(uuid.uuid4()),
                "type": asset_type,
                "transactions": []
            }
            
            if asset_type == "currency":
                asset["currency"] = kwargs.get("currency", "BRL")
                asset["balance"] = round(kwargs.get("initial_balance", 0), 2)
                if asset["balance"] > 0:
                    asset["transactions"].append({
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "description": "Initial balance",
                        "amount": asset["balance"],
                        "balance_after": asset["balance"]
                    })
            elif asset_type == "crypto":
                asset["symbol"] = kwargs.get("symbol", "bitcoin")
                asset["amount"] = round(kwargs.get("initial_amount", 0), 8)
                if asset["amount"] > 0:
                    asset["transactions"].append({
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "description": "Initial deposit",
                        "amount": asset["amount"],
                        "balance_after": asset["amount"]
                    })
            elif asset_type == "stock":
                asset["symbol"] = kwargs.get("symbol", "").upper()
                asset["quantity"] = kwargs.get("quantity", 0)
                asset["buy_price"] = round(kwargs.get("buy_price", 0), 2)
                asset["currency"] = kwargs.get("currency", "USD")
                if asset["quantity"] > 0:
                    asset["transactions"].append({
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "description": f"Bought {asset['quantity']} shares @ {asset['currency']} {asset['buy_price']}",
                        "quantity": asset["quantity"],
                        "balance_after": asset["quantity"]
                    })
            
            account["assets"].append(asset)
            break
    save_savings_data(user, data)
    return asset

def update_asset_balance(user, account_id, asset_id, amount, description):
    data = get_savings_data(user)
    for account in data["accounts"]:
        if account["id"] == account_id:
            for asset in account.get("assets", []):
                if asset["id"] == asset_id:
                    if asset["type"] == "crypto":
                        asset["amount"] = round(asset.get("amount", 0) + amount, 8)
                        balance_after = asset["amount"]
                    elif asset["type"] == "stock":
                        asset["quantity"] = round(asset.get("quantity", 0) + amount, 4)
                        balance_after = asset["quantity"]
                    else:
                        asset["balance"] = round(asset.get("balance", 0) + amount, 2)
                        balance_after = asset["balance"]
                    
                    asset["transactions"].insert(0, {
                        "date": datetime.date.today().strftime("%Y-%m-%d"),
                        "description": description,
                        "amount": round(amount, 8) if asset["type"] == "crypto" else round(amount, 2),
                        "balance_after": balance_after
                    })
                    break
            break
    save_savings_data(user, data)

def update_asset(user, account_id, asset_id, **kwargs):
    data = get_savings_data(user)
    for account in data["accounts"]:
        if account["id"] == account_id:
            for asset in account.get("assets", []):
                if asset["id"] == asset_id:
                    for key, value in kwargs.items():
                        if key in asset:
                            asset[key] = value
                    break
            break
    save_savings_data(user, data)

def delete_asset(user, account_id, asset_id):
    data = get_savings_data(user)
    for account in data["accounts"]:
        if account["id"] == account_id:
            account["assets"] = [a for a in account.get("assets", []) if a["id"] != asset_id]
            break
    save_savings_data(user, data)

def delete_savings_account(user, account_id):
    data = get_savings_data(user)
    data["accounts"] = [acc for acc in data["accounts"] if acc["id"] != account_id]
    save_savings_data(user, data)

def get_crypto_prices():
    import urllib.request
    import urllib.error
    
    ids = ",".join(CRYPTO_OPTIONS.keys())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FinanceApp/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except:
        return {}

def get_exchange_rates():
    import urllib.request
    import urllib.error
    
    url = "https://api.exchangerate-api.com/v4/latest/BRL"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FinanceApp/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            rates = data.get("rates", {})
            return {
                "BRL": 1.0,
                "USD": 1.0 / rates.get("USD", 1),
                "EUR": 1.0 / rates.get("EUR", 1),
                "GBP": 1.0 / rates.get("GBP", 1),
                "JPY": 1.0 / rates.get("JPY", 1),
                "CHF": 1.0 / rates.get("CHF", 1),
                "CAD": 1.0 / rates.get("CAD", 1),
                "AUD": 1.0 / rates.get("AUD", 1)
            }
    except:
        return {"BRL": 1.0, "USD": 5.0, "EUR": 5.5, "GBP": 6.3, "JPY": 0.034, "CHF": 5.6, "CAD": 3.7, "AUD": 3.3}

def get_stock_prices():
    return {}
