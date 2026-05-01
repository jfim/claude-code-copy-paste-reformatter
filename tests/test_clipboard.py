import sys
from unittest.mock import patch

from claude_code_copy_paste_reformatter.clipboard import _PyperclipBackend, make_clipboard


class FakePyperclip:
    def __init__(self, initial: str = "") -> None:
        self.value = initial
        self.copy_calls = 0
        self.paste_calls = 0

    def paste(self) -> str:
        self.paste_calls += 1
        return self.value

    def copy(self, value: str) -> None:
        self.copy_calls += 1
        self.value = value


def _backend_with(fake: FakePyperclip) -> _PyperclipBackend:
    backend = _PyperclipBackend.__new__(_PyperclipBackend)
    backend._pyperclip = fake
    backend._last_seen = None
    return backend


def test_pyperclip_poll_returns_initial_value_then_none():
    fake = FakePyperclip(initial="hello")
    backend = _backend_with(fake)

    assert backend.poll() == "hello"
    assert backend.poll() is None
    assert backend.poll() is None


def test_pyperclip_poll_detects_change():
    fake = FakePyperclip(initial="hello")
    backend = _backend_with(fake)

    backend.poll()  # consume initial
    fake.value = "world"
    assert backend.poll() == "world"
    assert backend.poll() is None


def test_pyperclip_write_suppresses_self_echo():
    fake = FakePyperclip(initial="hello   ")
    backend = _backend_with(fake)

    seen = backend.poll()
    assert seen == "hello   "
    backend.write("hello")
    # Next poll must not re-fire on our own write.
    assert backend.poll() is None


def test_pyperclip_read_does_not_advance_last_seen():
    fake = FakePyperclip(initial="hello")
    backend = _backend_with(fake)

    assert backend.read() == "hello"
    # read() must not consume the change; poll() should still report it.
    assert backend.poll() == "hello"


def test_pyperclip_poll_treats_empty_string_as_change_once():
    fake = FakePyperclip(initial="")
    backend = _backend_with(fake)

    assert backend.poll() == ""
    assert backend.poll() is None


def test_make_clipboard_falls_back_when_native_import_fails(capsys):
    # Force the native path to fail by removing AppKit / gi from sys.modules and
    # blocking re-import.
    with patch.dict(sys.modules, {"AppKit": None, "gi": None}):
        backend = make_clipboard()

    assert isinstance(backend, _PyperclipBackend)
    if sys.platform in ("darwin",) or sys.platform.startswith("linux"):
        captured = capsys.readouterr()
        assert "falling back to pyperclip" in captured.err
