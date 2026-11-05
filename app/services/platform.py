from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any
from urllib.parse import urlsplit

import aiohttp

logger = logging.getLogger(__name__)


class PlatformAPIError(RuntimeError):
    """Sanitized error returned by the Hendy PHP platform bridge."""


class HendyPlatformClient:
    """Read-only client for the PHP platform's four allowlisted resources."""

    RESOURCES = frozenset({"status", "jobs", "orders", "metrics"})
    MAX_RESPONSE_BYTES = 128 * 1024

    def __init__(self, base_url: str, token: str, timeout_seconds: float = 12.0) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("HENDY_PLATFORM_API_URL must be a clean HTTPS base URL")
        try:
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("HENDY_PLATFORM_API_URL contains an invalid port") from exc
        if len(base_url) > 2048 or len(token) < 32:
            raise ValueError("Platform URL or shared token is invalid")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=5)

    @classmethod
    def from_env(cls) -> HendyPlatformClient | None:
        base_url = os.getenv("HENDY_PLATFORM_API_URL", "").strip()
        token = os.getenv("HENDY_PLATFORM_API_TOKEN", "").strip()
        if not base_url or not token:
            return None
        try:
            return cls(base_url=base_url, token=token)
        except ValueError:
            logger.error("platform_bridge_configuration_invalid")
            return None

    async def get(self, resource: str) -> dict[str, Any]:
        if resource not in self.RESOURCES:
            raise ValueError("Unsupported platform resource")
        url = f"{self.base_url}/api/integrations/telegram/v1/{resource}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": "HendyTelegramBot/1.1",
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, trust_env=False) as session:
                async with session.get(url, headers=headers, allow_redirects=False) as response:
                    if response.status in (401, 403):
                        raise PlatformAPIError("Platform bridge rejected the bot credential")
                    if response.status == 404:
                        raise PlatformAPIError("Platform bridge endpoint is not installed")
                    if response.status >= 500:
                        raise PlatformAPIError("Platform service is temporarily unavailable")
                    if response.status >= 300:
                        raise PlatformAPIError(f"Platform request failed (HTTP {response.status})")
                    raw = await response.content.read(self.MAX_RESPONSE_BYTES + 1)
                    if len(raw) > self.MAX_RESPONSE_BYTES:
                        raise PlatformAPIError("Platform response exceeded the size limit")
                    try:
                        payload = json.loads(raw.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise PlatformAPIError("Platform returned an invalid response") from exc
                    if not isinstance(payload, dict) or payload.get("ok") is False:
                        raise PlatformAPIError("Platform returned an invalid response")
                    return payload
        except PlatformAPIError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise PlatformAPIError("Could not reach the Hendy platform") from exc
