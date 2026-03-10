# Masterson Transaction Tracker — Setup Guide

Complete these steps in order. Each section takes 15-30 minutes.
Total time: ~3-4 hours (mostly waiting for accounts to activate).

---

## Step 1 — Supabase (Database + Storage)

1. Go to https://supabase.com → Sign up (free)
2. Create a new project → name it "masterson-tracker" → choose a strong password → region: US West
3. Wait ~2 min for project to spin up
4. Go to **SQL Editor** → click **New Query**
5. Paste the entire contents of `supabase/schema.sql` → click **Run**
6. Go to **Storage** → click **New bucket** → name: `receipts` → toggle **Public bucket ON** → Save
7. Go to **Settings → API** → copy:
   - **Project URL** → this is your `SUPABASE_URL`
   - **service_role** secret key → this is your `SUPABASE_SERVICE_KEY` (NOT the anon key)

---

## Step 2 — Plaid (Capital One connection)

1. Go to https://dashboard.plaid.com/signup → Sign up (free)
2. After signup, in the dashboard go to **Team Settings → Keys**
3. Copy your **client_id** and **Secret** (use the Production secret)
4. Go to **API → Configure → Webhooks** → you'll fill in the URL after Step 5 (Railway deploy)
5. Plaid may ask you to apply for Production access — apply, it's usually approved same day for small businesses

---

## Step 3 — Twilio (SMS)

1. Go to https://twilio.com → Sign up (free trial gives $15 credit)
2. Once in the console, go to **Phone Numbers → Manage → Buy a Number**
   - Choose a US number with SMS capability → Buy (~$1/month)
3. From the Console homepage, copy:
   - **Account SID**
   - **Auth Token**
   - **Your Twilio phone number** (format: +12223334444)
4. Under **Phone Numbers → Manage → Active Numbers** → click your number
   - Scroll to **Messaging** → **A message comes in** → Webhook
   - You'll fill in the URL after Step 5 (Railway deploy)

---

## Step 4 — Fill in backend/.env

Copy `backend/.env.example` to `backend/.env` and fill in all values:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_BUCKET=receipts

PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=production
PLAID_ACCESS_TOKEN=        ← leave blank for now, filled in Step 6

TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

ADMIN_PHONE=+1XXXXXXXXXX   ← YOUR cell phone
ADMIN_EMAIL=brandon@...
REMINDER_INTERVAL_HOURS=24
MAX_REMINDERS=3
DAYS_TO_LOOK_BACK=7
SECRET_KEY=                ← run: python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 5 — Deploy Backend to Railway

1. Go to https://railway.app → Sign up with GitHub
2. Create a new project → **Deploy from GitHub repo**
   - If not in GitHub yet: push the `Transaction_Tracker/` folder to a new private GitHub repo first
   - `git init && git add . && git commit -m "init" && git remote add origin <your-repo-url> && git push -u origin main`
3. In Railway → select your repo → set **Root Directory** to `backend`
4. Go to **Variables** → add each variable from your `backend/.env` file
5. Railway auto-deploys — wait ~2 min → copy your app URL: `https://your-app.up.railway.app`
6. **Update Plaid webhook:** Dashboard → API → Webhooks → add: `https://your-app.up.railway.app/webhook/plaid`
7. **Update Twilio webhook:** Phone number settings → Messaging webhook → `https://your-app.up.railway.app/webhook/twilio`

---

## Step 6 — Link Capital One via Plaid (One-Time)

```bash
cd C:\Users\brand\OneDrive\Desktop\Transaction_Tracker
pip install -r backend/requirements.txt
python scripts/plaid_link.py
```

- A browser window opens → click **Connect Capital One**
- Log into your Capital One Spark account when prompted
- After success, the page shows your `PLAID_ACCESS_TOKEN`
- Copy it into `backend/.env` → `PLAID_ACCESS_TOKEN=access-production-xxxxx...`
- Update this variable in Railway too (Railway dashboard → Variables)

---

## Step 7 — Sync Plaid Accounts

After linking, tell the app which card belongs to which person:

```bash
# Hit the sync-accounts endpoint to map Plaid account IDs → card last4
curl -X POST https://your-app.up.railway.app/api/admin/sync-accounts
```

Then in Supabase → Table Editor → `employees` table → add a row for each person:

| name | card_last4 | phone_number | is_admin |
|------|-----------|--------------|----------|
| Brandon Masterson | XXXX | +14155551234 | true |
| Christian | XXXX | +14155555678 | false |

Get the card last4 values from: Supabase → `plaid_accounts` table (populated after sync-accounts)

---

## Step 8 — Sync Project Codes

```bash
python scripts/sync_projects.py
# or specify a path:
python scripts/sync_projects.py --csv "C:\Users\brand\OneDrive\Desktop\project_registry.csv"
```

Re-run this anytime you update your project registry.

---

## Step 9 — Deploy Frontend to Vercel

1. Go to https://vercel.com → Sign up with GitHub
2. **New Project** → import your same GitHub repo → set **Root Directory** to `frontend`
3. Add environment variable:
   - `VITE_API_URL` = `https://your-app.up.railway.app/api`
4. Deploy → Vercel gives you a URL like `https://masterson-tracker.vercel.app`
5. Share that URL with your bookkeeper — it's the dashboard

---

## Step 10 — Test the Whole Flow

```bash
# Trigger a manual sync + send reminders
curl -X POST https://your-app.up.railway.app/api/admin/sync
```

Or click **🔄 Sync Now** in the dashboard.

You should receive a test SMS on your phone for any uncoded transactions.
Reply with a project code (e.g. `JL`) and optionally attach a receipt photo.

---

## Christian's Card Note

Currently Christian uses your physical card (same card number), so the system
can't auto-distinguish his transactions. Two options:

**Option A (recommended):** Get Christian a free Capital One employee card.
- Capital One Spark → Account Services → Add Employee Card → free, instant
- His card gets its own last 4 → add him to the `employees` table → system routes automatically

**Option B:** All transactions on your card come to you. You code them manually
from the dashboard or reply to SMS reminders yourself.

---

## Day-to-Day Operations

| Task | How |
|------|-----|
| New transaction comes in | Plaid webhook → auto SMS reminder within minutes |
| Reply to reminder | Text the project code (+ photo) to your Twilio number |
| Bookkeeper reviews | Opens dashboard URL, views/codes transactions, downloads CSV |
| Add new project code | Re-run `sync_projects.py` or add directly in Supabase |
| Check for stuck reminders | Dashboard → filter "Uncoded" |
| Manual sync | Click Sync Now in dashboard or POST /api/admin/sync |

---

## File Structure Reference

```
Transaction_Tracker/
├── backend/
│   ├── main.py          ← FastAPI app (deploys to Railway)
│   ├── database.py      ← Supabase operations
│   ├── plaid_client.py  ← Plaid transaction fetching
│   ├── twilio_client.py ← SMS send/receive + receipt upload
│   ├── config.py        ← Settings from .env
│   ├── requirements.txt
│   ├── Procfile         ← Railway start command
│   └── .env             ← YOUR SECRETS (never commit this)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    ← Main app shell
│   │   ├── components/
│   │   │   ├── StatsBar.jsx           ← Coded/uncoded counts
│   │   │   ├── Filters.jsx            ← Date/employee/status filters
│   │   │   ├── TransactionList.jsx    ← Table of transactions
│   │   │   └── TransactionDetail.jsx  ← Side panel: code + receipt
│   │   └── lib/api.js                 ← Backend API calls
│   └── .env.local                     ← VITE_API_URL (set in Vercel)
├── supabase/
│   └── schema.sql       ← Run once in Supabase SQL editor
├── scripts/
│   ├── sync_projects.py ← Sync project_registry.csv → Supabase
│   └── plaid_link.py    ← One-time Capital One linking
└── SETUP.md             ← This file
```
