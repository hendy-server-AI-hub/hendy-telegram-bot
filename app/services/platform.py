from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import aiohttp


class PlatformAPIError(RuntimeError):
    """Sanitized error returned by the Hendy PHP platform bridge."""


class HendyPlatformClient:
    """Read-only client for the PHP platform's restricted bot API."""

    RESOURCES = frozenset({"status", "jobs", "orders", "metrics"})

    def __init__(self, base_url: str, token: str, timeout_seconds: float = 12.0) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("HENDY_PLATFORM_API_URL must be an HTTPS origin or base URL")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    @classmethod
    def from_env(cls) -> "HendyPlatformClient | None":
        base_url = os.getenv("HENDY_PLATFORM_API_URL", "").strip()
        token = os.getenv("HENDY_PLATFORM_API_TOKEN", "").strip()
        if not base_url or not token:
            return None
        return cls(base_url=base_url, token=token)

    async def get(self, resource: str) -> dict[str, Any]:
        if resource not in self.RESOURCES:
            raise ValueError("Unsupported platform resource")
        url = f"{self.base_url}/api/integrations/telegram/v1/{resource}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "HendyTelegramBot/1.0",
        }
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=False) as response:
                    if response.status in (401, 403):
                        raise PlatformAPIError("Platform bridge rejected the bot credential")
                    if response.status == 404:
                        raise PlatformAPIError("Platform bridge endpoint is not installed")
                    if response.status >= 500:
                        raise PlatformAPIError("Platform service is temporarily unavailable")
                    if response.status >= 400:
                        raise PlatformAPIError(f"Platform request failed (HTTP {response.status})")
                    payload = await response.json(content_type=None)
                    if not isinstance(payload, dict):
                        raise PlatformAPIError("Platform returned an invalid response")
                    return payload
        except (aiohttp.ClientError, TimeoutError) as exc:
            raise PlatformAPIError("Could not reach the Hendy platform") from exc
