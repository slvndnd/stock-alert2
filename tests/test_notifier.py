from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import os

from stock_alert.models import ScanResult
from stock_alert.notifier import find_newly_in_stock, send_alert_email, EmailConfig, load_email_config_from_env


def _make_result(product_id: str, site_id: str, in_stock: bool | None) -> ScanResult:
    return ScanResult(
        scanned_at=datetime.now(tz=timezone.utc),
        product_id=product_id,
        product_name=f"Product {product_id}",
        site_id=site_id,
        site_label=f"Site {site_id}",
        site_icon="🛒",
        target_url="https://example.com",
        matched_name=None,
        title="Test product",
        price="199.99",
        availability="En stock" if in_stock else "Rupture",
        in_stock=in_stock,
        status_emoji="✅" if in_stock else "❌",
        currency="EUR",
        notes=[],
    )


class TestFindNewlyInStock:
    def test_returns_only_new_in_stock_when_flag_true(self):
        results = [
            _make_result("ps5", "amazon", True),   # new
            _make_result("ps5", "darty", True),    # already known
            _make_result("ps5", "boulanger", False),
        ]
        previous = {"ps5::darty": True}
        alerts = find_newly_in_stock(results, previous, only_on_restock=True)
        assert len(alerts) == 1
        assert alerts[0].site_id == "amazon"

    def test_returns_all_in_stock_when_flag_false(self):
        results = [
            _make_result("ps5", "amazon", True),
            _make_result("ps5", "darty", True),
        ]
        previous = {"ps5::darty": True}
        alerts = find_newly_in_stock(results, previous, only_on_restock=False)
        assert len(alerts) == 2

    def test_no_alerts_when_nothing_in_stock(self):
        results = [
            _make_result("ps5", "amazon", False),
            _make_result("ps5", "darty", None),
        ]
        alerts = find_newly_in_stock(results, {}, only_on_restock=True)
        assert alerts == []


class TestSendAlertEmail:
    def test_does_not_connect_when_no_alerts(self):
        cfg = EmailConfig(
            smtp_host="smtp.example.com", smtp_port=587, use_tls=True,
            smtp_user="u", smtp_password="p",
            from_address="u@example.com", to_address="dest@example.com",
        )
        with patch("smtplib.SMTP") as mock_smtp:
            send_alert_email(cfg, [])
            mock_smtp.assert_not_called()

    def test_sends_email_when_alerts(self):
        cfg = EmailConfig(
            smtp_host="smtp.example.com", smtp_port=587, use_tls=True,
            smtp_user="u", smtp_password="p",
            from_address="u@example.com", to_address="dest@example.com",
        )
        alerts = [_make_result("ps5", "amazon", True)]
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server) as mock_smtp_cls:
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
            send_alert_email(cfg, alerts)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("u", "p")
            mock_server.sendmail.assert_called_once()


class TestLoadEmailConfigFromEnv:
    def test_returns_none_when_env_vars_empty(self):
        """GitHub Actions injects empty strings for undefined secrets."""
        with patch.dict(os.environ, {
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "ALERT_EMAIL_TO": "",
        }, clear=True):
            cfg = load_email_config_from_env()
            assert cfg is None

    def test_parses_valid_env_vars(self):
        """Test parsing with all required vars set."""
        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASSWORD": "pass123",
            "ALERT_EMAIL_TO": "alert@example.com",
            "SMTP_USE_TLS": "true",
        }, clear=True):
            cfg = load_email_config_from_env()
            assert cfg is not None
            assert cfg.smtp_host == "smtp.gmail.com"
            assert cfg.smtp_port == 587
            assert cfg.smtp_user == "test@gmail.com"
            assert cfg.use_tls is True

    def test_uses_defaults_for_optional_vars(self):
        """Test default values for SMTP_PORT and SMTP_USE_TLS."""
        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_USER": "test@gmail.com",
            "SMTP_PASSWORD": "pass123",
            "ALERT_EMAIL_TO": "alert@example.com",
        }, clear=True):
            cfg = load_email_config_from_env()
            assert cfg is not None
            assert cfg.smtp_port == 587
            assert cfg.use_tls is True


