import sys
import threading
import time

import pyperclip

from claude_code_copy_paste_reformatter.reformat import strip_trailing_spaces

POLL_INTERVAL_S = 0.3


class ClipboardWatcher:
    """Polls the system clipboard and strips trailing spaces from text content.

    A daemon thread reads the clipboard every POLL_INTERVAL_S seconds. When the
    contents change AND stripping trailing spaces would change them, the cleaned
    text is written back. The watcher remembers the last value it saw (after its
    own writes) so it never reprocesses its own output.
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._enabled = True
        self._last_seen: str | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="ClipboardWatcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            if self._enabled:
                try:
                    self._tick()
                except pyperclip.PyperclipException as e:
                    print(f"claude-code-copy-paste-reformatter: clipboard error: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"claude-code-copy-paste-reformatter: unexpected error: {e!r}", file=sys.stderr)
            self._stop.wait(POLL_INTERVAL_S)

    def _tick(self) -> None:
        current = pyperclip.paste()
        if not current or current == self._last_seen:
            return
        cleaned = strip_trailing_spaces(current)
        if cleaned != current:
            pyperclip.copy(cleaned)
        self._last_seen = cleaned
