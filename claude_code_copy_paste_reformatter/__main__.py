import sys
import tkinter
import tkinter.messagebox

import pyperclip

from claude_code_copy_paste_reformatter.tray import build_tray
from claude_code_copy_paste_reformatter.watcher import ClipboardWatcher


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
