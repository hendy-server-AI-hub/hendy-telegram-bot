from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import load_settings
from app.handlers import build_router
from app.middlewares.admin import AdminOnlyMiddleware, RateLimitMiddleware
from app.services.ai import AIService
from app.services.api import ApiClient
from app.services.github import GitHubService
from app.services.render import RenderService
from app.services.security import SecurityService
from app.services.servers import ServerService

logger = logging.getLogger(__name__)


from app.handlers.platform import router as platform_router
def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # HTTP library debug logs can contain request metadata; keep them quiet by default.
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)


async def run() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)

    timeout = aiohttp.ClientTimeout(total=settings.http_timeout_seconds, connect=5)
    connector = aiohttp.TCPConnector(limit=30, ssl=True, ttl_dns_cache=300)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector, trust_env=False) as session:
        api_client = ApiClient(session, settings.http_timeout_seconds)
        bot = Bot(
            token=settings.bot_token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dispatcher = Dispatcher()
        dispatcher.message.outer_middleware(AdminOnlyMiddleware(settings))
        dispatcher.callback_query.outer_middleware(AdminOnlyMiddleware(settings))
        dispatcher.message.middleware(RateLimitMiddleware())
        dispatcher.callback_query.middleware(RateLimitMiddleware())
        dispatcher.include_router(build_router())

        dispatcher.include_router(platform_router)
        # Dispatcher workflow data is injected into handler arguments by aiogram.
        # Every service shares one bounded aiohttp session for the process lifetime.
        dispatcher["github_service"] = GitHubService(api_client, settings)
        dispatcher["render_service"] = RenderService(api_client, settings)
        dispatcher["ai_service"] = AIService(api_client, settings)
        dispatcher["server_service"] = ServerService(settings)
        dispatcher["security_service"] = SecurityService(settings)

        try:
            # Long polling and webhooks are mutually exclusive in Telegram.
            # Delete any old webhook but preserve queued updates.
            await bot.delete_webhook(drop_pending_updates=False)
            me = await bot.get_me()
            logger.info("bot_start username=%s admins=%d", me.username, len(settings.admin_ids))
            await dispatcher.start_polling(
                bot,
                allowed_updates=dispatcher.resolve_used_update_types(),
                close_bot_session=False,
                handle_signals=True,
            )
        finally:
            logger.info("bot_shutdown")
            with suppress(Exception):
                await bot.session.close()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("shutdown_requested")


if __name__ == "__main__":
    main()
