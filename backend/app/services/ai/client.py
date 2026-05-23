from typing import Any

import httpx

from app.core.config import get_settings


def chat_completion(messages: list[dict[str, str]], model: str | None = None, temperature: float = 0.7) -> str:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return "[PartnerOS] AI key not configured. Set OPENAI_API_KEY for live output."
    m = model or settings.DEFAULT_MODEL
    url = f"{settings.OPENAI_API_BASE.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {"model": m, "messages": messages, "temperature": temperature}
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"]


def embed_texts(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return [[0.0] * 1536 for _ in texts]
    url = f"{settings.OPENAI_API_BASE.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "input": texts}
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


def truncate_linkedin_note(text: str, max_chars: int = 300) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"
