from __future__ import annotations
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import msgspec
from msgspec import Struct

import logging

from filelock import FileLock

from ..version import __version__
from ..utility import normal_relative, ensure_parent
from .virtual import FileCache
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

    def changed_files(self, fs: FileCache) -> Generator[Path]:
        return (Path(p) for p, known_stat in self.files.items()
                if fs[Path(p)].stat != known_stat)

    def create_target(self, fs: FileCache, path: Path):
        path = normal_relative(path)
        self.update(fs, path)
        self.targets.add(path.as_posix())

    def update(self, fs: FileCache, path: Path):
        path = normal_relative(path)
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


def read_filedb() -> FileDB:
    if not FILEDB_PATH.exists():
        return FileDB(__version__, {}, set())

    logging.debug("Reading FileDB")
    db = msgspec.json.decode(FILEDB_PATH.open("br").read(), type=FileDB)
    if db.version != __version__:
        logging.debug(f"FileDB was written with version {db.version}, running version {__version__}; updating.")
    db.version = __version__

    undead = list(filter(lambda p: not p.exists(), db))
    for path in undead:
        logging.warning(f"undead file `{path}` (found in db but not on drive)")

    return db


def write_filedb(db: FileDB):
    logging.debug("Writing FileDB")
    _ = FILEDB_PATH.open("wb").write(msgspec.json.encode(db, order="sorted"))


@contextmanager
def filedb(readonly: bool = False):
    lock = FileLock(ensure_parent(FILEDB_LOCK_PATH))
    with lock:
        db = read_filedb()
        yield db
        if not readonly:
            write_filedb(db)
