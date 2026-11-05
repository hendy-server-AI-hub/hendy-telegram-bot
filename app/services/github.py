from __future__ import annotations

import base64
import re
from typing import Any
from urllib.parse import quote

from app.config import Settings
from app.services.api import ApiClient

REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
WORKFLOW_RE = re.compile(r"^[A-Za-z0-9_./-]{1,180}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9_./-]{1,180}$")


def validate_repo_slug(value: str) -> str:
    value = value.strip()
    if not REPO_SLUG_RE.fullmatch(value) or value in {".", ".."} or ".." in value:
        raise ValueError("Tên repository không hợp lệ.")
    return value


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, client: ApiClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Hendy-Telegram-Bot/1.0",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token.get_secret_value()}"

    def _repo_path(self, repo: str) -> str:
        slug = validate_repo_slug(repo)
        return f"/repos/{quote(self.settings.github_org, safe='')}/{quote(slug, safe='')}"

    async def list_repositories(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        limit = min(max(limit, 1), 300)
        repos: list[dict[str, Any]] = []
        for page in range(1, 4):
            batch = await self.client.request(
                "GET",
                f"{self.BASE_URL}/orgs/{quote(self.settings.github_org, safe='')}/repos",
                headers=self.headers,
                params={"type": "all", "sort": "updated", "per_page": min(100, limit - len(repos)), "page": page},
            )
            if not isinstance(batch, list):
                raise RuntimeError("GitHub API trả về dữ liệu repository không hợp lệ.")
            repos.extend(batch)
            if len(batch) < 100 or len(repos) >= limit:
                break
        return repos[:limit]

    async def get_repository(self, repo: str) -> dict[str, Any]:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        return await self.client.request("GET", f"{self.BASE_URL}{self._repo_path(repo)}", headers=self.headers)

    async def read_file(self, repo: str, path: str, ref: str | None = None) -> str:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        path = path.strip().replace("\\", "/")
        segments = path.split("/")
        if not path or path.startswith("/") or len(path) > 300 or any(part in {"", ".", ".."} for part in segments):
            raise ValueError("Đường dẫn file không hợp lệ.")
        if ref and len(ref) > 150:
            raise ValueError("Git ref quá dài.")
        params = {"ref": ref} if ref else None
        data = await self.client.request(
            "GET",
            f"{self.BASE_URL}{self._repo_path(repo)}/contents/{quote(path, safe='/')}",
            headers=self.headers,
            params=params,
        )
        if not isinstance(data, dict) or data.get("type") != "file" or data.get("encoding") != "base64":
            raise ValueError("Đường dẫn không phải file văn bản được GitHub Contents API hỗ trợ.")
        if int(data.get("size", 0) or 0) > 100_000:
            raise ValueError("File vượt giới hạn đọc 100 KB của bot.")
        try:
            raw = base64.b64decode(data.get("content", ""), validate=False)
            return raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError("Không thể đọc file này dưới dạng văn bản UTF-8.") from exc

    async def list_workflows(self, repo: str) -> list[dict[str, Any]]:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        data = await self.client.request("GET", f"{self.BASE_URL}{self._repo_path(repo)}/actions/workflows", headers=self.headers)
        return data.get("workflows", []) if isinstance(data, dict) else []

    async def dispatch_workflow(self, repo: str, workflow: str, branch: str) -> None:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        if not WORKFLOW_RE.fullmatch(workflow) or ".." in workflow:
            raise ValueError("Workflow ID/tên file không hợp lệ.")
        if not BRANCH_RE.fullmatch(branch) or ".." in branch:
            raise ValueError("Tên branch không hợp lệ.")
        await self.client.request(
            "POST",
            f"{self.BASE_URL}{self._repo_path(repo)}/actions/workflows/{quote(workflow, safe='')}/dispatches",
            headers=self.headers,
            json_body={"ref": branch},
        )

    async def create_issue(self, repo: str, title: str, body: str) -> dict[str, Any]:
        if not self.settings.github_token:
            raise RuntimeError("Chưa cấu hình GITHUB_TOKEN.")
        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Tiêu đề issue phải từ 1 đến 200 ký tự.")
        return await self.client.request(
            "POST",
            f"{self.BASE_URL}{self._repo_path(repo)}/issues",
            headers=self.headers,
            json_body={"title": title, "body": body[:10000]},
        )
