from __future__ import annotations

import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.utils import send_lines
from app.services.api import ApiError
from app.services.github import GitHubService

router = Router(name="github")

@router.message(Command("gh_repos"))
async def list_repositories(message: Message, github_service: GitHubService) -> None:
    try:
        repos = await github_service.list_repositories(100)
        if not repos:
            await message.answer("GitHub không trả về repository nào. Kiểm tra quyền truy cập token.")
            return
        lines = ["<b>HENDY-SERVER-AI-HUB / REPOSITORIES</b>"]
        for repo in repos:
            visibility = "private" if repo.get("private") else "public"
            lines.append(f"• <code>{html.escape(str(repo.get('name', 'unknown')))}</code> · {visibility} · ⭐ {repo.get('stargazers_count', 0)}")
        lines.append(f"\nĐã nhận {len(repos)} repository (tối đa 100).")
        await send_lines(message, lines)
    except (ApiError, RuntimeError) as exc:
        await message.answer(f"Không thể lấy repository: {html.escape(str(exc))}")


@router.message(Command("gh_repo"))
async def get_repository(message: Message, github_service: GitHubService) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Cách dùng: <code>/gh_repo ten-repo</code>")
        return
    try:
        repo = await github_service.get_repository(parts[1])
        full_name = html.escape(str(repo.get("full_name", "unknown")))
        desc = html.escape(str(repo.get("description") or "Không có mô tả"))
        await message.answer(
            f"<b>{full_name}</b>\n{desc}\n"
            f"Visibility: {'private' if repo.get('private') else 'public'}\n"
            f"Language: {html.escape(str(repo.get('language') or 'N/A'))}\n"
            f"Default branch: <code>{html.escape(str(repo.get('default_branch') or 'N/A'))}</code>\n"
            f"Stars: {repo.get('stargazers_count', 0)} · Forks: {repo.get('forks_count', 0)}\n"
            f"URL: {html.escape(str(repo.get('html_url', '')))}"
        )
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể đọc repository: {html.escape(str(exc))}")


@router.message(Command("gh_file"))
async def read_repository_file(message: Message, github_service: GitHubService) -> None:
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) < 3:
        await message.answer("Cách dùng: <code>/gh_file ten-repo path/to/file [branch]</code>")
        return
    repo, path = parts[1], parts[2]
    ref = parts[3] if len(parts) == 4 else None
    try:
        content = await github_service.read_file(repo, path, ref)
        displayed = content[:3300]
        suffix = "\n\n[Đã cắt bớt nội dung để vừa giới hạn Telegram.]" if len(content) > 3300 else ""
        await message.answer(
            f"File: {repo}/{path}\n{displayed}{suffix}",
            parse_mode=None,
        )
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể đọc file: {html.escape(str(exc))}")


@router.message(Command("gh_workflows"))
async def list_workflows(message: Message, github_service: GitHubService) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Cách dùng: <code>/gh_workflows ten-repo</code>")
        return
    try:
        workflows = await github_service.list_workflows(parts[1])
        if not workflows:
            await message.answer("Không tìm thấy workflow hoặc token thiếu Actions: read.")
            return
        lines = ["<b>GITHUB ACTIONS WORKFLOWS</b>"]
        for wf in workflows[:30]:
            lines.append(f"• <code>{html.escape(str(wf.get('id', '')))}</code> · {html.escape(str(wf.get('name', 'workflow')))} · {html.escape(str(wf.get('state', 'unknown')))}")
        await send_lines(message, lines)
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể lấy workflow: {html.escape(str(exc))}")


@router.message(Command("gh_dispatch"))
async def dispatch_workflow(message: Message, github_service: GitHubService) -> None:
    parts = (message.text or "").split()
    if len(parts) != 4:
        await message.answer("Cách dùng: <code>/gh_dispatch ten-repo workflow.yml main</code>")
        return
    _, repo, workflow, branch = parts
    try:
        await github_service.dispatch_workflow(repo, workflow, branch)
        await message.answer("✅ Đã gửi yêu cầu GitHub Actions dispatch. Kiểm tra tab Actions của repository.")
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể chạy workflow: {html.escape(str(exc))}")


@router.message(Command("gh_issue"))
async def create_issue(message: Message, github_service: GitHubService) -> None:
    raw = (message.text or "").partition(" ")[2]
    parts = [part.strip() for part in raw.split("|", maxsplit=2)]
    if len(parts) != 3:
        await message.answer("Cách dùng: <code>/gh_issue ten-repo | tiêu đề | nội dung</code>")
        return
    try:
        issue = await github_service.create_issue(parts[0], parts[1], parts[2])
        await message.answer(f"✅ Đã tạo issue #{issue.get('number')}: {html.escape(str(issue.get('html_url', '')))}")
    except (ApiError, RuntimeError, ValueError) as exc:
        await message.answer(f"Không thể tạo issue: {html.escape(str(exc))}")
