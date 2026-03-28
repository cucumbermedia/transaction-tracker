# Masterson Transaction Tracker — Blueprint

## Purpose
Automatically pulls Capital One Spark business credit card transactions via Plaid, sends SMS reminders (via Twilio) to the employee who made each purchase asking them to associate it with a project code and reply with a receipt photo. A React dashboard lets admins/bookkeepers review, manually code, and export transactions.

---

## Architecture Overview

```
Capital One Spark
      │
   [Plaid API]
      │ webhook / scheduled sync
      ▼
[Railway — FastAPI Backend]
      │─── Supabase (PostgreSQL + Storage)
      │─── Twilio (SMS out: reminders, queued 1 per employee)
      │◄── Twilio (SMS in: replies + MMS receipts)
      │─── Google Sheets (optional: project code sync)
      ▼
[Vercel — React Frontend]
      (dashboard: view / filter by employee / code / export)
```

**Stack:**
- **Backend:** Python, FastAPI, APScheduler → deployed on Railway
- **Frontend:** React 18, Vite, Tailwind CSS → deployed on Vercel
- **Database:** Supabase (PostgreSQL + object storage for receipt photos)
- **Bank Data:** Plaid API (Capital One Spark, production)
- **SMS:** Twilio A2P — **APPROVED ✅ (2026-03-28)**
- **Project Codes Source:** Google Sheets CSV (optional, synced every 24h)

---

## Entry Points

| How | Command / URL |
|-----|--------------|
| Backend (local dev) | `cd backend && uvicorn main:app --reload` |
| Frontend (local dev) | `cd frontend && npm run dev` |
| Frontend (production) | https://transaction-tracker-wheat.vercel.app |
| Backend (production) | https://transaction-tracker-production-0eda.up.railway.app |
| SMS Opt-In page | https://transaction-tracker-wheat.vercel.app/opt-in |
| Privacy Policy | https://transaction-tracker-wheat.vercel.app/privacy |
| Terms & Conditions | https://transaction-tracker-wheat.vercel.app/terms |
| Manual Plaid link (one-time) | `python scripts/plaid_link.py` |

---

## Dependencies & Config

### Backend — Railway Environment Variables

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Service role key (NOT anon) |
| `SUPABASE_BUCKET` | Storage bucket name (default: `receipts`) |
| `PLAID_CLIENT_ID` | Plaid API client ID (no prefix — just the ID) |
| `PLAID_SECRET` | Plaid **production** secret |
| `PLAID_ENV` | `production` |
| `PLAID_ACCESS_TOKEN` | From plaid_link.py one-time setup |
| `TWILIO_ACCOUNT_SID` | Twilio account ID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | (707) 343-4630 → `+17073434630` |
| `ADMIN_PHONE` | Brandon's phone — receives texts for unmapped transactions |
| `ADMIN_EMAIL` | Brandon's email (optional) |
| `REMINDER_INTERVAL_HOURS` | How often to re-remind (default: 24) |
| `MAX_REMINDERS` | Max reminders before stopping (set to 365 — effectively unlimited) |
| `DAYS_TO_LOOK_BACK` | History window for Plaid fetch (default: 7) |
| `GOOGLE_SHEETS_URL` | Public CSV export URL for project code sync |
| `TEST_MODE` | `true` = all texts go to ADMIN_PHONE only. Remove or set `false` for production. |

### Frontend — Vercel Environment Variables
| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | `https://transaction-tracker-production-0eda.up.railway.app/api` |

---

## Data Flow

### Transaction Coding Flow (Automated)
1. Employee makes purchase on Capital One Spark card
2. Plaid detects transaction → fires webhook to `/webhook/plaid` on Railway
3. Backend fetches new transactions, maps `account_owner` field (card last 4) to employee
4. Transaction stored in `transactions` table (Supabase)
5. For each active employee with uncoded transactions: sends **1 SMS** (newest uncoded first)
   - Message includes queue position: "#1 of 3 transactions"
   - `TEST_MODE=true` sends all to `ADMIN_PHONE` instead
6. Employee replies with project code (e.g. `JL`) and optional receipt photo
7. Twilio fires webhook to `/webhook/twilio` on Railway
8. Backend parses project code:
   - Exact match first (e.g. `JL`)
   - Fuzzy name match if no exact (e.g. "Coastside" → finds project with "Coastside" in name)
   - If no match: stores raw reply in `raw_reply` field for admin review
9. If MMS attached: downloads photo from Twilio, uploads to Supabase Storage
10. Transaction marked coded, confirmation sent, **next transaction in queue fires automatically**
11. When all coded: "All transactions coded! You're all caught up 🎉"

### Card → Employee Mapping
- Plaid returns each transaction with `account_owner` = card last 4 digits
- Backend looks up `card_last4` in `employees` table to find the employee
- Capital One Spark shows as one account in Plaid but individual card numbers per authorized user are in `account_owner`

### Manual Coding (Dashboard)
1. Bookkeeper opens dashboard, sees uncoded transactions (red)
2. Clicks transaction → detail panel
3. Assigns project code → PATCH `/api/transactions/{id}/code`
4. Transaction marked `coded_by = 'dashboard'`

### Background Jobs
- **Reminder job (every 24h):** Fetch new Plaid transactions + send 1 reminder per active employee with uncoded transactions
- **Project sync job (every 24h):** Pull Google Sheets CSV → upsert `project_codes` table

---

## Database Schema (Supabase)

### `employees` — Who holds each card
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid | Auto-generated |
| `name` | text | Employee name |
| `card_last4` | text | Last 4 of their company card |
| `phone_number` | text | E.164 format (+1XXXXXXXXXX) |
| `is_admin` | boolean | True for Brandon |
| `is_active` | boolean | **Toggle to enable/disable SMS for this person** |
| `created_at` | timestamptz | Auto |

### `transactions` — Core ledger
| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid | Auto |
| `plaid_transaction_id` | text | Unique — prevents duplicates |
| `date` | date | Transaction date |
| `merchant_name` | text | From Plaid |
| `amount` | numeric | Positive = debit |
| `card_last4` | text | From Plaid `account_owner` field |
| `employee_id` | uuid | FK to employees |
| `project_code` | text | Assigned code |
| `receipt_url` | text | Supabase Storage URL |
| `coded_at` | timestamptz | When coded |
| `coded_by` | text | `sms` / `dashboard` |
| `reminder_count` | int | How many reminders sent |
| `reminder_sent_at` | timestamptz | Last reminder timestamp |
| `raw_reply` | text | Stored if reply didn't match any code |
| `is_pending` | boolean | True if Plaid transaction is pending |

### `pending_sms` — Tracks active transaction per employee (Supabase-backed, survives restarts)
- `phone` (PK), `txn_id` (FK → transactions), `updated_at`

### `project_codes`
- `id`, `code` (unique), `name`, `description`, `is_active`
- **OPS** = Masterson Operations (fuel, supplies, general overhead)

### `sms_log` — Full audit trail
- `id`, `transaction_id`, `direction`, `from_number`, `to_number`, `body`, `media_url`, `twilio_sid`, `created_at`

### `opt_ins` — Web form opt-in records
- `id`, `name`, `phone`, `created_at`

---

## API Routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/webhook/plaid` | Plaid transaction webhook |
| POST | `/webhook/twilio` | Twilio SMS/MMS reply webhook |
| GET | `/api/transactions` | List with filters |
| PATCH | `/api/transactions/{id}/code` | Manually assign project code |
| GET | `/api/projects` | List project codes |
| GET | `/api/employees` | List employees |
| GET | `/api/export/csv` | Download CSV |
| POST | `/api/admin/sync` | Manual: Plaid fetch + send reminders |
| POST | `/api/admin/sync-projects` | Manual: Google Sheets sync |
| POST | `/api/admin/sync-accounts` | Manual: Populate plaid_accounts |
| POST | `/api/admin/remap-employees` | Re-map card/employee on existing transactions |
| POST | `/api/optin` | Record SMS opt-in submission |

---

## Integration Points

| Service | Role | Notes |
|---------|------|-------|
| **Plaid** | Pull Capital One transactions | Webhook: `{railway_url}/webhook/plaid`. Access token from `plaid_link.py`. Production env + production secret. |
| **Twilio** | Send/receive SMS + MMS | Webhook: `{railway_url}/webhook/twilio`. A2P **APPROVED** ✅. Messaging Service SID: `MG652df4da...`. Number: (707) 343-4630. |
| **Supabase** | PostgreSQL + receipt storage | Service key required (not anon key) |
| **Railway** | Backend hosting | Auto-deploys on git push to main |
| **Vercel** | Frontend hosting | Auto-deploys on git push. VITE_API_URL must include `/api` suffix. |
| **Google Sheets** | Project code source | Must be public CSV export URL |

---

## Employee Rollout

Employees are enabled one at a time using `is_active` in the Supabase `employees` table:
- `is_active = true` → receives SMS reminders
- `is_active = false` → transactions tracked in dashboard, no texts sent

**Current status (2026-03-28):**
- Brandon ✅ active (admin, card 6703)
- Tony Durenberger ✅ active (card 2665) — being onboarded 2026-03-28
- Everyone else → inactive, pending rollout

**To activate next person:** Set `is_active = true` in Supabase employees table.

---

## Known Limitations / Pending

- **TEST_MODE** — Set `TEST_MODE=true` in Railway to route all texts to `ADMIN_PHONE`. Remove when rolling out to team.
- **Scheduled sync not yet configured** — Currently manual sync only. Plan to add Railway cron job (`0 * * * *`) once system is validated.
- **Pending transactions not yet implemented** — Currently only settled transactions trigger SMS. Plaid pending transaction support would enable near-instant notification on card swipe.
- **CORS is open** — `allow_origins=["*"]` in `main.py`. Should be locked to Vercel URL.
- **No API auth** — Anyone with Railway URL can read/modify data. Add API key later.
- **Plaid access token** — Must be obtained by running `scripts/plaid_link.py` locally and pasting into Railway env vars. Token: stored in Railway.

---

## Operating Procedures

### Adding a New Employee
1. Insert row into `employees` table in Supabase
2. `card_last4` must match Capital One card number (last 4)
3. `phone_number` must be E.164 (`+15555551234`)
4. `is_active = false` until ready to roll out
5. Set `is_active = true` when ready

### Adding Project Codes
- Option A: Insert directly into `project_codes` table in Supabase
- Option B: Add to Google Sheets → hit `POST /api/admin/sync-projects`

### Enabling a Scheduled Sync (TODO)
- Railway → project → Add → Cron
- Schedule: `0 * * * *` (every hour)
- Command: `curl -X POST https://transaction-tracker-production-0eda.up.railway.app/api/admin/sync`

### If Plaid Stops Working
- Check `PLAID_ACCESS_TOKEN` is still valid in Railway
- Re-run `scripts/plaid_link.py` locally to get a new token
- Update `PLAID_ACCESS_TOKEN` in Railway → redeploy

---

## Future Work
- [ ] Pending transaction support (near-instant SMS on card swipe)
- [ ] Scheduled hourly sync via Railway cron
- [ ] Lock CORS to Vercel URL only
- [ ] Add API key auth to protect routes
- [ ] Spend-by-project reporting in dashboard
- [ ] Raw reply review UI in dashboard (transactions with unrecognized codes)
- [ ] QuickBooks/accounting export format
- [ ] Receipt OCR (auto-extract vendor/amount from photo)
- [ ] Employee self-service view (see your own transactions)

---

<details>
<summary>📖 The Story — How This Was Built</summary>

## How This Came Together

The idea started simple: Brandon at Masterson Solutions kept running into the same problem. The company uses a Capital One Spark business credit card, with multiple employees carrying their own authorized user cards. At the end of every month, the bookkeeper would get a statement full of transactions — Home Depot, Chevron, Ace Hardware — and have no idea which job site they belonged to. Someone had to manually chase down receipts and ask "hey what was this $247 at Pete's Hardware for?"

The question was: **what if the system asked them automatically, right after the purchase?**

**The pieces that make it work:**

- **Plaid** is a service that connects to bank accounts (with permission) and reads transaction data. Think of it as a secure bridge between Capital One and our system. When someone swipes their card, Plaid eventually sees the transaction and can notify us.

- **Twilio** is a service that sends and receives text messages programmatically. It's how the system sends "hey, you just spent $88 at Pete's Hardware — what project is this for?" and receives the reply back.

- **Railway** is where the brain of the system lives — a Python server that runs 24/7, talks to Plaid and Twilio, and handles all the logic.

- **Supabase** is the database — it stores every transaction, every employee's card info, every project code, every receipt photo, and every text message sent or received.

- **Vercel** hosts the dashboard — a simple web app where Brandon and the bookkeeper can see all transactions, filter by employee or date, manually assign codes, and export to CSV.

**What happens when someone buys something:**

1. Card gets swiped at the store
2. Capital One processes it, Plaid picks it up (usually within hours)
3. Our system matches the card number to the employee who carries it
4. Twilio sends that employee a text: "You have 3 transactions to code. #1: Pete's Hardware $88.19 on 3/26 — reply with your project code"
5. Employee replies with the job code (like `JL` for a specific project) and optionally a photo of the receipt
6. System codes the transaction, saves the receipt, and immediately asks about the next one
7. Dashboard updates automatically

**The Twilio A2P saga:**

Getting Twilio approved to send business SMS messages (called A2P 10DLC registration) turned out to be the most painful part. The automated review system rejected the campaign multiple times — once for the consent language, once for missing privacy/terms pages, once because Twilio's bot couldn't read the website (the pages were built in React which doesn't work for bots that can't run JavaScript). After building static HTML pages, getting a human reviewer (Monica from Twilio compliance) involved, and adding the required SMS data sharing language to the privacy policy, the campaign was finally approved.

**The card mapping discovery:**

Initially assumed Plaid would show each employee card as a separate account. It doesn't — Capital One shows everything under one "Spark Cash" account. The breakthrough was discovering that Plaid includes the individual card's last 4 digits in a field called `account_owner` on each transaction. That's how the system knows Tony's transaction vs Brandon's transaction even though they're all on the same account.

**Rollout strategy:**

Rather than flipping it on for all 7 employees at once, there's an `is_active` flag on each employee. Brandon tested it first, then Tony (ride-along on 2026-03-28), then one by one from there. `TEST_MODE` in the config routes all texts to Brandon's phone during testing so no one gets surprised.

</details>
