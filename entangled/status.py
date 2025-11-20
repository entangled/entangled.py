from collections.abc import Iterable
from .io import filedb
from .config import get_input_files, Config, read_config

from pathlib import Path


def safe_glob(pattern: str) -> Iterable[Path]:
    """The `glob` method of `Path` raises a FileNotFound error when
    there are rapid changes in the filesystem.

    `safe_glob` catches this error and returns an empty list instead."""
    try:
        return Path().glob(pattern)
    except FileNotFoundError:
        return []


def find_watch_dirs():
    """List all directories that contain files that need watching."""
    cfg = Config() | read_config()
    input_file_list = get_input_files(cfg)
    markdown_dirs = set(p.parent for p in input_file_list)
    with filedb(readonly=True) as db:
        code_dirs = set(p.parent for p in db.managed_files)
    return code_dirs.union(markdown_dirs)


def list_dependent_files():
    with filedb(readonly=True) as db:
        result = list(db.managed_files)
    return result
