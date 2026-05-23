"""D5.2.12 optional local screenshot capture (PNG gitignored).

Usage (backend + frontend running):
  set FRONTEND_BASE_URL=http://127.0.0.1:5174
  python backend/scripts/capture_demo_screenshots.py

Review outputs for email/token masking before external share.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "records" / "screenshots" / "20260523"
BASE = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5174").rstrip("/")
EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "admin@example.com")
PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "admin123")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed: pip install playwright && playwright install chromium")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            page.goto(f"{BASE}/login", wait_until="networkidle")
            page.fill('input[type="email"]', EMAIL)
            page.fill('input[type="password"]', PASSWORD)
            page.click('button:has-text("Sign in")')
            page.wait_for_timeout(3000)
            if "/login" in page.url:
                raise RuntimeError(f"Login did not redirect — still at {page.url}")
            page.screenshot(path=str(OUT / "login_success.png"), full_page=True)
            print(f"Saved login_success.png")

            page.goto(f"{BASE}/lead-intelligence", wait_until="networkidle")
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / "lead_intelligence_daily_summary.png"), full_page=True)
            page.screenshot(path=str(OUT / "operation_filters.png"), full_page=True)
            page.screenshot(path=str(OUT / "manual_outreach_queue.png"), full_page=True)
            print("Saved lead-intelligence screenshots")

            row = page.locator(".el-table__row").first
            if row.count():
                row.click()
                page.wait_for_timeout(1500)
            gen = page.locator('button:has-text("Generate Draft")')
            if gen.count():
                gen.first.click()
                page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / "outreach_draft_panel.png"), full_page=True)
            print("Saved outreach_draft_panel.png")

            mark = page.locator('button:has-text("Mark as Sent")')
            if mark.count() and mark.first.is_enabled():
                mark.first.click()
                page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / "mark_as_sent_success.png"), full_page=True)
            print("Saved mark_as_sent_success.png")

            page.goto(f"{BASE}/system-health", wait_until="networkidle")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "system_health_portal_readiness.png"), full_page=True)
            print("Saved system_health_portal_readiness.png")

            page.goto(f"{BASE}/portal-consumer-mock", wait_until="networkidle")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "portal_consumer_mock.png"), full_page=True)
            print("Saved portal_consumer_mock.png")
        finally:
            browser.close()

    print(f"Done — files in {OUT} (gitignored). Mask emails/tokens before sharing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
