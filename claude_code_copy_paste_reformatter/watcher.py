import sys
import threading

from claude_code_copy_paste_reformatter.clipboard import ClipboardBackend, make_clipboard
from claude_code_copy_paste_reformatter.reformat import strip_trailing_spaces

POLL_INTERVAL_S = 0.3


class ClipboardWatcher:
    """Polls the system clipboard and strips trailing spaces from text content.

    A daemon thread polls every POLL_INTERVAL_S seconds via a platform-specific
    clipboard backend (NSPasteboard on macOS, GTK on Linux, pyperclip otherwise).
    When the clipboard changes AND stripping trailing spaces would change it, the
    cleaned text is written back. Backends remember their own writes so the
    watcher never reprocesses its own output.
    """

    def __init__(self, clipboard: ClipboardBackend | None = None) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._enabled = True
        self._clipboard = clipboard if clipboard is not None else make_clipboard()

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
                except Exception as e:
                    print(
                        f"claude-code-copy-paste-reformatter: clipboard error: {e!r}",
                        file=sys.stderr,
                    )
            self._stop.wait(POLL_INTERVAL_S)

    def _tick(self) -> None:
        current = self._clipboard.poll()
        if not current:
            return
        cleaned = strip_trailing_spaces(current)
        if cleaned != current:
            self._clipboard.write(cleaned)
