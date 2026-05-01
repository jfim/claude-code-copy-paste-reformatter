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

- Target: Linux / X11 (developer is on Ubuntu GNOME + X11).
- System dependencies the user must have:
  - `xclip` (or `xsel`) — pyperclip shells out to it.
  - GNOME **AppIndicator Support** extension — otherwise the tray icon will not appear under GNOME.

## Stack

- Python 3.11+
- `uv` for project/dependency management
- `pyperclip` — clipboard read/write
- `pystray` — system tray icon and menu
- `Pillow` — generate the tray icon image
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

- `pyperclip.PyperclipException` (e.g. xclip missing): log to stderr, sleep,
  retry on next tick. Don't crash the tray.
- Any other exception inside the loop: log and continue. The watcher must not
  die silently — a tray app that has stopped working is worse than one that is
  visibly off.

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
- Hotkey trigger / manual mode
- Other reformat rules (case, JSON, etc.)
- Persisting "enabled" state across restarts
- Autostart on login
