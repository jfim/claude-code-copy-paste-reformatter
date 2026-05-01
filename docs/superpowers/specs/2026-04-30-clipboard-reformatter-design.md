# Clipboard Reformatter — Design

## Purpose

A small Linux background app that watches the clipboard and automatically strips
trailing spaces from every line of any text copied to it. Lives in the system
tray with a minimal menu (toggle on/off, quit).

## Scope

- Text clipboard only. Non-text or empty clipboards are ignored.
- Strip **spaces only** at end of lines: `re.sub(r' +$', '', line, flags=re.MULTILINE)`.
- Leading whitespace, blank lines, tabs, and the trailing newline (if any) are preserved.

## Platform

Supported: **Linux (X11)** and **macOS**.

- **Linux / X11** (developer is on Ubuntu GNOME + X11):
  - `xclip` (or `xsel`) — pyperclip shells out to it.
  - GNOME **AppIndicator Support** extension — otherwise the tray icon will not appear under GNOME.
- **macOS**:
  - No extra system deps — pyperclip uses built-in `pbcopy`/`pbpaste`; pystray uses the native status bar.

Wayland is out of scope for v1.

## Stack

- Python 3.11+
- `uv` for project/dependency management
- `pyperclip` — clipboard read/write
- `pystray` — system tray / macOS status bar icon and menu
- `Pillow` — generate the tray icon image
- `tkinter` (stdlib) — for the startup error message box (cross-platform)
- Standard `threading` — background poll loop
- `pytest` — unit tests for the pure reformat function

## Architecture

Three small modules with clear boundaries:

```
clipboard_reformatter/
├── __main__.py     # entry point: wire watcher + tray, run
├── reformat.py     # pure: strip_trailing_spaces(text) -> text
├── watcher.py      # ClipboardWatcher: polls clipboard in a thread
└── tray.py         # build_tray(watcher): pystray icon + menu
```

### `reformat.py`
Pure function, no I/O. Trivial to unit test.

```python
def strip_trailing_spaces(text: str) -> str:
    return re.sub(r' +$', '', text, flags=re.MULTILINE)
```

### `watcher.py`
- `ClipboardWatcher` owns a daemon thread and a `threading.Event` for enable/disable.
- Poll interval: 300ms.
- State: `last_seen` — the last clipboard string we observed (after our own writes).
- Loop:
  1. If disabled, sleep and continue.
  2. `current = pyperclip.paste()`.
  3. If `current == last_seen` or `current` is empty → continue.
  4. `cleaned = strip_trailing_spaces(current)`.
  5. If `cleaned != current`: `pyperclip.copy(cleaned)`.
  6. `last_seen = cleaned`.
- The `last_seen = cleaned` step prevents the watcher from reprocessing its own writes.
- API: `start()`, `stop()`, `set_enabled(bool)`, `enabled` property.

### `tray.py`
- Generates a small PIL image for the icon (simple colored square — fine for v1).
- Builds a `pystray.Menu` with:
  - **Enabled** — checkable item, toggles `watcher.set_enabled(...)`.
  - **Quit** — stops the watcher and calls `icon.stop()`.

### `__main__.py`
```python
def main():
    # Startup probe: one clipboard read. If this fails, show a dialog and exit.
    try:
        pyperclip.paste()
    except Exception as e:
        import tkinter, tkinter.messagebox
        root = tkinter.Tk(); root.withdraw()
        tkinter.messagebox.showerror("Clipboard Reformatter", f"Cannot access clipboard:\n\n{e}")
        sys.exit(1)

    watcher = ClipboardWatcher()
    watcher.start()
    icon = build_tray(watcher)
    icon.run()  # blocks; pystray owns the main thread
```

## Data Flow

```
user copies text
      │
      ▼
   X11 clipboard
      │  (polled every 300ms)
      ▼
 ClipboardWatcher ── reads ──► pyperclip.paste()
      │
      ▼
strip_trailing_spaces()
      │
      ▼
  changed? ── no ──► update last_seen, done
      │ yes
      ▼
pyperclip.copy(cleaned)  → X11 clipboard
      │
      ▼
last_seen = cleaned   (prevents re-processing our own write)
```

## Error Handling

**Startup probe.** Before starting the watcher thread or showing the tray icon,
`__main__.py` performs a single `pyperclip.paste()` call. If it raises, we show
a modal error dialog (via `tkinter.messagebox.showerror`) containing the
exception message — typically pointing the user at missing `xclip`/`xsel` on
Linux — and exit with a non-zero status. This makes first-run setup problems
immediately visible instead of leaving a silent tray icon.

**Runtime.** Once past the startup probe, exceptions inside the polling loop
are logged to stderr and the loop continues:

- `pyperclip.PyperclipException`: log and retry on next tick.
- Any other exception: log and continue. The watcher must not die silently —
  a tray app that has stopped working is worse than one that is visibly off.

## Testing

- `tests/test_reformat.py` — unit tests for `strip_trailing_spaces`:
  - trims trailing spaces from a single line
  - leaves leading spaces alone
  - preserves blank lines
  - leaves tabs alone (only spaces are stripped)
  - preserves the trailing newline (or its absence)
  - no-op when there's nothing to strip
- The watcher and tray are integration-only and not unit tested in v1.

## Project Layout

```
clipboard-reformatter/
├── pyproject.toml
├── README.md
├── docs/superpowers/specs/2026-04-30-clipboard-reformatter-design.md
├── clipboard_reformatter/
│   ├── __init__.py
│   ├── __main__.py
│   ├── reformat.py
│   ├── watcher.py
│   └── tray.py
└── tests/
    └── test_reformat.py
```

`pyproject.toml` declares a `clipboard-reformatter` script entry point so
`uv run clipboard-reformatter` launches the app.

## Out of Scope (v1)

- Wayland support
- Windows support
- Hotkey trigger / manual mode
- Other reformat rules (case, JSON, etc.)
- Persisting "enabled" state across restarts
- Autostart on login
