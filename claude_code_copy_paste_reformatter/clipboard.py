import sys
from typing import Protocol


class ClipboardBackend(Protocol):
    def read(self) -> str: ...
    def write(self, value: str) -> None: ...
    def poll(self) -> str | None:
        """Return the current clipboard text if it changed since the last poll, else None.

        The first call after construction returns the current text (treated as a change).
        Backends are responsible for ignoring writes performed via this same object.
        """
        ...


class _PyperclipBackend:
    """Fallback backend. Reads every poll and compares to last seen value."""

    def __init__(self) -> None:
        import pyperclip

        self._pyperclip = pyperclip
        self._last_seen: str | None = None

    def read(self) -> str:
        return self._pyperclip.paste()

    def write(self, value: str) -> None:
        self._pyperclip.copy(value)
        self._last_seen = value

    def poll(self) -> str | None:
        current = self._pyperclip.paste()
        if current == self._last_seen:
            return None
        self._last_seen = current
        return current


class _NSPasteboardBackend:
    """macOS backend using AppKit.NSPasteboard. Polls the cheap changeCount integer."""

    def __init__(self) -> None:
        from AppKit import NSPasteboard, NSPasteboardTypeString

        self._pb = NSPasteboard.generalPasteboard()
        self._string_type = NSPasteboardTypeString
        self._last_change_count = self._pb.changeCount() - 1  # force first poll to fire

    def read(self) -> str:
        return self._pb.stringForType_(self._string_type) or ""

    def write(self, value: str) -> None:
        self._pb.clearContents()
        self._pb.setString_forType_(value, self._string_type)
        self._last_change_count = self._pb.changeCount()

    def poll(self) -> str | None:
        cc = self._pb.changeCount()
        if cc == self._last_change_count:
            return None
        self._last_change_count = cc
        return self.read()


class _GtkClipboardBackend:
    """Linux backend using Gdk.Clipboard. Reads synchronously via the X11 selection."""

    def __init__(self) -> None:
        import gi

        gi.require_version("Gdk", "3.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, Gtk

        # wait_for_text() is synchronous and talks to the display server directly
        # (no xclip subprocess). SELECTION_CLIPBOARD is the standard ctrl-c/ctrl-v
        # selection; SELECTION_PRIMARY (middle-click paste) is a separate buffer.
        self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self._last_seen: str | None = None

    def read(self) -> str:
        return self._clipboard.wait_for_text() or ""

    def write(self, value: str) -> None:
        self._clipboard.set_text(value, -1)
        self._clipboard.store()
        self._last_seen = value

    def poll(self) -> str | None:
        current = self._clipboard.wait_for_text() or ""
        if current == self._last_seen:
            return None
        self._last_seen = current
        return current


def make_clipboard() -> ClipboardBackend:
    """Construct the best clipboard backend for this platform.

    Falls back to pyperclip if the platform-native backend cannot be loaded.
    """
    if sys.platform == "darwin":
        try:
            return _NSPasteboardBackend()
        except Exception as e:
            print(
                f"claude-code-copy-paste-reformatter: NSPasteboard unavailable ({e!r}),"
                " falling back to pyperclip",
                file=sys.stderr,
            )
    elif sys.platform.startswith("linux"):
        try:
            return _GtkClipboardBackend()
        except Exception as e:
            print(
                f"claude-code-copy-paste-reformatter: GTK clipboard unavailable ({e!r}),"
                " falling back to pyperclip",
                file=sys.stderr,
            )
    return _PyperclipBackend()
