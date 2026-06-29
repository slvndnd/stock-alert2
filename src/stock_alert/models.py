from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TargetConfig:
    site: str
    url: str


@dataclass(slots=True)
class ProductConfig:
    id: str
    display_name: str
    names: list[str]
    targets: list[TargetConfig]


@dataclass(slots=True)
class SiteConfig:
    id: str
    label: str
    icon: str
    fetch_mode: str = "auto"


@dataclass(slots=True)
class ScanResult:
    scanned_at: datetime
    product_id: str
    product_name: str
    site_id: str
    site_label: str
    site_icon: str
    target_url: str
    matched_name: str | None
    title: str | None
    price: str | None
    availability: str
    in_stock: bool | None
    status_emoji: str
    currency: str | None
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "scanned_at": self.scanned_at.isoformat(),
            "product_id": self.product_id,
            "product_name": self.product_name,
            "site_id": self.site_id,
            "site_label": self.site_label,
            "site_icon": self.site_icon,
            "target_url": self.target_url,
            "matched_name": self.matched_name,
            "title": self.title,
            "price": self.price,
            "availability": self.availability,
            "in_stock": self.in_stock,
            "status_emoji": self.status_emoji,
            "currency": self.currency,
            "notes": self.notes,
        }

