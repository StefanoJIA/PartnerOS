"""HTTP fetch with SSRF re-check after redirects; duplicate hash (D5.2)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import Settings
from app.services.enrichment.html_text import html_to_text_and_title
from app.services.enrichment.ssrf import validate_public_http_url


@dataclass
class FetchResult:
    url: str
    page_type: str
    http_status: int | None
    fetch_status: str
    page_title: str | None
    content_text: str | None
    content_excerpt: str | None
    content_hash: str | None
    fetched_at: datetime | None


def _excerpt(text: str, n: int = 240) -> str:
    t = " ".join(text.split())
    if len(t) <= n:
        return t
    return t[: n - 1] + "…"


def fetch_single_page(
    url: str,
    page_type: str,
    allowed_hostname: str,
    settings: Settings,
    seen_hashes: set[str],
) -> FetchResult:
    from app.models.enrichment import (
        FETCH_BLOCKED,
        FETCH_DUPLICATE,
        FETCH_HTTP_ERROR,
        FETCH_INVALID_URL,
        FETCH_OK,
        FETCH_TIMEOUT,
    )

    ok, reason = validate_public_http_url(url, allowed_hostname)
    if not ok:
        return FetchResult(
            url=url,
            page_type=page_type,
            http_status=None,
            fetch_status=FETCH_INVALID_URL if reason != "blocked_host" else FETCH_BLOCKED,
            page_title=None,
            content_text=None,
            content_excerpt=None,
            content_hash=None,
            fetched_at=None,
        )

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=settings.ENRICHMENT_FETCH_TIMEOUT_SEC,
            headers={"User-Agent": "intelliOffice-enrichment/1.0"},
        ) as client:
            r = client.get(url)
    except httpx.TimeoutException:
        return FetchResult(
            url=url,
            page_type=page_type,
            http_status=None,
            fetch_status=FETCH_TIMEOUT,
            page_title=None,
            content_text=None,
            content_excerpt=None,
            content_hash=None,
            fetched_at=datetime.now(timezone.utc),
        )
    except httpx.RequestError:
        return FetchResult(
            url=url,
            page_type=page_type,
            http_status=None,
            fetch_status=FETCH_BLOCKED,
            page_title=None,
            content_text=None,
            content_excerpt=None,
            content_hash=None,
            fetched_at=datetime.now(timezone.utc),
        )

    final_url = str(r.url)
    ok2, _ = validate_public_http_url(final_url, allowed_hostname)
    if not ok2 or r.status_code >= 400:
        return FetchResult(
            url=final_url,
            page_type=page_type,
            http_status=r.status_code,
            fetch_status=FETCH_HTTP_ERROR,
            page_title=None,
            content_text=None,
            content_excerpt=None,
            content_hash=None,
            fetched_at=datetime.now(timezone.utc),
        )

    raw = r.content[: settings.ENRICHMENT_MAX_RESPONSE_BYTES]
    ctype = (r.headers.get("content-type") or "").lower()
    text_body: str | None = None
    title: str | None = None
    if "html" in ctype or not ctype:
        try:
            decoded = raw.decode(r.encoding or "utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            decoded = raw.decode("utf-8", errors="replace")
        text_body, title = html_to_text_and_title(decoded, settings.ENRICHMENT_MAX_TEXT_CHARS_PER_PAGE)
    else:
        text_body = raw.decode("utf-8", errors="replace")[: settings.ENRICHMENT_MAX_TEXT_CHARS_PER_PAGE]

    h = hashlib.sha256((text_body or "").encode("utf-8")).hexdigest()
    if h in seen_hashes:
        return FetchResult(
            url=final_url,
            page_type=page_type,
            http_status=r.status_code,
            fetch_status=FETCH_DUPLICATE,
            page_title=title,
            content_text=text_body,
            content_excerpt=_excerpt(text_body) if text_body else None,
            content_hash=h,
            fetched_at=datetime.now(timezone.utc),
        )
    seen_hashes.add(h)

    return FetchResult(
        url=final_url,
        page_type=page_type,
        http_status=r.status_code,
        fetch_status=FETCH_OK,
        page_title=title,
        content_text=text_body,
        content_excerpt=_excerpt(text_body) if text_body else None,
        content_hash=h,
        fetched_at=datetime.now(timezone.utc),
    )
