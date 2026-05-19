from app.models.schemas import Intent
from app.services.llm_parser import parsed_command_from_llm_json


def test_llm_parser_accepts_high_confidence_task() -> None:
    parsed = parsed_command_from_llm_json(
        "tengo que llamar a Elayne el viernes",
        """
        {
          "intent": "task",
          "confidence": 0.91,
          "title": "Llamar a Elayne",
          "date": "2026-05-22",
          "datetime": null,
          "url": null,
          "needs_clarification": false,
          "clarification_question": null
        }
        """,
        model="test-model",
    )

    assert parsed.intent == Intent.TASK
    assert parsed.body == "Llamar a Elayne"
    assert parsed.parsed_payload["date"] == "2026-05-22"
    assert parsed.parsed_payload["llm"]["confidence"] == 0.91


def test_llm_parser_rejects_low_confidence_result() -> None:
    parsed = parsed_command_from_llm_json(
        "something vague",
        """
        {
          "intent": "note",
          "confidence": 0.52,
          "title": "something vague",
          "date": null,
          "datetime": null,
          "url": null,
          "needs_clarification": true,
          "clarification_question": "Is this a note or a task?"
        }
        """,
        model="test-model",
    )

    assert parsed.intent == Intent.UNKNOWN
    assert parsed.needs_clarification
    assert parsed.error == "Is this a note or a task?"


def test_llm_parser_handles_invalid_json() -> None:
    parsed = parsed_command_from_llm_json("hi", "not json", model="test-model")
    assert parsed.intent == Intent.UNKNOWN
    assert parsed.needs_clarification


def test_llm_parser_accepts_fenced_json() -> None:
    parsed = parsed_command_from_llm_json(
        "remind me tomorrow",
        """```json
        {
          "intent": "reminder",
          "confidence": 0.95,
          "title": "Review invoices",
          "date": null,
          "datetime": "2026-05-20T09:00:00-04:00",
          "url": null,
          "needs_clarification": false,
          "clarification_question": null
        }
        ```""",
        model="test-model",
    )

    assert parsed.intent == Intent.REMINDER
    assert parsed.parsed_payload["datetime"] == "2026-05-20T09:00:00-04:00"
