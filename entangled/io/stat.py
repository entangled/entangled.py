from __future__ import annotations

from dataclasses import dataclass
from typing import override
from datetime import datetime
from pathlib import Path

import hashlib
import os
import logging
import time


def hexdigest(s: str) -> str:
    """Creates a SHA-256 hash digest from a string. Before hashing, the string
    has carriage return `\\r` characters, trailing white space on each line
    and trailing newlines removed, and the string is encoded as UTF-8. This
    way, changes in white space only, like the ones made by editors that
    strip trailing white space on save, don't count as changes."""
    lines = s.replace("\r", "").split("\n")
    content = "\n".join(line.rstrip() for line in lines).rstrip().encode()
    return hashlib.sha256(content).hexdigest()


@dataclass
class Stat:
    modified: datetime
    hexdigest: str

    def __lt__(self, other: Stat) -> bool:
        return self.modified < other.modified

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stat):
            return False
        return self.hexdigest == other.hexdigest


@dataclass
class FileData:
    path: Path
    content: str
    stat: Stat

    @staticmethod
    def from_path(path: Path) -> FileData | None:
        stat: os.stat_result | None = None
        for _ in range(5):
            try:
                stat = os.stat(path)
            except FileNotFoundError:
                logging.warning("File `%s` not found.", path)
                time.sleep(0.1)

        if stat is None:
            return None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            digest = hexdigest(content)

        return FileData(
            path,
            content,
            Stat(datetime.fromtimestamp(stat.st_mtime), digest))


def stat(path: Path) -> FileData | None:
    if path.is_absolute():
        path = path.relative_to(Path.cwd())
    return FileData.from_path(path)
