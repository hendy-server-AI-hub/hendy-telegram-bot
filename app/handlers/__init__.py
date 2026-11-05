from aiogram import Router

from app.handlers.ai import router as ai_router
from app.handlers.github import router as github_router
from app.handlers.render import router as render_router
from app.handlers.security import router as security_router
from app.handlers.server import router as server_router
from app.handlers.start import router as start_router


def build_router() -> Router:
    router = Router(name="hendy-root")
    for child in (start_router, github_router, render_router, ai_router, server_router, security_router):
        router.include_router(child)
    return router
