from collections.abc import Callable, Generator

from ..text_location import TextLocation
from ..iterators.peekable import Peekable
from ..model import Content, RawContent


type InputToken = tuple[TextLocation, str]
type InputStream = Peekable[InputToken]
type Reader[OutputToken, Result] = Callable[[InputStream], Generator[OutputToken, None, Result]]
type RawMarkdownStream[Result] = Generator[RawContent, None, Result]
type MarkdownStream[Result] = Generator[Content, None, Result]


