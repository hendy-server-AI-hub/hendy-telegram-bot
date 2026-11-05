from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.security import SecurityService

router = Router(name="security")


@router.message(Command("security"))
async def security_report(message: Message, security_service: SecurityService) -> None:
    report = security_service.report()
    lines = ["<b>HENDY SECURITY CONFIGURATION</b>"]
    for name, enabled, detail in report:
        icon = "🟢" if enabled else "⚪"
        lines.append(f"{icon} <b>{name}</b>: {detail}")
    lines.append("\nSecrets được che trong log; thao tác API chạy bằng token environment.")
    await message.answer("\n".join(lines))
