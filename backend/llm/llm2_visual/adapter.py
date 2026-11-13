from llm.llm2_visual.prompts import build_prompt
from llm.llm2_visual.schemas import VisualQueryOutput
import json
from typing import Protocol


class LLM2Client(Protocol):
    """Define the direct completion contract expected from the LLM provider."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError


class LLM2Adapter:
    """Adapts a concrete LLM provider to the VisualModel port."""

    def __init__(self, client: LLM2Client) -> None:
        self._client = client

    async def call(self, idea: str, details: list[str]) -> VisualQueryOutput:
        messages = build_prompt(idea, details)
        raw = await self._client.complete(messages)
        data = json.loads(raw)
        return VisualQueryOutput(**data)
