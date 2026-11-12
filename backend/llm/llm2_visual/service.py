from application.ports.visual_model import VisualModel
from domain.analysis.entities import AnalysisResult, VisualQuery
from llm.llm2_visual.adapter import LLM2Adapter


class LLM2VisualService(VisualModel):
    def __init__(self, adapter: LLM2Adapter) -> None:
        self._adapter = adapter

    async def build_query(self, result: AnalysisResult) -> VisualQuery:
        output = await self._adapter.call(result.idea, result.details)
        return VisualQuery(analysis_id=result.analysis_id, query=output.query)
