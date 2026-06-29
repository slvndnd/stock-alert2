from __future__ import annotations

import logging
from datetime import datetime, timezone

from .fetcher import fetch_page
from .fetcher import FetchResponse
from .models import ProductConfig, ScanResult, SiteConfig
from .parser import parse_product_page
from .scraperapi_fetcher import ScraperApiConfig

LOGGER = logging.getLogger(__name__)

VALID_FETCH_MODES = {"auto", "requests", "browser", "scraperapi"}


def _status_emoji(in_stock: bool | None) -> str:
    if in_stock is True:
        return "✅"
    if in_stock is False:
        return "❌"
    return "⚪"


def _build_strategy_order(
    fetch_mode: str,
    use_browser: bool,
    use_scraperapi: bool,
    has_scraperapi: bool,
) -> list[str]:
    mode = (fetch_mode or "auto").strip().lower()
    if mode not in VALID_FETCH_MODES:
        LOGGER.warning("Unknown fetch_mode '%s', falling back to auto", fetch_mode)
        mode = "auto"

    if mode == "requests":
        return ["requests"]
    if mode == "browser":
        return ["browser", "requests"]
    if mode == "scraperapi":
        return ["scraperapi", "requests"] if has_scraperapi else ["requests"]

    order = ["requests"]
    if use_scraperapi and has_scraperapi:
        order.append("scraperapi")
    if use_browser:
        order.append("browser")
    return order


def scan_targets(
    products: list[ProductConfig],
    sites: dict[str, SiteConfig],
    use_browser: bool = False,
    use_scraperapi: bool = False,
    scraperapi_config: ScraperApiConfig | None = None,
) -> list[ScanResult]:
    """
    Scan products on target sites.

    Args:
        products: List of products to scan
        sites: Map of site configurations
        use_browser: If True, use Playwright fallback on blocked targets.
        use_scraperapi: If True, retry blocked targets via ScraperAPI.
        scraperapi_config: ScraperAPI config loaded from env.

    Returns:
        List of scan results
    """
    scraper_fetch_fn = None
    if scraperapi_config:
        from .scraperapi_fetcher import fetch_with_scraperapi

        scraper_fetch_fn = fetch_with_scraperapi

    browser_fetch_fn = None

    now = datetime.now(tz=timezone.utc)
    results: list[ScanResult] = []

    for product in products:
        for target in product.targets:
            site = sites.get(target.site, SiteConfig(id=target.site, label=target.site, icon="🛒"))
            try:
                strategy_order = _build_strategy_order(
                    fetch_mode=site.fetch_mode,
                    use_browser=use_browser,
                    use_scraperapi=use_scraperapi,
                    has_scraperapi=scraperapi_config is not None,
                )

                response: FetchResponse | None = None
                for strategy in strategy_order:
                    candidate: FetchResponse | None = None
                    if strategy == "requests":
                        candidate = fetch_page(target.url)
                    elif strategy == "scraperapi" and scraper_fetch_fn and scraperapi_config:
                        candidate = scraper_fetch_fn(target.url, scraperapi_config)
                    elif strategy == "browser":
                        if browser_fetch_fn is None:
                            from .browser_fetcher import fetch_with_browser

                            browser_fetch_fn = fetch_with_browser
                        candidate = browser_fetch_fn(target.url)

                    if candidate is None:
                        continue

                    response = candidate
                    if not candidate.blocked:
                        if strategy != "requests":
                            LOGGER.info("Recovered %s with %s strategy", target.url, strategy)
                        break

                if response is None:
                    response = fetch_page(target.url)

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

