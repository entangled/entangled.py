from typing import Optional, TypeVar
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from textwrap import indent

import re
import mawk
import argh
import logging

from ..document import ReferenceMap
from ..config import config, AnnotationMethod
from ..error import CyclicReference
from ..markdown_reader import MarkdownReader
from ..transaction import transaction, TransactionMode
from ..filedb import file_db


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


@argh.arg("-a", "--annotate", choices=[m.name.lower() for m in AnnotationMethod], help="annotation method")
@argh.arg("--force", help="force overwrite on conflict")
@argh.arg("-s", "--show", help="only show, don't act")
def tangle(*, annotate: Optional[str] = None, force: bool = False, show: bool = False):
    if annotate is not None:
        config.annotation = AnnotationMethod[annotate.upper()]

    input_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
    refs = ReferenceMap()

    if show:
        mode = TransactionMode.SHOW
    elif force:
        mode = TransactionMode.FORCE
    else:
        mode = TransactionMode.FAIL

    with transaction(mode) as t:
        for path in input_file_list:
            logging.debug("reading `%s`", path)
            t.db.update(path)
            with open(path, "r") as f:
                MarkdownReader(str(path), refs).run(f.read())

        for tgt in refs.targets:
            result, deps = tangle_ref(refs, tgt)
            t.write(Path(tgt), result, list(map(Path, deps)))
        t.clear_orphans()
