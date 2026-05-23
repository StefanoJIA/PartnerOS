"""Preview CSV lead intake rows (D5.2.4 / D5.3). Default read-only; use --apply --confirm to import."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.models import User
from app.services.a_domain.lead_import_service import apply_lead_csv_text, preview_lead_csv_text
from app.services.a_domain.lead_import_intake import read_csv_rows


def _admin_user(db) -> User | None:
    return db.query(User).filter(User.email == "admin@example.com").first()


def _print_preview(result) -> None:
    print("Lead Import Preview")
    for w in result.header_warnings:
        print(f"[HEADER WARN] {w}")
    for r in result.rows:
        tag = r.status.upper()
        print(f"[{tag}] {r.company_name or '(empty)'}")
        if r.duplicate_status != "new":
            print(f"  duplicate: {r.duplicate_status}")
        if r.missing_fields:
            print(f"  missing: {', '.join(r.missing_fields)}")
        seg = ", ".join(r.likely_segments) if r.likely_segments else "(none)"
        print(f"  segments: {seg}")
        print(f"  priority: {r.priority_hint}")
        print(f"  next_action: {r.recommended_next_action}")
        print()
    s = result.summary
    print(
        f"Summary: total={s.total} ok={s.ok} warn={s.warnings} "
        f"errors={s.errors} duplicates={s.duplicates} ready={s.ready_to_import}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview CSV lead intake (D5.2.4 / D5.3)")
    parser.add_argument("csv_path", type=Path, help="Path to lead_import_template.csv")
    parser.add_argument("--apply", action="store_true", help="Create companies/contacts/leads")
    parser.add_argument("--confirm", action="store_true", help="Required with --apply")
    args = parser.parse_args()

    if not args.csv_path.is_file():
        print(f"File not found: {args.csv_path}")
        return 1

    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        return 1

    try:
        csv_text = args.csv_path.read_text(encoding="utf-8-sig")
        read_csv_rows(args.csv_path)
    except ValueError as e:
        print(f"CSV error: {e}")
        return 1

    db = SessionLocal()
    try:
        result = preview_lead_csv_text(db, csv_text)
        _print_preview(result)

        if args.apply:
            user = _admin_user(db)
            if not user:
                print("Cannot find admin@example.com — run seed first")
                return 1
            print("--- Apply ---")
            try:
                applied = apply_lead_csv_text(db, user, csv_text, confirm=True)
            except ValueError as e:
                print(f"Apply refused: {e}")
                return 1
            print(
                f"created_companies={applied.created_companies} "
                f"skipped_duplicates={applied.skipped_duplicates} "
                f"created_contacts={applied.created_contacts} "
                f"linked_leads={applied.linked_leads}"
            )
            for w in applied.warnings:
                print(f"  warn: {w}")
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
