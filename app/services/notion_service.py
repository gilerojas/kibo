from __future__ import annotations

from typing import Any

import requests

from app.config import Settings
from app.models.schemas import ActionResult, Intent


class NotionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = "https://api.notion.com/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.notion_api_key}",
            "Notion-Version": self.settings.notion_api_version,
            "Content-Type": "application/json",
        }

    def create_for_intent(self, intent: Intent, payload: dict[str, Any], raw_text: str) -> ActionResult:
        database_id = self._database_for_intent(intent)
        title = str(payload.get("text") or raw_text).strip()
        properties = self._properties_for_intent(intent, title, payload, raw_text)
        body = {"parent": {"database_id": database_id}, "properties": properties}

        response = requests.post(f"{self.base_url}/pages", headers=self._headers(), json=body, timeout=20)
        if response.status_code >= 400:
            return ActionResult(
                destination="notion",
                action_type=intent.value,
                status="failed",
                error_message=f"Notion API returned {response.status_code}",
            )

        data = response.json()
        return ActionResult(
            destination="notion",
            action_type=intent.value,
            status="succeeded",
            external_id=data.get("id"),
            external_url=data.get("url"),
        )

    def create_log(self, title: str, content: str) -> ActionResult:
        body = {
            "parent": {"database_id": self.settings.notion_logs_database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Type": {"select": {"name": "Summary"}},
                "Content": {"rich_text": [{"text": {"content": content[:1900]}}]},
            },
        }
        response = requests.post(f"{self.base_url}/pages", headers=self._headers(), json=body, timeout=20)
        if response.status_code >= 400:
            return ActionResult("notion", "summary_log", "failed", error_message=f"Notion API returned {response.status_code}")
        data = response.json()
        return ActionResult("notion", "summary_log", "succeeded", external_id=data.get("id"), external_url=data.get("url"))

    def mark_done(self, page_id: str, intent: Intent) -> ActionResult:
        response = requests.patch(
            f"{self.base_url}/pages/{page_id}",
            headers=self._headers(),
            json={"properties": {"Status": {"status": {"name": "Done"}}}},
            timeout=20,
        )
        if response.status_code >= 400:
            return ActionResult(
                "notion",
                "done",
                "failed",
                external_id=page_id,
                error_message=f"Notion API returned {response.status_code}",
            )
        data = response.json()
        return ActionResult("notion", "done", "succeeded", external_id=data.get("id"), external_url=data.get("url"))

    def _database_for_intent(self, intent: Intent) -> str:
        mapping = {
            Intent.NOTE: self.settings.notion_inbox_database_id,
            Intent.TASK: self.settings.notion_tasks_database_id,
            Intent.LINK: self.settings.notion_links_database_id,
            Intent.BOOK: self.settings.notion_inbox_database_id,
            Intent.REMINDER: self.settings.notion_schedule_database_id,
            Intent.EVENT: self.settings.notion_schedule_database_id,
        }
        return mapping[intent]

    def _properties_for_intent(
        self,
        intent: Intent,
        title: str,
        payload: dict[str, Any],
        raw_text: str,
    ) -> dict[str, Any]:
        if intent == Intent.NOTE:
            return {
                "Name": {"title": [{"text": {"content": title[:2000]}}]},
                "Type": {"select": {"name": "Note"}},
                "Content": {"rich_text": [{"text": {"content": raw_text[:1900]}}]},
                "Source": {"select": {"name": "Telegram"}},
            }
        if intent == Intent.TASK:
            props: dict[str, Any] = {
                "Name": {"title": [{"text": {"content": title[:2000]}}]},
                "Status": {"status": {"name": "Inbox"}},
                "Source": {"select": {"name": "Telegram"}},
            }
            if payload.get("date"):
                props["Due Date"] = {"date": {"start": str(payload["date"])}}
            return props
        if intent == Intent.LINK:
            props = {
                "Name": {"title": [{"text": {"content": title[:2000]}}]},
                "Status": {"status": {"name": "Inbox"}},
                "Source": {"select": {"name": "Telegram"}},
            }
            if payload.get("url"):
                props["URL"] = {"url": str(payload["url"])}
            return props
        if intent == Intent.BOOK:
            props = {
                "Name": {"title": [{"text": {"content": title[:2000]}}]},
                "Type": {"select": {"name": "Book"}},
                "Content": {"rich_text": [{"text": {"content": raw_text[:1900]}}]},
                "Source": {"select": {"name": "Telegram"}},
            }
            return props
        if intent in {Intent.REMINDER, Intent.EVENT}:
            props = {
                "Name": {"title": [{"text": {"content": title[:2000]}}]},
                "Type": {"select": {"name": "Reminder" if intent == Intent.REMINDER else "Event"}},
                "Status": {"status": {"name": "Scheduled"}},
                "Source": {"select": {"name": "Telegram"}},
            }
            if payload.get("datetime"):
                date_value = {"start": str(payload["datetime"])}
                if payload.get("end_datetime"):
                    date_value["end"] = str(payload["end_datetime"])
                props["Scheduled For"] = {"date": date_value}
            elif payload.get("date"):
                props["Scheduled For"] = {"date": {"start": str(payload["date"])}}
            return props
        raise ValueError(f"Unsupported Notion intent: {intent}")
