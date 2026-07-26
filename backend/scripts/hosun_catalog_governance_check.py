"""Check strict HOSUN quote catalog governance.

HOSUN catalog scope is intentionally narrow:
- 50 rows from 产品分类.20260226.xlsx
- 5 hand control panels: HS11A-HS11E
- 1 Four Color Roll Swatch Sample Set

The active and total HOSUN quote catalog counts must both be 56. Historical
demo samples and old numeric-name pricing imports must not remain as HOSUN
catalog rows.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.models import ManufacturingPartner, ProductCatalog
from scripts.sync_hosun_classification_catalog import (
    additional_hosun_rows,
    load_classification_rows,
    normalize_model,
    resolve_default_classification,
)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"[PASS] {message}")


def main() -> int:
    classification = resolve_default_classification()
    workbook_rows = load_classification_rows(classification)
    expected_rows = workbook_rows + additional_hosun_rows()
    expected_models = {normalize_model(row["model"]) for row in expected_rows}

    if len(workbook_rows) != 50:
        fail(f"classification workbook should contain 50 HOSUN rows, got {len(workbook_rows)}")
    ok("classification workbook has 50 HOSUN rows")

    if len(expected_models) != 56:
        fail(f"HOSUN whitelist should contain 56 models, got {len(expected_models)}")
    ok("HOSUN whitelist has 56 models")

    with SessionLocal() as db:
        partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == "HOSUN").first()
        if not partner:
            fail("HOSUN partner not found")

        rows = db.query(ProductCatalog).filter(ProductCatalog.partner_id == partner.id).all()
        active = [row for row in rows if row.status == "active"]
        inactive = [row for row in rows if row.status != "active"]
        active_models = {normalize_model(row.partner_product_code) for row in active}

        if len(rows) != 56:
            fail(f"HOSUN catalog total must be 56, got {len(rows)}")
        ok("HOSUN catalog total is 56")

        if len(active) != 56:
            fail(f"HOSUN active catalog must be 56, got {len(active)}")
        ok("HOSUN active catalog is 56")

        if inactive:
            fail(f"HOSUN inactive leftovers found: {len(inactive)}")
        ok("no inactive HOSUN leftovers remain")

        missing = sorted(expected_models - active_models)
        extra = sorted(active_models - expected_models)
        if missing or extra:
            fail(f"HOSUN active models mismatch; missing={missing}, extra={extra}")
        ok("HOSUN active models match latest whitelist")

        bad_names = [
            row.product_name
            for row in active
            if re.match(r"^\s*\d", row.product_name or "") or "demo sample" in (row.product_name or "").lower()
        ]
        if bad_names:
            fail(f"obsolete numeric/demo names still active: {bad_names[:8]}")
        ok("no numeric-prefix or demo-sample HOSUN products remain active")

        missing_images = [row.partner_product_code or row.internal_sku for row in active if not row.image_url]
        if missing_images:
            fail(f"HOSUN products missing image_url: {missing_images[:8]}")
        ok("all 56 HOSUN products have image_url")

        active_demo = (
            db.query(ProductCatalog)
            .filter(ProductCatalog.status == "active", ProductCatalog.product_name.ilike("%demo sample%"))
            .all()
        )
        if active_demo:
            fail(f"active demo sample products remain: {[row.internal_sku for row in active_demo]}")
        ok("no active demo sample products remain in quote catalog")

    print("[PASS] safety: no quote creation, no external sending, no order mutation, no STAGING_VALIDATED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
