# Clipboard Reformatter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Linux/macOS systray app that watches the clipboard and strips trailing spaces from every line of any text copied to it.

**Architecture:** A `pystray` icon owns the main thread and exposes Enabled/Quit menu items. A background `ClipboardWatcher` thread polls `pyperclip` every 300ms; when contents differ from the last seen value AND stripping trailing spaces would change them, it writes the cleaned text back. A pure `strip_trailing_spaces()` function holds the entire reformat logic and is the only thing covered by unit tests. At startup, the entry point performs a single clipboard read; if it raises, a `tkinter.messagebox` shows the error and the app exits with status 1.

**Tech Stack:** Python 3.11+, uv, pyperclip, pystray, Pillow, tkinter (stdlib), pytest.

---

## File Structure

```
clipboard-reformatter/
├── pyproject.toml                       # uv project, deps, script entry point
├── .gitignore
├── README.md
├── docs/superpowers/
│   ├── specs/2026-04-30-clipboard-reformatter-design.md   (already exists)
│   └── plans/2026-04-30-clipboard-reformatter.md          (this file)
├── clipboard_reformatter/
│   ├── __init__.py                      # empty
│   ├── __main__.py                      # entry: startup probe + wire watcher + tray
│   ├── reformat.py                      # pure: strip_trailing_spaces(text)
│   ├── watcher.py                       # ClipboardWatcher: polling thread
│   └── tray.py                          # build_tray(watcher): pystray icon + menu
└── tests/
    ├── __init__.py                      # empty
    └── test_reformat.py                 # unit tests for reformat.py
```

Each module has one responsibility. `reformat.py` is pure (no I/O) and is the only file with unit tests. `watcher.py` depends on `reformat.py` + `pyperclip`. `tray.py` depends on `pystray` + `Pillow` and exposes a single `build_tray(watcher)` function. `__main__.py` ties them together and owns the startup probe.

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `clipboard_reformatter/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)

- [ ] **Step 1: Initialize the uv project**

Run from the project root:

```bash
uv init --package --name clipboard-reformatter --python 3.11
```

This creates a baseline `pyproject.toml` and a `src/` layout. We are NOT using src layout, so the next step overwrites `pyproject.toml`.

- [ ] **Step 2: Replace `pyproject.toml` with the project layout we want**

Overwrite `pyproject.toml` with:

```toml
[project]
name = "clipboard-reformatter"
version = "0.1.0"
description = "Systray app that strips trailing spaces from clipboard text"
requires-python = ">=3.11"
dependencies = [
    "pyperclip>=1.8",
    "pystray>=0.19",
    "Pillow>=10",
]

[project.scripts]
clipboard-reformatter = "clipboard_reformatter.__main__:main"

[dependency-groups]
dev = [
    "pytest>=8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["clipboard_reformatter"]
```

If `uv init` created a `src/clipboard_reformatter/` directory or a `hello.py`, delete them — we want the package directly under the repo root.

```bash
rm -rf src hello.py
```

- [ ] **Step 3: Create the package and tests directories**

```bash
mkdir -p clipboard_reformatter tests
touch clipboard_reformatter/__init__.py tests/__init__.py
```

- [ ] **Step 4: Write `.gitignore`**

Contents of `.gitignore`:

```
__pycache__/
*.pyc
.venv/
.pytest_cache/
dist/
build/
*.egg-info/
uv.lock
```

(We deliberately ignore `uv.lock` for now — this is a personal/dev project and locking can come later.)

- [ ] **Step 5: Sync dependencies**

```bash
uv sync
```

Expected: creates `.venv/`, installs pyperclip, pystray, Pillow, pytest. No errors.

- [ ] **Step 6: Verify pytest runs (with no tests yet)**

```bash
uv run pytest
```

Expected: exits 5 (no tests collected) or 0. Either is fine — confirms pytest is installed and importable.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore clipboard_reformatter/ tests/
git commit -m "Scaffold clipboard-reformatter with uv"
```

---

### Task 2: `strip_trailing_spaces` (TDD)

**Files:**
- Create: `tests/test_reformat.py`
- Create: `clipboard_reformatter/reformat.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_reformat.py`:

```python
from clipboard_reformatter.reformat import strip_trailing_spaces


def test_strips_trailing_spaces_from_single_line():
    assert strip_trailing_spaces("hello   ") == "hello"


def test_leaves_leading_spaces_alone():
    assert strip_trailing_spaces("    hello") == "    hello"


def test_strips_per_line_in_multiline_text():
    assert strip_trailing_spaces("a   \nb  \nc") == "a\nb\nc"


def test_preserves_blank_lines():
    assert strip_trailing_spaces("a\n\nb") == "a\n\nb"


def test_does_not_strip_tabs():
    # Spec says spaces only.
    assert strip_trailing_spaces("hello\t\t") == "hello\t\t"


def test_preserves_trailing_newline():
    assert strip_trailing_spaces("hello   \n") == "hello\n"


def test_preserves_absence_of_trailing_newline():
    assert strip_trailing_spaces("hello   ") == "hello"


def test_noop_when_nothing_to_strip():
    assert strip_trailing_spaces("hello\nworld") == "hello\nworld"


def test_empty_string():
    assert strip_trailing_spaces("") == ""


def test_line_of_only_spaces_becomes_empty():
    assert strip_trailing_spaces("a\n   \nb") == "a\n\nb"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_reformat.py -v
```

Expected: ImportError / ModuleNotFoundError on `clipboard_reformatter.reformat`.

- [ ] **Step 3: Implement `strip_trailing_spaces`**

Create `clipboard_reformatter/reformat.py`:

```python
import re

_TRAILING_SPACES = re.compile(r' +$', flags=re.MULTILINE)


def strip_trailing_spaces(text: str) -> str:
    """Remove trailing spaces (U+0020) from every line of `text`.

    Tabs and other whitespace are left untouched. Line endings and blank
    lines are preserved.
    """
    return _TRAILING_SPACES.sub('', text)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_reformat.py -v
```

Expected: all 10 tests pass.

- [ ] **Step 5: Commit**

```bash
git add clipboard_reformatter/reformat.py tests/test_reformat.py
git commit -m "Add strip_trailing_spaces with tests"
```

---

### Task 3: `ClipboardWatcher`

**Files:**
- Create: `clipboard_reformatter/watcher.py`

No unit tests for this module — it's integration-only (depends on a live system clipboard). Manual verification at the end.

- [ ] **Step 1: Write `watcher.py`**

Create `clipboard_reformatter/watcher.py`:

```python
import sys
import threading
import time

import pyperclip

from clipboard_reformatter.reformat import strip_trailing_spaces

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
                    print(f"clipboard-reformatter: clipboard error: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"clipboard-reformatter: unexpected error: {e!r}", file=sys.stderr)
            self._stop.wait(POLL_INTERVAL_S)

    def _tick(self) -> None:
        current = pyperclip.paste()
        if not current or current == self._last_seen:
            return
        cleaned = strip_trailing_spaces(current)
        if cleaned != current:
            pyperclip.copy(cleaned)
        self._last_seen = cleaned
```

- [ ] **Step 2: Smoke-import the module**

```bash
uv run python -c "from clipboard_reformatter.watcher import ClipboardWatcher; w = ClipboardWatcher(); print('ok')"
```

Expected: prints `ok`. (Don't call `start()` here — without a clipboard backend in CI this would fail; we exercise it from the entry point in Task 5.)

- [ ] **Step 3: Commit**

```bash
git add clipboard_reformatter/watcher.py
git commit -m "Add ClipboardWatcher polling thread"
```

---

### Task 4: Tray icon and menu

**Files:**
- Create: `clipboard_reformatter/tray.py`

- [ ] **Step 1: Write `tray.py`**

Create `clipboard_reformatter/tray.py`:

```python
from PIL import Image, ImageDraw
import pystray

from clipboard_reformatter.watcher import ClipboardWatcher

ICON_SIZE = 64


def _make_icon_image() -> Image.Image:
    """Create a simple 64x64 icon: dark background with a light 'C' shape."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    # A thick arc that reads as a 'C' for clipboard.
    draw.arc((10, 10, ICON_SIZE - 10, ICON_SIZE - 10), start=40, end=320, fill=(220, 220, 220, 255), width=8)
    return img


def build_tray(watcher: ClipboardWatcher) -> pystray.Icon:
    """Return a pystray.Icon wired to the given watcher.

    Menu items:
      - Enabled (checkable; toggles watcher.set_enabled)
      - Quit (stops the watcher and the icon)
    """

    def on_toggle_enabled(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        watcher.set_enabled(not watcher.enabled)
        icon.update_menu()

    def on_quit(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        watcher.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            "Enabled",
            on_toggle_enabled,
            checked=lambda item: watcher.enabled,
        ),
        pystray.MenuItem("Quit", on_quit),
    )

    return pystray.Icon(
        name="clipboard-reformatter",
        icon=_make_icon_image(),
        title="Clipboard Reformatter",
        menu=menu,
    )
```

- [ ] **Step 2: Smoke-import the module**

```bash
uv run python -c "from clipboard_reformatter.tray import build_tray, _make_icon_image; _make_icon_image(); print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add clipboard_reformatter/tray.py
git commit -m "Add pystray tray icon with Enabled toggle and Quit"
```

---

### Task 5: Entry point with startup probe

**Files:**
- Create: `clipboard_reformatter/__main__.py`

- [ ] **Step 1: Write `__main__.py`**

Create `clipboard_reformatter/__main__.py`:

```python
import sys
import tkinter
import tkinter.messagebox

import pyperclip

from clipboard_reformatter.tray import build_tray
from clipboard_reformatter.watcher import ClipboardWatcher


def _show_startup_error(message: str) -> None:
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showerror(
        "Clipboard Reformatter",
        f"Cannot access clipboard:\n\n{message}",
    )
    root.destroy()


def main() -> int:
    # Startup probe: a single clipboard read. If this fails, surface the error
    # in a dialog and exit non-zero. After this point, clipboard errors only
    # log to stderr.
    try:
        pyperclip.paste()
    except Exception as e:
        _show_startup_error(str(e))
        return 1

    watcher = ClipboardWatcher()
    watcher.start()
    icon = build_tray(watcher)
    icon.run()  # blocks until the Quit menu item stops the icon
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke-import the module**

```bash
uv run python -c "from clipboard_reformatter.__main__ import main; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 3: Verify the script entry point resolves**

```bash
uv run clipboard-reformatter --help 2>&1 | head -5 || true
```

This will actually launch the app, not print help (we have no CLI args). So instead verify the entry point exists by importing:

```bash
uv run python -c "import importlib.metadata as m; eps = m.entry_points(group='console_scripts'); print([e.name for e in eps if e.name == 'clipboard-reformatter'])"
```

Expected: `['clipboard-reformatter']`.

- [ ] **Step 4: Manual end-to-end test (developer machine, X11)**

This is a manual step — there is no automated way to verify a tray icon and clipboard interaction.

1. Run: `uv run clipboard-reformatter`
2. Confirm the tray icon appears (under GNOME, AppIndicator extension must be enabled).
3. Copy this exact string somewhere (note the trailing spaces): `hello   `
4. Paste — expected: `hello` (trailing spaces stripped).
5. Copy a multi-line block with trailing spaces; paste; verify all lines stripped, blank lines preserved.
6. Click the tray icon → uncheck **Enabled**. Copy `goodbye   `. Paste — expected: `goodbye   ` (unchanged).
7. Re-enable. Copy something with trailing spaces; verify it strips again.
8. Click tray icon → **Quit**. Process should exit cleanly.
9. Confirm no stderr spam during normal operation.

If anything fails, fix and re-test before committing.

- [ ] **Step 5: Commit**

```bash
git add clipboard_reformatter/__main__.py
git commit -m "Add entry point with startup clipboard probe"
```

---

### Task 6: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# clipboard-reformatter

A small Linux/macOS systray app that strips trailing spaces from every line of
any text copied to the clipboard.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- **Linux only:** `xclip` or `xsel` (`sudo apt install xclip`)
- **GNOME only:** the [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/)
  extension, otherwise the tray icon will not appear.

## Install / Run

```bash
uv sync
uv run clipboard-reformatter
```

## Usage

The icon appears in the system tray / status bar. Anything you copy to the
clipboard has trailing spaces stripped from each line, in place.

Menu:
- **Enabled** — toggle stripping on/off.
- **Quit** — exit the app.

If the clipboard cannot be accessed at startup (e.g. `xclip` not installed),
a dialog with the error appears and the app exits.

## Development

```bash
uv sync
uv run pytest
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Add README"
```

---

## Self-Review

**Spec coverage:**
- Strip spaces only at end of lines → Task 2 (regex `r' +$'`, MULTILINE).
- Linux + macOS support → Task 1 deps (pyperclip + pystray are cross-platform); Task 6 README documents Linux extras.
- Auto-watch clipboard → Task 3 polling loop.
- Systray with Enabled toggle + Quit → Task 4 menu.
- Startup probe → message dialog → exit non-zero → Task 5 `main()`.
- Runtime errors logged to stderr → Task 3 `_run()` exception handlers.
- `last_seen = cleaned` to avoid reprocessing own writes → Task 3 `_tick()`.
- pyproject with `clipboard-reformatter` script → Task 1.
- Unit tests for the pure reformat function → Task 2.
- Out of scope (Wayland, Windows, hotkeys, persistence, autostart) — correctly NOT in any task.

**Placeholder scan:** No TBDs, no "implement later", no "similar to Task N", no vague error-handling. All code blocks are complete.

**Type/name consistency:**
- `strip_trailing_spaces` — same name in `reformat.py`, tests, and `watcher.py`. ✓
- `ClipboardWatcher` — `start()`, `stop()`, `set_enabled()`, `enabled` property — same in `watcher.py`, `tray.py`, `__main__.py`. ✓
- `build_tray(watcher)` — same in `tray.py` and `__main__.py`. ✓

No issues found.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-30-clipboard-reformatter.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
