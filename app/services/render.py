from __future__ import annotations

import re
import secrets
import time
from typing import Any
from urllib.parse import quote

from app.config import Settings
from app.services.api import ApiClient


class RenderService:
    BASE_URL = "https://api.render.com/v1"

    def __init__(self, client: ApiClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self._confirmations: dict[str, tuple[str, float]] = {}
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if settings.render_api_key:
            self.headers["Authorization"] = f"Bearer {settings.render_api_key.get_secret_value()}"

    def _require_key(self) -> None:
        if not self.settings.render_api_key:
            raise RuntimeError("Chưa cấu hình RENDER_API_KEY.")

    async def list_services(self) -> list[dict[str, Any]]:
        self._require_key()
        data = await self.client.request("GET", f"{self.BASE_URL}/services", headers=self.headers, params={"limit": 100})
        services: list[dict[str, Any]] = []
        for item in data if isinstance(data, list) else []:
            services.append(item.get("service", item) if isinstance(item, dict) else {})
        return services

    @staticmethod
    def _validate_service_id(service_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", service_id or ""):
            raise ValueError("Render service ID không hợp lệ.")
        return service_id

    def create_deploy_confirmation(self, service_id: str) -> str:
        self._validate_service_id(service_id)
        now = time.monotonic()
        self._confirmations = {key: value for key, value in self._confirmations.items() if value[1] > now}
        token = secrets.token_urlsafe(8)
        self._confirmations[token] = (service_id, now + 300)
        return token

    def consume_deploy_confirmation(self, token: str) -> str | None:
        item = self._confirmations.pop(token, None)
        if item is None or item[1] <= time.monotonic():
            return None
        return item[0]

    async def get_service(self, service_id: str) -> dict[str, Any]:
        self._require_key()
        self._validate_service_id(service_id)
        data = await self.client.request("GET", f"{self.BASE_URL}/services/{quote(service_id, safe='')}", headers=self.headers)
        return data.get("service", data) if isinstance(data, dict) else {}

    async def list_deploys(self, service_id: str) -> list[dict[str, Any]]:
        self._require_key()
        self._validate_service_id(service_id)
        data = await self.client.request(
            "GET", f"{self.BASE_URL}/services/{quote(service_id, safe='')}/deploys",
            headers=self.headers, params={"limit": 5},
        )
        return data if isinstance(data, list) else []

    async def trigger_deploy(self, service_id: str, clear_cache: bool = False) -> dict[str, Any]:
        self._require_key()
        self._validate_service_id(service_id)
        return await self.client.request(
            "POST",
            f"{self.BASE_URL}/services/{quote(service_id, safe='')}/deploys",
            headers=self.headers,
            json_body={"clearCache": "clear" if clear_cache else "do_not_clear", "deployMode": "build_and_deploy"},
        )
