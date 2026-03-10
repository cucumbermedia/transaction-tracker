"""
Sync project_registry.csv → Supabase project_codes table.

Usage:
    python scripts/sync_projects.py
    python scripts/sync_projects.py --csv "C:/path/to/other_registry.csv"

Expects CSV columns (flexible — adjust COLUMN_MAP below to match your actual headers):
    Code, Name, Description   (or similar)
"""
import csv
import sys
import os
from pathlib import Path

# Default path to your existing project registry
DEFAULT_CSV = r"C:\Users\brand\OneDrive\Desktop\project_registry.csv"

# ─── Adjust these to match your actual CSV column names ──────────────────────
COLUMN_MAP = {
    "code":        ["location_code", "Code", "code", "PROJECT_CODE", "ProjectCode", "project_code"],
    "name":        ["project_name", "Name", "name", "Project Name", "ProjectName"],
    "description": ["client", "Description", "description", "Notes", "notes"],
}
# ─────────────────────────────────────────────────────────────────────────────

# Add backend to path so we can import database.py
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import database as db


def find_col(headers: list[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in headers:
            return c
    return None


def sync(csv_path: str):
    if not os.path.exists(csv_path):
        print(f"[error] CSV not found: {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        code_col = find_col(headers, COLUMN_MAP["code"])
        name_col = find_col(headers, COLUMN_MAP["name"])
        desc_col  = find_col(headers, COLUMN_MAP["description"])

        if not code_col:
            print(f"[error] Could not find a 'code' column in: {headers}")
            print(f"  Expected one of: {COLUMN_MAP['code']}")
            sys.exit(1)

        print(f"Using columns → code: '{code_col}', name: '{name_col}', description: '{desc_col}'")
        print(f"Syncing from: {csv_path}\n")

        count = 0
        skipped = 0
        for row in reader:
            code = row.get(code_col, "").strip().upper()
            if not code:
                skipped += 1
                continue
            name = row.get(name_col, "").strip() if name_col else ""
            description = row.get(desc_col, "").strip() if desc_col else ""
            db.upsert_project_code(code, name, description)
            print(f"  ✓ {code:<12} {name}")
            count += 1

    print(f"\nDone. {count} project codes synced, {skipped} blank rows skipped.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to project_registry.csv")
    args = parser.parse_args()
    sync(args.csv)
