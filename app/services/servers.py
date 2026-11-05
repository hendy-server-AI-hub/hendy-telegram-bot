from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp

from app.config import Settings


@dataclass(frozen=True)
class HealthResult:
    name: str
    healthy: bool
    status: int | None
    detail: str


class ServerService:
    """Checks only operator-configured HTTPS endpoints; no user-provided URL or shell execution."""

    def __init__(self, settings: Settings) -> None:
        self.targets = settings.server_targets

    async def _check_one(self, session: aiohttp.ClientSession, name: str, url: str) -> HealthResult:
        timeout = aiohttp.ClientTimeout(total=8, connect=3)
        try:
            async with session.get(url, timeout=timeout, allow_redirects=False) as response:
                good = 200 <= response.status < 300
                return HealthResult(name, good, response.status, "OK" if good else "HTTP không thành công")
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            return HealthResult(name, False, None, type(exc).__name__)

    async def check_all(self) -> list[HealthResult]:
        if not self.targets:
            return []
        connector = aiohttp.TCPConnector(limit=10, ssl=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            return list(await asyncio.gather(*(self._check_one(session, name, url) for name, url in self.targets)))
