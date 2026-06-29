from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import requests

from .fetcher import BLOCKED_CODES, FetchResponse

LOGGER = logging.getLogger(__name__)
SCRAPERAPI_ENDPOINT = "https://api.scraperapi.com/"


@dataclass(slots=True)
class ScraperApiConfig:
    api_key: str
    country_code: str = "fr"
    render: bool = False


def load_scraperapi_config_from_env() -> ScraperApiConfig | None:
    api_key = os.getenv("SCRAPERAPI_KEY", "").strip()
    if not api_key:
        return None

    country_code = os.getenv("SCRAPERAPI_COUNTRY_CODE", "fr").strip() or "fr"
    render = os.getenv("SCRAPERAPI_RENDER", "false").strip().lower() in {"1", "true", "yes", "on"}

    return ScraperApiConfig(
        api_key=api_key,
        country_code=country_code,
        render=render,
    )


def fetch_with_scraperapi(
    target_url: str,
    config: ScraperApiConfig,
    timeout: float = 45.0,
) -> FetchResponse:
    params = {
        "api_key": config.api_key,
        "url": target_url,
        "keep_headers": "true",
        "country_code": config.country_code,
        "render": "true" if config.render else "false",
    }

    try:
        response = requests.get(
            SCRAPERAPI_ENDPOINT,
            params=params,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.Timeout:
        LOGGER.warning("ScraperAPI timeout for %s", target_url)
        return FetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"ScraperAPI timeout after {timeout}s",
        )
    except requests.RequestException as exc:
        LOGGER.warning("ScraperAPI request failed for %s: %s", target_url, exc)
        return FetchResponse(
            url=target_url,
            status_code=0,
            text="",
            blocked=True,
            blocked_reason=f"Erreur ScraperAPI: {type(exc).__name__}",
        )

    if response.status_code in BLOCKED_CODES:
        return FetchResponse(
            url=target_url,
            status_code=response.status_code,
            text="",
            blocked=True,
            blocked_reason=f"ScraperAPI HTTP {response.status_code}",
        )

    if response.status_code >= 400:
        return FetchResponse(
            url=target_url,
            status_code=response.status_code,
            text="",
            blocked=True,
            blocked_reason=f"ScraperAPI HTTP {response.status_code} {response.reason}",
        )

    LOGGER.info("Fetched %s via ScraperAPI (%d)", target_url, response.status_code)
    return FetchResponse(
        url=target_url,
        status_code=response.status_code,
        text=response.text,
    )

