"""Seed public candidate suppliers from official public pages only.

Candidates are stored as PUBLIC_CANDIDATE discovery records — NOT active partners.
Unknown fields use UNKNOWN; no copyrighted catalog/price copy.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import User
from app.services.commercial_pilot_service import import_public_candidate, seed_platform_benchmark_backlog

RETRIEVED_AT = datetime(2026, 7, 26, tzinfo=timezone.utc)

LIFTING_CANDIDATES = [
    {
        "company_name": "Jiecang Linear Motion Technology",
        "brand_name": "Jiecang",
        "country": "CN",
        "manufacturing_region": "Zhejiang, CN",
        "source_url": "https://www.jiecang.com/",
        "categories": ["Lifting Systems", "Actuators", "Desk Columns"],
        "capabilities": ["linear actuators", "lifting columns", "OEM desk frames"],
        "certifications": ["CE (public claim — verify)"],
        "export_markets": ["EU", "NA", "UNKNOWN"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
        "notes": "Public website product categories only.",
    },
    {
        "company_name": "Loctek Ergonomic Technology",
        "brand_name": "Loctek",
        "country": "CN",
        "manufacturing_region": "Ningbo, CN",
        "source_url": "https://www.loctekmotion.com/",
        "categories": ["Lifting Systems", "Desk Frames"],
        "capabilities": ["height-adjustable desk frames", "monitor arms"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["Global B2B (public claim)"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "TiMOTION Technology",
        "brand_name": "TiMOTION",
        "country": "TW",
        "manufacturing_region": "Taoyuan, TW",
        "source_url": "https://www.timotion.com/",
        "categories": ["Lifting Systems", "Actuators", "Control Boxes"],
        "capabilities": ["electric actuators", "control systems", "medical/industrial motion"],
        "certifications": ["UL/CE (public claim — verify)"],
        "export_markets": ["NA", "EU", "APAC"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Richmat Technology",
        "brand_name": "Richmat",
        "country": "CN",
        "manufacturing_region": "Hangzhou, CN",
        "source_url": "https://www.richmat.com/",
        "categories": ["Lifting Systems", "Actuators"],
        "capabilities": ["linear actuators", "lifting columns"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["UNKNOWN"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Ergomotion",
        "brand_name": "Ergomotion",
        "country": "CN",
        "manufacturing_region": "UNKNOWN",
        "source_url": "https://www.ergomotion.com/",
        "categories": ["Lifting Systems", "Bed/Motion"],
        "capabilities": ["adjustable bases", "actuator systems"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["NA (public claim)"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Logicdata International",
        "brand_name": "Logicdata",
        "country": "AT",
        "manufacturing_region": "Austria/EU",
        "source_url": "https://www.logicdata.net/",
        "categories": ["Lifting Systems", "Columns", "Controls"],
        "capabilities": ["lifting columns", "control units", "office motion"],
        "certifications": ["CE (public claim — verify)"],
        "export_markets": ["EU", "NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "DewertOkin GmbH",
        "brand_name": "DewertOkin",
        "country": "DE",
        "manufacturing_region": "Germany/EU",
        "source_url": "https://www.dewertokin.com/",
        "categories": ["Lifting Systems", "Actuators"],
        "capabilities": ["drive systems", "adjustable furniture motion"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["Global OEM"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Kesseböhmer Ergotech",
        "brand_name": "Ergotech",
        "country": "DE",
        "manufacturing_region": "Germany",
        "source_url": "https://www.kesseboehmer-ergotech.de/",
        "categories": ["Lifting Systems", "Desk Frames"],
        "capabilities": ["height-adjustable desk systems"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["EU"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "FlexiSpot Business",
        "brand_name": "FlexiSpot",
        "country": "CN/US",
        "manufacturing_region": "UNKNOWN",
        "source_url": "https://www.flexispot.com/business",
        "categories": ["Lifting Systems", "Desk Frames", "B2B"],
        "capabilities": ["B2B standing desks", "OEM programs (public page)"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Stand Up Desk Store OEM Program",
        "brand_name": "SUDS OEM",
        "country": "US",
        "manufacturing_region": "US distribution",
        "source_url": "https://www.standupdeskstore.com/",
        "categories": ["Lifting Systems", "Desk Frames"],
        "capabilities": ["height-adjustable frames", "B2B sourcing reference"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
        "notes": "Reference for U.S. market expectations — not a manufacturing partner.",
    },
    {
        "company_name": "Progressive Desk",
        "brand_name": "Progressive Desk",
        "country": "CA",
        "manufacturing_region": "Canada",
        "source_url": "https://www.progressivedesk.ca/",
        "categories": ["Lifting Systems", "Desk Frames"],
        "capabilities": ["adjustable desk frames", "columns"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
]

EDUCATION_CANDIDATES = [
    {
        "company_name": "VS America",
        "brand_name": "VS",
        "country": "DE/US",
        "source_url": "https://www.vs.de/en/",
        "categories": ["Education Furniture", "School"],
        "capabilities": ["classroom furniture", "mobile tables/chairs"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["EU", "NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Smith System",
        "brand_name": "Smith System",
        "country": "US",
        "source_url": "https://smithsystem.com/",
        "categories": ["Education Furniture", "Classroom"],
        "capabilities": ["school desks", "chairs", "collaborative learning"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Scholar Craft",
        "brand_name": "Scholar Craft",
        "country": "US",
        "source_url": "https://www.scholarcraft.com/",
        "categories": ["Education Furniture"],
        "capabilities": ["student desks", "chairs"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "MooreCo",
        "brand_name": "MooreCo",
        "country": "US",
        "source_url": "https://www.moorecoinc.com/",
        "categories": ["Education Furniture", "Office"],
        "capabilities": ["education environments", "desks", "visual boards"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Fleetwood Group",
        "brand_name": "Fleetwood",
        "country": "US",
        "source_url": "https://www.fleetwoodfurniture.com/",
        "categories": ["Education Furniture"],
        "capabilities": ["school furniture", "casework"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Marco Group",
        "brand_name": "Marco",
        "country": "US",
        "source_url": "https://www.marco-group.com/",
        "categories": ["Education Furniture"],
        "capabilities": ["school furniture systems"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "HON Company Education",
        "brand_name": "HON",
        "country": "US",
        "source_url": "https://www.hon.com/education",
        "categories": ["Education Furniture", "Office"],
        "capabilities": ["education seating", "desks"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "KI (Krueger International)",
        "brand_name": "KI",
        "country": "US",
        "source_url": "https://www.ki.com/markets/education",
        "categories": ["Education Furniture"],
        "capabilities": ["education seating", "tables"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
]

CONTRACT_OFFICE_CANDIDATES = [
    {
        "company_name": "National Office Furniture",
        "brand_name": "National",
        "country": "US",
        "source_url": "https://www.nationalofficefurniture.com/",
        "categories": ["Contract Office", "Workstation"],
        "capabilities": ["office systems", "conference", "casegoods"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Trendway Corporation",
        "brand_name": "Trendway",
        "country": "US",
        "source_url": "https://www.trendway.com/",
        "categories": ["Contract Office", "Workstation"],
        "capabilities": ["architectural walls", "workstations"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Global Furniture Group",
        "brand_name": "Global",
        "country": "CA/US",
        "source_url": "https://www.globalfurnituregroup.com/",
        "categories": ["Contract Office", "Conference"],
        "capabilities": ["office seating", "desks", "conference"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["NA"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "AIS (Affiliated International Services)",
        "brand_name": "AIS",
        "country": "US",
        "source_url": "https://www.ais-inc.com/",
        "categories": ["Contract Office", "Workstation"],
        "capabilities": ["systems furniture", "private office"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Kimball International",
        "brand_name": "Kimball",
        "country": "US",
        "source_url": "https://www.kimballinternational.com/",
        "categories": ["Contract Office"],
        "capabilities": ["workplace furniture", "healthcare"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Teknion",
        "brand_name": "Teknion",
        "country": "CA",
        "source_url": "https://www.teknion.com/",
        "categories": ["Contract Office", "Workstation"],
        "capabilities": ["systems furniture", "conference"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["Global"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Watson Furniture Group",
        "brand_name": "Watson",
        "country": "US",
        "source_url": "https://www.watsonfurnituregroup.com/",
        "categories": ["Contract Office", "Conference"],
        "capabilities": ["conference tables", "desking"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
    {
        "company_name": "Studio Other",
        "brand_name": "Studio Other",
        "country": "US",
        "source_url": "https://www.studioother.com/",
        "categories": ["Contract Office", "Workstation"],
        "capabilities": ["modular workstations", "quick-ship programs (public claim)"],
        "certifications": ["UNKNOWN"],
        "export_markets": ["US"],
        "moq_notes": "UNKNOWN",
        "lead_time_notes": "UNKNOWN",
        "sample_policy": "UNKNOWN",
    },
]


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.isnot(None)).first()
        if not user:
            print("No user — run bootstrap first.")
            return 1

        all_candidates = LIFTING_CANDIDATES + EDUCATION_CANDIDATES + CONTRACT_OFFICE_CANDIDATES
        created = 0
        for payload in all_candidates:
            payload["retrieved_at"] = RETRIEVED_AT
            payload["data_source"] = "public_official_page"
            payload["evidence_status"] = "partial_public"
            import_public_candidate(db, payload=payload, actor_id=user.id)
            created += 1

        benchmark_count = seed_platform_benchmark_backlog(db, actor_id=user.id)
        db.commit()

        print(
            f"Public candidates processed: {created} "
            f"(lifting={len(LIFTING_CANDIDATES)}, education={len(EDUCATION_CANDIDATES)}, "
            f"contract={len(CONTRACT_OFFICE_CANDIDATES)})"
        )
        print(f"Platform benchmark rows created/updated: {benchmark_count}")
        print("COMMERCIAL_PILOT_PUBLIC_CANDIDATES: OK")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
