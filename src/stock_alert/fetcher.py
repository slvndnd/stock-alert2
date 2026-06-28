from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)

# Realistic browser headers — reduces bot-detection 403s
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}

# HTTP status codes that indicate anti-bot blocking (not real errors)
BLOCKED_CODES = {403, 429, 503}

# Delay between requests to avoid rate limiting (seconds)
REQUEST_DELAY = 1.5


@dataclass(slots=True)
class FetchResponse:
    url: str
    status_code: int
    text: str
    blocked: bool = False
    blocked_reason: str = ""


def fetch_page(url: str, timeout: float = 20.0) -> FetchResponse:
    time.sleep(REQUEST_DELAY)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    # First request: let the site set cookies (helps bypass some protections)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        session.get(origin, timeout=timeout, allow_redirects=True)
    except Exception:
        pass  # Ignore errors on the pre-visit

    response = session.get(url, timeout=timeout, allow_redirects=True)

    if response.status_code in BLOCKED_CODES:
        reason = {
            403: "Accès refusé (403 Forbidden) — site protégé anti-bot",
            429: "Trop de requêtes (429 Too Many Requests) — réessayer plus tard",
            503: "Service indisponible (503) — site protégé ou en maintenance",
        }.get(response.status_code, f"HTTP {response.status_code}")
        LOGGER.warning("Blocked fetching %s: %s", url, reason)
        return FetchResponse(
            url=response.url,
            status_code=response.status_code,
            text="",
            blocked=True,
            blocked_reason=reason,
        )

    response.raise_for_status()
    LOGGER.info("Fetched %s (%s)", url, response.status_code)
    return FetchResponse(url=response.url, status_code=response.status_code, text=response.text)

