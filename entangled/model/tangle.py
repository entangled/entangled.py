from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import PurePath

import re
import os
from typing import override


from ..config import AnnotationMethod
from ..iterators.lines import lines
from ..errors.user import UserError
from ..text_location import TextLocation

from .reference_map import ReferenceMap
from .reference_id import ReferenceId
from .reference_name import ReferenceName


@dataclass
class CyclicReference(UserError):
    ref_name: str
    cycle: list[str]

    @override
    def __str__(self):
        cycle_str = " -> ".join(self.cycle)
        return f"Cyclic reference in <<{self.ref_name}>>: {cycle_str}"


@dataclass
class MissingReference(UserError):
    origin: TextLocation
    ref_name: ReferenceName

    @override
    def __str__(self):
        return f"{self.origin}: Missing reference `{self.ref_name}`"


@dataclass
class MissingLanguageError(UserError):
    origin: TextLocation

    @override
    def __str__(self):
        return f"{self.origin}: Missing language for code block."


@dataclass
class Visitor[T]:
    _visited: dict[T, int] = field(default_factory=dict)

    def in_order(self) -> list[T]:
        return [k for k, _ in sorted(self._visited.items(), key=lambda kv: kv[1])]

    @contextmanager
    def visit(self, x: T):
        if x in self._visited:
            raise CyclicReference(str(x), [str(r) for r in self.in_order()])
        self._visited[x] = len(self._visited)
        yield
        del self._visited[x]


type Deps = set[PurePath]
type Tangler = Callable[[Tangler, Deps, ReferenceId, bool, bool], Iterator[str]]


def indent(prefix: str, g: Iterator[str]) -> Iterator[str]:
    return map(lambda line: "" if not line else prefix + line, g)


def naked_tangler(refs: ReferenceMap) -> Tangler:
    visitor: Visitor[ReferenceId] = Visitor()

    def tangler(
        recur: Tangler, deps: set[PurePath], ref: ReferenceId, skip_header: bool, _: bool
    ) -> Generator[str]:
        code_block = refs[ref]
        deps.add(code_block.origin.filename)

        if code_block.header and not skip_header:
            yield code_block.header

        with visitor.visit(ref):
            for line in lines(code_block.source):
                if m := re.match(r"^(?P<indent>\s*)<<(?P<refname>[\w:-]+)>>\s*$", line.rstrip()):
                    ref_name = ReferenceName.from_str(m["refname"], code_block.namespace)
                    if not refs.has_name(ref_name):
                        raise MissingReference(code_block.origin, ref_name)
                    ref_lst = refs.select_by_name(ref_name)
                    yield from indent(m["indent"], recur(recur, deps, ref_lst[0], False, True))
                    for ref in ref_lst[1:]:
                        yield from indent(m["indent"], recur(recur, deps, ref, False, False))
                else:
                    yield line

    return tangler


def annotated_tangler(refs: ReferenceMap) -> Tangler:
    naked = naked_tangler(refs)

    def tangler(
        recur: Tangler, deps: set[PurePath], ref: ReferenceId, skip_header: bool, first: bool
    ) -> Generator[str]:
        code_block = refs[ref]
        if code_block.language is None:
            raise MissingLanguageError(code_block.origin)

        language = code_block.language
        open_comment = language.comment.open
        close_comment = (
            "" if language.comment.close is None else f" {language.comment.close}"
        )

        if code_block.header and not skip_header:
            yield code_block.header
        ref_count_str = "init" if first else str(ref.ref_count)
        yield f"{open_comment} ~/~ begin <<{ref.file.as_posix()}#{ref.name}>>[{ref_count_str}]{close_comment}{os.linesep}"
        yield from naked(recur, deps, ref, True, first)
        yield f"{open_comment} ~/~ end{close_comment}{os.linesep}"

    return tangler


tanglers = {
    AnnotationMethod.NAKED: naked_tangler,
    AnnotationMethod.STANDARD: annotated_tangler,
    AnnotationMethod.SUPPLEMENTED: annotated_tangler,
}


def tangle_ref(
    refs: ReferenceMap,
    name: ReferenceName,
    annotation: AnnotationMethod = AnnotationMethod.STANDARD,
) -> tuple[str, set[PurePath]]:
    if not refs.has_name(name):
        raise KeyError(name)
    tangler = tanglers[annotation](refs)
    deps: set[PurePath] = set()
    out = ""

    ref_lst = refs.select_by_name(name)
    for line in tangler(tangler, deps, ref_lst[0], False, True):
        out += line
    for ref in ref_lst[1:]:
        for line in tangler(tangler, deps, ref, False, False):
            out += line

    return out, deps
