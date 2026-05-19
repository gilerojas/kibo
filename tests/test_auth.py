from app.config import Settings
from app.services.auth import is_authorized_user


def test_authorized_user() -> None:
    settings = Settings(telegram_allowed_user_ids="123,456")
    assert is_authorized_user(123, settings)


def test_unauthorized_user() -> None:
    settings = Settings(telegram_allowed_user_ids="123,456")
    assert not is_authorized_user(789, settings)


def test_empty_allowed_list_rejects_all() -> None:
    settings = Settings(telegram_allowed_user_ids="")
    assert not is_authorized_user(123, settings)
