from __future__ import annotations

import logging
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

LOGGER = logging.getLogger(__name__)

# Global browser instance
_BROWSER: Browser | None = None


def _get_browser() -> Browser:
    """Get or create the Playwright browser instance."""
    global _BROWSER
    if _BROWSER is None:
        playwright = sync_playwright().start()
        _BROWSER = playwright.chromium.launch(headless=True)
    return _BROWSER


def close_browser() -> None:
    """Close the browser."""
    global _BROWSER
    if _BROWSER:
        _BROWSER.close()
        _BROWSER = None


@dataclass(slots=True)
class BrowserFetchResponse:
    url: str
    status_code: int
    text: str
    blocked: bool = False
    blocked_reason: str = ""


def fetch_with_browser(target_url: str, timeout: float = 30.0) -> BrowserFetchResponse:
    """
    Fetch a page using Playwright headless browser.
    Contours WAF and Cloudflare by executing JavaScript.

    Returns:
        BrowserFetchResponse with the page content or error info.
    """
    browser = _get_browser()
    page: Page | None = None

    try:
        page = browser.new_page()

        # Set realistic user agent
        page.set_extra_http_headers({
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
        })

        LOGGER.info("Fetching %s with Playwright...", target_url)
        response = page.goto(target_url, wait_until="networkidle", timeout=timeout * 1000)

        if response is None:
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
                403: "Accès refusé (403 Forbidden)",
                429: "Trop de requêtes (429)",
                503: "Service indisponible (503)",
            }.get(status, f"HTTP {status}")
            LOGGER.warning("Blocked: %s returned %d", target_url, status)
            return BrowserFetchResponse(
                url=target_url,
                status_code=status,
                text="",
                blocked=True,
                blocked_reason=reason,
            )

        if status >= 400:
            LOGGER.warning("Error: %s returned %d", target_url, status)
            return BrowserFetchResponse(
                url=target_url,
                status_code=status,
                text="",
                blocked=True,
                blocked_reason=f"HTTP {status}",
            )

        # Get the rendered HTML content
        content = page.content()
        LOGGER.info("Fetched %s (%d)", target_url, status)

        return BrowserFetchResponse(
            url=page.url,
            status_code=status,
            text=content,
        )

    except PlaywrightTimeoutError:
        LOGGER.warning("Timeout fetching %s", target_url)
        return BrowserFetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Timeout après {timeout}s",
        )

    except Exception as exc:
        LOGGER.error("Error fetching %s with Playwright: %s", target_url, exc)
        return BrowserFetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Erreur: {type(exc).__name__}: {str(exc)[:50]}",
        )

    finally:
        if page:
            page.close()

