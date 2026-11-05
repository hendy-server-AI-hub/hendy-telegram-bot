from __future__ import annotations

import html
import logging
import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.platform import HendyPlatformClient, PlatformAPIError

router = Router(name="platform")
logger = logging.getLogger(__name__)


def _admin_ids() -> set[int]:
    raw = os.getenv("TELEGRAM_ADMIN_IDS", "")
    result: set[int] = set()
    for value in raw.split(","):
        value = value.strip()
        if value.isdigit():
            result.add(int(value))
    return result


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in _admin_ids())


def _display(payload: dict, title: str) -> str:
    # Keep Telegram messages bounded and render remote values as plain text.
    import json

    body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    body = body[:3200]
    return f"<b>{html.escape(title)}</b>\n<pre>{html.escape(body)}</pre>"


async def _read_platform(message: Message, resource: str, title: str) -> None:
    if not _is_admin(message):
        await message.answer("Bạn không có quyền sử dụng lệnh quản trị này.")
        return
    client = HendyPlatformClient.from_env()
    if client is None:
        await message.answer(
            "Chưa cấu hình kết nối nền tảng PHP. Hãy đặt HENDY_PLATFORM_API_URL "
            "và HENDY_PLATFORM_API_TOKEN trong Render Environment."
        )
        return
    try:
        payload = await client.get(resource)
    except PlatformAPIError as exc:
        logger.warning("Hendy platform read failed: %s", exc)
        await message.answer(f"Không thể đọc dữ liệu nền tảng: {html.escape(str(exc))}")
        return
    await message.answer(_display(payload, title), parse_mode="HTML")


@router.message(Command("platform"))
async def platform_status(message: Message) -> None:
    await _read_platform(message, "status", "HENDY PLATFORM STATUS")


@router.message(Command("platform_jobs"))
async def platform_jobs(message: Message) -> None:
    await _read_platform(message, "jobs", "HENDY PLATFORM JOBS")


@router.message(Command("platform_orders"))
async def platform_orders(message: Message) -> None:
    await _read_platform(message, "orders", "HENDY PLATFORM ORDERS")


@router.message(Command("platform_metrics"))
async def platform_metrics(message: Message) -> None:
    await _read_platform(message, "metrics", "HENDY PLATFORM METRICS")
