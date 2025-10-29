from collections.abc import Generator
from pathlib import PurePath

from .types import InputToken
from .text_location import TextLocation
from .peekable import peekable


@peekable
def lines(filename: PurePath, text: str) -> Generator[InputToken]:
    """
    Iterate the lines in a file. Doesn't strip newlines. Works with both
    Windows and Unix line endings.
    """
    location = TextLocation(filename)
    pos = 0
    while (next_pos := text.find("\n", pos)) != -1:
        yield (location, text[pos:next_pos + 1])
        pos = next_pos + 1
        location.increment()

    yield (location, text[pos:])
