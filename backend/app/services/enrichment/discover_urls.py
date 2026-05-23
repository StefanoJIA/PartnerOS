"""Build candidate URLs from company website (fixed paths, D5.2 MVP)."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


def normalize_base_website(website: str | None) -> tuple[str | None, str | None]:
    """Returns (base_url_with_scheme, hostname) or (None, None)."""
    if not website or not str(website).strip():
        return None, None
    w = str(website).strip()
    if not w.startswith(("http://", "https://")):
        w = "https://" + w
    p = urlparse(w)
    if not p.scheme or not p.netloc:
        return None, None
    host = p.hostname
    if not host:
        return None, None
    base = f"{p.scheme}://{p.netloc}"
    return base.rstrip("/"), host


FIXED_PATHS: tuple[tuple[str, str], ...] = (
    ("/", "root"),
    ("/about", "about"),
    ("/products", "products"),
    ("/services", "services"),
    ("/solutions", "solutions"),
    ("/contact", "contact"),
)


def candidate_urls(base: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for path, ptype in FIXED_PATHS:
        u = urljoin(base + "/", path.lstrip("/"))
        if u not in seen:
            seen.add(u)
            out.append((u, ptype))
    return out
