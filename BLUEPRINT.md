# Masterson Transaction Tracker — System Codex

## Purpose
Automatically pulls Capital One Spark business credit card transactions via Plaid, sends SMS reminders (via Twilio) to the employee who made each purchase asking them to associate it with a project code and reply with a receipt photo. A React dashboard lets admins/bookkeepers review, manually code, and export transactions.

---

## Architecture Overview

```
Capital One Spark
      │
   [Plaid API]
      │ webhook
      ▼
[Railway — FastAPI Backend]
      │─── Supabase (PostgreSQL + Storage)
      │─── Twilio (SMS out: reminders)
      │◄── Twilio (SMS in: replies + MMS receipts)
      │─── Google Sheets (optional: project code sync)
      ▼
[Vercel — React Frontend]
      (dashboard: view / code / export)
```

**Stack:**
- **Backend:** Python, FastAPI, APScheduler → deployed on Railway
- **Frontend:** React 18, Vite, Tailwind CSS → deployed on Vercel
- **Database:** Supabase (PostgreSQL + object storage for receipt photos)
- **Bank Data:** Plaid API (Capital One Spark)
- **SMS:** Twilio (A2P — pending registration as of 2026-03)
- **Project Codes Source:** Google Sheets CSV (optional, synced every 24h)

---

## Entry Points

| How | Command / URL |
|-----|--------------|
| Backend (local dev) | `cd backend && uvicorn main:app --reload` |
| Frontend (local dev) | `cd frontend && npm run dev` |
| Frontend (production) | https://transaction-tracker-wheat.vercel.app |
| Backend (production) | Railway app URL (set as `VITE_API_URL` in Vercel) |
| Manual Plaid link (one-time) | `python scripts/plaid_link.py` |
| Sync project codes from CSV | `python scripts/sync_projects.py --csv path/to/file.csv` |

---

## Dependencies & Config

### Backend — `backend/.env` (copy from `.env.example`)

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role key (NOT anon) |
| `SUPABASE_BUCKET` | Storage bucket name (default: `receipts`) |
| `PLAID_CLIENT_ID` | Plaid API client ID |
| `PLAID_SECRET` | Plaid API secret |
| `PLAID_ENV` | `sandbox`, `development`, or `production` |
| `PLAID_ACCESS_TOKEN` | From plaid_link.py one-time setup |
| `TWILIO_ACCOUNT_SID` | Twilio account ID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Twilio phone (E.164, e.g. `+18005551234`) |
| `ADMIN_PHONE` | Brandon's phone for unmapped transactions |
| `ADMIN_EMAIL` | Brandon's email (optional) |
| `REMINDER_INTERVAL_HOURS` | Frequency of reminder checks (default: 24) |
| `MAX_REMINDERS` | Max reminders before stopping (default: 3) |
| `DAYS_TO_LOOK_BACK` | History window for Plaid fetch (default: 7) |
| `GOOGLE_SHEETS_URL` | Optional: public CSV export for project sync |

### Frontend — `frontend/.env.local`
| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Railway backend URL (e.g. `https://xxx.up.railway.app/api`) |

---

## Data Flow

### Transaction Coding Flow (Automated)
1. Employee makes purchase on Capital One Spark card
2. Plaid detects transaction → fires webhook to `/webhook/plaid` on Railway
3. Backend fetches new transactions, stores in `transactions` table (Supabase)
4. For each uncoded transaction: Twilio sends SMS to matched employee
   - Match is via `card_last4` → `plaid_accounts` → `employees` table
   - If no match: SMS goes to `ADMIN_PHONE`
5. Employee replies with project code (e.g. `JL`, `SR-15`) and optional photo
6. Twilio fires webhook to `/webhook/twilio` on Railway
7. Backend parses project code from reply (regex: 1-5 uppercase letters, optional `-code`)
8. If MMS attached: downloads photo from Twilio, uploads to Supabase Storage
9. Transaction marked `coded_by = 'sms'`, `project_code` set, `receipt_url` saved
10. Dashboard reflects changes on next refresh

### Manual Coding (Dashboard)
1. Bookkeeper opens dashboard, sees uncoded transactions (red)
2. Clicks transaction → detail panel opens
3. Clicks project code button or types code manually
4. Clicks Save → PATCH `/api/transactions/{id}/code`
5. Transaction marked `coded_by = 'dashboard'`

### Background Jobs (every 24h)
- **Reminder job:** Fetch new Plaid transactions + re-send reminders to uncoded transactions under `MAX_REMINDERS` threshold
- **Project sync job:** Pull Google Sheets CSV → upsert `project_codes` table

---

## Database Schema (Supabase)

### Tables

**`employees`** — Who holds each card
- `id`, `name`, `card_last4` (unique), `phone_number` (E.164), `is_admin`, `created_at`

**`project_codes`** — Valid project codes
- `id`, `code` (unique, e.g. `JL`), `name` (e.g. `Jewish Living`), `description`, `is_active`, `created_at`, `updated_at`

**`transactions`** — Core ledger
- `id`, `plaid_transaction_id` (unique), `plaid_account_id`, `date`, `merchant_name`, `description`, `amount`, `card_last4`, `employee_id` (fk), `project_code` (fk), `receipt_url`, `coded_at`, `coded_by` (`sms`/`dashboard`/`auto`), `reminder_sent_at`, `reminder_count`, `notes`, `created_at`, `updated_at`

**`plaid_accounts`** — Maps Plaid account IDs to employees
- `id`, `plaid_account_id` (unique), `account_name`, `card_last4`, `employee_id` (fk), `created_at`

**`sms_log`** — Full audit trail of all SMS in/out
- `id`, `transaction_id` (fk), `direction` (`outbound`/`inbound`), `from_number`, `to_number`, `body`, `media_url`, `twilio_sid`, `created_at`

**Indexes:** `date DESC`, `project_code IS NULL` (uncoded), `employee_id`, `card_last4`

---

## API Routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/webhook/plaid` | Plaid transaction webhook |
| POST | `/webhook/twilio` | Twilio SMS/MMS reply webhook |
| GET | `/api/transactions` | List with filters (limit, offset, coded/uncoded, employee, date range) |
| GET | `/api/transactions/{id}` | Single transaction detail |
| PATCH | `/api/transactions/{id}/code` | Manually assign project code |
| GET | `/api/projects` | List project codes |
| GET | `/api/employees` | List employees |
| GET | `/api/export/csv` | Download CSV export |
| POST | `/api/admin/sync` | Manual: Plaid fetch + send reminders |
| POST | `/api/admin/sync-projects` | Manual: Google Sheets project sync |
| POST | `/api/admin/sync-accounts` | Manual: Populate plaid_accounts from Plaid |

---

## Integration Points

| Service | Role | Config Location | Notes |
|---------|------|----------------|-------|
| **Plaid** | Pull Capital One transactions | `backend/.env` | Webhook URL: `{railway_url}/webhook/plaid` |
| **Twilio** | Send/receive SMS + MMS | `backend/.env` | Webhook URL: `{railway_url}/webhook/twilio` — **A2P pending** |
| **Supabase** | PostgreSQL database + receipt photo storage | `backend/.env` | Run `supabase/schema.sql` on new project |
| **Railway** | Backend hosting | Environment variables in Railway dashboard | Deploy from `backend/` directory |
| **Vercel** | Frontend hosting | `VITE_API_URL` env var | Deploy from `frontend/` directory |
| **Google Sheets** | Optional project code source | `GOOGLE_SHEETS_URL` env var | Must be public CSV export URL |
| **Capital One Spark** | Source of truth for transactions | Accessed via Plaid | |

---

## Known Limitations / Pending

- **Twilio A2P registration pending (as of 2026-03)** — SMS reminders will not send to real numbers until A2P is approved. This is the main blocker for full production use.
- **CORS is open** — `allow_origins=["*"]` in `main.py`. Should be locked to Vercel URL in production.
- **No authentication on API routes** — Anyone with the Railway URL can read/modify transactions. Consider adding an API key or auth layer.
- **Pending state is in-memory** — Restarting the Railway backend clears the in-memory pending transaction tracker. Would need Redis for true production resilience.
- **Plaid access token** — Must be obtained by running `scripts/plaid_link.py` once locally and manually copying the token into Railway env vars.
- **Employees must be added manually** to Supabase with correct `card_last4` values.

---

## Operating Procedures

### First-Time Setup
1. Create Supabase project → run `supabase/schema.sql`
2. Create Plaid account → get `PLAID_CLIENT_ID` and `PLAID_SECRET`
3. Create Twilio account → buy phone number
4. Run `python scripts/plaid_link.py` locally → copy access token output
5. Fill `backend/.env` with all credentials
6. Push to GitHub
7. Deploy backend to Railway (set all env vars in Railway dashboard)
8. Deploy frontend to Vercel (set `VITE_API_URL`)
9. Set webhook URLs in Plaid and Twilio dashboards
10. Add employees to Supabase (`employees` table) with correct `card_last4` and phone numbers
11. Hit `POST /api/admin/sync-accounts` to populate `plaid_accounts`
12. Hit `POST /api/admin/sync` to pull first batch of transactions

### Adding a New Employee
- Insert row into `employees` table in Supabase
- `card_last4` must match what Plaid reports for their card
- `phone_number` must be E.164 format (e.g. `+15555551234`)
- Run `POST /api/admin/sync-accounts` after adding

### Adding Project Codes
- Option A: Insert directly into `project_codes` table in Supabase
- Option B: Add to the Google Sheets CSV and hit `POST /api/admin/sync-projects`
- Option C: Update `project_registry.csv` on Desktop and run `python scripts/sync_projects.py`

### Resetting/Redeploying
- Backend: redeploy from Railway dashboard (env vars persist)
- Frontend: redeploy from Vercel (automatic on git push)
- If Plaid access token changes: update `PLAID_ACCESS_TOKEN` in Railway

---

## Future Work
- [ ] Lock CORS to Vercel URL only
- [ ] Add API key or JWT auth to protect API routes
- [ ] Move pending state to Redis (Railway add-on) for restart resilience
- [ ] Add real-time updates to dashboard (Supabase Realtime subscriptions)
- [ ] Add email digest for admin (weekly uncoded summary)
- [ ] Multi-card account support (currently one Plaid access token)
- [ ] Receipt OCR for auto-extracting vendor/amount from photos
- [ ] Employee self-service portal (view their own transactions)
