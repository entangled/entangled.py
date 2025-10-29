from dataclasses import dataclass
from collections.abc import Callable

import re

from .text_location import TextLocation
from .types import InputStream
from ..errors.user import ParseError


@dataclass
class DelimitedToken:
    origin: TextLocation
    open_line: str
    open_match: re.Match[str]
    content: str
    close_line: str
    close_match: re.Match[str]

    @property
    def string(self) -> str:
        """
        Reconstructs the original input string.
        """
        return self.open_line + self.content + self.close_line
    

def delimited_token_getter(open: str, close: str) -> Callable[[InputStream], DelimitedToken | None]:
    """
    Creates a function that reads a given `DelimitedToken` from
    the input stream or returns `None` if the stream does not start
    with a match for the opening pattern.

    Args:
        open: a regex on which the token is triggered
        close: a regex on which the enclosed content is closed

    Returns:
        A `DelimitedToken` object containing the text location of
        the token, the `re.Match` objects for both opening and closing
        patterns, and the contained text.

    The first line in the input stream is peeked. If it does not match
    the `open` expression, `None` is returned. Otherwise the lines
    upto and including the closing expression are consumed.
    """
    open_pattern = re.compile(open)
    close_pattern = re.compile(close)

    def get(input: InputStream) -> DelimitedToken | None:
        if not input:
            return None
        
        origin, open_line = input.peek()
        open_match = open_pattern.match(open_line.rstrip())
        if not open_match:
            return None

        _ = next(input)
        content = ""

        # We consumed the single buffered token, so we can
        # iterate directly from the inner iterator.
        for _, line in input.iterator:
            close_match = close_pattern.match(line.rstrip())
            if not close_match:
                content += line
            else:
                close_line = line
                return DelimitedToken(
                    origin, open_line, open_match,
                    content, close_line, close_match)

        raise ParseError(origin, "unexpected end of file")
            
    return get
