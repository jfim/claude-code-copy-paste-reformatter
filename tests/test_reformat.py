from claude_code_copy_paste_reformatter.reformat import strip_trailing_spaces


def test_strips_trailing_spaces_from_single_line():
    assert strip_trailing_spaces("hello   ") == "hello"


def test_leaves_leading_spaces_alone():
    assert strip_trailing_spaces("    hello") == "    hello"


def test_strips_per_line_in_multiline_text():
    assert strip_trailing_spaces("a   \nb  \nc") == "a\nb\nc"


def test_preserves_blank_lines():
    assert strip_trailing_spaces("a\n\nb") == "a\n\nb"


def test_does_not_strip_tabs():
    # Spec says spaces only.
    assert strip_trailing_spaces("hello\t\t") == "hello\t\t"


def test_preserves_trailing_newline():
    assert strip_trailing_spaces("hello   \n") == "hello\n"


def test_preserves_absence_of_trailing_newline():
    assert strip_trailing_spaces("hello   ") == "hello"


def test_noop_when_nothing_to_strip():
    assert strip_trailing_spaces("hello\nworld") == "hello\nworld"


def test_empty_string():
    assert strip_trailing_spaces("") == ""


def test_line_of_only_spaces_becomes_empty():
    assert strip_trailing_spaces("a\n   \nb") == "a\n\nb"
