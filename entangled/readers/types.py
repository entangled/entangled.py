from collections.abc import Callable, Generator

from .text_location import TextLocation
from .peekable import Peekable
from ..document import Content


type InputToken = tuple[TextLocation, str]
type InputStream = Peekable[InputToken]
type Reader[OutputToken, Result] = Callable[[InputStream], Generator[OutputToken, None, Result]]
type MarkdownStream[Result] = Generator[Content, None, Result]
