"""
Twilio SMS/MMS — sends reminders and processes replies.
"""
from twilio.rest import Client as TwilioClient
from config import get_settings
import database as db
import httpx
import re


def _get_client() -> TwilioClient:
    s = get_settings()
    return TwilioClient(s.twilio_account_sid, s.twilio_auth_token)


def _format_reminder(txn: dict, project_codes: list[dict], position: int = 1, total: int = 1) -> str:
    """Build the SMS reminder text with queue position."""
    merchant = txn.get("merchant_name") or txn.get("description") or "Unknown Merchant"
    amount = f"${txn['amount']:.2f}"
    date_str = txn["date"]
    codes_preview = ", ".join([p["code"] for p in project_codes[:8]])
    if len(project_codes) > 8:
        codes_preview += f" (+{len(project_codes)-8} more)"

    queue_line = f"#{position} of {total} transactions" if total > 1 else "transaction"

    return (
        f"[Masterson] Uncoded {queue_line}:\n"
        f"📍 {merchant}\n"
        f"💰 {amount}  |  📅 {date_str}\n\n"
        f"Reply with project code + receipt photo.\n"
        f"OPS = Masterson Operations\n"
        f"Example: JL\n\n"
        f"Codes: {codes_preview}"
    )


def send_reminder(txn: dict, position: int = 1, total: int = 1) -> str | None:
    """
    Send an SMS reminder for an uncoded transaction.
    position/total used for queue messaging (e.g. '#1 of 3 transactions').
    Returns Twilio message SID or None if no phone to send to.
    """
    s = get_settings()

    # Determine who to text
    employee = txn.get("employees")
    if s.test_mode:
        to_phone = s.admin_phone
    elif employee and employee.get("phone_number"):
        to_phone = employee["phone_number"]
    else:
        to_phone = s.admin_phone

    project_codes = db.get_all_project_codes()
    body = _format_reminder(txn, project_codes, position, total)

    client = _get_client()
    message = client.messages.create(
        body=body,
        from_=s.twilio_phone_number,
        to=to_phone
    )

    db.log_sms(
        direction="outbound",
        from_number=s.twilio_phone_number,
        to_number=to_phone,
        body=body,
        transaction_id=txn["id"],
        twilio_sid=message.sid
    )

    db.mark_reminder_sent(txn["id"], txn.get("reminder_count", 0))
    db.set_pending(to_phone, txn["id"])

    return message.sid


def send_sms(to: str, body: str) -> str:
    """Send a plain SMS (for confirmations/errors)."""
    s = get_settings()
    client = _get_client()
    message = client.messages.create(
        body=body,
        from_=s.twilio_phone_number,
        to=to
    )
    db.log_sms("outbound", s.twilio_phone_number, to, body, twilio_sid=message.sid)
    return message.sid


def upload_receipt_to_storage(media_url: str, txn_id: str) -> str | None:
    """
    Download the MMS photo from Twilio and upload to Supabase Storage.
    Returns the public URL or None.
    """
    s = get_settings()
    supabase = db.get_db()

    try:
        # Download image from Twilio (requires auth)
        client = _get_client()
        with httpx.Client() as http:
            resp = http.get(
                media_url,
                auth=(s.twilio_account_sid, s.twilio_auth_token),
                follow_redirects=True,
                timeout=15
            )
            resp.raise_for_status()
            image_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg")
            ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]

        # Upload to Supabase Storage
        path = f"receipts/{txn_id}.{ext}"
        supabase.storage.from_(s.supabase_bucket).upload(
            path,
            image_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # Get public URL
        public_url = supabase.storage.from_(s.supabase_bucket).get_public_url(path)
        return public_url

    except Exception as e:
        print(f"[receipt upload error] {e}")
        return None


def parse_project_code_from_reply(body: str) -> str | None:
    """
    Extract project code from an SMS reply body.
    Handles: "JL", "sr", "S-O", "code is JL", "JL thanks", etc.
    """
    if not body:
        return None
    # Strip and upper
    body = body.strip().upper()
    # Try to match known patterns: 1-5 uppercase letters optionally followed by - and more letters/numbers
    match = re.search(r'\b([A-Z]{1,5}(?:-[A-Z0-9]{1,4})?)\b', body)
    return match.group(1) if match else None
