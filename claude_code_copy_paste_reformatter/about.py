import sys
from importlib.metadata import PackageNotFoundError, version

APP_NAME = "Clipboard Reformatter"
APP_COMMENTS = "Strips trailing spaces from clipboard text pasted out of Claude Code."
APP_WEBSITE = "https://github.com/jfim/claude-code-copy-paste-reformatter"


def _app_version() -> str:
    try:
        return version("claude-code-copy-paste-reformatter")
    except PackageNotFoundError:
        return "unknown"


def show_about() -> None:
    if sys.platform == "darwin":
        _show_about_macos()
    elif sys.platform.startswith("linux"):
        _show_about_linux()
    elif sys.platform == "win32":
        _show_about_windows()
    else:
        print(f"{APP_NAME} {_app_version()} — {APP_COMMENTS}")


def _show_about_macos() -> None:
    from AppKit import NSAlert, NSAlertFirstButtonReturn, NSApplication, NSWorkspace
    from Foundation import NSURL

    NSApplication.sharedApplication()
    alert = NSAlert.alloc().init()
    alert.setMessageText_(f"{APP_NAME} {_app_version()}")
    alert.setInformativeText_(f"{APP_COMMENTS}\n\n{APP_WEBSITE}")
    alert.addButtonWithTitle_("OK")
    alert.addButtonWithTitle_("Open Website")
    response = alert.runModal()
    if response == NSAlertFirstButtonReturn + 1:
        NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(APP_WEBSITE))


def _show_about_linux() -> None:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    dialog = Gtk.AboutDialog()
    dialog.set_program_name(APP_NAME)
    dialog.set_version(_app_version())
    dialog.set_comments(APP_COMMENTS)
    dialog.set_website(APP_WEBSITE)
    dialog.set_website_label("Project on GitHub")
    dialog.set_license_type(Gtk.License.MIT_X11)
    dialog.run()
    dialog.destroy()


def _show_about_windows() -> None:
    import ctypes

    text = f"{APP_NAME} {_app_version()}\n\n{APP_COMMENTS}\n\n{APP_WEBSITE}"
    ctypes.windll.user32.MessageBoxW(None, text, f"About {APP_NAME}", 0x40)
