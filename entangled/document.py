from typing import Union, Optional, Iterable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatchmethod
from itertools import chain
from pathlib import Path
import mawk

from .config import Language, AnnotationMethod, config
from .properties import Property, get_attribute
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
    targets: set[str] = field(default_factory=set)

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

    @singledispatchmethod
    def get_decorated(self, ref):
        raise NotImplementedError(f"Invalid key: {type(ref)}")

    @get_decorated.register
    def _(self, ref: ReferenceId) -> list[str]:
        init = ref == self.index[ref.name][0]
        count = "init" if init else str(ref.ref_count)
        cb = self.map[ref]
        close_comment = (
            "" if cb.language.comment.close is None else f" {cb.language.comment.close}"
        )
        start = (
            f"{cb.language.comment.open} ~/~ begin <<{ref.file}#{ref.name}>>[{count}]"
        )
        end = f"{cb.language.comment.open} ~/~ end{close_comment}"
        match config.annotation:
            case AnnotationMethod.STANDARD:
                return [start + close_comment, cb.source, end]
            case AnnotationMethod.NAKED:
                return [cb.source]
            case AnnotationMethod.SUPPLEMENTED:
                if config.annotation_format is None:
                    return [start + close_comment, cb.source, end]

                supplement = config.annotation_format.format(
                    file=cb.origin.filename, linenumber=cb.origin.line_number
                )
                return [
                    start + " " + supplement + close_comment,
                    cb.source,
                    end,
                ]

    @get_decorated.register
    def _(self, ref_name: str) -> Iterable[str]:
        return chain.from_iterable(
            self.get_decorated(ref) for ref in self.index[ref_name]
        )
