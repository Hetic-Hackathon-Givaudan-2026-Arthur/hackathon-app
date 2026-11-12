from llm.llm1_analysis.adapter import LLM1Adapter
from llm.llm1_analysis.service import LLM1AnalysisService
from llm.llm2_visual.adapter import LLM2Adapter
from llm.llm2_visual.service import LLM2VisualService
from infrastructure.outbox import OutboxDelivery
from infrastructure.neon_events import NeonEventPublisher
from infrastructure.neon_queue import NeonTaskQueue
from infrastructure.neon_store import NeonStore
from application.orchestrator import Orchestrator
from application.visual_worker import VisualWorker
from domain.analysis.policies import BatchPolicy
from pipelines.visual.service import VisualPipelineService


def build_orchestrator(
    llm_client,
    ws_manager,
    neon_store: NeonStore,
) -> Orchestrator:
    """Assemble the text orchestrator with Neon-backed infrastructure."""
    llm1 = LLM1AnalysisService(LLM1Adapter(llm_client))
    task_queue = NeonTaskQueue(neon_store)
    delivery = OutboxDelivery(neon_store, ws_manager)
    policy = BatchPolicy()

    return Orchestrator(
        analysis_model=llm1,
        event_publisher=NeonEventPublisher(neon_store),
        task_queue=task_queue,
        result_delivery=delivery,
        batch_policy=policy,
    )


def build_visual_worker(
    llm_client,
    neon_store: NeonStore,
    delivery: OutboxDelivery,
    rag,
    image_search,
) -> VisualWorker:
    """Assemble the FIFO visual worker with Neon-backed task handling."""
    visual_model = LLM2VisualService(LLM2Adapter(llm_client))
    pipeline = VisualPipelineService(
        visual_model=visual_model,
        rag=rag,
        image_search=image_search,
        delivery=delivery,
        publisher=NeonEventPublisher(neon_store),
        task_queue=NeonTaskQueue(neon_store),
    )
    return VisualWorker(NeonTaskQueue(neon_store), pipeline)
