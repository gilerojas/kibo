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

    def create_reminder(
        self,
        *,
        command_id: UUID,
        user_id: UUID,
        telegram_chat_id: int,
        title: str,
        reminder_at: datetime,
        notion_url: str | None,
    ) -> UUID:
        with self.connect() as conn:
            row = conn.execute(
                """
                insert into kibo.reminders (
                    command_id, user_id, telegram_chat_id, title, reminder_at, notion_url
                )
                values (%s, %s, %s, %s, %s, %s)
                returning id
                """,
                (command_id, user_id, telegram_chat_id, title, reminder_at, notion_url),
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

    def today_items(self, user_id: UUID, day: date) -> dict[str, Any]:
        day_text = day.isoformat()
        with self.connect() as conn:
            rows = conn.execute(
                """
                select c.intent, c.raw_text, c.parsed_payload, c.created_at, a.external_url
                from kibo.commands c
                left join lateral (
                    select external_url
                    from kibo.actions
                    where command_id = c.id and destination = 'notion' and status = 'succeeded'
                    order by created_at desc
                    limit 1
                ) a on true
                where c.user_id = %s
                  and c.status = 'processed'
                  and c.intent in ('task', 'reminder', 'event')
                  and (
                    c.parsed_payload ->> 'date' = %s
                    or left(coalesce(c.parsed_payload ->> 'datetime', ''), 10) = %s
                  )
                order by
                  coalesce(c.parsed_payload ->> 'datetime', c.parsed_payload ->> 'date') asc,
                  c.created_at asc
                """,
                (user_id, day_text, day_text),
            ).fetchall()
        return {"date": day_text, "items": rows}

    def upcoming_items(self, user_id: UUID, start_day: date, end_day: date) -> dict[str, Any]:
        start_text = start_day.isoformat()
        end_text = end_day.isoformat()
        with self.connect() as conn:
            rows = conn.execute(
                """
                select c.intent, c.raw_text, c.parsed_payload, c.created_at, a.external_url
                from kibo.commands c
                left join lateral (
                    select external_url
                    from kibo.actions
                    where command_id = c.id and destination = 'notion' and status = 'succeeded'
                    order by created_at desc
                    limit 1
                ) a on true
                where c.user_id = %s
                  and c.status = 'processed'
                  and c.intent in ('task', 'reminder', 'event')
                  and (
                    c.parsed_payload ->> 'date' between %s and %s
                    or left(coalesce(c.parsed_payload ->> 'datetime', ''), 10) between %s and %s
                  )
                order by
                  coalesce(c.parsed_payload ->> 'datetime', c.parsed_payload ->> 'date') asc,
                  c.created_at asc
                """,
                (user_id, start_text, end_text, start_text, end_text),
            ).fetchall()
        return {"start_date": start_text, "end_date": end_text, "items": rows}

    def search_items(self, user_id: UUID, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        with self.connect() as conn:
            rows = conn.execute(
                """
                select c.id as command_id, c.intent, c.raw_text, c.parsed_payload, c.created_at,
                       a.external_id, a.external_url
                from kibo.commands c
                left join lateral (
                    select external_id, external_url
                    from kibo.actions
                    where command_id = c.id and destination = 'notion' and status = 'succeeded'
                    order by created_at desc
                    limit 1
                ) a on true
                where c.user_id = %s
                  and c.status = 'processed'
                  and c.intent in ('note', 'task', 'link', 'reminder', 'event')
                  and (
                    c.raw_text ilike %s
                    or c.parsed_payload ->> 'text' ilike %s
                  )
                order by c.created_at desc
                limit %s
                """,
                (user_id, pattern, pattern, limit),
            ).fetchall()
        return list(rows)

    def best_open_item(self, user_id: UUID, query: str) -> dict[str, Any] | None:
        rows = self.search_items(user_id, query, limit=1)
        return rows[0] if rows else None

    def best_completable_item(self, user_id: UUID, query: str) -> dict[str, Any] | None:
        pattern = f"%{query}%"
        with self.connect() as conn:
            row = conn.execute(
                """
                select c.id as command_id, c.intent, c.raw_text, c.parsed_payload, c.created_at,
                       a.external_id, a.external_url
                from kibo.commands c
                join lateral (
                    select external_id, external_url
                    from kibo.actions
                    where command_id = c.id and destination = 'notion' and status = 'succeeded'
                    order by created_at desc
                    limit 1
                ) a on true
                where c.user_id = %s
                  and c.status = 'processed'
                  and c.intent in ('task', 'reminder', 'event')
                  and (
                    c.raw_text ilike %s
                    or c.parsed_payload ->> 'text' ilike %s
                  )
                order by c.created_at desc
                limit 1
                """,
                (user_id, pattern, pattern),
            ).fetchone()
        return row

    def mark_reminder_done_for_command(self, command_id: UUID) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                update kibo.reminders
                set status = 'done', sent_at = coalesce(sent_at, now())
                where command_id = %s and status in ('scheduled', 'sent')
                """,
                (command_id,),
            )
            conn.commit()

    def due_reminders(self, now: datetime, *, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, telegram_chat_id, title, reminder_at, notion_url
                from kibo.reminders
                where status = 'scheduled' and reminder_at <= %s
                order by reminder_at asc
                limit %s
                """,
                (now, limit),
            ).fetchall()
        return list(rows)

    def mark_reminder_sent(self, reminder_id: UUID) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                update kibo.reminders
                set status = 'sent', sent_at = now()
                where id = %s and status = 'scheduled'
                """,
                (reminder_id,),
            )
            conn.commit()

    def mark_reminder_failed(self, reminder_id: UUID, error_message: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                update kibo.reminders
                set error_message = %s
                where id = %s
                """,
                (error_message[:1000], reminder_id),
            )
            conn.commit()
