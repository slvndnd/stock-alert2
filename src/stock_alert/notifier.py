from __future__ import annotations

import json
import logging
import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from .models import ScanResult

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class EmailConfig:
    smtp_host: str
    smtp_port: int
    use_tls: bool
    smtp_user: str
    smtp_password: str
    from_address: str
    to_address: str


def load_previous_state(json_path: Path) -> dict[str, bool | None]:
    """Load in_stock status from the previous scan JSON, keyed by (product_id, site_id)."""
    if not json_path.exists():
        return {}
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return {
            f"{r['product_id']}::{r['site_id']}": r.get("in_stock")
            for r in data.get("results", [])
        }
    except Exception as exc:
        LOGGER.warning("Could not load previous state: %s", exc)
        return {}


def find_newly_in_stock(
    results: list[ScanResult],
    previous: dict[str, bool | None],
    only_on_restock: bool = True,
) -> list[ScanResult]:
    """Return results that are newly in stock (or all in-stock if only_on_restock=False)."""
    alerts = []
    for result in results:
        if result.in_stock is not True:
            continue
        key = f"{result.product_id}::{result.site_id}"
        was_in_stock = previous.get(key)
        if only_on_restock and was_in_stock is True:
            # Already known as in stock — skip to avoid repeat emails
            continue
        alerts.append(result)
    return alerts


def _build_email_text(alerts: list[ScanResult]) -> tuple[str, str]:
    """Build plain-text and HTML bodies for the alert email."""
    lines_text = [
        "🔔 Alerte stock — des produits sont disponibles !\n",
        "=" * 60,
    ]
    lines_html = [
        "<html><body>",
        "<h2>🔔 Alerte stock — des produits sont disponibles !</h2>",
        "<table border='1' cellpadding='8' cellspacing='0' "
        "style='border-collapse:collapse;font-family:sans-serif;'>",
        "<tr style='background:#f0f0f0;'>"
        "<th>Produit</th><th>Site</th><th>Prix</th><th>Lien</th>"
        "</tr>",
    ]

    for r in alerts:
        price_str = f"{r.price} {r.currency or ''}".strip() if r.price else "N/A"
        lines_text.extend([
            f"\n✅ Produit  : {r.product_name}",
            f"   Site    : {r.site_icon} {r.site_label}",
            f"   Prix    : {price_str}",
            f"   Lien    : {r.target_url}",
            "-" * 60,
        ])
        lines_html.append(
            f"<tr>"
            f"<td><strong>{r.product_name}</strong></td>"
            f"<td>{r.site_icon} {r.site_label}</td>"
            f"<td>{price_str}</td>"
            f"<td><a href='{r.target_url}'>Voir la fiche produit</a></td>"
            f"</tr>"
        )

    lines_html.extend(["</table>", "</body></html>"])
    return "\n".join(lines_text), "\n".join(lines_html)


def send_alert_email(cfg: EmailConfig, alerts: list[ScanResult]) -> None:
    if not alerts:
        LOGGER.info("No new in-stock alerts to send.")
        return

    subject = (
        f"[Stock Alert] {len(alerts)} produit(s) disponible(s) — "
        + ", ".join({r.product_name for r in alerts})
    )
    body_text, body_html = _build_email_text(alerts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.from_address
    msg["To"] = cfg.to_address
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    LOGGER.info("Sending alert email to %s (%d items)", cfg.to_address, len(alerts))
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as server:
        if cfg.use_tls:
            server.starttls()
        server.login(cfg.smtp_user, cfg.smtp_password)
        server.sendmail(cfg.from_address, [cfg.to_address], msg.as_string())
    LOGGER.info("Alert email sent successfully.")


def load_email_config_from_env() -> EmailConfig | None:
    """
    Load email config from environment variables.
    Returns None if required variables are missing (alerts disabled).

    Required env vars:
      SMTP_HOST       e.g. smtp.gmail.com
      SMTP_USER       e.g. moncompte@gmail.com
      SMTP_PASSWORD   App password or SMTP password
      ALERT_EMAIL_TO  Recipient address

    Optional env vars:
      SMTP_PORT       default: 587
      SMTP_USE_TLS    default: true
    """
    host = os.getenv("SMTP_HOST", "").strip() or None
    user = os.getenv("SMTP_USER", "").strip() or None
    password = os.getenv("SMTP_PASSWORD", "").strip() or None
    to_addr = os.getenv("ALERT_EMAIL_TO", "").strip() or None

    if not all([host, user, password, to_addr]):
        missing = [k for k, v in {
            "SMTP_HOST": host, "SMTP_USER": user,
            "SMTP_PASSWORD": password, "ALERT_EMAIL_TO": to_addr,
        }.items() if not v]
        LOGGER.info("Email alerts disabled — missing env vars: %s", ", ".join(missing))
        return None

    port_str = os.getenv("SMTP_PORT", "587").strip()
    port = int(port_str) if port_str else 587

    use_tls_str = os.getenv("SMTP_USE_TLS", "true").strip()
    use_tls = use_tls_str.lower() in ("1", "true", "yes") if use_tls_str else True

    return EmailConfig(
        smtp_host=host,
        smtp_port=port,
        use_tls=use_tls,
        smtp_user=user,
        smtp_password=password,
        from_address=user,
        to_address=to_addr,
    )

