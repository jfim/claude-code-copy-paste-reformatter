import pystray
from PIL import Image, ImageDraw

from claude_code_copy_paste_reformatter.watcher import ClipboardWatcher

ICON_SIZE = 64


def _make_icon_image() -> Image.Image:
    """Create a simple 64x64 icon: dark background with a light 'C' shape."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    # A thick arc that reads as a 'C' for clipboard.
    draw.arc(
        (10, 10, ICON_SIZE - 10, ICON_SIZE - 10),
        start=40,
        end=320,
        fill=(220, 220, 220, 255),
        width=8,
    )
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
        name="claude-code-copy-paste-reformatter",
        icon=_make_icon_image(),
        title="Clipboard Reformatter",
        menu=menu,
    )
