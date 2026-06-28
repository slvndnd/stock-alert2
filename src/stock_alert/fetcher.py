from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# Retry strategy with exponential backoff
RETRY_STRATEGY = Retry(
    total=3,  # Max 3 attempts
    backoff_factor=1.0,  # 1s, 2s, 4s delays
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these codes
    allowed_methods=["HEAD", "GET", "OPTIONS"],
)

# Sessions per domain to persist cookies
_SESSIONS: dict[str, requests.Session] = {}


def _get_session(url: str) -> requests.Session:
    """Get or create a persistent session for the domain."""
    parsed = urlparse(url)
    domain = parsed.netloc

    if domain not in _SESSIONS:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        # Mount retry adapter
        adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        _SESSIONS[domain] = session

    return _SESSIONS[domain]


@dataclass(slots=True)
class FetchResponse:
    url: str
    status_code: int
    text: str
    blocked: bool = False
    blocked_reason: str = ""


def fetch_page(url: str, timeout: float = 30.0) -> FetchResponse:
    """
    Fetch a page with anti-bot resistance:
    - Persistent sessions (cookies)
    - Exponential backoff retries
    - Random delays between requests
    - Realistic headers
    """
    # Random delay: 1.5-3.5s
    delay = random.uniform(1.5, 3.5)
    time.sleep(delay)

    session = _get_session(url)

    # Add Referer header for this request
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    headers = {"Referer": origin}

    try:
        response = session.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers,
        )
    except requests.Timeout as exc:
        LOGGER.warning("Timeout fetching %s (timeout=%s)", url, timeout)
        return FetchResponse(
            url=url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Timeout after {timeout}s — site trop lent",
        )
    except requests.RequestException as exc:
        LOGGER.warning("Error fetching %s: %s", url, exc)
        return FetchResponse(
            url=url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Erreur réseau: {type(exc).__name__}",
        )

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

    if response.status_code >= 400:
        reason = f"HTTP {response.status_code} {response.reason}"
        LOGGER.warning("Error fetching %s: %s", url, reason)
        return FetchResponse(
            url=response.url,
            status_code=response.status_code,
            text="",
            blocked=True,
            blocked_reason=reason,
        )

    LOGGER.info("Fetched %s (%s)", url, response.status_code)
    return FetchResponse(url=response.url, status_code=response.status_code, text=response.text)

