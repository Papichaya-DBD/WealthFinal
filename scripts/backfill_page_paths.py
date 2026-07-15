#!/usr/bin/env python3
"""
Backfill HubDB "Page Path" so every hot-issue / asset-class-outlook topic row
becomes its own dynamic page at "{week_slug}-{slug}".

Idempotent — rows whose Page Path already matches the computed value are skipped,
so this is safe to re-run (e.g. daily via cron) without re-touching unchanged rows.

Usage:
  HUBSPOT_ACCESS_KEY=... python3 scripts/backfill_page_paths.py            # dry run, prints only
  HUBSPOT_ACCESS_KEY=... python3 scripts/backfill_page_paths.py --live     # actually writes + publishes
"""

import os
import re
import sys
import requests

HUBSPOT_ACCESS_KEY = os.environ.get("HUBSPOT_ACCESS_KEY")
API_BASE = "https://api.hubapi.com"

# table_id -> whether sub_title needs Thai->English translation before slugifying
TABLES = {
    "2599182038": {"name": "weekly hot-issue", "translate": False},
    "2601147111": {"name": "monthly hot-issue", "translate": False},
    "2601147112": {"name": "monthly asset-class-outlook", "translate": True},
}

# Known Thai asset-class sub_title values -> English slug component.
# Extend this as the data team introduces new asset classes; unmapped values
# are skipped (never guess-translated) and logged so this table can be updated.
THAI_TO_ENGLISH = {
    "ตราสารทุน": "equity",
    "ตราสารหนี้": "fixed-income",
    "พอร์ตตราสารหนี้ต่างประเทศ": "foreign-fixed-income-portfolio",
    "พอร์ตตราสารหนี้โลก": "global-fixed-income-portfolio",
    "Gold": "gold",
}


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def headers():
    if not HUBSPOT_ACCESS_KEY:
        sys.exit("HUBSPOT_ACCESS_KEY environment variable is required")
    return {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_KEY}",
        "Content-Type": "application/json",
    }


def fetch_rows(table_id):
    rows = []
    after = None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        resp = requests.get(
            f"{API_BASE}/cms/v3/hubdb/tables/{table_id}/rows",
            headers=headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return rows


def compute_slug(table_id, sub_title):
    if TABLES[table_id]["translate"]:
        mapped = THAI_TO_ENGLISH.get(sub_title.strip())
        if not mapped:
            print(
                f"  [SKIP] unmapped sub_title for table {table_id}: {sub_title!r} "
                "— add it to THAI_TO_ENGLISH and re-run"
            )
            return None
        return mapped
    return slugify(sub_title)


def update_row_path(table_id, row_id, path, live):
    if not live:
        print(f"  [DRY RUN] would set table {table_id} row {row_id} path = {path!r}")
        return
    resp = requests.patch(
        f"{API_BASE}/cms/v3/hubdb/tables/{table_id}/rows/{row_id}/draft",
        headers=headers(),
        json={"path": path},
    )
    resp.raise_for_status()


def publish_table(table_id, live):
    if not live:
        print(f"  [DRY RUN] would publish table {table_id}")
        return
    resp = requests.post(
        f"{API_BASE}/cms/v3/hubdb/tables/{table_id}/draft/push-live",
        headers=headers(),
    )
    resp.raise_for_status()


def main():
    live = "--live" in sys.argv
    only_table = None
    if "--table" in sys.argv:
        only_table = sys.argv[sys.argv.index("--table") + 1]
        if only_table not in TABLES:
            sys.exit(f"Unknown table id {only_table!r} — must be one of {list(TABLES)}")
    print(f"Mode: {'LIVE (will write + publish)' if live else 'DRY RUN (no writes)'}\n")

    tables = {only_table: TABLES[only_table]} if only_table else TABLES
    for table_id, meta in tables.items():
        print(f"=== Table {table_id} ({meta['name']}) ===")
        rows = fetch_rows(table_id)
        changed = 0
        for row in rows:
            values = row.get("values", {})
            week_slug = values.get("week_slug")
            sub_title = values.get("sub_title")
            if not week_slug or not sub_title:
                print(f"  [SKIP] row {row['id']} missing week_slug or sub_title")
                continue

            slug = compute_slug(table_id, sub_title)
            if not slug:
                continue

            new_path = f"{week_slug}-{slug}"
            existing_path = (row.get("path") or "").strip()
            if existing_path == new_path:
                continue  # already correct

            update_row_path(table_id, row["id"], new_path, live)
            changed += 1

        if changed:
            publish_table(table_id, live)
        print(f"  {changed} row(s) {'updated' if live else 'would be updated'}\n")


if __name__ == "__main__":
    main()
