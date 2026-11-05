from __future__ import annotations

import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.ai import AIService
from app.services.api import ApiError

router = Router(name="ai")


@router.message(Command("ask"))
async def ask_ai(message: Message, ai_service: AIService) -> None:
    prompt = (message.text or "").partition(" ")[2].strip()
    if not prompt:
        await message.answer("Cách dùng: <code>/ask nội dung cần AI hỗ trợ</code>")
        return
    try:
        answer = await ai_service.ask(prompt)
        # Plain text parse mode prevents model output from being interpreted as Telegram HTML.
        await message.answer(answer[:3900], parse_mode=None)
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"AI chưa xử lý được yêu cầu: {html.escape(str(exc))}")
