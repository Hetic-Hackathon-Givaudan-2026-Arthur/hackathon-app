from application.ports.analysis_model import AnalysisModel
from domain.analysis.entities import Batch, AnalysisResult
from llm.llm1_analysis.adapter import LLM1Adapter


class LLM1AnalysisService(AnalysisModel):
    def __init__(self, adapter: LLM1Adapter) -> None:
        self._adapter = adapter

    async def analyze(self, batch: Batch) -> AnalysisResult:
        combined = " ".join(s.text for s in batch.segments)
        output = await self._adapter.call(combined)
        return AnalysisResult(
            analysis_id="",
            session_id=batch.session_id,
            idea=output.idea,
            details=output.details,
        )
