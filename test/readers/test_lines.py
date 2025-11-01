from pathlib import PurePath
from entangled.readers.lines import lines, numbered_lines
from entangled.readers.peekable import Peekable
from entangled.readers.text_location import TextLocation


def test_lines():
    assert lines("") == [""]
    assert lines("\n") == ["\n", ""]
    assert lines("a\nb") == ["a\n", "b"]
    assert lines("a\nb\n") == ["a\n", "b\n", ""]
    assert lines("a\r\nb\r\n") == ["a\r\n", "b\r\n", ""]


def test_numbered_lines():
    assert isinstance(numbered_lines(PurePath("-"), ""), Peekable)
    assert list(numbered_lines(PurePath("-"), "a\nb\n")) == [
        (TextLocation(PurePath("-"), 1), "a\n"),
        (TextLocation(PurePath("-"), 2), "b\n")
    ]
