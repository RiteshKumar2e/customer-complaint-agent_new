"""Production startup validation: secrets are fatal, non-secret config degrades safely."""
import pytest

from app.core import config
from app.core.config import ConfigError, get_settings, validate_for_startup

PROD = {
    "ENVIRONMENT": "production",
    "TURSO_DATABASE_URL": "libsql://db-org.turso.io",
    "TURSO_AUTH_TOKEN": "token",
    "JWT_SECRET_KEY": "x" * 40,
    "EMAIL_TRANSPORT": "",
    "SMTP_HOST": "",
    "BREVO_API_KEY": "",
    "FRONTEND_URL": "",
    "APP_URL": "https://riteshkr.online",
}


@pytest.fixture
def prod_env(monkeypatch):
    for key, value in PROD.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def test_missing_email_and_frontend_url_warn_but_start(prod_env):
    warnings = validate_for_startup(get_settings())
    assert any("email delivery is not configured" in w for w in warnings)
    assert any("FRONTEND_URL is not set" in w for w in warnings)
    assert get_settings().frontend_urls == ["https://riteshkr.online", "https://www.riteshkr.online"]


@pytest.mark.parametrize("missing", ["JWT_SECRET_KEY", "TURSO_AUTH_TOKEN", "TURSO_DATABASE_URL"])
def test_missing_secrets_still_refuse_to_start(prod_env, missing):
    prod_env.setenv(missing, "")
    get_settings.cache_clear()
    with pytest.raises(ConfigError):
        validate_for_startup(get_settings())


def test_short_jwt_secret_refused(prod_env):
    prod_env.setenv("JWT_SECRET_KEY", "short")
    get_settings.cache_clear()
    with pytest.raises(ConfigError):
        validate_for_startup(get_settings())


def test_explicit_frontend_url_wins(prod_env):
    prod_env.setenv("FRONTEND_URL", "https://app.example.com, https://example.com/")
    get_settings.cache_clear()
    assert get_settings().frontend_urls == ["https://app.example.com", "https://example.com"]


def test_brevo_with_legacy_sender_email_counts_as_configured(prod_env):
    prod_env.setenv("BREVO_API_KEY", "key")
    prod_env.setenv("SENDER_EMAIL", "support@example.com")
    get_settings.cache_clear()
    assert get_settings().email_transport == "brevo" and get_settings().email_configured
    assert not any("email" in w.lower() for w in validate_for_startup(get_settings()))


def test_app_url_fallback_helper():
    assert config._origins_from_app_url("https://www.a.com/x") == ["https://www.a.com", "https://a.com"]
    assert config._origins_from_app_url("http://localhost:5173") == ["http://localhost:5173"]
    assert config._origins_from_app_url("") == []
