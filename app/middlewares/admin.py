from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.config import Settings

logger = logging.getLogger(__name__)


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.admin_ids = settings.admin_ids

    async def __call__(self, handler: Any, event: Any, data: dict[str, Any]) -> Any:
        user = data.get("event_from_user")
        if not user or user.id not in self.admin_ids:
            if user:
                logger.warning("unauthorized_telegram_user user_id=%s", user.id)
            if isinstance(event, Message):
                await event.answer("⛔ Tài khoản Telegram này không có quyền quản trị bot.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Không có quyền quản trị.", show_alert=True)
            return None
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Per-user command throttle. Keep memory bounded and avoid logging message contents."""

    def __init__(self, max_events: int = 8, window_seconds: int = 10) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self.events: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(self, handler: Any, event: Any, data: dict[str, Any]) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        now = time.monotonic()
        bucket = self.events[user.id]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_events:
            if isinstance(event, Message):
                await event.answer("Bạn thao tác quá nhanh. Vui lòng thử lại sau vài giây.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Thao tác quá nhanh.", show_alert=False)
            return None
        bucket.append(now)
        return await handler(event, data)
