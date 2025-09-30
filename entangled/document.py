from textwrap import indent
from typing import Optional, Union, Iterable, Any, override
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatchmethod
from itertools import chain
from pathlib import PurePath

from .config import Language, AnnotationMethod, config
from .properties import Property, get_attribute
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
    def __getitem__(self, key):
        raise NotImplementedError(f"Invalid key: {type(key)}")

    @__getitem__.register
    def _(self, key: ReferenceId) -> CodeBlock:
        return self.map[key]

    @__getitem__.register
    def _(self, key: str) -> Iterable[CodeBlock]:
        return self.by_name(key)
