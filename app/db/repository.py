from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Iterator
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import Settings
from app.models.schemas import ActionResult, CommandStatus, ParsedCommand, TelegramMessage


class SupabaseRepository:
    def __init__(self, settings: Settings):
        self.database_url = settings.supabase_database_url

    @contextmanager
    def connect(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    def upsert_user(self, message: TelegramMessage, *, timezone: str) -> UUID:
        with self.connect() as conn:
            row = conn.execute(
                """
                insert into kibo.users (telegram_user_id, telegram_chat_id, timezone)
                values (%s, %s, %s)
                on conflict (telegram_user_id)
                do update set telegram_chat_id = excluded.telegram_chat_id, updated_at = now()
                returning id
                """,
                (message.user_id, message.chat_id, timezone),
            ).fetchone()
            conn.commit()
            return row["id"]

    def create_command(
        self,
        *,
        user_id: UUID | None,
        message: TelegramMessage,
        parsed: ParsedCommand,
        status: CommandStatus = CommandStatus.RECEIVED,
        error_message: str | None = None,
    ) -> UUID:
        with self.connect() as conn:
            row = conn.execute(
                """
                insert into kibo.commands (
                    user_id, telegram_chat_id, telegram_user_id, telegram_message_id,
                    raw_text, intent, status, parsed_payload, source, error_message
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, 'telegram', %s)
                returning id
                """,
                (
                    user_id,
                    message.chat_id,
                    message.user_id,
                    message.message_id,
                    parsed.raw_text,
                    parsed.intent.value,
                    status.value,
                    Jsonb(parsed.parsed_payload),
                    error_message,
                ),
            ).fetchone()
            conn.commit()
            return row["id"]

    def update_command_status(
        self,
        command_id: UUID,
        status: CommandStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                update kibo.commands
                set status = %s, processed_at = now(), error_message = %s
                where id = %s
                """,
                (status.value, error_message, command_id),
            )
            conn.commit()

    def create_action(self, *, command_id: UUID, user_id: UUID | None, result: ActionResult) -> UUID:
        with self.connect() as conn:
            row = conn.execute(
                """
                insert into kibo.actions (
                    command_id, user_id, action_type, destination, external_id,
                    external_url, status, error_message
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    command_id,
                    user_id,
                    result.action_type,
                    result.destination,
                    result.external_id,
                    result.external_url,
                    result.status,
                    result.error_message,
                ),
            ).fetchone()
            conn.commit()
            return row["id"]

    def summary_for_day(self, user_id: UUID, day: date) -> dict[str, Any]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day + date.resolution, datetime.min.time())
        with self.connect() as conn:
            rows = conn.execute(
                """
                select intent, status, count(*) as count
                from kibo.commands
                where user_id = %s and created_at >= %s and created_at < %s
                group by intent, status
                order by intent, status
                """,
                (user_id, start, end),
            ).fetchall()
        return {"date": day.isoformat(), "counts": rows}
