import os
import httpx2 as httpx


class OllamaClient:
    """Client HTTP async vers l'API Ollama (/api/chat)."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self._base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or os.environ.get("LLM1_MODEL", "qwen2.5:1.5b")

    async def complete(self, messages: list[dict]) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "messages": messages,
            "options": {"temperature": 0.1},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["message"]["content"]
