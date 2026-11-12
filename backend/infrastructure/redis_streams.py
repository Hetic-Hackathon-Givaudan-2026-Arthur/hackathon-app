import json
import uuid
import redis.asyncio as redis
from application.ports.task_queue import TaskQueue
from domain.analysis.entities import VisualTask, AnalysisResult

STREAM_KEY = "visual_tasks"
GROUP_NAME = "visual_workers"
CONSUMER_NAME = "worker_1"


class RedisStreamsTaskQueue(TaskQueue):
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    async def enqueue(self, task: VisualTask) -> None:
        task.task_id = str(uuid.uuid4())
        payload = {
            "task_id": task.task_id,
            "analysis_id": task.analysis_id,
            "context": json.dumps({
                "analysis_id": task.context.analysis_id,
                "session_id": task.context.session_id,
                "idea": task.context.idea,
                "details": task.context.details,
            }),
        }
        await self._client.xadd(STREAM_KEY, payload)

    async def dequeue(self) -> VisualTask | None:
        try:
            await self._client.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
        except Exception:
            pass

        results = await self._client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=0
        )
        if not results:
            return None

        _, messages = results[0]
        msg_id, fields = messages[0]
        ctx = json.loads(fields[b"context"])
        context = AnalysisResult(
            analysis_id=ctx["analysis_id"],
            session_id=ctx["session_id"],
            idea=ctx["idea"],
            details=ctx["details"],
        )
        return VisualTask(
            analysis_id=fields[b"analysis_id"].decode(),
            context=context,
            task_id=fields[b"task_id"].decode(),
        )

    async def ack(self, task_id: str) -> None:
        await self._client.xack(STREAM_KEY, GROUP_NAME, task_id)
