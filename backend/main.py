"""
Masterson Transaction Tracker — FastAPI Backend
Deploy to Railway: push to GitHub, connect repo in Railway dashboard.
"""
from fastapi import FastAPI, Request, Form, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import csv
import io
import requests as _requests

import database as db
import plaid_client
import twilio_client
from config import get_settings


# ─── Scheduler: run reminders on a schedule ───────────────────────────────────

def run_reminder_job():
    """Called by scheduler — checks for uncoded transactions and sends reminders."""
    s = get_settings()
    print("[scheduler] Running reminder check...")

    # Pull fresh transactions from Plaid first
    try:
        plaid_client.fetch_and_store_transactions(days_back=s.days_to_look_back)
    except Exception as e:
        print(f"[plaid] fetch error: {e}")

    # Find uncoded transactions due a reminder
    due = db.get_uncoded_transactions_due_reminder(
        interval_hours=s.reminder_interval_hours,
        max_reminders=s.max_reminders
    )
    print(f"[scheduler] {len(due)} transactions need reminders")
    for txn in due:
        try:
            sid = twilio_client.send_reminder(txn)
            print(f"  → Reminded for txn {txn['id']} (merchant: {txn.get('merchant_name')}) → SID {sid}")
        except Exception as e:
            print(f"  [error] {e}")


_SHEETS_COLUMN_MAP = {
    "code":        ["location_code", "Code", "code", "PROJECT_CODE", "ProjectCode", "project_code"],
    "name":        ["project_name", "Name", "name", "Project Name", "ProjectName"],
    "description": ["client", "Description", "description", "Notes", "notes"],
}

def _find_col(headers, candidates):
    for c in candidates:
        if c in headers:
            return c
    return None

def sync_projects_job():
    """Fetch project codes from Google Sheets and upsert into Supabase."""
    s = get_settings()
    if not s.google_sheets_url:
        print("[sheets] No GOOGLE_SHEETS_URL configured, skipping.")
        return
    try:
        print("[sheets] Fetching URL...")
        resp = _requests.get(s.google_sheets_url.strip(), timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        print(f"[sheets] HTTP {resp.status_code} — content-type: {resp.headers.get('content-type','?')}")
        resp.raise_for_status()
        print("[sheets] Decoding content...")
        content = resp.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []
        print(f"[sheets] CSV headers: {headers}")
        code_col = _find_col(headers, _SHEETS_COLUMN_MAP["code"])
        name_col = _find_col(headers, _SHEETS_COLUMN_MAP["name"])
        desc_col  = _find_col(headers, _SHEETS_COLUMN_MAP["description"])
        if not code_col:
            print(f"[sheets] Could not find code column in: {headers}")
            return
        count = 0
        for row in reader:
            code = row.get(code_col, "").strip().upper()
            if not code:
                continue
            name = row.get(name_col, "").strip() if name_col else ""
            desc = row.get(desc_col, "").strip() if desc_col else ""
            print(f"[sheets] Upserting {code}...")
            db.upsert_project_code(code, name, desc)
            count += 1
        print(f"[sheets] Synced {count} project codes.")
    except Exception as e:
        print(f"[sheets] ERROR type={type(e).__name__} msg={e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background scheduler
    scheduler = BackgroundScheduler()
    s = get_settings()
    scheduler.add_job(run_reminder_job, "interval", hours=s.reminder_interval_hours, id="reminders")
    scheduler.add_job(sync_projects_job, "interval", hours=24, id="sheets_sync")
    scheduler.start()
    print(f"[scheduler] Started — running every {s.reminder_interval_hours} hour(s)")
    # Sync project codes on startup
    sync_projects_job()
    yield
    scheduler.shutdown()


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Masterson Transaction Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock this down to your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "service": "Masterson Transaction Tracker"}


# ─── Plaid Webhook ────────────────────────────────────────────────────────────

@app.post("/webhook/plaid")
async def plaid_webhook(request: Request):
    """
    Plaid sends POST here when new transactions are available.
    Configure this URL in Plaid Dashboard > API > Webhooks.
    """
    payload = await request.json()
    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")

    print(f"[plaid webhook] {webhook_type}/{webhook_code}")

    if webhook_type == "TRANSACTIONS" and webhook_code in ("DEFAULT_UPDATE", "INITIAL_UPDATE", "HISTORICAL_UPDATE"):
        try:
            s = get_settings()
            new_txns = plaid_client.fetch_and_store_transactions(days_back=s.days_to_look_back)
            print(f"[plaid webhook] Stored {len(new_txns)} new transactions")
            # Immediately check for uncoded ones and remind
            due = db.get_uncoded_transactions_due_reminder(
                interval_hours=0,   # immediate on webhook
                max_reminders=s.max_reminders
            )
            for txn in due:
                try:
                    twilio_client.send_reminder(txn)
                except Exception as e:
                    print(f"[reminder error] {e}")
        except Exception as e:
            print(f"[plaid webhook error] {e}")

    return {"received": True}


# ─── Twilio Webhook (incoming SMS reply) ─────────────────────────────────────

@app.post("/webhook/twilio")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None),
    MessageSid: str = Form(None)
):
    """
    Twilio sends POST here when someone replies to a reminder SMS.
    Configure this URL in Twilio Console > Phone Numbers > your number > Messaging Webhook.
    Set to: https://your-railway-app.up.railway.app/webhook/twilio
    """
    from_phone = From.strip()
    reply_body = Body.strip()
    has_media = int(NumMedia) > 0
    media_url = MediaUrl0

    print(f"[twilio] Reply from {from_phone}: '{reply_body}' (media: {has_media})")

    # Log inbound
    db.log_sms(
        direction="inbound",
        from_number=from_phone,
        to_number=get_settings().twilio_phone_number,
        body=reply_body,
        media_url=media_url,
        twilio_sid=MessageSid
    )

    # Find which transaction this person is being asked about
    txn_id = db.get_pending(from_phone)
    if not txn_id:
        # No pending transaction — find the most recent uncoded for this employee
        employee = db.get_employee_by_phone(from_phone)
        if employee:
            uncoded = db.get_transactions(uncoded_only=True, employee_id=employee["id"], limit=1)
            txn_id = uncoded[0]["id"] if uncoded else None

    if not txn_id:
        twilio_client.send_sms(from_phone, "No pending transaction found. Contact Brandon if you think this is an error.")
        return {"ok": True}

    txn = db.get_transaction_by_id(txn_id)
    if not txn:
        twilio_client.send_sms(from_phone, "Transaction not found. Contact Brandon.")
        return {"ok": True}

    # Already coded?
    if txn.get("project_code"):
        twilio_client.send_sms(from_phone, f"That transaction is already coded as {txn['project_code']}. No action needed.")
        db.clear_pending(from_phone)
        return {"ok": True}

    # Parse the project code from their reply
    code = twilio_client.parse_project_code_from_reply(reply_body)

    if not code:
        twilio_client.send_sms(
            from_phone,
            "Couldn't read a project code from your reply. Please reply with just the code, like: JL"
        )
        return {"ok": True}

    # Validate code
    if not db.is_valid_project_code(code):
        codes = db.get_all_project_codes()
        code_list = ", ".join([p["code"] for p in codes])
        twilio_client.send_sms(
            from_phone,
            f"'{code}' is not a valid project code. Valid codes: {code_list}\n\nReply again with the correct code."
        )
        return {"ok": True}

    # Upload receipt photo if attached
    receipt_url = None
    if has_media and media_url:
        receipt_url = twilio_client.upload_receipt_to_storage(media_url, txn_id)

    # Assign the code
    db.assign_project_code(txn_id, code, receipt_url=receipt_url, coded_by="sms")
    db.clear_pending(from_phone)

    merchant = txn.get("merchant_name") or txn.get("description") or "that transaction"
    receipt_note = " Receipt saved ✅" if receipt_url else " (No receipt attached — remember to keep receipts!)"
    twilio_client.send_sms(
        from_phone,
        f"Got it! {merchant} → coded as {code}.{receipt_note}"
    )

    return {"ok": True}


# ─── API: Transactions ────────────────────────────────────────────────────────

@app.get("/api/transactions")
def list_transactions(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    coded_only: bool = False,
    uncoded_only: bool = False,
    employee_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
):
    rows = db.get_transactions(
        limit=limit, offset=offset,
        coded_only=coded_only, uncoded_only=uncoded_only,
        employee_id=employee_id, date_from=date_from, date_to=date_to
    )
    return {"transactions": rows, "count": len(rows)}


@app.get("/api/transactions/{txn_id}")
def get_transaction(txn_id: str):
    txn = db.get_transaction_by_id(txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return txn


@app.patch("/api/transactions/{txn_id}/code")
async def update_code(txn_id: str, request: Request):
    """Bookkeeper or admin manually assigns a project code from the dashboard."""
    body = await request.json()
    code = body.get("code", "").strip().upper()
    if not code:
        raise HTTPException(400, "code is required")
    if not db.is_valid_project_code(code):
        raise HTTPException(400, f"'{code}' is not a valid project code")
    db.assign_project_code(txn_id, code, receipt_url=body.get("receipt_url"), coded_by="dashboard")
    return {"ok": True, "code": code}


# ─── API: Project Codes ───────────────────────────────────────────────────────

@app.get("/api/projects")
def list_projects(active_only: bool = True):
    return {"projects": db.get_all_project_codes(active_only=active_only)}


# ─── API: Employees ───────────────────────────────────────────────────────────

@app.get("/api/employees")
def list_employees():
    return {"employees": db.get_all_employees()}


# ─── API: Export CSV ──────────────────────────────────────────────────────────

@app.get("/api/export/csv")
def export_csv(date_from: str | None = None, date_to: str | None = None):
    """Download all transactions as CSV for the bookkeeper."""
    rows = db.get_transactions(limit=5000, date_from=date_from, date_to=date_to)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "date", "merchant_name", "description", "amount",
        "card_last4", "employee", "project_code", "coded_by", "coded_at", "receipt_url", "notes"
    ])
    writer.writeheader()
    for r in rows:
        employee_name = ""
        if r.get("employees"):
            employee_name = r["employees"].get("name", "")
        writer.writerow({
            "date": r["date"],
            "merchant_name": r.get("merchant_name", ""),
            "description": r.get("description", ""),
            "amount": r["amount"],
            "card_last4": r.get("card_last4", ""),
            "employee": employee_name,
            "project_code": r.get("project_code", ""),
            "coded_by": r.get("coded_by", ""),
            "coded_at": r.get("coded_at", ""),
            "receipt_url": r.get("receipt_url", ""),
            "notes": r.get("notes", ""),
        })

    output.seek(0)
    filename = f"masterson_transactions_{date_from or 'all'}_{date_to or 'all'}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ─── API: Manual trigger (admin use) ─────────────────────────────────────────

@app.post("/api/admin/sync")
def manual_sync():
    """Manually trigger a Plaid sync + reminder check. For testing."""
    s = get_settings()
    try:
        plaid_client.fetch_and_store_transactions(days_back=s.days_to_look_back)
        due = db.get_uncoded_transactions_due_reminder(interval_hours=0, max_reminders=s.max_reminders)
        sent = 0
        for txn in due:
            twilio_client.send_reminder(txn)
            sent += 1
        return {"ok": True, "reminders_sent": sent}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/plaid-debug")
def plaid_debug():
    """Return raw Plaid transaction data for the last 3 transactions to inspect available fields."""
    import datetime
    s = get_settings()
    client = plaid_client._get_client()
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
    import datetime as dt
    req = TransactionsGetRequest(
        access_token=s.plaid_access_token,
        start_date=dt.date.today() - dt.timedelta(days=30),
        end_date=dt.date.today(),
        options=TransactionsGetRequestOptions(count=3)
    )
    resp = client.transactions_get(req)
    return {"transactions": [dict(t) for t in resp["transactions"]]}


@app.post("/api/admin/sync-projects")
def manual_sync_projects():
    """Manually trigger a Google Sheets → Supabase project code sync."""
    try:
        sync_projects_job()
        return {"ok": True, "message": "Project codes synced from Google Sheets"}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/admin/sync-accounts")
def sync_accounts():
    """Sync Plaid accounts → plaid_accounts table. Run after linking."""
    try:
        accounts = plaid_client.sync_accounts()
        return {"ok": True, "accounts": accounts}
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Opt-In ───────────────────────────────────────────────────────────────────

@app.post("/api/optin")
async def optin(request: Request):
    """Records an SMS opt-in submission from the /opt-in page."""
    body = await request.json()
    name = body.get("name", "").strip()
    phone = body.get("phone", "").strip()
    if not name or not phone:
        raise HTTPException(400, "name and phone are required")
    # Normalize to E.164 if needed
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        phone_e164 = f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        phone_e164 = f"+{digits}"
    else:
        raise HTTPException(400, "Invalid phone number")
    print(f"[optin] {name} — {phone_e164}")
    db.log_optin(name, phone_e164)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
