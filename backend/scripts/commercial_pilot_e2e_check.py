"""Commercial pilot operations E2E gate."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    expected = "0033_commercial_pilot"
    print(f"Migration head: {head} (expected {expected})")

    checks: list[tuple[str, bool]] = [("migration head", head == expected)]

    try:
        from app.models.enums import SupplierRelationshipType, SupplierDevelopmentTaskType

        checks.append(("PUBLIC_CANDIDATE relationship", SupplierRelationshipType.public_candidate.value == "PUBLIC_CANDIDATE"))
        checks.append(("development task types", len(SupplierDevelopmentTaskType) >= 9))
    except Exception:
        checks.append(("commercial pilot enums", False))

    try:
        from app.services.commercial_pilot_service import (
            DEVELOPMENT_TASK_TEMPLATES,
            INDUSTRY_NEEDS,
            build_doc_request_checklist,
            build_email_draft,
        )

        checks.append(("development task templates", len(DEVELOPMENT_TASK_TEMPLATES) >= 9))
        checks.append(("three industry needs", len(INDUSTRY_NEEDS) == 3))
        draft = build_email_draft(company_name="Test Co", task_type="information_request")
        checks.append(("email draft blocked", draft.get("auto_send_blocked") == "true"))
        checks.append(("doc checklist", len(build_doc_request_checklist(task_type="catalog_requested")) >= 5))
    except Exception:
        checks.append(("commercial pilot service", False))

    try:
        from app.api.routes import commercial_pilot_operations

        checks.append(("commercial pilot routes", hasattr(commercial_pilot_operations, "router")))
    except Exception:
        checks.append(("commercial pilot routes", False))

    try:
        from app.core.database import SessionLocal
        from app.models import CommercialPilotRun, SupplierDiscoveryRecord
        from app.models.enums import PartnerLifecycle, SupplierRelationshipType
        from app.services.partner_lifecycle import is_partner_selectable_for_new_quote

        with SessionLocal() as db:
            public_count = (
                db.query(SupplierDiscoveryRecord)
                .filter(SupplierDiscoveryRecord.relationship_type == SupplierRelationshipType.public_candidate.value)
                .count()
            )
            checks.append(("public candidates seeded", public_count >= 26))
            pilot_count = db.query(CommercialPilotRun).count()
            checks.append(("commercial pilots present", pilot_count >= 3))
            from app.models import ManufacturingPartner

            legacy = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == "HOSUN").first()
            if legacy:
                checks.append(("legacy hosun not quote eligible", not is_partner_selectable_for_new_quote(legacy)))
            candidate = (
                db.query(ManufacturingPartner)
                .filter(ManufacturingPartner.lifecycle_status == PartnerLifecycle.candidate.value)
                .first()
            )
            if candidate:
                checks.append(("candidate partner not quote eligible", not is_partner_selectable_for_new_quote(candidate)))
    except Exception as exc:
        checks.append(("database commercial pilot state", False))
        print(f"  DB check error: {exc}")

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("Commercial pilot E2E gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
