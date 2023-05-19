from typing import Optional
from itertools import chain
from pathlib import Path

import argh  # type: ignore
import logging

from ..document import ReferenceMap
from ..config import config, AnnotationMethod
from ..markdown_reader import MarkdownReader
from ..transaction import transaction, TransactionMode
from ..tangle import tangle_ref
from ..hooks import get_hooks


@argh.arg(
    "-a",
    "--annotate",
    choices=[m.name.lower() for m in AnnotationMethod],
    help="annotation method",
)
@argh.arg("--force", help="force overwrite on conflict")
@argh.arg("-s", "--show", help="only show, don't act")
def tangle(*, annotate: Optional[str] = None, force: bool = False, show: bool = False):
    """Tangle codes from Markdown"""
    if annotate is not None:
        config.annotation = AnnotationMethod[annotate.upper()]

    input_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
    refs = ReferenceMap()
    hooks = get_hooks()

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
                MarkdownReader(str(path), refs, hooks).run(f.read())

        for tgt in refs.targets:
            result, deps = tangle_ref(refs, tgt)
            t.write(Path(tgt), result, list(map(Path, deps)))
        t.clear_orphans()

    for h in hooks:
        h.post_tangle(refs)
