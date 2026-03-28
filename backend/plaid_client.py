"""
Plaid integration — fetches transactions from Capital One Spark.
"""
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.accounts_get_request import AccountsGetRequest
from datetime import date, timedelta
from config import get_settings
import database as db


def _get_client() -> plaid_api.PlaidApi:
    s = get_settings()
    env_map = {
        "sandbox": plaid.Environment.Sandbox,
        "production": plaid.Environment.Production,
    }
    config = plaid.Configuration(
        host=env_map.get(s.plaid_env, plaid.Environment.Production),
        api_key={"clientId": s.plaid_client_id, "secret": s.plaid_secret}
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def fetch_and_store_transactions(days_back: int = 7) -> list[dict]:
    """
    Pull recent transactions from Plaid, map to employees, upsert into Supabase.
    Returns list of newly stored transactions.
    """
    s = get_settings()
    if not s.plaid_access_token:
        raise ValueError("PLAID_ACCESS_TOKEN not set. Run scripts/plaid_link.py first.")

    client = _get_client()
    start_date = date.today() - timedelta(days=days_back)
    end_date = date.today()

    request = TransactionsGetRequest(
        access_token=s.plaid_access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=500)
    )
    response = client.transactions_get(request)
    transactions = response["transactions"]

    # Handle pagination
    while len(transactions) < response["total_transactions"]:
        request = TransactionsGetRequest(
            access_token=s.plaid_access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(
                count=500,
                offset=len(transactions)
            )
        )
        response = client.transactions_get(request)
        transactions.extend(response["transactions"])

    stored = []
    for txn in transactions:
        # Skip credits/refunds — only process debits (positive amounts in Plaid)
        if txn["amount"] <= 0:
            continue

        # Look up which card/employee this account belongs to
        account_info = db.get_plaid_account(txn["account_id"])
        card_last4 = account_info["card_last4"] if account_info else None
        employee_id = account_info["employee_id"] if account_info else None

        row = {
            "plaid_transaction_id": txn["transaction_id"],
            "plaid_account_id": txn["account_id"],
            "date": str(txn["date"]),
            "merchant_name": txn.get("merchant_name") or txn.get("name", ""),
            "description": txn.get("name", ""),
            "amount": float(txn["amount"]),
            "card_last4": card_last4,
            "employee_id": employee_id,
        }
        result = db.upsert_transaction(row)
        if result:
            stored.extend(result)

    return stored


def sync_accounts() -> list[dict]:
    """
    Fetch all Plaid accounts and store in plaid_accounts table.
    Run this once after linking, and whenever you add a new employee card.
    """
    s = get_settings()
    if not s.plaid_access_token:
        raise ValueError("PLAID_ACCESS_TOKEN not set.")

    client = _get_client()
    request = AccountsGetRequest(access_token=s.plaid_access_token)
    response = client.accounts_get(request)

    synced = []
    for account in response["accounts"]:
        mask = account.get("mask", "")   # last 4 digits
        name = account.get("name", "")
        plaid_account_id = account["account_id"]

        result = db.upsert_plaid_account(
            plaid_account_id=plaid_account_id,
            account_name=name,
            card_last4=mask
        )
        synced.append({"account_id": plaid_account_id, "name": name, "last4": mask})
        print(f"  Synced account: {name} (****{mask})")

    return synced
