"""
A virtual file system layer to cache file reads and stats.
"""

from dataclasses import dataclass, field
from pathlib import Path
from .stat import stat, FileData


@dataclass
class FileCache:
    _data: dict[Path, FileData] = field(default_factory=dict)

    def __getitem__(self, key: Path) -> FileData:
        if key not in self._data:
            if (s := stat(key)) is None:
                raise KeyError()
            self._data[key] = s
        return self._data[key]

    def __contains__(self, key: Path) -> bool:
        return key.exists()

    def reset(self):
        self._data = {}
