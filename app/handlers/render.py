from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.handlers.utils import send_lines
from app.services.api import ApiError
from app.services.render import RenderService

router = Router(name="render")


@router.message(Command("render_services"))
async def list_services(message: Message, render_service: RenderService) -> None:
    try:
        services = await render_service.list_services()
        if not services:
            await message.answer("Render chưa trả về service nào trong workspace được cấp quyền.")
            return
        lines = ["<b>RENDER SERVICES</b>"]
        for service in services[:40]:
            lines.append(
                f"• <b>{html.escape(str(service.get('name', 'unknown')))}</b>\n"
                f"  <code>{html.escape(str(service.get('id', '')))}</code> · "
                f"{html.escape(str(service.get('type', 'unknown')))} · "
                f"{html.escape(str(service.get('suspended', 'status n/a')))}"
            )
        await send_lines(message, lines)
    except (ApiError, RuntimeError) as exc:
        await message.answer(f"Không thể lấy Render services: {html.escape(str(exc))}")


@router.message(Command("render_service"))
async def get_service(message: Message, render_service: RenderService) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Cách dùng: <code>/render_service SERVICE_ID</code>")
        return
    try:
        service_id = parts[1].strip()
        service = await render_service.get_service(service_id)
        deploys = await render_service.list_deploys(service_id)
        lines = [
            f"<b>{html.escape(str(service.get('name', 'Render service')))}</b>",
            f"ID: <code>{html.escape(str(service.get('id', service_id)))}</code>",
            f"Type: {html.escape(str(service.get('type', 'N/A')))}",
            f"Branch: {html.escape(str(service.get('branch', 'N/A')))}",
            f"Suspended: {html.escape(str(service.get('suspended', 'N/A')))}",
            f"Dashboard: {html.escape(str(service.get('dashboardUrl', '')))}",
            "<b>Deploy gần đây:</b>",
        ]
        for item in deploys[:5]:
            deploy = item.get("deploy", item) if isinstance(item, dict) else {}
            lines.append(f"• {html.escape(str(deploy.get('status', 'unknown')))} · {html.escape(str(deploy.get('id', '')))}")
        await send_lines(message, lines)
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể lấy thông tin Render: {html.escape(str(exc))}")


@router.message(Command("render_deploy"))
async def request_deploy(message: Message, render_service: RenderService) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Cách dùng: <code>/render_deploy SERVICE_ID</code>")
        return
    service_id = parts[1].strip()
    # Validate and display the target before asking for a second, explicit confirmation.
    try:
        service = await render_service.get_service(service_id)
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể xác thực service: {html.escape(str(exc))}")
        return
    token = render_service.create_deploy_confirmation(service_id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Xác nhận deploy", callback_data=f"render:deploy:{token}"),
        InlineKeyboardButton(text="Huỷ", callback_data="render:cancel"),
    ]])
    await message.answer(
        "<b>XÁC NHẬN TRIỂN KHAI</b>\n"
        f"Service: {html.escape(str(service.get('name', service_id)))}\n"
        f"ID: <code>{html.escape(service_id)}</code>\n"
        "Hành động này tạo deploy mới trên Render.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "render:cancel")
async def cancel_deploy(callback: CallbackQuery) -> None:
    await callback.answer("Đã huỷ.")
    if callback.message:
        await callback.message.edit_text("Đã huỷ yêu cầu deploy.")


@router.callback_query(F.data.startswith("render:deploy:"))
async def confirm_deploy(callback: CallbackQuery, render_service: RenderService) -> None:
    token = (callback.data or "").split(":", maxsplit=2)[-1]
    service_id = render_service.consume_deploy_confirmation(token)
    if service_id is None:
        await callback.answer("Xác nhận đã hết hạn hoặc đã được sử dụng.", show_alert=True)
        return
    try:
        result = await render_service.trigger_deploy(service_id)
        deploy_id = result.get("id", "đã gửi") if isinstance(result, dict) else "đã gửi"
        await callback.answer("Đã gửi lệnh deploy.")
        if callback.message:
            await callback.message.edit_text(
                f"✅ Đã gửi yêu cầu deploy\nService: <code>{html.escape(service_id)}</code>\n"
                f"Deploy ID: <code>{html.escape(str(deploy_id))}</code>"
            )
    except (ApiError, RuntimeError, ValueError) as exc:
        await callback.answer("Deploy thất bại.", show_alert=True)
        if callback.message:
            await callback.message.edit_text(f"Không thể deploy: {html.escape(str(exc))}")
