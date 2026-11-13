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


def test_brevo_is_preferred_and_names_the_missing_sender(prod_env):
    prod_env.setenv("BREVO_API_KEY", "key")
    prod_env.setenv("SMTP_HOST", "smtp.example.com")
    prod_env.setenv("SENDER_EMAIL", "")
    prod_env.setenv("SMTP_FROM_EMAIL", "")
    prod_env.setenv("BREVO_SENDER_EMAIL", "")
    get_settings.cache_clear()
    assert get_settings().email_transport == "brevo"
    warning = next(w for w in validate_for_startup(get_settings()) if "email" in w)
    assert "BREVO_SENDER_EMAIL" in warning and "BREVO_API_KEY" not in warning.split("missing:")[1]
    prod_env.setenv("BREVO_SENDER_EMAIL", "support@example.com")
    prod_env.setenv("BREVO_SENDER_NAME", "Quickfix AI")
    get_settings.cache_clear()
    assert get_settings().email_configured and get_settings().smtp_from_name == "Quickfix AI"


def test_app_url_fallback_helper():
    assert config._origins_from_app_url("https://www.a.com/x") == ["https://www.a.com", "https://a.com"]
    assert config._origins_from_app_url("http://localhost:5173") == ["http://localhost:5173"]
    assert config._origins_from_app_url("") == []


def test_inline_comments_from_pasted_templates_are_ignored(prod_env):
    prod_env.setenv("FRONTEND_URL", "https://riteshkr.online,https://www.riteshkr.online   # REQUIRED in production")
    prod_env.setenv("EMAIL_TRANSPORT", "brevo  # brevo | smtp | console")
    get_settings.cache_clear()
    assert get_settings().frontend_urls == ["https://riteshkr.online", "https://www.riteshkr.online"]
    assert get_settings().email_transport == "brevo"


def test_origins_are_normalized(prod_env):
    prod_env.setenv("FRONTEND_URL", "riteshkr.online, https://WWW.riteshkr.online/app/, https://*.bad.com, ftp://x.com")
    get_settings.cache_clear()
    assert get_settings().frontend_urls == ["https://riteshkr.online", "https://www.riteshkr.online"]


def test_cors_preflight_allows_configured_origin_only(client):
    ok = client.options("/auth/google", headers={"Origin": "http://testserver-frontend",
                                                 "Access-Control-Request-Method": "POST",
                                                 "Access-Control-Request-Headers": "content-type"})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "http://testserver-frontend"
    bad = client.options("/auth/google", headers={"Origin": "https://evil.example",
                                                  "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_production_defaults_to_live_site_when_nothing_is_set(prod_env):
    prod_env.setenv("FRONTEND_URL", "")
    prod_env.setenv("APP_URL", "")
    get_settings.cache_clear()
    assert get_settings().frontend_urls == ["https://riteshkr.online", "https://www.riteshkr.online"]
