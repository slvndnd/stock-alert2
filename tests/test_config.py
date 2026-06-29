from pathlib import Path

from stock_alert.config import load_sites


def test_load_sites_supports_fetch_mode(tmp_path: Path) -> None:
    config_file = tmp_path / "sites.yaml"
    config_file.write_text(
        """
sites:
  - id: boulanger
    label: Boulanger
    icon: "B"
    fetch_mode: requests
  - id: darty
    fetch_mode: scraperapi
""".strip(),
        encoding="utf-8",
    )

    sites = load_sites(config_file)

    assert sites["boulanger"].fetch_mode == "requests"
    assert sites["darty"].fetch_mode == "scraperapi"


def test_load_sites_defaults_fetch_mode_to_auto(tmp_path: Path) -> None:
    config_file = tmp_path / "sites.yaml"
    config_file.write_text(
        """
sites:
  - id: amazon
""".strip(),
        encoding="utf-8",
    )

    sites = load_sites(config_file)

    assert sites["amazon"].fetch_mode == "auto"

