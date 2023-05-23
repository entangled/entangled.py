from typing import Optional, TypeVar, Generic
from dataclasses import dataclass, field
from textwrap import indent
from contextlib import contextmanager

import re
import mawk

from .document import ReferenceMap, AnnotationMethod
from .errors.user import CyclicReference
from .config import config


T = TypeVar("T")


@dataclass
class Visitor(Generic[T]):
    _visited: dict[T, int] = field(default_factory=dict)

    def in_order(self) -> list[T]:
        return [k for k, v in sorted(self._visited.items(), key=lambda kv: kv[1])]
    
    @contextmanager
    def visit(self, x: T):
        if x in self._visited:
            raise CyclicReference(str(x), list(map(str, self.in_order())))
        self._visited[x] = len(self._visited)
        yield
        del self._visited[x]


@dataclass
class Tangler(mawk.RuleSet):
    reference_map: ReferenceMap
    visited: Visitor[str]
    deps: set[str]
    annotation: AnnotationMethod

    @mawk.on_match(r"^(?P<indent>\s*)<<(?P<refname>[\w-]+)>>\s*$")
    def on_noweb(self, m: re.Match):
        result, deps = tangle_ref(self.reference_map, m["refname"], self.annotation, self.visited)
        self.deps.update(deps)
        return [indent(result, m["indent"])]


def tangle_ref(
    refs: ReferenceMap, ref_name: str, 
    annotation: AnnotationMethod = config.annotation,
    _visited: Optional[Visitor[str]] = None
) -> tuple[str, set[str]]:
    v = _visited or Visitor()
    with v.visit(ref_name):
        deps = set(cb.origin.filename for cb in refs.by_name(ref_name))
        source = "\n".join(refs.get_decorated(ref_name, annotation))
        t = Tangler(refs, v, deps, annotation)
        result = t.run(source)
    return result, deps

