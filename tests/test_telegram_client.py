from datetime import timezone

from app.bot.telegram_client import telegram_message_from_update


def test_telegram_message_from_update_includes_chat_type() -> None:
    message = telegram_message_from_update(
        {
            "update_id": 1,
            "message": {
                "message_id": 2,
                "date": 1779141600,
                "text": "/start",
                "from": {"id": 123},
                "chat": {"id": 456, "type": "group"},
            },
        },
        tz=timezone.utc,
    )

    assert message is not None
    assert message.chat_type == "group"
