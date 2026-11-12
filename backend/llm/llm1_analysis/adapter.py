from llm.llm1_analysis.prompts import build_prompt
from llm.llm1_analysis.schemas import AnalysisOutput
import json


class LLM1Adapter:
    """Adapts a concrete LLM provider to the AnalysisModel port."""

    def __init__(self, client) -> None:
        self._client = client

    async def call(self, batch_text: str) -> AnalysisOutput:
        messages = build_prompt(batch_text)
        raw = await self._client.complete(messages)
        data = json.loads(raw)
        return AnalysisOutput(**data)
