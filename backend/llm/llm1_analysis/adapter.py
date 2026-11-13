import json
import re

from llm.llm1_analysis.prompts import build_prompt
from llm.llm1_analysis.schemas import AnalysisOutput


class LLM1Adapter:
    """Adapts a concrete LLM provider to the AnalysisModel port."""

    def __init__(self, client) -> None:
        self._client = client

    async def call(self, batch_text: str) -> AnalysisOutput:
        messages = build_prompt(batch_text)
        raw = await self._client.complete(messages)
        data = _parse_json(raw)
        return AnalysisOutput(**data)


def _parse_json(raw: str) -> dict:
    """Extrait le JSON d'une réponse LLM, même si elle contient du texte parasite."""
    # Nettoyage des blocs ```json ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # Tentative directe
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extraction du premier objet JSON trouvé dans le texte
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Réponse LLM non parseable en JSON : {raw[:200]!r}")
