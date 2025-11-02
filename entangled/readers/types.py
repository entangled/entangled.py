from collections.abc import Callable, Generator
import functools

from .text_location import TextLocation
from .peekable import Peekable
from ..document import Content, RawContent


type InputToken = tuple[TextLocation, str]
type InputStream = Peekable[InputToken]
type Reader[OutputToken, Result] = Callable[[InputStream], Generator[OutputToken, None, Result]]
type RawMarkdownStream[Result] = Generator[RawContent, None, Result]
type MarkdownStream[Result] = Generator[Content, None, Result]


def map_reader[Out, T, U](f: Callable[[T], U], reader: Reader[Out, T]) -> Reader[Out, U]:
    def mapped(input: InputStream) -> Generator[Out, None, U]:
        x = yield from reader(input)
        return f(x)
    return mapped
