import re

_TRAILING_SPACES = re.compile(r" +$", flags=re.MULTILINE)


def strip_trailing_spaces(text: str) -> str:
    """Remove trailing spaces (U+0020) from every line of `text`.

    Tabs and other whitespace are left untouched. Line endings and blank
    lines are preserved.
    """
    return _TRAILING_SPACES.sub("", text)
