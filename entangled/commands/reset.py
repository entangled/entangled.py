"""
The `reset` command resets the file database in `.entangled/filedb.json`.
This database gets updated every time you tangle or stitch, but sometimes
its contents may become invalid, for instance when switching branches.
This command will read the markdown sources, then pretend to be tangling
without actually writing out to source files.
"""

from ..io import TransactionMode, transaction
from ..errors.user import UserError
from ..interface import Document
from .main import main

import logging


@main.command(short_help="Reset the file database.")
def reset():
    """
    Resets the file database. This performs a tangle without actually
    writing output to the files, but updating the database as if we were.
    """
    
    try:
        doc = Document()
        mode = TransactionMode.RESETDB

        with transaction(mode) as t:
            doc.load(t)
            annotation_method = doc.config.annotation

            for h in doc.context.hooks:
                h.pre_tangle(doc.reference_map)
            
            doc.tangle(t, annotation_method)

            for h in doc.context.hooks:
                h.on_tangle(t, doc.reference_map)

            t.clear_orphans()

        for h in doc.context.hooks:
            h.post_tangle(doc.reference_map)

    except UserError as e:
        logging.error(str(e))
