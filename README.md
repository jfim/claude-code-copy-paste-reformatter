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
