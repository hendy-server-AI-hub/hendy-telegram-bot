from __future__ import annotations

from app.config import Settings


class SecurityService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def report(self) -> list[tuple[str, bool, str]]:
        return [
            ("Danh sách Telegram Admin", bool(self.settings.admin_ids), f"{len(self.settings.admin_ids)} tài khoản"),
            ("GitHub API token", bool(self.settings.github_token), "đã cấu hình" if self.settings.github_token else "chưa cấu hình"),
            ("Render API key", bool(self.settings.render_api_key), "đã cấu hình" if self.settings.render_api_key else "chưa cấu hình"),
            ("OpenAI API key", bool(self.settings.openai_api_key), "đã cấu hình" if self.settings.openai_api_key else "chưa cấu hình"),
            ("Server HTTPS targets", bool(self.settings.server_targets), f"{len(self.settings.server_targets)} endpoint"),
            ("HTTPS health check", True, "chỉ dùng URL khai báo trong environment"),
            ("Shell tùy ý", False, "đã tắt; bot không thực thi lệnh hệ điều hành"),
            ("GitHub destructive actions", False, "không cung cấp xóa repository / xóa branch"),
        ]
