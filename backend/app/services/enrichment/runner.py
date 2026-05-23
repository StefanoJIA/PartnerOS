"""Execute enrichment run in background (D5.2)."""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.models import Company
from app.models.enrichment import (
    ENRICHMENT_STATUS_COMPLETED,
    ENRICHMENT_STATUS_FAILED,
    ENRICHMENT_STATUS_RUNNING,
    CompanyEnrichmentRun,
    CompanyEnrichmentSource,
    CompanyEnrichmentSuggestion,
)
from app.services.enrichment.discover_urls import candidate_urls, normalize_base_website
from app.services.enrichment.fetch_pages import FetchResult, fetch_single_page
from app.services.enrichment.suggestion_builder import build_suggestion_dicts


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


FetchCallable = Callable[..., FetchResult]


def execute_enrichment_run(
    run_id: uuid.UUID,
    fetch_impl: FetchCallable | None = None,
) -> None:
    """fetch_impl replaces fetch_single_page in tests."""
    settings = get_settings()
    fetch_one: FetchCallable = fetch_impl or fetch_single_page
    db: Session = get_session_factory()()
    try:
        run = db.get(CompanyEnrichmentRun, run_id)
        if not run:
            return
        run.status = ENRICHMENT_STATUS_RUNNING
        run.started_at = _utcnow()
        db.commit()
        company = db.get(Company, run.company_id)
        if not company:
            run.status = ENRICHMENT_STATUS_FAILED
            run.error_message = "company not found"
            run.completed_at = _utcnow()
            db.commit()
            return

        base, host = normalize_base_website(company.website)
        if not base or not host:
            run.status = ENRICHMENT_STATUS_FAILED
            run.error_message = "company has no usable website URL"
            run.completed_at = _utcnow()
            db.commit()
            return

        seen_hashes: set[str] = set()
        sources_orm: list[CompanyEnrichmentSource] = []
        cap = min(run.max_pages, settings.ENRICHMENT_MAX_PAGES)
        for url, ptype in candidate_urls(base)[:cap]:
            fr: FetchResult = fetch_one(url, ptype, host, settings, seen_hashes)
            src = CompanyEnrichmentSource(
                enrichment_run_id=run.id,
                url=fr.url,
                page_title=fr.page_title,
                page_type=fr.page_type,
                fetched_at=fr.fetched_at,
                http_status=fr.http_status,
                fetch_status=fr.fetch_status,
                content_text=fr.content_text,
                content_excerpt=fr.content_excerpt,
                content_hash=fr.content_hash,
            )
            db.add(src)
            sources_orm.append(src)

        db.flush()

        sug_rows = build_suggestion_dicts(sources_orm, company.company_name)
        for row in sug_rows:
            db.add(CompanyEnrichmentSuggestion(enrichment_run_id=run.id, **row))

        run.pages_fetched = len(sources_orm)
        run.status = ENRICHMENT_STATUS_COMPLETED
        run.completed_at = _utcnow()
        run.error_message = None
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        try:
            run = db.get(CompanyEnrichmentRun, run_id)
            if run:
                run.status = ENRICHMENT_STATUS_FAILED
                run.completed_at = _utcnow()
                run.error_message = f"{type(e).__name__}: {e}"[:4000]
                db.add(run)
                db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
            try:
                run2 = db.get(CompanyEnrichmentRun, run_id)
                if run2:
                    run2.status = ENRICHMENT_STATUS_FAILED
                    run2.completed_at = _utcnow()
                    run2.error_message = traceback.format_exc()[:4000]
                    db.add(run2)
                    db.commit()
            except Exception:  # noqa: BLE001
                pass
    finally:
        db.close()
