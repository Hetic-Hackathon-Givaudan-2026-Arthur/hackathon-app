import json
from typing import Any
from uuid import uuid4

import psycopg


class NeonStore:
    """Persist outbox entries and processing events in Neon PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._connection: psycopg.AsyncConnection | None = None

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
        connection = self._require_connection()
        async with connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE outbox_events SET sent = TRUE WHERE id = %s",
                (entry["id"],),
            )
        await connection.commit()

    async def append(self, entry: dict[str, Any]) -> None:
        """Append a processing event without updating previous records."""
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

    def _require_connection(self) -> psycopg.AsyncConnection:
        """Return the active connection or fail explicitly when not started."""
        if self._connection is None:
            raise RuntimeError("NeonStore is not connected")
        return self._connection
