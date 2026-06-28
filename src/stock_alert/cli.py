from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_sites, load_watchlist
from .render import write_html, write_json
from .scanner import scan_targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stock and price scanner")
    parser.add_argument("--sites", type=Path, default=Path("config/sites.yaml"))
    parser.add_argument("--watchlist", type=Path, default=Path("config/watchlist.yaml"))
    parser.add_argument("--json-out", type=Path, default=Path("data/latest.json"))
    parser.add_argument("--html-out", type=Path, default=Path("docs/index.html"))
    parser.add_argument("--template-dir", type=Path, default=Path("templates"))
    return parser


def main() -> int:
    args = build_parser().parse_args()

    sites = load_sites(args.sites)
    products = load_watchlist(args.watchlist)
    results = scan_targets(products, sites)

    write_json(results, args.json_out)
    write_html(results, args.template_dir, args.html_out)

    print(f"OK - {len(results)} checks generated")
    print(f"HTML dashboard: {args.html_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

