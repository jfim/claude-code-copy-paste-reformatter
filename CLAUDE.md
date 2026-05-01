# Claude Code Copy-Paste Reformatter

Tiny systray app: polls the clipboard, strips trailing spaces from each line in place. macOS + Linux primary; Windows has a fallback path but isn't a primary target.

## Layout

- `clipboard.py` — `ClipboardBackend` protocol + per-platform implementations:
  `_NSPasteboardBackend` (macOS, polls cheap `changeCount` integer),
  `_GtkClipboardBackend` (Linux, `Gtk.Clipboard.wait_for_text`),
  `_PyperclipBackend` (fallback). `make_clipboard()` picks the right one.
- `watcher.py` — `ClipboardWatcher` daemon thread, polls every 300ms, calls
  `strip_trailing_spaces` and writes back only on change. Backends remember
  their own writes so the watcher never reprocesses its output.
- `reformat.py` — pure string transformation (`strip_trailing_spaces`).
- `tray.py` — pystray icon and menu.
- `about.py` — native About dialogs per platform.
- `__main__.py` — entry point.

## Conventions

- **No new GUI deps.** About dialogs deliberately reuse AppKit / Gtk that the
  clipboard backends already pull in. Don't introduce Qt or Tk.
- **300ms poll interval is intentional.** Humans can copy-paste in under
  300ms (Ctrl+C → tab switch → Ctrl+V), so this is the floor, not a
  conservative default. Don't bump it without discussion.
- **Linux venv quirk:** GTK needs the system `python3-gi`, so the venv must
  be created with `--system-site-packages` against the system Python. See
  README.

## Commands

- `uv run pytest` — run tests
- `uv run ruff check claude_code_copy_paste_reformatter/` — lint
- `uv run claude-code-copy-paste-reformatter` — launch the tray app
