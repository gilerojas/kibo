from app.bot.polling import initial_offset


class FakeTelegram:
    def __init__(self, updates):
        self.updates = updates

    def get_updates(self, *, offset, timeout):
        return self.updates


def test_initial_offset_skips_pending_updates() -> None:
    offset = initial_offset(FakeTelegram([{"update_id": 10}, {"update_id": 12}]), object())
    assert offset == 13


def test_initial_offset_none_without_updates() -> None:
    offset = initial_offset(FakeTelegram([]), object())
    assert offset is None
