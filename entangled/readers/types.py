from collections.abc import Callable, Generator
from typing import cast

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


def run_generator[O, R](g: Generator[O, None, R]) -> tuple[list[O], R]:
    result: R | None = None

    def h() -> Generator[O]:
        nonlocal result
        result = yield from g

    out = list(h())

    return out, cast(R, result)
