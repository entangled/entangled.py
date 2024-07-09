from .config import config
from .filedb import file_db

from itertools import chain
from pathlib import Path


def safe_glob(pattern):
    """The `glob` method of `Path` raises a FileNotFound error when
    there are rapid changes in the filesystem.

    `safe_glob` catches this error and returns an empty list instead."""
    try:
        return Path().glob(pattern)
    except FileNotFoundError:
        return []


def find_watch_dirs():
    """List all directories that contain files that need watching."""
    input_file_list = list_input_files()
    markdown_dirs = set(p.parent for p in input_file_list)
    with file_db(readonly=True) as db:
        code_dirs = set(p.parent for p in db.managed)
    return code_dirs.union(markdown_dirs)


def list_input_files():
    """List all input files."""
    include_file_list = chain.from_iterable(map(safe_glob, config.watch_list))
    exclude_file_list = list(
        chain.from_iterable(map(safe_glob, config.ignore_list))
    )
    return [path for path in include_file_list if not path in exclude_file_list]


def list_dependent_files():
    with file_db(readonly=True) as db:
        result = list(db.managed)
    return result
