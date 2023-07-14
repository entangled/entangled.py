from .config import config
from .filedb import file_db

from itertools import chain
from pathlib import Path


def find_watch_dirs():
    """List all directories that contain files that need watching."""
    input_file_list = list_input_files()
    markdown_dirs = set(p.parent for p in input_file_list)
    with file_db(readonly=True) as db:
        code_dirs = set(p.parent for p in db.managed)
    return code_dirs.union(markdown_dirs)


def list_input_files():
    """List all input files."""
    return chain.from_iterable(map(Path(".").glob, config.watch_list))


def list_dependent_files():
    with file_db(readonly=True) as db:
        result = list(db.managed)
    return result
