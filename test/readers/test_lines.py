from pathlib import PurePath
from entangled.readers.lines import lines, numbered_lines
from entangled.readers.peekable import Peekable
from entangled.text_location import TextLocation


def test_lines():
    def ll(inp: str):
        return list(lines(inp))

    assert ll("") == [""]
    assert ll("\n") == ["\n", ""]
    assert ll("a\nb") == ["a\n", "b"]
    assert ll("a\nb\n") == ["a\n", "b\n", ""]
    assert ll("a\r\nb\r\n") == ["a\r\n", "b\r\n", ""]


def test_numbered_lines():
    assert isinstance(numbered_lines(PurePath("-"), ""), Peekable)
    assert list(numbered_lines(PurePath("-"), "a\nb\n")) == [
        (TextLocation(PurePath("-"), 1), "a\n"),
        (TextLocation(PurePath("-"), 2), "b\n"),
        (TextLocation(PurePath("-"), 3), "")
    ]
