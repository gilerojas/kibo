from app.config import Settings
from app.models.schemas import Intent
from app.services.notion_service import NotionService


def test_schedule_event_includes_end_datetime() -> None:
    service = NotionService(Settings())

    props = service._properties_for_intent(
        Intent.EVENT,
        "schedule gym from 6 to 7 pm",
        {
            "text": "schedule gym from 6 to 7 pm",
            "datetime": "2026-05-19T18:00:00-04:00",
            "end_datetime": "2026-05-19T19:00:00-04:00",
        },
        "schedule gym from 6 to 7 pm",
    )

    assert props["Scheduled For"]["date"]["start"] == "2026-05-19T18:00:00-04:00"
    assert props["Scheduled For"]["date"]["end"] == "2026-05-19T19:00:00-04:00"


def test_mark_done_payload(monkeypatch) -> None:
    captured = {}

    class Response:
        status_code = 200

        def json(self):
            return {"id": "page-id", "url": "https://notion.so/page-id"}

    def fake_patch(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return Response()

    monkeypatch.setattr("app.services.notion_service.requests.patch", fake_patch)
    service = NotionService(Settings(notion_api_key="secret"))

    result = service.mark_done("page-id", Intent.TASK)

    assert result.status == "succeeded"
    assert captured["url"].endswith("/pages/page-id")
    assert captured["json"]["properties"]["Status"]["status"]["name"] == "Done"
