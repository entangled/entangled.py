"""
Generic machinery for weaving: transforming the Markdown source of a page,
code block by code block, into Markdown that renders well in some target.
"""

from collections.abc import Callable, Iterable, Iterator
from functools import partial, reduce, wraps
from itertools import chain
from pathlib import PurePath

from ..interface import Context, markdown
from ..iterators import numbered_lines
from ..model import Content, PlainText, ReferenceId, ReferenceMap, content_to_text


type ContentFilter = Callable[[ReferenceMap, Content], Iterable[Content]]
type CodeBlockFilter = Callable[[ReferenceMap, ReferenceId], Iterable[Content]]


def codeblock_filter(f: CodeBlockFilter) -> ContentFilter:
    """Lift a filter on code blocks to a filter on content, passing plain text
    through unchanged."""
    @wraps(f)
    def _filter(rm: ReferenceMap, c: Content) -> Iterable[Content]:
        match c:
            case PlainText():
                return [c]
            case ReferenceId():
                return f(rm, c)
    return _filter


def iter_bind[T, U](lst: Iterable[T], f: Callable[[T], Iterable[U]]) -> Iterator[U]:
    return chain.from_iterable(map(f, lst))


def compose_filter(a: ContentFilter, b: ContentFilter) -> ContentFilter:
    def _joined(rm: ReferenceMap, c: Content) -> Iterable[Content]:
        return iter_bind(a(rm, c), partial(b, rm))
    return _joined


def compose_filters(*args: ContentFilter) -> ContentFilter:
    """Compose filters left to right: the first filter is applied first."""
    identity: ContentFilter = lambda _, c: [c]
    return reduce(compose_filter, args, identity)


def transform_markdown(
    context: Context,
    text: str,
    *filters: ContentFilter,
    filename: PurePath = PurePath("-"),
    reference_map: ReferenceMap | None = None,
) -> Iterator[str]:
    """
    Read a Markdown document, pass its content through the given filters,
    and yield the resulting Markdown text.

    Filters may modify code blocks in the reference map in place. If no
    `reference_map` is given, a fresh one is used for this document only.
    """
    refs = ReferenceMap() if reference_map is None else reference_map
    content = markdown(context, refs, numbered_lines(filename, text))
    for c in iter_bind(content, partial(compose_filters(*filters), refs)):
        yield content_to_text(refs, c)[0]
