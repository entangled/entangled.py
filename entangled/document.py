from textwrap import indent
from collections.abc import Iterable
from typing import override
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatchmethod
from pathlib import PurePath

from .config.language import Language
from .properties import Property
from .errors.internal import InternalError
from .text_location import TextLocation


def length[T](iter: Iterable[T]) -> int:
    return sum(1 for _ in iter)


@dataclass
class ReferenceId:
    name: str
    file: PurePath
    ref_count: int

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.file, self.ref_count))


@dataclass
class PlainText:
    content: str


@dataclass
class CodeBlock:
    properties: list[Property]
    indent: str
    open_line: str
    close_line: str
    source: str
    origin: TextLocation
    language: Language | None = None
    header: str | None = None
    mode: int | None = None

    @property
    def text(self) -> str:
        return self.open_line + "\n" + self.source + "\n" + self.close_line

    @property
    def indented_text(self) -> str:
        return indent(self.text, self.indent)


Content = PlainText | ReferenceId
RawContent = PlainText | CodeBlock


@dataclass
class ReferenceMap:
    """
    Members:
        `map`: maps references to actual code block content
        `index`: maps names to list of references
        `targets`: lists filenames; a target should be in `index`
    """

    map: dict[ReferenceId, CodeBlock] = field(default_factory=dict)
    index: defaultdict[str, list[ReferenceId]] = field(
        default_factory=lambda: defaultdict(list)
    )
    targets: set[str] = field(default_factory=set)
    alias: dict[str, str] = field(default_factory=dict)

    def names(self) -> Iterable[str]:
        return self.index.keys()

    def by_name(self, n: str) -> Iterable[CodeBlock]:
        if n not in self.index and n not in self.alias:
            raise AttributeError(name=n, obj=self)
        if n not in self.index:
            return self.by_name(self.alias[n])

        return (self.map[r] for r in self.index[n])

    def new_id(self, filename: PurePath, name: str) -> ReferenceId:
        c = length(filter(lambda r: r.file == filename, self.index[name]))
        return ReferenceId(name, filename, c)

    def __setitem__(self, key: ReferenceId, value: CodeBlock):
        if key in self.map:
            raise InternalError("Duplicate key in ReferenceMap", [key])
        self.map[key] = value
        self.index[key.name].append(key)

    def __contains__(self, key: str) -> bool:
        return key in self.index

    def get_codeblock(self, key: ReferenceId) -> CodeBlock:
        return self.map[key]

    @singledispatchmethod
    def __getitem__(self, key: ReferenceId | str) -> CodeBlock | Iterable[CodeBlock]:
        raise NotImplementedError(f"Invalid key: {type(key)}")

    @__getitem__.register
    def _(self, key: ReferenceId) -> CodeBlock:
        return self.map[key]

    @__getitem__.register
    def _(self, key: str) -> Iterable[CodeBlock]:
        return self.by_name(key)


def content_to_text(r: ReferenceMap, c: Content) -> str:
    """
    Reconstruct original plain text from a piece of content.

    Args:
        r: the reference map.
        c: the content.

    Returns:
        A string, usually not terminated by a newline.
    """
    match c:
        case PlainText(s):
            return s
        case ReferenceId():
            return r.get_codeblock(c).indented_text


def document_to_text(r: ReferenceMap, cs: Iterable[Content]) -> str:
    """
    Reconstruct original plain text content from a reference map and
    list of content.

    Args:
        r: the reference map.
        cs: a list of content.

    Returns:
        A string, including a final newline.

    Usually this is the reconstructed content of a Markdown file. Most
    editors have a convention to end a file with a newline, but this
    newline is usually stripped when we read a file.

    Context:
        In Python `"foo".splitlines()` gives the same as `"foo\n".splitlines()`,
        with the exception of `"\n".splitlines()` giving `['']`, while
        `"".splitlines()` returns `[]`.

        As an alternative, we could keep line endings by splitting with `keepends=True`,
        and joining with `"".join(...)`.
    """
    text = "\n".join(content_to_text(r, c) for c in cs)
    if text[-1] != "\n":
        return text + "\n"
    else:
        return text
