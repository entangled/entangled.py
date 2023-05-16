from typing import Optional, TypeVar
from dataclasses import dataclass, field
from itertools import chain
from functools import singledispatch
from copy import copy
from pathlib import Path
from textwrap import indent
import re
import mawk
import click


from .document import (
    ReferenceMap,
)
from .properties import read_properties, get_id, get_attribute, get_classes
from .config import Language, config, AnnotationMethod
from .error import CyclicReference
from .markdown_reader import read_markdown, MarkdownReader
from .transaction import transaction


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
    refs: ReferenceMap, ref_name: str,
    _visited: Optional[set[str]] = None
) -> tuple[str, set[str]]:
    visited = _visited or set()
    visited.add(ref_name)
    deps = set(cb.origin.filename for cb in refs.by_name(ref_name))
    source = "\n".join(refs.get_decorated(ref_name))
    t = Tangler(refs, visited, deps)
    result = t.run(source)
    return result, deps


@click.command()
@click.option("-a", "--annotate", default=None)
def tangle(annotate: Optional[AnnotationMethod]):
    input_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
    refs = ReferenceMap()
    for path in input_file_list:
        with open(path, "r") as f:
            MarkdownReader(str(path), refs).run(f.read())

    with transaction() as t:
        for tgt in refs.targets:
            result, deps = tangle_ref(refs, tgt)
            t.write(Path(tgt), result, map(Path, deps))

