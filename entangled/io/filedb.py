from __future__ import annotations
from collections.abc import Generator
from contextlib import contextmanager, nullcontext
import json
from pathlib import Path
from typing import Any

import msgspec
from msgspec import Struct

import logging

from filelock import FileLock

from entangled.errors.user import HelpfulUserError

from ..version import __version__
from ..utility import ensure_parent
from .virtual import AbstractFileCache, FileCache
from .stat import Stat, hexdigest


class FileDB(Struct):
    """Persistent storage for file stats of both Markdown and generated
    files. We can use this to detect conflicts.

    This data is stored in `.entangled/files.json`. It is recommended to
    keep this file under version control. That way entangled shouldn't get
    too confused when switching branches.

    All files are stored in a single dictionary, the distinction between
    source and target files is made in two separate indices."""

    version: str
    files: dict[str, Stat]
    targets: set[str]

    def clear(self):
        self.files = {}
        self.targets = set()

    @property
    def managed_files(self) -> set[Path]:
        """List all managed files. These are files that can be reconstructed
        from the sources, at least when things are in a consistent state.

        For example: markdown sources cannot be reconstructed, so are not
        listed here. However, generated code is first constructed from
        the markdown, so is considered to be managed."""
        return {Path(p) for p in self.targets}

    def changed_files(self, fs: AbstractFileCache) -> Generator[Path]:
        # A tracked file that no longer exists (e.g. a source that was moved or
        # deleted) counts as changed. Without this guard `fs[Path(p)]` would
        # raise `FileNotFoundError` and crash, see issue #88.
        return (Path(p) for p, known_stat in self.files.items()
                if Path(p) not in fs or fs[Path(p)].stat != known_stat)

    def create_target(self, fs: AbstractFileCache, path: Path):
        if path.is_absolute():
            path = path.relative_to(Path.cwd())
        self.update(fs, path)
        self.targets.add(path.as_posix())

    def update(self, fs: AbstractFileCache, path: Path):
        if path.is_absolute():
            path = path.relative_to(Path.cwd())
        if path in fs:
            self.files[path.as_posix()] = fs[path].stat

    def __contains__(self, path: Path) -> bool:
        return path.as_posix() in self.files

    def __getitem__(self, path: Path) -> Stat:
        return self.files[path.as_posix()]

    def __delitem__(self, path: Path):
        path_str = path.as_posix()
        if path_str in self.targets:
            self.targets.remove(path_str)
        del self.files[path_str]

    def __iter__(self):
        return (Path(p) for p in self.files)

    def check(self, path: Path, content: str) -> bool:
        return hexdigest(content) == self.files[path.as_posix()].hexdigest


FILEDB_PATH =  Path(".") / ".entangled" / "filedb.json"
FILEDB_LOCK_PATH = Path(".") / ".entangled" / "filedb.lock"


def new_db() -> FileDB:
    return FileDB(__version__, {}, set())


def read_filedb(fs: AbstractFileCache | None = None) -> FileDB:
    if fs is None:
        fs = FileCache()

    if FILEDB_PATH not in fs:
        return new_db()

    logging.debug("Reading FileDB")
    db_contents = fs[FILEDB_PATH].content
    raw: Any = json.loads(db_contents)   # pyright: ignore[reportExplicitAny, reportAny]
    if raw["version"] != __version__:
        raise HelpfulUserError(
            f"File database was created with a different version of Entangled ({raw["version"]}).\n" +
            f"Run `entangled reset` to regenerate the database to version {__version__}.")

    db = msgspec.convert(raw, type=FileDB)

    undead = list(filter(lambda p: not p.exists(), db))
    for path in undead:
        logging.warning(f"undead file `{path}` (found in db but not on drive)")

    return db


def write_filedb(db: FileDB, fs: AbstractFileCache | None = None):
    if fs is None:
        fs = FileCache()

    logging.debug("Writing FileDB")
    content = msgspec.json.encode(db, order="sorted").decode(encoding="utf-8")
    _ = fs.write(FILEDB_PATH, content)


@contextmanager
def filedb(readonly: bool = False, writeonly: bool = False, virtual: bool = False, fs: AbstractFileCache | None = None):
    if fs is None:
        fs = FileCache()

    if virtual:
        yield new_db()
        return

    lock = FileLock(ensure_parent(FILEDB_LOCK_PATH)) if fs.is_for_real() \
        else nullcontext()

    with lock:
        db = read_filedb(fs) if not writeonly else new_db()
        yield db
        if not readonly:
            write_filedb(db, fs)
