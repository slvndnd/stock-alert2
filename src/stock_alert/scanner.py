from __future__ import annotations

import logging
from datetime import datetime, timezone

from .fetcher import fetch_page
from .models import ProductConfig, ScanResult, SiteConfig
from .parser import parse_product_page

LOGGER = logging.getLogger(__name__)


def _status_emoji(in_stock: bool | None) -> str:
    if in_stock is True:
        return "✅"
    if in_stock is False:
        return "❌"
    return "⚪"


def scan_targets(
    products: list[ProductConfig],
    sites: dict[str, SiteConfig],
    use_browser: bool = False,
) -> list[ScanResult]:
    """
    Scan products on target sites.

    Args:
        products: List of products to scan
        sites: Map of site configurations
        use_browser: If True, use Playwright headless browser. Otherwise use requests.

    Returns:
        List of scan results
    """
    if use_browser:
        from .browser_fetcher import fetch_with_browser
        fetch_fn = fetch_with_browser
    else:
        fetch_fn = fetch_page  # type: ignore

    now = datetime.now(tz=timezone.utc)
    results: list[ScanResult] = []

    for product in products:
        for target in product.targets:
            site = sites.get(target.site, SiteConfig(id=target.site, label=target.site, icon="🛒"))
            try:
                response = fetch_fn(target.url)

                if response.blocked:
                    results.append(
                        ScanResult(
                            scanned_at=now,
                            product_id=product.id,
                            product_name=product.display_name,
                            site_id=site.id,
                            site_label=site.label,
                            site_icon=site.icon,
                            target_url=target.url,
                            matched_name=None,
                            title=None,
                            price=None,
                            availability="Accès bloqué",
                            in_stock=None,
                            status_emoji="🚫",
                            currency=None,
                            notes=[response.blocked_reason],
                        )
                    )
                    continue

                parsed = parse_product_page(response.text, aliases=product.names)

                results.append(
                    ScanResult(
                        scanned_at=now,
                        product_id=product.id,
                        product_name=product.display_name,
                        site_id=site.id,
                        site_label=site.label,
                        site_icon=site.icon,
                        target_url=target.url,
                        matched_name=parsed.matched_name,
                        title=parsed.title,
                        price=parsed.price,
                        availability=parsed.availability_text,
                        in_stock=parsed.in_stock,
                        status_emoji=_status_emoji(parsed.in_stock),
                        currency=parsed.currency,
                        notes=parsed.notes,
                    )
                )
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Error scanning %s on %s", product.id, target.site)
                results.append(
                    ScanResult(
                        scanned_at=now,
                        product_id=product.id,
                        product_name=product.display_name,
                        site_id=site.id,
                        site_label=site.label,
                        site_icon=site.icon,
                        target_url=target.url,
                        matched_name=None,
                        title=None,
                        price=None,
                        availability=f"Erreur: {type(exc).__name__}",
                        in_stock=None,
                        status_emoji="⚠️",
                        currency=None,
                        notes=[str(exc)],
                    )
                )

    return results

