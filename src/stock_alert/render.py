from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import ScanResult


def write_json(results: list[ScanResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "results": [item.to_dict() for item in results],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_html(results: list[ScanResult], template_dir: Path, out_path: Path) -> None:
    grouped: dict[str, list[ScanResult]] = defaultdict(list)
    for result in results:
        grouped[result.product_name].append(result)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html.j2")

    html = template.render(
        generated_at=datetime.now(tz=timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        grouped_results=dict(sorted(grouped.items())),
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

