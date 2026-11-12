import asyncio
import json
from typing import Any
from uuid import uuid4

import psycopg

from domain.analysis.entities import AnalysisResult, VisualTask


class NeonStore:
    """Persist outbox entries and processing events in Neon PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._connection: psycopg.AsyncConnection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Open the Neon connection and create the backend persistence tables."""
        self._connection = await psycopg.AsyncConnection.connect(self._database_url)
        async with self._connection.cursor() as cursor:
            await cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox_events (
                    id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    sent BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE TABLE IF NOT EXISTS processing_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    occurred_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS visual_tasks (
                    task_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL UNIQUE,
                    context JSONB NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    locked_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        await self._connection.commit()

    async def close(self) -> None:
        """Close the Neon connection when the application stops."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def save(self, entry: dict[str, Any]) -> None:
        """Store an outbox entry before attempting client delivery."""
        async with self._lock:
            connection = self._require_connection()
            entry.setdefault("id", str(uuid4()))
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO outbox_events (id, payload) VALUES (%s, %s)",
                    (entry["id"], json.dumps(entry, default=str)),
                )
            await connection.commit()

    async def mark_sent(self, entry: dict[str, Any]) -> None:
        """Mark a previously persisted outbox entry as delivered."""
        async with self._lock:
            connection = self._require_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "UPDATE outbox_events SET sent = TRUE WHERE id = %s",
                    (entry["id"],),
                )
            await connection.commit()

    async def append(self, entry: dict[str, Any]) -> None:
        """Append a processing event without updating previous records."""
        async with self._lock:
            connection = self._require_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO processing_events (event_type, payload, occurred_at)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        entry["event_type"],
                        json.dumps(entry["payload"], default=str),
                        entry["occurred_at"],
                    ),
                )
            await connection.commit()

    async def enqueue_task(self, task: VisualTask) -> None:
        """Persist a visual task once so retries cannot create duplicates."""
        async with self._lock:
            connection = self._require_connection()
            task.task_id = task.task_id or str(uuid4())
            context = {
                "analysis_id": task.context.analysis_id,
                "session_id": task.context.session_id,
                "idea": task.context.idea,
                "details": task.context.details,
            }
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO visual_tasks (task_id, analysis_id, context)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (analysis_id) DO NOTHING
                    """,
                    (task.task_id, task.analysis_id, json.dumps(context)),
                )
            await connection.commit()

    async def dequeue_task(self) -> VisualTask | None:
        """Claim the oldest pending Neon task in FIFO order."""
        async with self._lock:
            connection = self._require_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    WITH next_task AS (
                        SELECT task_id
                        FROM visual_tasks
                        WHERE status = 'pending'
                        ORDER BY created_at, task_id
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE visual_tasks AS task
                    SET status = 'in_progress',
                        attempts = task.attempts + 1,
                        locked_at = now()
                    FROM next_task
                    WHERE task.task_id = next_task.task_id
                    RETURNING task.task_id, task.analysis_id, task.context
                    """
                )
                row = await cursor.fetchone()
            await connection.commit()
        if row is None:
            return None
        task_id, analysis_id, context = row
        return VisualTask(
            task_id=task_id,
            analysis_id=analysis_id,
            context=AnalysisResult(**context),
        )

    async def ack_task(self, task_id: str) -> None:
        """Remove a visual task only after durable processing completes."""
        async with self._lock:
            connection = self._require_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM visual_tasks WHERE task_id = %s",
                    (task_id,),
                )
            await connection.commit()

    async def retry_expired_tasks(self, timeout_seconds: int = 300) -> None:
        """Return abandoned tasks to the pending state for bounded retries."""
        async with self._lock:
            connection = self._require_connection()
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    UPDATE visual_tasks
                    SET status = 'pending', locked_at = NULL
                    WHERE status = 'in_progress'
                      AND locked_at < now() - make_interval(secs => %s)
                    """,
                    (timeout_seconds,),
                )
            await connection.commit()

    def _require_connection(self) -> psycopg.AsyncConnection:
        """Return the active connection or fail explicitly when not started."""
        if self._connection is None:
            raise RuntimeError("NeonStore is not connected")
        return self._connection
