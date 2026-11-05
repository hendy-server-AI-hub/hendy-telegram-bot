import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.servers import ServerService

router = Router(name="server")


@router.message(Command("server_status"))
async def server_status(message: Message, server_service: ServerService) -> None:
    results = await server_service.check_all()
    if not results:
        await message.answer("Chưa cấu hình SERVER_HEALTH_URLS. Thêm các endpoint HTTPS trong Render Environment.")
        return
    lines = ["<b>SERVER HEALTH</b>"]
    for result in results:
        icon = "🟢" if result.healthy else "🔴"
        status = str(result.status) if result.status is not None else "timeout/error"
        lines.append(f"{icon} <b>{html.escape(result.name)}</b> — HTTP {status} ({html.escape(result.detail)})")
    await message.answer("\n".join(lines))
