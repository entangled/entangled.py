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


def get_input_files() -> list[Path]:
    include_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
    input_file_list = [
        path for path in include_file_list
        if not any(path.match(pat) for pat in config.ignore_list)
    ]
    return input_file_list


@argh.arg(
    "-a",
    "--annotate",
    choices=[m.name.lower() for m in AnnotationMethod],
    help="annotation method",
)
@argh.arg("--force", help="force overwrite on conflict")
@argh.arg("-s", "--show", help="only show, don't act")
@argh.arg("-r", "--reset-db", help="resets database")
def tangle(*, annotate: Optional[str] = None, force: bool = False, show: bool = False, reset_db = False):
    """Tangle codes from Markdown"""
    config.read()

    # these imports depend on config being read
    from ..markdown_reader import read_markdown_file
    from ..tangle import tangle_ref

    if annotate is None:
        annotation_method = config.annotation
    else:
        annotation_method = AnnotationMethod[annotate.upper()]

    input_file_list = get_input_files()

    refs = ReferenceMap()
    hooks = get_hooks()
    logging.debug("tangling with hooks: %s", [h.__module__ for h in hooks])

    if show:
        mode = TransactionMode.SHOW
    elif reset_db:
        mode = TransactionMode.RESETDB
    elif force:
        mode = TransactionMode.FORCE
    else:
        mode = TransactionMode.FAIL

    try:
        with transaction(mode) as t:
            for path in input_file_list:
                logging.debug("reading `%s`", path)
                t.update(path)
                read_markdown_file(path, refs=refs, hooks=hooks)

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
