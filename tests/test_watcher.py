from claude_code_copy_paste_reformatter.watcher import ClipboardWatcher


class FakeClipboard:
    """In-memory ClipboardBackend for testing the watcher's tick logic."""

    def __init__(self) -> None:
        self._value: str = ""
        self._pending: str | None = None
        self.writes: list[str] = []

    def set_external(self, value: str) -> None:
        """Simulate something else putting text on the clipboard."""
        self._value = value
        self._pending = value

    def read(self) -> str:
        return self._value

    def write(self, value: str) -> None:
        self._value = value
        self._pending = None
        self.writes.append(value)

    def poll(self) -> str | None:
        out = self._pending
        self._pending = None
        return out


def test_tick_strips_trailing_spaces_when_present():
    fake = FakeClipboard()
    watcher = ClipboardWatcher(clipboard=fake)
    fake.set_external("hello   \nworld  ")

    watcher._tick()

    assert fake.writes == ["hello\nworld"]


def test_tick_does_not_write_when_already_clean():
    fake = FakeClipboard()
    watcher = ClipboardWatcher(clipboard=fake)
    fake.set_external("clean text")

    watcher._tick()

    assert fake.writes == []


def test_tick_is_noop_when_no_change():
    fake = FakeClipboard()
    watcher = ClipboardWatcher(clipboard=fake)

    watcher._tick()
    watcher._tick()

    assert fake.writes == []


def test_tick_skips_empty_clipboard():
    fake = FakeClipboard()
    watcher = ClipboardWatcher(clipboard=fake)
    fake.set_external("")

    watcher._tick()

    assert fake.writes == []


def test_disabled_watcher_skips_processing():
    fake = FakeClipboard()
    watcher = ClipboardWatcher(clipboard=fake)
    watcher.set_enabled(False)
    fake.set_external("dirty   ")

    # _run would call _tick only when enabled; emulate by checking the flag.
    if watcher.enabled:
        watcher._tick()

    assert fake.writes == []
