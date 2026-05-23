"""Extract visible text and title from HTML (BeautifulSoup)."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def html_to_text_and_title(html: str, max_chars: int) -> tuple[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    blob = "\n".join(lines)
    blob = re.sub(r"\n{3,}", "\n\n", blob)
    if len(blob) > max_chars:
        blob = blob[:max_chars]
    return blob, title
