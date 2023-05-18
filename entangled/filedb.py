from __future__ import annotations
from typing import Optional, Iterable
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

import hashlib
import json
import os
import logging

from filelock import FileLock

from .version import __version__
from .utility import normal_relative, ensure_parent


@dataclass
class FileStat:
    path: Path
    deps: Optional[list[Path]]
    modified: datetime
    hexdigest: str

    @staticmethod
    def from_path(path: Path, deps: Optional[list[Path]]):
        stat = os.stat(path)
        with open(path, "rb") as f:
            hash = hashlib.sha256(f.read())
        return FileStat(
            path, deps, datetime.fromtimestamp(stat.st_mtime), hash.hexdigest()
        )

    def __lt__(self, other: FileStat) -> bool:
        return self.modified < other.modified

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FileStat) and self.hexdigest == other.hexdigest

    @staticmethod
    def from_json(data) -> FileStat:
        return FileStat(
            Path(data["path"]),
            None if data["deps"] is None else [Path(d) for d in data["deps"]],
            datetime.fromisoformat(data["modified"]),
            data["hexdigest"],
        )

    def to_json(self):
        return {
            "path": str(self.path),
            "deps": None if self.deps is None else [str(p) for p in self.deps],
            "modified": self.modified.isoformat(),
            "hexdigest": self.hexdigest,
        }


def stat(path: Path, deps: Optional[list[Path]] = None) -> FileStat:
    path = normal_relative(path)
    deps = None if deps is None else [normal_relative(d) for d in deps]
    return FileStat.from_path(path, deps)


@dataclass
class FileDB:
    """Persistent storage for file stats of both Markdown and generated
    files. We can use this to detect conflicts.

    This data is stored in `.entangled/files.json`. It is recommended to
    keep this file under version control. That way entangled shouldn't get
    too confused when switching branches.

    All files are stored in a single dictionary, the distinction between
    source and target files is made in two separate indices."""

    _files: dict[Path, FileStat]
    _source: set[Path]
    _target: set[Path]

    @staticmethod
    def path():
        return Path(".") / ".entangled" / "filedb.json"

    @staticmethod
    def read() -> FileDB:
        logging.debug("Reading FileDB")
        raw = json.load(open(FileDB.path()))
        return FileDB(
            {stat.path: stat for stat in (FileStat.from_json(r) for r in raw["files"])},
            set(map(Path, raw["source"])),
            set(map(Path, raw["target"])),
        )

    @property
    def managed(self) -> set[Path]:
        return self._target

    def write(self):
        logging.debug("Writing FileDB")
        raw = {
            "version": __version__,
            "files": [stat.to_json() for stat in self._files.values()],
            "source": list(map(str, self._source)),
            "target": list(map(str, self._target)),
        }
        json.dump(raw, open(FileDB.path(), "w"), indent=2)

    def changed(self) -> list[Path]:
        """List all target files that have changed w.r.t. the database."""
        return [p for p, s in self._files.items() if s != stat(p)]

    def has_changed(self, path: Path) -> bool:
        return stat(path) != self[path]

    def update(self, path: Path, deps: Optional[list[Path]] = None):
        """Update the given path to a new stat."""
        path = normal_relative(path)
        if path in self.managed and deps is None:
            deps = self[path].deps
        self._files[path] = stat(path, deps)

    def __contains__(self, path: Path) -> bool:
        return path in self._files

    def __getitem__(self, path: Path) -> FileStat:
        return self._files[path]

    def __delitem__(self, path: Path):
        if path in self._target:
            self._target.remove(path)
        del self._files[path]

    @property
    def files(self) -> Iterable[Path]:
        return self._files.keys()

    def check(self, path: Path, content: str) -> bool:
        return (
            hashlib.sha256(content.encode()).hexdigest() == self._files[path].hexdigest
        )

    @staticmethod
    def initialize() -> FileDB:
        if FileDB.path().exists():
            db = FileDB.read()
            undead = list(filter(lambda p: not p.exists(), db.files))
            for path in undead:
                logging.warn(
                    "File `%s` in DB doesn't exist. Removing entry from DB.", path
                )
                del db[path]
            return db

        FileDB.path().parent.mkdir(parents=True, exist_ok=True)
        data = {"version": __version__, "files": [], "source": [], "target": []}
        json.dump(data, open(FileDB.path(), "w"))
        return FileDB.read()


@contextmanager
def file_db(readonly=False):
    lock = FileLock(ensure_parent(Path.cwd() / ".entangled" / "filedb.lock"))
    with lock:
        db = FileDB.initialize()
        yield db
        if not readonly:
            db.write()
