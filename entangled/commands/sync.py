from enum import Enum

from ..io import filedb, FileCache, transaction
from ..interface import Document
from ..errors.user import UserError

from .main import main

import logging


class Action(Enum):
    NOTHING = 0
    TANGLE = 1
    STITCH = 2


def sync_action(doc: Document) -> Action:
    input_file_list = doc.input_files()
    fs = FileCache()

    with filedb(readonly=True) as db:
        changed = set(db.changed_files(fs))

        if not all(f in db for f in input_file_list):
            return Action.TANGLE

        if not changed:
            return Action.NOTHING

        if changed.isdisjoint(db.managed_files):
            return Action.TANGLE

        if changed.issubset(db.managed_files):
            return Action.STITCH

        logging.error("changed: %s", [str(p) for p in changed])
        logging.error(
            "Both markdown and code seem to have changed, don't know what to do now."
        )
        return Action.NOTHING


def tangle(doc: Document):
    with transaction() as t:
        doc.load(t)
        doc.tangle(t)
        t.clear_orphans()
        for h in doc.context.hooks:
            h.post_tangle(doc.reference_map)


def stitch(doc: Document):
    with transaction() as t:
        doc.load(t)
        doc.load_all_code(t)
        doc.stitch(t)
    with transaction() as t:
        doc.tangle(t)
        for h in doc.context.hooks:
            h.post_tangle(doc.reference_map)
        

def run_sync():
    try:
        doc = Document()
        match sync_action(doc):
            case Action.TANGLE:
                logging.info("Tangling.")
                tangle(doc)

            case Action.STITCH:
                logging.info("Stitching.")
                stitch(doc)

            case Action.NOTHING:
                pass

    except UserError as e:
        e.handle()


@main.command()
def sync():
    """Be smart wether to tangle or stich"""
    run_sync()

