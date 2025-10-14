"""
The `reset` command resets the file database in `.entangled/filedb.json`.
This database gets updated every time you tangle or stitch, but sometimes
its contents may become invalid, for instance when switching branches.
This command will read the markdown sources, then pretend to be tangling
without actually writing out to source files.
"""

from ..io import TransactionMode, transaction
from ..config import config, get_input_files
from ..hooks import  get_hooks
from ..document import ReferenceMap
from ..errors.user import UserError

import logging
from pathlib import Path


def reset():
    """
    Resets the database. This performs a tangle without actually writing
    output to the files, but updating the database as if we were.
    """
    config.read()

    # these imports depend on config being read
    from ..markdown_reader import read_markdown_file
    from ..tangle import tangle_ref

    input_file_list = get_input_files()

    refs = ReferenceMap()
    hooks = get_hooks()
    logging.debug("tangling with hooks: %s", [h.__module__ for h in hooks])
    mode = TransactionMode.RESETDB
    annotation_method = config.get.annotation

    try:
        with transaction(mode) as t:
            for path in input_file_list:
                logging.debug("reading `%s`", path)
                t.update(path)
                _, _ = read_markdown_file(path, refs=refs, hooks=hooks)

            for h in hooks:
                h.pre_tangle(refs)

            for tgt in refs.targets:
                result, deps = tangle_ref(refs, tgt, annotation_method)
                mask = next(iter(refs.by_name(tgt))).mode
                t.write(Path(tgt), result, list(map(Path, deps)), mask)

            for h in hooks:
                h.on_tangle(t, refs)

            t.clear_orphans()

        for h in hooks:
            h.post_tangle(refs)

    except UserError as e:
        logging.error(str(e))
