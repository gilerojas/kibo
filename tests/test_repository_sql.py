from app.config import Settings
from app.db.repository import SupabaseRepository


def test_search_items_excludes_control_intents(monkeypatch) -> None:
    captured = {}

    class Cursor:
        def fetchall(self):
            return []

    class Connection:
        def execute(self, query, params):
            captured["query"] = query
            captured["params"] = params
            return Cursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.db.repository.psycopg.connect", lambda *args, **kwargs: Connection())
    repo = SupabaseRepository(Settings(supabase_database_url="postgresql://example"))

    repo.search_items("00000000-0000-0000-0000-000000000000", "gym")

    assert "c.intent in ('note', 'task', 'link', 'reminder', 'event')" in captured["query"]
