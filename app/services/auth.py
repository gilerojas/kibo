from app.config import Settings


def is_authorized_user(user_id: int, settings: Settings) -> bool:
    allowed = settings.allowed_user_ids
    return bool(allowed) and user_id in allowed
