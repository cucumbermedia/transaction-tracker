-- =====================================================
-- Masterson Transaction Tracker — Supabase Schema
-- Run this in: Supabase Dashboard > SQL Editor > New Query
-- =====================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- =====================================================
-- EMPLOYEES
-- Maps each Capital One employee card to a person + phone
-- =====================================================
create table if not exists employees (
    id              uuid primary key default uuid_generate_v4(),
    name            text not null,
    card_last4      text not null unique,   -- last 4 digits of their Capital One card
    phone_number    text not null,          -- E.164 format: +14155551234
    is_admin        boolean default false,
    created_at      timestamptz default now()
);

-- =====================================================
-- PROJECT CODES
-- Synced from project_registry.csv via scripts/sync_projects.py
-- =====================================================
create table if not exists project_codes (
    id              uuid primary key default uuid_generate_v4(),
    code            text not null unique,   -- e.g. "JL", "SR", "S-O"
    name            text,                   -- e.g. "Jewish Living"
    description     text,
    is_active       boolean default true,
    created_at      timestamptz default now(),
    updated_at      timestamptz default now()
);

-- =====================================================
-- TRANSACTIONS
-- Core table — one row per Capital One transaction
-- =====================================================
create table if not exists transactions (
    id                  uuid primary key default uuid_generate_v4(),
    plaid_transaction_id text unique not null,  -- Plaid's stable transaction ID
    plaid_account_id    text,                   -- Plaid account (maps to card)
    date                date not null,
    merchant_name       text,
    description         text,                   -- raw Plaid name field
    amount              numeric(10,2) not null, -- positive = expense
    card_last4          text,                   -- derived from account mapping
    employee_id         uuid references employees(id),
    project_code        text references project_codes(code),
    receipt_url         text,                   -- Supabase Storage URL
    coded_at            timestamptz,
    coded_by            text,                   -- 'sms', 'dashboard', 'auto'
    reminder_sent_at    timestamptz,
    reminder_count      int default 0,
    notes               text,
    created_at          timestamptz default now(),
    updated_at          timestamptz default now()
);

-- =====================================================
-- PLAID ACCOUNTS
-- Maps Plaid account IDs to card last4 + employee
-- Populated after Plaid link (scripts/plaid_link.py)
-- =====================================================
create table if not exists plaid_accounts (
    id              uuid primary key default uuid_generate_v4(),
    plaid_account_id text unique not null,
    account_name    text,
    card_last4      text,
    employee_id     uuid references employees(id),
    created_at      timestamptz default now()
);

-- =====================================================
-- SMS LOG
-- Every outbound reminder + inbound reply
-- =====================================================
create table if not exists sms_log (
    id              uuid primary key default uuid_generate_v4(),
    transaction_id  uuid references transactions(id),
    direction       text check (direction in ('outbound', 'inbound')),
    from_number     text,
    to_number       text,
    body            text,
    media_url       text,           -- MMS receipt photo URL (inbound)
    twilio_sid      text,
    created_at      timestamptz default now()
);

-- =====================================================
-- INDEXES
-- =====================================================
create index if not exists idx_transactions_date on transactions(date desc);
create index if not exists idx_transactions_coded on transactions(project_code) where project_code is null;
create index if not exists idx_transactions_employee on transactions(employee_id);
create index if not exists idx_transactions_card on transactions(card_last4);

-- =====================================================
-- ROW LEVEL SECURITY
-- Bookkeeper: read-only on transactions + project_codes
-- Admin (you): full access
-- =====================================================
alter table transactions enable row level security;
alter table project_codes enable row level security;
alter table employees enable row level security;
alter table sms_log enable row level security;
alter table plaid_accounts enable row level security;

-- Service role (backend) bypasses RLS automatically
-- Authenticated users (bookkeeper/admin) get read access to transactions + project_codes
create policy "Authenticated read transactions"
    on transactions for select
    to authenticated
    using (true);

create policy "Authenticated read project_codes"
    on project_codes for select
    to authenticated
    using (true);

create policy "Authenticated read employees"
    on employees for select
    to authenticated
    using (true);

-- Admin update policy (restrict to specific email in your app logic)
create policy "Authenticated update transactions"
    on transactions for update
    to authenticated
    using (true);

-- =====================================================
-- UPDATED_AT TRIGGER
-- =====================================================
create or replace function update_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger trg_transactions_updated_at
    before update on transactions
    for each row execute function update_updated_at();

create trigger trg_project_codes_updated_at
    before update on project_codes
    for each row execute function update_updated_at();
