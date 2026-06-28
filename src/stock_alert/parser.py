from __future__ import annotations

import json
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

PRICE_RE = re.compile(r"(\d{1,4}[\s.,]\d{2})\s?(€|EUR|\$|USD)", re.IGNORECASE)

STOCK_PATTERNS = {
    "in_stock": ["en stock", "disponible", "livraison", "in stock", "add to cart"],
    "out_of_stock": ["rupture", "indisponible", "out of stock", "épuisé"],
}


@dataclass(slots=True)
class ParsedPage:
    title: str | None
    price: str | None
    currency: str | None
    availability_text: str
    in_stock: bool | None
    matched_name: str | None
    notes: list[str]


def parse_product_page(html: str, aliases: list[str]) -> ParsedPage:
    soup = BeautifulSoup(html, "html.parser")
    notes: list[str] = []

    title = _extract_title(soup)
    price, currency = _extract_price(soup, html)
    availability_text, in_stock = _extract_availability(soup, html)
    matched_name = _find_matched_alias(title or "", aliases)

    if matched_name is None and aliases:
        notes.append("Aucun alias de produit detecte dans le titre")
    if price is None:
        notes.append("Prix non detecte automatiquement")
    if in_stock is None:
        notes.append("Disponibilite non determinee automatiquement")

    return ParsedPage(
        title=title,
        price=price,
        currency=currency,
        availability_text=availability_text,
        in_stock=in_stock,
        matched_name=matched_name,
        notes=notes,
    )


def _extract_title(soup: BeautifulSoup) -> str | None:
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    return None


def _extract_price(soup: BeautifulSoup, raw_html: str) -> tuple[str | None, str | None]:
    # First try schema.org payload, then fallback to textual regex.
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = (script.string or "").strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue

        offers = _find_offers(payload)
        if not offers:
            continue

        price = str(offers.get("price") or "").strip() or None
        currency = str(offers.get("priceCurrency") or "").strip() or None
        if price:
            return price, currency

    match = PRICE_RE.search(raw_html.replace("\xa0", " "))
    if match:
        raw_price, raw_currency = match.groups()
        return raw_price.replace(" ", "").replace(",", "."), raw_currency.upper()
    return None, None


def _find_offers(payload: object) -> dict | None:
    if isinstance(payload, dict):
        if "offers" in payload and isinstance(payload["offers"], dict):
            return payload["offers"]
        for value in payload.values():
            found = _find_offers(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_offers(item)
            if found:
                return found
    return None


def _extract_availability(soup: BeautifulSoup, raw_html: str) -> tuple[str, bool | None]:
    text = " ".join(soup.get_text(" ", strip=True).lower().split())
    html_lower = raw_html.lower()

    for pattern in STOCK_PATTERNS["out_of_stock"]:
        if pattern in text or pattern in html_lower:
            return "Rupture / indisponible", False

    for pattern in STOCK_PATTERNS["in_stock"]:
        if pattern in text or pattern in html_lower:
            return "En stock", True

    return "Inconnu", None


def _find_matched_alias(title: str, aliases: list[str]) -> str | None:
    normalized_title = title.lower()
    for alias in aliases:
        if alias.lower() in normalized_title:
            return alias
    return None

