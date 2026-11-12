from llm.llm2_visual.prompts import build_prompt
from llm.llm2_visual.schemas import VisualQueryOutput
import json


class LLM2Adapter:
    """Adapts a concrete LLM provider to the VisualModel port."""

    def __init__(self, client) -> None:
        self._client = client

    async def call(self, idea: str, details: list[str]) -> VisualQueryOutput:
        messages = build_prompt(idea, details)
        raw = await self._client.complete(messages)
        data = json.loads(raw)
        return VisualQueryOutput(**data)
