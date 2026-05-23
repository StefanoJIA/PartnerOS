"""Unit tests for D5.2 enrichment (no database)."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.models.enrichment import FETCH_OK
from app.services.enrichment.discover_urls import candidate_urls, normalize_base_website
from app.services.enrichment.ssrf import validate_public_http_url
from app.services.enrichment.suggestion_builder import TAG_SUGGESTION_RULES, build_suggestion_dicts
from app.services.a_domain.intelligence_score import infer_market_fit_segments


def test_normalize_website_adds_scheme():
    base, host = normalize_base_website("example.com/about")
    assert host == "example.com"
    assert base == "https://example.com"


def test_candidate_urls_cover_mvp_paths():
    urls = candidate_urls("https://example.com")
    assert len(urls) == 6
    types = {t for _, t in urls}
    assert "contact" in types
    assert "root" in types


def test_ssrf_blocks_localhost():
    ok, _ = validate_public_http_url("http://127.0.0.1/", "example.com")
    assert ok is False


def test_ssrf_allows_same_host():
    ok, _ = validate_public_http_url("https://www.example.com/products", "example.com")
    assert ok is True


def test_tag_rules_no_partner_names():
    blob = " ".join(t[0] for t in TAG_SUGGESTION_RULES)
    assert "hosun" not in blob.lower()
    assert "jooboo" not in blob.lower()


def _src(cid, text, url="https://x/y", ex=None):
    return SimpleNamespace(
        id=cid,
        fetch_status=FETCH_OK,
        content_text=text,
        url=url,
        content_excerpt=ex or text[:120],
        page_title="T",
    )


def test_enrichment_suggestions_general_office_only_segment():
    s = _src(uuid.uuid4(), "We are a contract furniture dealer for office projects.")
    rows = build_suggestion_dicts([s], "Acme")
    seg_vals = [r["suggested_value"] for r in rows if r["suggestion_type"] == "market_segment"]
    assert "general_office_furniture_only" in seg_vals
    assert "lift_system_signal" not in seg_vals


def test_enrichment_suggestions_lift_not_general_office():
    s = _src(
        uuid.uuid4(),
        "Office furniture programs including height adjustable desk and lifting column.",
    )
    rows = build_suggestion_dicts([s], "Acme")
    seg_vals = [r["suggested_value"] for r in rows if r["suggestion_type"] == "market_segment"]
    assert "lift_system_signal" in seg_vals
    assert "general_office_furniture_only" not in seg_vals


def test_infer_segments_mutual_exclusion_on_combined_blob():
    blob = "office furniture\nheight adjustable desk"
    segs = infer_market_fit_segments(blob.lower())
    assert "lift_system_signal" in segs
    assert "general_office_furniture_only" not in segs
