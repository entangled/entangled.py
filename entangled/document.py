from typing import Union, Optional, Iterable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatchmethod
import mawk

from .config import Language
from .properties import Property
from .error import InternalError, CyclicReference


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


Content = Union[PlainText, ReferenceId]


@dataclass
class TextLocation:
    filename: str
    line_number: int = 0


@dataclass
class CodeBlock:
    language: Language
    properties: list[Property]
    indent: str
    source: str
    origin: TextLocation


@dataclass
class ReferenceMap:
    map: dict[ReferenceId, CodeBlock] = field(default_factory=dict)
    index: defaultdict[str, list[ReferenceId]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def names(self) -> Iterable[str]:
        return self.index.keys()

    def by_name(self, n: str) -> Iterable[CodeBlock]:
        return (self.map[r] for r in self.index[n])

    def new_id(self, filename: str, name: str) -> ReferenceId:
        c = length(filter(lambda r: r.file == filename, self.index[name]))
        return ReferenceId(name, filename, c)

    def __setitem__(self, key: ReferenceId, value: CodeBlock):
        if key in self.map:
            raise InternalError("Duplicate key in ReferenceMap", [key])
        self.map[key] = value
        self.index[key.name].append(key)

    @singledispatchmethod
    def __getitem__(self, key):
        raise NotImplementedError(f"Invalid key: {type(key)}")

    @__getitem__.register
    def _(self, key: ReferenceId) -> CodeBlock:
        return self.map[key]

    @__getitem__.register
    def _(self, key: str) -> Iterable[CodeBlock]:
        return self.by_name(key)


def retrieve_markdown(reference_map: ReferenceMap, content: list[Content]) -> str:
    def get(item: Content):
        match item:
            case PlainText(s):
                return s
            case ReferenceId():
                return reference_map[item].source

    return "\n".join(get(i) for i in content) + "\n"
