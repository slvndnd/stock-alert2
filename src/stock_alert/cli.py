from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import load_sites, load_watchlist
from .notifier import (
    find_newly_in_stock,
    load_email_config_from_env,
    load_previous_state,
    send_alert_email,
)
from .render import write_html, write_json
from .scanner import scan_targets
from .scraperapi_fetcher import load_scraperapi_config_from_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stock and price scanner")
    parser.add_argument("--sites", type=Path, default=Path("config/sites.yaml"))
    parser.add_argument("--watchlist", type=Path, default=Path("config/watchlist.yaml"))
    parser.add_argument("--json-out", type=Path, default=Path("data/latest.json"))
    parser.add_argument("--html-out", type=Path, default=Path("docs/index.html"))
    parser.add_argument("--template-dir", type=Path, default=Path("templates"))
    parser.add_argument(
        "--always-alert",
        action="store_true",
        help="Send email for every in-stock product, not just new ones",
    )
    parser.add_argument(
        "--use-browser",
        action="store_true",
        help="Use Playwright fallback for blocked targets (slower, but can bypass some WAF)",
    )
    parser.add_argument(
        "--use-scraperapi",
        action="store_true",
        help="Use ScraperAPI fallback for blocked targets (requires SCRAPERAPI_KEY)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    sites = load_sites(args.sites)
    products = load_watchlist(args.watchlist)

    # Load previous state BEFORE overwriting the JSON
    previous_state = load_previous_state(args.json_out)

    if args.use_browser:
        print("📱 Mode hybride activé — HTTP d'abord, Playwright en fallback sur les blocages")
    else:
        print("⚡ Mode requests (HTTP classique) — plus rapide")

    scraperapi_cfg = load_scraperapi_config_from_env()
    if args.use_scraperapi:
        if scraperapi_cfg:
            print("🌐 Fallback ScraperAPI activé pour les sites bloqués")
        else:
            LOGGER.warning("--use-scraperapi ignoré: SCRAPERAPI_KEY absent")

    try:
        results = scan_targets(
            products,
            sites,
            use_browser=args.use_browser,
            use_scraperapi=args.use_scraperapi,
            scraperapi_config=scraperapi_cfg,
        )
    except KeyboardInterrupt:
        print("\n⏹️  Scan interrompu par l'utilisateur")
        return 130
    finally:
        # Clean up browser if used
        if args.use_browser:
            from .browser_fetcher import close_browser
            close_browser()

    write_json(results, args.json_out)
    write_html(results, args.template_dir, args.html_out)

    print(f"✓ OK - {len(results)} checks générés")
    print(f"📊 Dashboard HTML: {args.html_out}")

    # ── Email notifications ───────────────────────────────────────────────────
    email_cfg = load_email_config_from_env()
    if email_cfg:
        alerts = find_newly_in_stock(
            results,
            previous_state,
            only_on_restock=not args.always_alert,
        )
        if alerts:
            LOGGER.info("%d new in-stock item(s) — sending alert email...", len(alerts))
        send_alert_email(email_cfg, alerts)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

