from typing import Optional, TypeVar
from dataclasses import dataclass
from textwrap import indent

import re
import mawk

from .document import ReferenceMap
from .error import CyclicReference


T = TypeVar("T")


@dataclass
class Tangler(mawk.RuleSet):
    reference_map: ReferenceMap
    visited: set[str]
    deps: set[str]

    @mawk.on_match(r"^(?P<indent>\s*)<<(?P<refname>[\w-]+)>>\s*$")
    def on_noweb(self, m: re.Match):
        if m["refname"] in self.visited:
            raise CyclicReference(m["refname"])
        result, deps = tangle_ref(self.reference_map, m["refname"], self.visited)
        self.deps.update(deps)
        return [indent(result, m["indent"])]


def tangle_ref(
    refs: ReferenceMap, ref_name: str, _visited: Optional[set[str]] = None
) -> tuple[str, set[str]]:
    visited = _visited or set()
    visited.add(ref_name)
    deps = set(cb.origin.filename for cb in refs.by_name(ref_name))
    source = "\n".join(refs.get_decorated(ref_name))
    t = Tangler(refs, visited, deps)
    result = t.run(source)
    return result, deps

