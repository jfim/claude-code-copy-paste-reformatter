import re

_LINE = re.compile(r"^  (.*?) *$", flags=re.MULTILINE)
_TRAILING_SPACES = re.compile(r" +$", flags=re.MULTILINE)


def strip_trailing_spaces(text: str) -> str:
    """Strip up to two leading spaces and all trailing spaces from each line.

    Tabs and other whitespace are left untouched. Line endings and blank
    lines are preserved.
    """
    text = _LINE.sub(r"\1", text)
    return _TRAILING_SPACES.sub("", text)
