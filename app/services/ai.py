from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.api import ApiClient


def extract_response_text(payload: dict[str, Any]) -> str:
    """Extract text from the Responses API output array without assuming item order."""
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str) and text:
                    chunks.append(text)
    return "\n".join(chunks).strip()


class AIService:
    BASE_URL = "https://api.openai.com/v1/responses"

    def __init__(self, client: ApiClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def ask(self, prompt: str) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("Chưa cấu hình OPENAI_API_KEY.")
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Hãy nhập nội dung sau lệnh /ask.")
        if len(prompt) > self.settings.ai_max_input_chars:
            raise ValueError(f"Nội dung quá dài; giới hạn {self.settings.ai_max_input_chars} ký tự.")
        payload = await self.client.request(
            "POST",
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key.get_secret_value()}",
                "Content-Type": "application/json",
            },
            json_body={"model": self.settings.openai_model, "input": prompt, "store": False},
        )
        answer = extract_response_text(payload if isinstance(payload, dict) else {})
        if not answer:
            raise RuntimeError("AI không trả về nội dung văn bản.")
        return answer
