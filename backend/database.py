"""
Supabase client wrapper — all DB operations live here.
"""
from supabase import create_client, Client
from config import get_settings
from functools import lru_cache


@lru_cache()
def get_db() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


# ─── Employees ────────────────────────────────────────────────────────────────

def get_all_employees() -> list[dict]:
    db = get_db()
    return db.table("employees").select("*").execute().data


def get_employee_by_card(card_last4: str) -> dict | None:
    db = get_db()
    rows = db.table("employees").select("*").eq("card_last4", card_last4).execute().data
    return rows[0] if rows else None


def get_employee_by_phone(phone: str) -> dict | None:
    db = get_db()
    rows = db.table("employees").select("*").eq("phone_number", phone).execute().data
    return rows[0] if rows else None


# ─── Project Codes ─────────────────────────────────────────────────────────────

def get_all_project_codes(active_only: bool = True) -> list[dict]:
    db = get_db()
    q = db.table("project_codes").select("*")
    if active_only:
        q = q.eq("is_active", True)
    return q.order("code").execute().data


def is_valid_project_code(code: str) -> bool:
    db = get_db()
    rows = db.table("project_codes").select("code").eq("code", code.upper()).eq("is_active", True).execute().data
    return len(rows) > 0


def upsert_project_code(code: str, name: str = "", description: str = "") -> dict:
    db = get_db()
    return db.table("project_codes").upsert({
        "code": code.upper(),
        "name": name,
        "description": description,
        "is_active": True
    }, on_conflict="code").execute().data


# ─── Plaid Accounts ────────────────────────────────────────────────────────────

def upsert_plaid_account(plaid_account_id: str, account_name: str, card_last4: str) -> dict:
    db = get_db()
    # Try to find matching employee
    employee = get_employee_by_card(card_last4)
    employee_id = employee["id"] if employee else None

    return db.table("plaid_accounts").upsert({
        "plaid_account_id": plaid_account_id,
        "account_name": account_name,
        "card_last4": card_last4,
        "employee_id": employee_id
    }, on_conflict="plaid_account_id").execute().data


def get_plaid_account(plaid_account_id: str) -> dict | None:
    db = get_db()
    rows = db.table("plaid_accounts").select("*, employees(*)").eq("plaid_account_id", plaid_account_id).execute().data
    return rows[0] if rows else None


# ─── Transactions ──────────────────────────────────────────────────────────────

def upsert_transaction(txn: dict) -> dict:
    """Insert or skip a transaction (plaid_transaction_id is unique)."""
    db = get_db()
    return db.table("transactions").upsert(txn, on_conflict="plaid_transaction_id", ignore_duplicates=True).execute().data


def get_transactions(
    limit: int = 100,
    offset: int = 0,
    coded_only: bool = False,
    uncoded_only: bool = False,
    employee_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> list[dict]:
    db = get_db()
    q = db.table("transactions").select("*, employees(name, phone_number, card_last4)").order("date", desc=True)

    if coded_only:
        q = q.not_.is_("project_code", "null")
    if uncoded_only:
        q = q.is_("project_code", "null")
    if employee_id:
        q = q.eq("employee_id", employee_id)
    if date_from:
        q = q.gte("date", date_from)
    if date_to:
        q = q.lte("date", date_to)

    return q.range(offset, offset + limit - 1).execute().data


def get_transaction_by_id(txn_id: str) -> dict | None:
    db = get_db()
    rows = db.table("transactions").select("*, employees(*)").eq("id", txn_id).execute().data
    return rows[0] if rows else None


def get_uncoded_transactions_due_reminder(interval_hours: int = 24, max_reminders: int = 3) -> list[dict]:
    """Fetch uncoded transactions that need a reminder sent."""
    from datetime import datetime, timedelta, timezone
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=interval_hours)).isoformat()

    # Uncoded + (never reminded OR last reminder was > interval_hours ago) + under max_reminders
    rows = (
        db.table("transactions")
        .select("*, employees(name, phone_number)")
        .is_("project_code", "null")
        .lt("reminder_count", max_reminders)
        .or_(f"reminder_sent_at.is.null,reminder_sent_at.lt.{cutoff}")
        .execute()
        .data
    )
    return rows


def assign_project_code(txn_id: str, code: str, receipt_url: str | None, coded_by: str = "sms") -> dict:
    from datetime import datetime, timezone
    db = get_db()
    updates = {
        "project_code": code.upper(),
        "coded_at": datetime.now(timezone.utc).isoformat(),
        "coded_by": coded_by,
    }
    if receipt_url:
        updates["receipt_url"] = receipt_url
    return db.table("transactions").update(updates).eq("id", txn_id).execute().data


def mark_reminder_sent(txn_id: str, current_count: int) -> None:
    from datetime import datetime, timezone
    db = get_db()
    db.table("transactions").update({
        "reminder_sent_at": datetime.now(timezone.utc).isoformat(),
        "reminder_count": current_count + 1
    }).eq("id", txn_id).execute()


# ─── SMS Log ──────────────────────────────────────────────────────────────────

def log_sms(direction: str, from_number: str, to_number: str, body: str,
            transaction_id: str | None = None, media_url: str | None = None,
            twilio_sid: str | None = None) -> None:
    db = get_db()
    db.table("sms_log").insert({
        "transaction_id": transaction_id,
        "direction": direction,
        "from_number": from_number,
        "to_number": to_number,
        "body": body,
        "media_url": media_url,
        "twilio_sid": twilio_sid
    }).execute()


# ─── Pending SMS State ─────────────────────────────────────────────────────────
# Tracks which transaction a person is currently being asked about
# Uses a simple in-memory dict keyed by phone number → transaction_id
# For production, this could be a Redis key or a Supabase table

_pending_state: dict[str, str] = {}   # phone → transaction_id


def set_pending(phone: str, txn_id: str) -> None:
    _pending_state[phone] = txn_id


def get_pending(phone: str) -> str | None:
    return _pending_state.get(phone)


def clear_pending(phone: str) -> None:
    _pending_state.pop(phone, None)
