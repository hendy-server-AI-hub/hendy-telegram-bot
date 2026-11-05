from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class ApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class ApiClient:
    """Small shared-session HTTP client with bounded timeouts and sanitized failures."""

    def __init__(self, session: aiohttp.ClientSession, timeout_seconds: int = 20) -> None:
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=5, sock_read=timeout_seconds)

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> Any:
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout or self.timeout,
                allow_redirects=False,
            ) as response:
                raw = await response.text()
                try:
                    payload: Any = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    payload = {"message": "Non-JSON response"}

                if response.status >= 400:
                    logger.warning("external_api_error status=%s method=%s host=%s", response.status, method, response.url.host)
                    raise ApiError(response.status, self._safe_error(response.status))
                return payload
        except ApiError:
            raise
        except (asyncio.TimeoutError, aiohttp.ServerTimeoutError) as exc:
            raise ApiError(0, "Dịch vụ bên ngoài phản hồi quá thời gian.") from exc
        except aiohttp.ClientError as exc:
            logger.warning("external_api_connection_error method=%s error_type=%s", method, type(exc).__name__)
            raise ApiError(0, "Không thể kết nối dịch vụ bên ngoài.") from exc

    @staticmethod
    def _safe_error(status: int) -> str:
        return {
            401: "API key/token không hợp lệ.",
            403: "Token thiếu quyền hoặc đã chạm giới hạn API.",
            404: "Không tìm thấy tài nguyên hoặc tài khoản không có quyền xem.",
            409: "Tài nguyên đang ở trạng thái không cho phép thao tác.",
            422: "Dữ liệu gửi lên không hợp lệ.",
            429: "Đã vượt giới hạn API; hãy thử lại sau.",
        }.get(status, f"Dịch vụ bên ngoài trả về lỗi HTTP {status}.")
