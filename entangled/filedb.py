from __future__ import annotations
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import override

import msgspec
from msgspec import Struct

import hashlib
import os
import time
import logging

from filelock import FileLock

from .version import __version__
from .utility import normal_relative, ensure_parent
from .errors.user import FileError


def hexdigest(s: str) -> str:
    """Creates a MD5 hash digest from a string. Before hashing, the string has
    linefeed `\\r` characters and trailing newlines removed, and the string
    is encoded as UTF-8."""
    content = s.replace("\r", "").rstrip().encode()
    return hashlib.sha256(content).hexdigest()


class FileStat(Struct):
    path: str
    deps: list[str] | None
    modified: datetime
    hexdigest: str
    size: int

    @staticmethod
    def from_path(path: Path, deps: list[Path] | None) -> FileStat:
        stat: os.stat_result | None = None
        for _ in range(5):
            try:
                stat = os.stat(path)
            except FileNotFoundError:
                logging.warning("File `%s` not found.", path)
                time.sleep(0.1)

        if stat is None:
            raise FileError(path)

        size = stat.st_size
        with open(path, "r") as f:
            digest = hexdigest(f.read())

        return FileStat(
            path.as_posix(),
            [d.as_posix() for d in deps] if deps else None,
            datetime.fromtimestamp(stat.st_mtime), digest, size)

    def __lt__(self, other: FileStat) -> bool:
        return self.modified < other.modified

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, FileStat) and self.hexdigest == other.hexdigest


def stat(path: Path, deps: list[Path] | None = None) -> FileStat:
    path = normal_relative(path)
    deps = None if deps is None else [normal_relative(d) for d in deps]
    return FileStat.from_path(path, deps)


class FileDB(Struct):
    """Persistent storage for file stats of both Markdown and generated
    files. We can use this to detect conflicts.

    This data is stored in `.entangled/files.json`. It is recommended to
    keep this file under version control. That way entangled shouldn't get
    too confused when switching branches.

    All files are stored in a single dictionary, the distinction between
    source and target files is made in two separate indices."""

    version: str
    files: dict[str, FileStat]
    source: set[str]
    target: set[str]

    def clear(self):
        self.files = {}
        self.source = set()
        self.target = set()

    @property
    def managed(self) -> set[Path]:
        """List all managed files. These are files that can be reconstructed
        from the sources, at least when things are in a consistent state.

        For example: markdown sources cannot be reconstructed, so are not
        listed here. However, generated code is first constructed from
        the markdown, so is considered to be managed."""
        return {Path(p) for p in self.target}

    def changed(self) -> list[Path]:
        """List all target files that have changed w.r.t. the database."""
        return [Path(p) for p, s in self.files.items() if s != stat(Path(p))]

    def has_changed(self, path: Path) -> bool:
        return stat(path) != self[path]

    def update_target(self, path: Path, deps: list[Path]):
        self.update(path, deps)
        self.target.add(path.as_posix())

    def update(self, path: Path, deps: list[Path] | None = None):
        """Update the given path to a new stat."""
        path = normal_relative(path)
        if path in self.managed and deps is None:
            logging.warning(f"updating managed file {path} without deps given.")
            known_deps = self[path].deps
            if known_deps is not None:
                deps = [Path(p) for p in known_deps]
        self.files[path.as_posix()] = stat(path, deps)

    def __contains__(self, path: Path) -> bool:
        return path.as_posix() in self.files

    def __getitem__(self, path: Path) -> FileStat:
        return self.files[path.as_posix()]

    def __delitem__(self, path: Path):
        if path in self.target:
            self.target.remove(str(path))
        del self.files[str(path)]

    def __iter__(self):
        return (Path(p) for p in self.files)

    def check(self, path: Path, content: str) -> bool:
        return hexdigest(content) == self.files[str(path)].hexdigest


FILEDB_PATH =  Path(".") / ".entangled" / "filedb.json"
FILEDB_LOCK_PATH = Path(".") / ".entangled" / "filedb.lock"


def read_filedb() -> FileDB:
    if not FILEDB_PATH.exists():
        return FileDB(__version__, {}, set(), set())

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
