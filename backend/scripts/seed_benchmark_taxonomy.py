"""Seed industry benchmark taxonomy — facts from public references only."""

from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.benchmark_knowledge import (
    BenchmarkBrand,
    BenchmarkDataRights,
    BenchmarkProductCapability,
    BenchmarkSourceReference,
)

DISCLAIMER = "Industry reference only — not a PartnerOS partner, supplier, or authorized dealer."

LIFTING_BRANDS = (
    {
        "code": "LINAK",
        "name": "LINAK (public benchmark)",
        "vertical": "lifting_systems",
        "country": "Denmark",
        "url": "https://www.linak.com/",
        "caps": [
            ("load_capacity_kg", "Load capacity", "8000", "fact"),
            ("speed_mm_s", "Speed", "38", "fact"),
            ("stroke_range_mm", "Stroke range", "700", "inferred"),
            ("stages", "Stages", "2-3 column sync", "fact"),
            ("noise_db", "Noise level", "low-noise desk actuators", "inferred"),
            ("duty_cycle", "Duty cycle", "10% ED", "fact"),
            ("ip_rating", "IP rating", "IP54 options", "fact"),
            ("controller_type", "Controller", "CBD6 / DESKLINE", "fact"),
            ("anti_collision", "Anti-collision", "PIES / IC", "fact"),
            ("multi_column_sync", "Multi-column sync", "Yes", "fact"),
            ("application", "Applications", "office, medical, industrial", "fact"),
        ],
    },
    {
        "code": "JIECANG",
        "name": "JIECANG (public benchmark)",
        "vertical": "lifting_systems",
        "country": "China",
        "url": "https://www.jiecang.com/",
        "caps": [
            ("load_capacity_kg", "Load capacity", "800", "fact"),
            ("speed_mm_s", "Speed", "35", "inferred"),
            ("stroke_range_mm", "Stroke range", "650", "pending_verification"),
            ("stages", "Stages", "2-stage lifting columns", "fact"),
            ("noise_db", "Noise level", "<50 dB desk columns", "inferred"),
            ("duty_cycle", "Duty cycle", "10 min / 2 hr", "pending_verification"),
            ("ip_rating", "IP rating", "IP20 default", "inferred"),
            ("controller_type", "Controller", "JC35 / handsets", "fact"),
            ("anti_collision", "Anti-collision", "Optional", "pending_verification"),
            ("multi_column_sync", "Multi-column sync", "Yes", "fact"),
            ("application", "Applications", "office, industrial", "fact"),
        ],
    },
    {
        "code": "TIMOTION",
        "name": "TiMOTION (public benchmark)",
        "vertical": "lifting_systems",
        "country": "Taiwan",
        "url": "https://www.timotion.com/",
        "caps": [
            ("load_capacity_kg", "Load capacity", "1200", "fact"),
            ("speed_mm_s", "Speed", "40", "inferred"),
            ("stroke_range_mm", "Stroke range", "500-700", "inferred"),
            ("stages", "Stages", "2-stage", "fact"),
            ("noise_db", "Noise level", "Quiet desk actuators", "inferred"),
            ("duty_cycle", "Duty cycle", "10%", "pending_verification"),
            ("ip_rating", "IP rating", "IP54 medical options", "fact"),
            ("controller_type", "Controller", "TC21 / TCB series", "fact"),
            ("anti_collision", "Anti-collision", "T-Safety", "fact"),
            ("multi_column_sync", "Multi-column sync", "Yes", "fact"),
            ("application", "Applications", "office, medical", "fact"),
        ],
    },
    {
        "code": "KESSEBOHMER",
        "name": "Kesseböhmer (public benchmark)",
        "vertical": "lifting_systems",
        "country": "Germany",
        "url": "https://www.kesseboehmer.de/",
        "caps": [
            ("load_capacity_kg", "Load capacity", "120", "inferred"),
            ("speed_mm_s", "Speed", "38", "pending_verification"),
            ("stroke_range_mm", "Stroke range", "650", "inferred"),
            ("stages", "Stages", "2-stage", "fact"),
            ("noise_db", "Noise level", "Quiet office focus", "inferred"),
            ("duty_cycle", "Duty cycle", "Office duty", "pending_verification"),
            ("ip_rating", "IP rating", "Office grade", "inferred"),
            ("controller_type", "Controller", "Integrated desk systems", "inferred"),
            ("anti_collision", "Anti-collision", "Standard on premium lines", "pending_verification"),
            ("multi_column_sync", "Multi-column sync", "Conference table focus", "fact"),
            ("application", "Applications", "office, conference", "fact"),
        ],
    },
)

CONTRACT_OFFICE_CAPS = (
    ("desks", "Desks / workstations", "height-adjustable, benching, private office", "fact"),
    ("seating", "Seating", "task, executive, conference", "fact"),
    ("conference", "Conference", "tables, power, AV integration", "fact"),
    ("partitions", "Partitions", "demountable, acoustic", "inferred"),
    ("storage", "Storage", "lateral, tower, lockers", "fact"),
    ("acoustic", "Acoustic", "panels, pods", "inferred"),
    ("quick_ship", "Quick ship", "5-15 day programs", "pending_verification"),
    ("finishes", "Finishes", "laminate, veneer, powder coat", "fact"),
    ("certifications", "Certifications", "BIFMA, GREENGUARD", "fact"),
    ("project_delivery", "Project delivery", "dealer + project team", "fact"),
)

EDUCATION_CAPS = (
    ("student_desks", "Student desks/chairs", "fixed + adjustable", "fact"),
    ("activity_tables", "Activity tables", "collaborative shapes", "fact"),
    ("teacher_stations", "Teacher stations", "height-adjustable options", "inferred"),
    ("storage", "Storage", "mobile + built-in", "fact"),
    ("library", "Library furniture", "tables, seating, shelving", "inferred"),
    ("steam", "STEAM furniture", "maker tables, lab stools", "inferred"),
    ("cafeteria", "Cafeteria", "tables, benches", "fact"),
    ("ada", "ADA compliance", "mobility-access seating", "fact"),
    ("mobility", "Mobility", "casters, fold-n-nest", "fact"),
    ("durability", "Durability", "school-duty cycle", "fact"),
    ("lead_time", "Lead time", "project-based 8-16 weeks", "pending_verification"),
)


def _ensure_brand(db, spec: dict) -> BenchmarkBrand:
    row = db.query(BenchmarkBrand).filter(BenchmarkBrand.brand_code == spec["code"]).first()
    if row:
        return row
    row = BenchmarkBrand(
        brand_code=spec["code"],
        display_name=spec["name"],
        industry_vertical=spec["vertical"],
        country=spec.get("country"),
        website_url=spec.get("url"),
        relationship_disclaimer=DISCLAIMER,
        review_status="reviewed",
    )
    db.add(row)
    db.flush()
    db.add(
        BenchmarkDataRights(
            brand_id=row.id,
            allowed_use="Internal capability comparison and engineering reference.",
            prohibited_use="No logo, catalog, image, or price reproduction.",
        )
    )
    db.add(
        BenchmarkSourceReference(
            brand_id=row.id,
            source_type="PUBLIC_REFERENCE",
            source_url=spec.get("url"),
            source_title=f"{spec['name']} public product pages",
            retrieved_at=date.today(),
            review_status="reviewed",
            excerpt_facts="Public specification summaries only.",
        )
    )
    return row


def _ensure_cap(db, brand: BenchmarkBrand, key: str, label: str, value: str, status: str) -> None:
    existing = (
        db.query(BenchmarkProductCapability)
        .filter(BenchmarkProductCapability.brand_id == brand.id, BenchmarkProductCapability.capability_key == key)
        .first()
    )
    if existing:
        return
    db.add(
        BenchmarkProductCapability(
            brand_id=brand.id,
            capability_key=key,
            capability_label=label,
            value_text=value,
            verification_status=status,
            source_type="PUBLIC_REFERENCE",
            source_url=brand.website_url,
            retrieved_at=date.today(),
        )
    )


def run(*, apply: bool = True) -> int:
    db = SessionLocal()
    try:
        for spec in LIFTING_BRANDS:
            brand = _ensure_brand(db, spec)
            for key, label, value, status in spec["caps"]:
                _ensure_cap(db, brand, key, label, value, status)

        office = _ensure_brand(
            db,
            {
                "code": "CONTRACT-OFFICE-BENCH",
                "name": "Contract Office (taxonomy benchmark)",
                "vertical": "contract_office",
                "country": "Multi",
                "url": None,
            },
        )
        for key, label, value, status in CONTRACT_OFFICE_CAPS:
            _ensure_cap(db, office, key, label, value, status)

        edu = _ensure_brand(
            db,
            {
                "code": "EDUCATION-FURNITURE-BENCH",
                "name": "Education Furniture (taxonomy benchmark)",
                "vertical": "education_furniture",
                "country": "Multi",
                "url": None,
            },
        )
        for key, label, value, status in EDUCATION_CAPS:
            _ensure_cap(db, edu, key, label, value, status)

        if apply:
            db.commit()
            print("Benchmark taxonomy seed applied.")
        else:
            db.rollback()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
