from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass(slots=True)
class FetchResponse:
    url: str
    status_code: int
    text: str


def fetch_page(url: str, timeout: float = 20.0) -> FetchResponse:
    response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    LOGGER.info("Fetched %s (%s)", url, response.status_code)
    return FetchResponse(url=response.url, status_code=response.status_code, text=response.text)

