from typing import Optional, TypeVar
from dataclasses import dataclass, field
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

T = TypeVar("T")


@dataclass
class Tangler(mawk.RuleSet):
    reference_map: ReferenceMap
    visited: set[str]

    @mawk.on_match(r"^(?P<indent>\s*)<<(?P<refname>[\w-]+)>>\s*$")
    def on_noweb(self, m: re.Match):
        if m["refname"] in self.visited:
            raise CyclicReference(m["refname"])
        return [
            indent(tangle_ref(self.reference_map, m["refname"], self.visited), m["indent"])
        ]


def tangle_ref(
    refs: ReferenceMap, ref_name: str, _visited: Optional[set[str]] = None
) -> str:
    visited = _visited or set()
    visited.add(ref_name)
    source = "\n".join(refs.get_decorated(ref_name))
    return Tangler(refs, visited).run(source)


@click.command()
@click.option("-a", "--annotate", default=None)
def tangle(annotate: Optional[AnnotationMethod]):
    pass

