from __future__ import annotations
from typing import Iterable, Optional
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

import hashlib
import json
import os

from .version import __version__

@dataclass
class FileStat:
    path: Path
    modified: datetime
    hexdigest: str

    @staticmethod
    def from_path(path: Path):
        stat = os.stat(path)
        with open(path, "rb") as f:
            hash = hashlib.sha256(f.read())
        return FileStat(path, datetime.fromtimestamp(stat.st_mtime), hash.hexdigest())

    def __lt__(self, other: FileStat) -> bool:
        return self.modified < other.modified

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FileStat) and self.hexdigest == other.hexdigest
    
    @staticmethod
    def from_json(data) -> FileStat:
        return FileStat(Path(data["path"]), datetime.fromisoformat(data["modified"]), data["hexdigest"])
    
    def to_json(self):
        return {"path": str(self.path), "modified": self.modified.isoformat(), "hexdigest": self.hexdigest}


def stat(path: Path) -> FileStat:
    return FileStat.from_path(path)


@dataclass
class FileDB:
    """Persistent storage for file stats of both Markdown and generated
    files. We can use this to detect conflicts.
    
    This data is stored in `.entangled/files.json`. It is recommended to
    keep this file under version control. That way entangled shouldn't get
    too confused when switching branches."""
    files: dict[Path, FileStat]

    @staticmethod
    def path():
        return Path.cwd() / ".entangled" / "files.json"

    @staticmethod
    def read() -> FileDB:
        raw = json.load(open(FileDB.path()))
        return FileDB({ stat.path: stat for stat in (FileStat.from_json(r) for r in raw["files"]) })

    def write(self):
        raw = {
            "version": __version__,
            "files": [stat.to_json() for stat in self.files.values()]
        }
        json.dump(raw, open(FileDB.path(), "w"))

    def changed(self) -> list[Path]:
        """List all files that have changed w.r.t. the database."""
        return [p for p, s in self.files.items() if s != stat(p)]
    
    def update(self, path: Path):
        """Update the given path to a new stat."""
        self.files[path] = stat(path)
    
    def __getitem__(self, key: Path) -> Optional[FileStat]:
        """Retrieve the stat for a path, if it is in the db."""
        return self.files.get(key, None)

    @staticmethod
    def initialize():
        if FileDB.path().exists():
            return
        
        FileDB.path().parent.mkdir(parents=True, exist_ok=True) 
        data = {
            "version": __version__,
            "files": []
        }
        json.dump(data, open(FileDB.path(), "w"))


@contextmanager
def file_db():
    FileDB.initialize()
    db = FileDB.read()
    yield db
    db.write()

