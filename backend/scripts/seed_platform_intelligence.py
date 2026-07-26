"""Seed platform benchmark matrix and channel intelligence fixtures."""

from __future__ import annotations

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.platform_intelligence import ChannelIntelligenceMetric, PlatformBenchmarkRecord

PLATFORM_ROWS = (
    ("Alibaba", "B2B discovery", "Supplier search and RFQ broadcast", False, "No structured project fit or quote interval governance", True, "P1"),
    ("Thomasnet", "Industrial supplier discovery", "Category search and supplier profiles", False, "No CPR → QIC → quote loop", True, "P2"),
    ("Shopify B2B", "Customer ordering", "Catalog + checkout for dealers", False, "No multi-supplier engineering fit or production tracking", True, "P2"),
    ("Zoho CRM", "CRM pipeline", "Lead and deal tracking", False, "No product capability schema or interval quote PDF", True, "P1"),
    ("PartnerOS", "Project export OS", "CPR → multi-supplier compare → QIC → interval quote → production", True, None, False, "P0"),
)

CHANNEL_ROWS = (
    ("direct", "2026-H1", 12, 5, 2, Decimal("4.2"), Decimal("0.42"), Decimal("0.40")),
    ("referral", "2026-H1", 8, 4, 2, Decimal("4.5"), Decimal("0.50"), Decimal("0.50")),
    ("trade_show", "2026-H1", 15, 3, 1, Decimal("3.1"), Decimal("0.20"), Decimal("0.33")),
    ("website", "2026-H1", 22, 6, 1, Decimal("3.8"), Decimal("0.27"), Decimal("0.17")),
    ("manual", "2026-H1", 6, 2, 1, Decimal("3.5"), Decimal("0.33"), Decimal("0.50")),
)


def run(*, apply: bool = True) -> int:
    db = SessionLocal()
    try:
        for platform, area, desc, has_it, gap, build, priority in PLATFORM_ROWS:
            exists = (
                db.query(PlatformBenchmarkRecord)
                .filter(
                    PlatformBenchmarkRecord.platform_name == platform,
                    PlatformBenchmarkRecord.capability_area == area,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                PlatformBenchmarkRecord(
                    platform_name=platform,
                    capability_area=area,
                    capability_description=desc,
                    partneros_has=has_it,
                    partneros_gap_notes=gap,
                    build_recommended=build,
                    build_priority=priority or "P2",
                    evidence_source="internal_fixture",
                )
            )

        for channel, period, leads, quotes, wins, quality, qrate, wrate in CHANNEL_ROWS:
            exists = (
                db.query(ChannelIntelligenceMetric)
                .filter(
                    ChannelIntelligenceMetric.channel_source == channel,
                    ChannelIntelligenceMetric.period_label == period,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                ChannelIntelligenceMetric(
                    channel_source=channel,
                    period_label=period,
                    lead_count=leads,
                    quote_count=quotes,
                    win_count=wins,
                    lead_quality_score=quality,
                    quote_rate=qrate,
                    win_rate=wrate,
                    data_source="manual",
                    notes="Fixture metrics — manual/import only.",
                )
            )

        if apply:
            db.commit()
            print("Platform intelligence seed applied.")
        else:
            db.rollback()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
