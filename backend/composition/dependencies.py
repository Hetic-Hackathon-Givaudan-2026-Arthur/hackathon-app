import os

import redis.asyncio as redis
from infrastructure.ollama_client import OllamaClient
from llm.llm1_analysis.adapter import LLM1Adapter
from llm.llm1_analysis.service import LLM1AnalysisService
from llm.llm2_visual.adapter import LLM2Adapter
from llm.llm2_visual.service import LLM2VisualService
from infrastructure.redis_streams import RedisStreamsTaskQueue
from infrastructure.outbox import OutboxDelivery
from infrastructure.processing_log import ProcessingLog
from application.orchestrator import Orchestrator
from domain.analysis.policies import BatchPolicy


def build_orchestrator(ws_manager, outbox_store, redis_url: str) -> Orchestrator:
    redis_client = redis.from_url(redis_url)
    llm_client = OllamaClient(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.environ.get("LLM1_MODEL", "qwen2.5:1.5b"),
    )

    llm1 = LLM1AnalysisService(LLM1Adapter(llm_client))
    llm2 = LLM2VisualService(LLM2Adapter(llm_client))
    task_queue = RedisStreamsTaskQueue(redis_client)
    delivery = OutboxDelivery(outbox_store, ws_manager)
    policy = BatchPolicy()

    return Orchestrator(
        analysis_model=llm1,
        event_publisher=_noop_publisher(),
        task_queue=task_queue,
        result_delivery=delivery,
        batch_policy=policy,
    )


class _noop_publisher:
    async def publish(self, event) -> None:
        pass
