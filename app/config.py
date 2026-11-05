from __future__ import annotations

import ipaddress
from functools import cached_property
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed configuration. Secrets are never rendered in repr/log output."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: SecretStr
    telegram_admin_ids: str
    github_org: str = "hendy-server-AI-hub"
    github_token: SecretStr | None = None
    render_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-6-luna"
    server_health_urls: str = ""
    http_timeout_seconds: int = 20
    log_level: str = "INFO"
    ai_max_input_chars: int = 4000

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw.lower() in {"replace_me", "changeme"}:
            raise ValueError("BOT_TOKEN must contain a real BotFather token")
        return SecretStr(raw)

    @field_validator("telegram_admin_ids")
    @classmethod
    def validate_admin_ids(cls, value: str) -> str:
        ids: list[int] = []
        for raw in value.split(","):
            raw = raw.strip()
            if not raw:
                continue
            if not raw.isdigit() or int(raw) <= 0:
                raise ValueError("TELEGRAM_ADMIN_IDS must be comma-separated positive numeric IDs")
            ids.append(int(raw))
        if not ids:
            raise ValueError("At least one TELEGRAM_ADMIN_IDS entry is required")
        if len(ids) != len(set(ids)):
            raise ValueError("TELEGRAM_ADMIN_IDS must not contain duplicates")
        return value

    @field_validator("github_token", "render_api_key", "openai_api_key", mode="before")
    @classmethod
    def normalize_optional_secrets(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            raw = value.get_secret_value().strip()
        else:
            raw = str(value).strip()
        if not raw or raw.lower() in {"replace_me", "changeme", "your_token_here"}:
            return None
        return raw

    @field_validator("http_timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if not 3 <= value <= 60:
            raise ValueError("HTTP_TIMEOUT_SECONDS must be between 3 and 60")
        return value

    @field_validator("ai_max_input_chars")
    @classmethod
    def validate_ai_limit(cls, value: int) -> int:
        if not 100 <= value <= 12000:
            raise ValueError("AI_MAX_INPUT_CHARS must be between 100 and 12000")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL is invalid")
        return normalized

    @model_validator(mode="after")
    def validate_org(self) -> "Settings":
        if not self.github_org or not self.github_org.strip():
            raise ValueError("GITHUB_ORG cannot be empty")
        return self

    @cached_property
    def admin_ids(self) -> frozenset[int]:
        return frozenset(int(part.strip()) for part in self.telegram_admin_ids.split(",") if part.strip())

    @cached_property
    def server_targets(self) -> tuple[tuple[str, str], ...]:
        """Parse fixed, operator-supplied HTTPS health URLs; users cannot submit target URLs."""
        targets: list[tuple[str, str]] = []
        for item in self.server_health_urls.split(";"):
            item = item.strip()
            if not item:
                continue
            if "=" not in item:
                raise ValueError("SERVER_HEALTH_URLS entries must use name=https://host/health")
            name, url = (part.strip() for part in item.split("=", 1))
            parts = urlsplit(url)
            if not name or not parts.hostname or parts.scheme != "https":
                raise ValueError("Health check targets must have a name and an HTTPS URL")
            if parts.username or parts.password:
                raise ValueError("Credentials must not be embedded in health check URLs")
            host = parts.hostname.lower()
            if host in {"localhost", "localhost.localdomain"}:
                raise ValueError("Localhost health check targets are not allowed")
            try:
                ip = ipaddress.ip_address(host)
                if not ip.is_global:
                    raise ValueError("Private or reserved IP health check targets are not allowed")
            except ValueError as exc:
                if str(exc) == "Private or reserved IP health check targets are not allowed":
                    raise
            targets.append((name, url))
        return tuple(targets)


def load_settings() -> Settings:
    return Settings()
