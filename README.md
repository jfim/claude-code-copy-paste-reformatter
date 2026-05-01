# claude-code-copy-paste-reformatter

A small Linux/macOS systray app that strips trailing spaces from every line of
any text copied to the clipboard.

## Requirements

- Python 3.12+ (on Linux, the system Python; see note below)
- [uv](https://docs.astral.sh/uv/)
- **Linux only:** `xclip` or `xsel` (`sudo apt install xclip`)
- **GNOME only:** the [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/)
  GNOME Shell extension, plus `gir1.2-ayatanaappindicator3-0.1` and
  `python3-gi` (`sudo apt install gir1.2-ayatanaappindicator3-0.1 python3-gi`).
  Without these the tray icon falls back to an XEMBED icon that GNOME
  cannot route clicks to.

## Install / Run

On Linux the venv must be able to see the system `python3-gi`, which means
matching the system Python version and using `--system-site-packages`:

```bash
uv venv --system-site-packages --python /usr/bin/python3
uv sync
uv run claude-code-copy-paste-reformatter
```

On macOS, `uv sync && uv run claude-code-copy-paste-reformatter` is enough — no system
packages or `--system-site-packages` needed.

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
