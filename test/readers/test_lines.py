from pathlib import PurePath
from entangled.readers.lines import lines
from entangled.readers.peekable import Peekable
from entangled.readers.types import InputStream


def test_lines():
    def collect(lst: InputStream) -> list[str]:
        return list(map(lambda x: x[1], lst))

    assert isinstance(lines(PurePath("-"), ""), Peekable)

    assert collect(lines(PurePath("-"), "")) == [""]
    assert collect(lines(PurePath("-"), "\n")) == ["\n", ""]
    assert collect(lines(PurePath("-"), "a\nb")) == ["a\n", "b"]
    assert collect(lines(PurePath("-"), "a\nb\n")) == ["a\n", "b\n", ""]
    assert collect(lines(PurePath("-"), "a\r\nb\r\n")) == ["a\r\n", "b\r\n", ""]
