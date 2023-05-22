from itertools import chain
from pathlib import Path
from textwrap import indent

import logging
import argh  # type: ignore

from ..config import config
from ..code_reader import CodeReader
from ..markdown_reader import MarkdownReader
from ..document import ReferenceMap, Content, PlainText, ReferenceId
from ..transaction import transaction, TransactionMode
from ..errors.user import UserError


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
    input_file_list = list(chain.from_iterable(map(Path(".").glob, config.watch_list)))

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
            with open(path, "r") as f:
                mr = MarkdownReader(str(path), refs)
                mr.run(f.read())
                content[path] = mr.content

        with transaction(mode) as t:
            for path in t.db.managed:
                logging.debug("reading `%s`", path)
                t.db.update(path)
                with open(path, "r") as f:
                    CodeReader(str(path), refs).run(f.read())

            for path in input_file_list:
                t.write(path, stitch_markdown(refs, content[path]), [])
                
    except UserError as e:
        logging.error(str(e))
