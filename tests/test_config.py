import pytest
from pydantic import ValidationError

from app.config import Settings


def build_settings(**overrides):
    values = {
        "bot_token": "123456:abcdefghijk",
        "telegram_admin_ids": "12345,67890",
        "github_org": "hendy-server-AI-hub",
    }
    values.update(overrides)
    return Settings(**values)


def test_admin_ids_are_parsed():
    settings = build_settings()
    assert settings.admin_ids == frozenset({12345, 67890})


def test_admin_ids_must_be_numeric():
    with pytest.raises(ValidationError):
        build_settings(telegram_admin_ids="admin")


def test_https_server_target_is_parsed():
    settings = build_settings(server_health_urls="studio=https://studio.example.com/health")
    assert settings.server_targets == (("studio", "https://studio.example.com/health"),)


def test_http_server_target_is_rejected():
    settings = build_settings(server_health_urls="studio=http://studio.example.com/health")
    with pytest.raises(ValueError):
        _ = settings.server_targets


def test_private_server_target_is_rejected():
    settings = build_settings(server_health_urls="private=https://127.0.0.1/health")
    with pytest.raises(ValueError):
        _ = settings.server_targets


def test_optional_secret_placeholders_are_ignored():
    settings = build_settings(github_token="replace_me", render_api_key="", openai_api_key=None)
    assert settings.github_token is None
    assert settings.render_api_key is None
    assert settings.openai_api_key is None
