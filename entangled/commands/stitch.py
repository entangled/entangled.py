from itertools import chain
from pathlib import Path
from textwrap import indent

import logging
import argh  # type: ignore

from ..config import config
from ..document import ReferenceMap, Content, PlainText, ReferenceId
from ..transaction import transaction, TransactionMode
from ..errors.user import UserError
from .tangle import get_input_files


def stitch_markdown(reference_map: ReferenceMap, content: list[Content]) -> str:
    def get(item: Content):
        match item:
            case PlainText(s):
                return s
            case ReferenceId():
                return indent(reference_map[item].source, reference_map[item].indent)

    return "\n".join(get(i) for i in content) + "\n"


@argh.arg("--force", help="force overwrite on conflict")
@argh.arg("-s", "--show", help="only show, don't act")
def stitch(*, force: bool = False, show: bool = False):
    """Stitch code changes back into the Markdown"""
    config.read()

    # these imports depend on config being read
    from ..markdown_reader import read_markdown_file
    from ..code_reader import CodeReader
    from ..hooks import get_hooks
    
    input_file_list = get_input_files()
    hooks = get_hooks()

    if show:
        mode = TransactionMode.SHOW
    elif force:
        mode = TransactionMode.FORCE
    else:
        mode = TransactionMode.FAIL

    refs = ReferenceMap()
    content: dict[Path, list[Content]] = {}
    try:
        for path in input_file_list:
            logging.debug("reading `%s`", path)
            _, c = read_markdown_file(path, refs=refs, hooks=hooks)
            content[path] = c

        with transaction(mode) as t:
            for path in t.db.managed:
                logging.debug("reading `%s`", path)
                t.update(path)
                with open(path, "r") as f:
                    CodeReader(str(path), refs).run(f.read())

            for path in input_file_list:
                t.write(path, stitch_markdown(refs, content[path]), [])

    except UserError as e:
        logging.error(str(e))
