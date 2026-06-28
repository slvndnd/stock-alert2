from __future__ import annotations

from pathlib import Path

import yaml

from .models import ProductConfig, SiteConfig, TargetConfig


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_sites(path: Path) -> dict[str, SiteConfig]:
    raw = _read_yaml(path)
    sites = {}
    for site in raw.get("sites", []):
        item = SiteConfig(
            id=site["id"],
            label=site.get("label", site["id"]),
            icon=site.get("icon", "🛒"),
        )
        sites[item.id] = item
    return sites


def load_watchlist(path: Path) -> list[ProductConfig]:
    raw = _read_yaml(path)
    products: list[ProductConfig] = []
    for product in raw.get("products", []):
        targets = [
            TargetConfig(site=t["site"], url=t["url"])
            for t in product.get("targets", [])
        ]
        products.append(
            ProductConfig(
                id=product["id"],
                display_name=product.get("display_name", product["id"]),
                names=product.get("names", [product.get("display_name", product["id"])]),
                targets=targets,
            )
        )
    return products

