from typing import Optional, Union, Iterable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatchmethod
from itertools import chain

from .config import Language, AnnotationMethod, config
from .properties import Property, get_attribute
from .errors.internal import InternalError
from .text_location import TextLocation


def length(iter: Iterable[Any]) -> int:
    return sum(1 for _ in iter)


@dataclass
class ReferenceId:
    name: str
    file: str
    ref_count: int

    def __hash__(self):
        return hash((self.name, self.file, self.ref_count))


@dataclass
class PlainText:
    content: str


@dataclass
class CodeBlock:
    properties: list[Property]
    indent: str
    source: str
    origin: TextLocation
    language: Optional[Language] = None
    header: Optional[str] = None
    mode: Optional[int] = None


Content = Union[PlainText, ReferenceId]
RawContent = Union[PlainText, CodeBlock]


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

    def new_id(self, filename: str, name: str) -> ReferenceId:
        c = length(filter(lambda r: r.file == filename, self.index[name]))
        return ReferenceId(name, filename, c)

    def __setitem__(self, key: ReferenceId, value: CodeBlock):
        if key in self.map:
            raise InternalError("Duplicate key in ReferenceMap", [key])
        self.map[key] = value
        self.index[key.name].append(key)

    def __contains__(self, key: str) -> bool:
        return key in self.index

    @singledispatchmethod
    def __getitem__(self, key):
        raise NotImplementedError(f"Invalid key: {type(key)}")

    @__getitem__.register
    def _(self, key: ReferenceId) -> CodeBlock:
        return self.map[key]

    @__getitem__.register
    def _(self, key: str) -> Iterable[CodeBlock]:
        return self.by_name(key)
