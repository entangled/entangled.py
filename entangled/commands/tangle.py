from typing import Optional
from itertools import chain
from pathlib import Path

import argh  # type: ignore
import logging

from ..document import ReferenceMap
from ..config import config, AnnotationMethod
from ..transaction import transaction, TransactionMode
from ..hooks import get_hooks
from ..errors.user import UserError


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
    config.read()

    # these imports depend on config being read
    from ..markdown_reader import MarkdownReader
    from ..tangle import tangle_ref

    if annotate is None:
        annotation_method = config.annotation
    else:
        annotation_method = AnnotationMethod[annotate.upper()]

    include_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
    exclude_file_list = list(
        chain.from_iterable(map(Path(".").glob, config.ignore_list))
    )
    input_file_list = [
        path for path in include_file_list if not path in exclude_file_list
    ]

    refs = ReferenceMap()
    hooks = get_hooks()

    if show:
        mode = TransactionMode.SHOW
    elif force:
        mode = TransactionMode.FORCE
    else:
        mode = TransactionMode.FAIL

    try:
        with transaction(mode) as t:
            for path in input_file_list:
                logging.debug("reading `%s`", path)
                t.update(path)
                with open(path, "r") as f:
                    MarkdownReader(str(path), refs, hooks).run(f.read())

            for h in hooks:
                h.pre_tangle(refs)

            for tgt in refs.targets:
                result, deps = tangle_ref(refs, tgt, annotation_method)
                mode = next(refs[tgt]).mode
                t.write(Path(tgt), result, list(map(Path, deps)), mode)

            for h in hooks:
                h.on_tangle(t, refs)

            t.clear_orphans()

        for h in hooks:
            h.post_tangle(refs)

    except UserError as e:
        logging.error(str(e))
