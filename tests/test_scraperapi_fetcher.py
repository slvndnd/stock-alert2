import os
from unittest.mock import patch

from stock_alert.scraperapi_fetcher import load_scraperapi_config_from_env


def test_load_scraperapi_config_from_env_returns_none_without_key() -> None:
    with patch.dict(os.environ, {"SCRAPERAPI_KEY": ""}, clear=True):
        assert load_scraperapi_config_from_env() is None


def test_load_scraperapi_config_from_env_parses_values() -> None:
    with patch.dict(
        os.environ,
        {
            "SCRAPERAPI_KEY": "abc123",
            "SCRAPERAPI_COUNTRY_CODE": "de",
            "SCRAPERAPI_RENDER": "true",
        },
        clear=True,
    ):
        config = load_scraperapi_config_from_env()

    assert config is not None
    assert config.api_key == "abc123"
    assert config.country_code == "de"
    assert config.render is True

