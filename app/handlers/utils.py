from __future__ import annotations

from aiogram.types import Message


async def send_lines(message: Message, lines: list[str], limit: int = 3800) -> None:
    """Send HTML-safe preformatted lines without exceeding Telegram's message limit."""
    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    for chunk in chunks:
        await message.answer(chunk)
