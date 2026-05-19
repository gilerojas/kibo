from __future__ import annotations

import os
import sys
from typing import Any

import requests


NOTION_VERSION = os.getenv("NOTION_API_VERSION", "2022-06-28")


def main() -> int:
    token = os.getenv("NOTION_API_KEY")
    parent_page_id = os.getenv("KIBO_NOTION_PARENT_PAGE_ID")
    if not token or not parent_page_id:
        print("Set NOTION_API_KEY and KIBO_NOTION_PARENT_PAGE_ID before running.", file=sys.stderr)
        return 1

    client = NotionSetupClient(token)
    databases = {
        "NOTION_INBOX_DATABASE_ID": client.create_database("Kibo Inbox", inbox_properties()),
        "NOTION_TASKS_DATABASE_ID": client.create_database("Kibo Tasks", task_properties()),
        "NOTION_LINKS_DATABASE_ID": client.create_database("Kibo Links", link_properties()),
        "NOTION_SCHEDULE_DATABASE_ID": client.create_database("Kibo Schedule", schedule_properties()),
        "NOTION_LOGS_DATABASE_ID": client.create_database("Kibo Logs", log_properties()),
    }

    print("Add these values to .env:")
    for key, value in databases.items():
        print(f"{key}={value}")
    return 0


class NotionSetupClient:
    def __init__(self, token: str):
        self.token = token
        self.parent_page_id = os.environ["KIBO_NOTION_PARENT_PAGE_ID"]

    def create_database(self, title: str, properties: dict[str, Any]) -> str:
        response = requests.post(
            "https://api.notion.com/v1/databases",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            json={
                "parent": {"type": "page_id", "page_id": self.parent_page_id},
                "title": [{"type": "text", "text": {"content": title}}],
                "properties": properties,
            },
            timeout=20,
        )
        if response.status_code >= 400:
            print(f"Failed creating {title}: {response.status_code} {response.text}", file=sys.stderr)
            raise SystemExit(1)
        data = response.json()
        print(f"Created {title}: {data['id']}")
        return data["id"]


def title_property() -> dict[str, Any]:
    return {"title": {}}


def source_property() -> dict[str, Any]:
    return {"select": {"options": [{"name": "Telegram", "color": "blue"}]}}


def inbox_properties() -> dict[str, Any]:
    return {
        "Name": title_property(),
        "Type": {"select": {"options": [{"name": "Note", "color": "green"}]}},
        "Content": {"rich_text": {}},
        "Source": source_property(),
    }


def task_properties() -> dict[str, Any]:
    return {
        "Name": title_property(),
        "Status": {"status": {"options": status_options(["Inbox", "Active", "Done"])}},
        "Due Date": {"date": {}},
        "Source": source_property(),
    }


def link_properties() -> dict[str, Any]:
    return {
        "Name": title_property(),
        "URL": {"url": {}},
        "Status": {"status": {"options": status_options(["Inbox", "Read", "Archived"])}},
        "Source": source_property(),
    }


def schedule_properties() -> dict[str, Any]:
    return {
        "Name": title_property(),
        "Type": {
            "select": {
                "options": [
                    {"name": "Reminder", "color": "yellow"},
                    {"name": "Event", "color": "purple"},
                ]
            }
        },
        "Status": {"status": {"options": status_options(["Scheduled", "Done", "Cancelled"])}},
        "Scheduled For": {"date": {}},
        "Source": source_property(),
    }


def log_properties() -> dict[str, Any]:
    return {
        "Name": title_property(),
        "Type": {
            "select": {
                "options": [
                    {"name": "Summary", "color": "green"},
                    {"name": "Error", "color": "red"},
                    {"name": "System", "color": "gray"},
                ]
            }
        },
        "Content": {"rich_text": {}},
    }


def status_options(names: list[str]) -> list[dict[str, str]]:
    colors = ["gray", "blue", "green", "red"]
    return [{"name": name, "color": colors[index % len(colors)]} for index, name in enumerate(names)]


if __name__ == "__main__":
    raise SystemExit(main())
