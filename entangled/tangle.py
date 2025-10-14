from typing import TypeVar, Generic, override
from dataclasses import dataclass, field
from textwrap import indent
from contextlib import contextmanager
from copy import copy
from pathlib import PurePath

import re
import mawk

from .config import AnnotationMethod
from .text_location import TextLocation
from .document import (
    ReferenceMap,
    ReferenceId,
    CodeBlock,
)
from .errors.user import CyclicReference, MissingReference
from .config import config


T = TypeVar("T")


@dataclass
class Visitor(Generic[T]):
    _visited: dict[T, int] = field(default_factory=dict)

    def in_order(self) -> list[T]:
        return [k for k, _ in sorted(self._visited.items(), key=lambda kv: kv[1])]

    @contextmanager
    def visit(self, x: T):
        if x in self._visited:
            raise CyclicReference(str(x), list(map(str, self.in_order())))
        self._visited[x] = len(self._visited)
        yield
        del self._visited[x]


@dataclass
class Tangler(mawk.RuleSet):
    refs: ReferenceMap
    ref: ReferenceId
    init: bool
    visited: Visitor[str]
    deps: set[PurePath] = field(init=False)
    cb: CodeBlock = field(init=False)
    location: TextLocation = field(init=False)

    def __post_init__(self):
        self.cb = self.refs.get_codeblock(self.ref)
        self.location = copy(self.cb.origin)
        self.deps = { self.cb.origin.filename }

    @mawk.always
    def lineno(self, _):
        self.location.line_number += 1

    @override
    def on_begin(self) -> list[str]:
        if self.cb.header is not None:
            return [self.cb.header]
        else:
            return []

    @mawk.on_match(r"^(?P<indent>\s*)<<(?P<refname>[\w-]+)>>\s*$")
    def on_noweb(self, m: re.Match[str]) -> list[str]:
        try:
            result, deps = tangle_ref(self.refs, m["refname"], type(self), self.visited)

        except KeyError:
            raise MissingReference(m["refname"], self.location)

        self.deps.update(deps)
        return [indent(result, m["indent"])]

    def tangle(self):
        return super().run(self.cb.source)


@dataclass
class AnnotatedTangler(Tangler):
    close_comment: str = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        assert self.cb.language
        self.close_comment = (
            ""
            if self.cb.language.comment.close is None
            else f" {self.cb.language.comment.close}"
        )

    @override
    def on_begin(self) -> list[str]:
        assert self.cb.language
        count = "init" if self.init else str(self.ref.ref_count)
        result: list[str] = []
        if self.cb.header is not None:
            result.append(self.cb.header)
        result.append(
            f"{self.cb.language.comment.open} ~/~ begin <<{self.ref.file.as_posix()}#{self.ref.name}>>[{count}]{self.close_comment}"
        )
        return result

    @override
    def on_eof(self):
        assert self.cb.language
        return [f"{self.cb.language.comment.open} ~/~ end{self.close_comment}"]


tanglers = {
    AnnotationMethod.NAKED: Tangler,
    AnnotationMethod.STANDARD: AnnotatedTangler,
    AnnotationMethod.SUPPLEMENTED: AnnotatedTangler,
}


def tangle_ref(
    refs: ReferenceMap,
    ref_name: str,
    annotation: type[Tangler] | AnnotationMethod | None = None,
    _visited: Visitor[str] | None = None,
) -> tuple[str, set[PurePath]]:
    if annotation is None:
        annotation = config.get.annotation

    if ref_name in refs.alias:
        ref_name = refs.alias[ref_name]

    if ref_name not in refs:
        raise KeyError(ref_name)
    v = _visited or Visitor()

    if isinstance(annotation, AnnotationMethod):
        tangler = tanglers[annotation]
    elif annotation is not None:
        tangler = annotation
    else:
        raise ValueError("impossible code path")

    with v.visit(ref_name):
        init = True
        result: list[str] = []
        deps: set[PurePath] = set()
        for ref in refs.index[ref_name]:
            t = tangler(refs, ref, init, v)
            result.append(t.tangle())
            deps.update(t.deps)
            init = False

    return "\n".join(result), deps
