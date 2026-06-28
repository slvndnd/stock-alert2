from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

LOGGER = logging.getLogger(__name__)

# Global browser instance
_BROWSER: Browser | None = None


def _get_browser() -> Browser:
    """Get or create the Playwright browser instance."""
    global _BROWSER
    if _BROWSER is None:
        try:
            LOGGER.info("Launching Playwright headless Chromium...")
            playwright = sync_playwright().start()
            _BROWSER = playwright.chromium.launch(headless=True)
            LOGGER.info("✓ Playwright browser launched successfully")
        except Exception as exc:
            LOGGER.error(
                "Failed to launch Playwright browser: %s\n"
                "Make sure you've run: python -m playwright install chromium",
                exc,
            )
            raise
    return _BROWSER


def close_browser() -> None:
    """Close the browser."""
    global _BROWSER
    if _BROWSER:
        try:
            _BROWSER.close()
            LOGGER.info("✓ Playwright browser closed")
        except Exception as exc:
            LOGGER.warning("Error closing browser: %s", exc)
        finally:
            _BROWSER = None


@dataclass(slots=True)
class BrowserFetchResponse:
    url: str
    status_code: int
    text: str
    blocked: bool = False
    blocked_reason: str = ""


def fetch_with_browser(target_url: str, timeout: float = 15.0) -> BrowserFetchResponse:
    """
    Fetch a page using Playwright headless browser.
    Contours WAF and Cloudflare by executing JavaScript.

    Args:
        target_url: URL to fetch
        timeout: Timeout in seconds (default 15s, reduced from 30s for speed)

    Returns:
        BrowserFetchResponse with the page content or error info.
    """
    # Random delay before fetch (anti-bot)
    delay = random.uniform(1.0, 2.0)
    time.sleep(delay)

    browser = None
    page: Page | None = None

    try:
        browser = _get_browser()
        page = browser.new_page()

        # Set realistic user agent (Playwright sets this by default)
        page.set_extra_http_headers({
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
        })

        LOGGER.debug("Fetching %s with Playwright (timeout %.0fs)...", target_url, timeout)

        # Use domcontentloaded instead of networkidle for speed
        # (doesn't wait for all resources, just DOM ready)
        response = page.goto(
            target_url,
            wait_until="domcontentloaded",  # Faster than networkidle
            timeout=timeout * 1000,
        )

        if response is None:
            LOGGER.warning("No response from %s", target_url)
            return BrowserFetchResponse(
                url=target_url,
                status_code=0,
                text="",
                blocked=True,
                blocked_reason="Aucune réponse du serveur",
            )

        status = response.status

        if status in (403, 429, 503):
            reason = {
                403: "Accès refusé (403) — WAF/Cloudflare bloque les navigateurs",
                429: "Trop de requêtes (429)",
                503: "Service indisponible (503)",
            }.get(status, f"HTTP {status}")
            LOGGER.warning("Blocked by WAF: %s returned %d", target_url, status)
            return BrowserFetchResponse(
                url=target_url,
                status_code=status,
                text="",
                blocked=True,
                blocked_reason=reason,
            )

        if status >= 400:
            LOGGER.warning("HTTP error: %s returned %d", target_url, status)
            return BrowserFetchResponse(
                url=target_url,
                status_code=status,
                text="",
                blocked=True,
                blocked_reason=f"HTTP {status}",
            )

        # Get the rendered HTML content (JavaScript already executed)
        content = page.content()
        LOGGER.info("✓ Fetched %s (%d)", target_url, status)

        return BrowserFetchResponse(
            url=page.url,
            status_code=status,
            text=content,
        )

    except PlaywrightTimeoutError as exc:
        LOGGER.warning("Timeout: %s didn't load in %.0fs (site too slow for browser mode)", target_url, timeout)
        return BrowserFetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Timeout {timeout:.0f}s — site trop lent en mode Playwright",
        )

    except Exception as exc:
        exc_type = type(exc).__name__
        exc_msg = str(exc)[:80]
        LOGGER.error("Error in Playwright: %s — %s", exc_type, exc_msg)
        return BrowserFetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Erreur Playwright: {exc_type}",
        )

    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

