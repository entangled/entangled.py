"""
A virtual file system layer to cache file reads and stats.
"""

from dataclasses import dataclass, field
from pathlib import Path

import os
import tempfile

from .stat import hexdigest, stat, FileData


def assure_final_newline(s: str) -> str:
    if s[-1] != "\n":
        return s + "\n"
    else:
        return s


def atomic_write(target: Path, content: str, mode: int | None):
    """
    Writes a file by first writing to a temporary location and then moving
    the file to the target path.
    """
    tmp_dir = Path() / ".entangled" / "tmp"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=tmp_dir) as f:
        _ = f.write(assure_final_newline(content))
        # Flush and sync contents to disk
        f.flush()
        if mode is not None:
            os.chmod(f.name, mode)
        os.fsync(f.fileno())
    os.replace(f.name, target)


@dataclass
class FileCache:
    """
    A virtualization layer between the file system and the rest of Entangled. This is to
    give file IO a cleaner semantics, and also to cache reading file contents and computing
    digests.

    This acts as a mapping from `Path` to `FileData`. Removing items actually deletes files.
    """
    _data: dict[Path, FileData] = field(default_factory=dict)

    def __getitem__(self, key: Path) -> FileData:
        """
        Get `FileData` belonging to given `Path`. The data is cached inbetween calls.
        If you expect data to have changed, you should first `reset` the cache.
        """
        if key not in self._data:
            if (s := stat(key)) is None:
                raise KeyError()
            self._data[key] = s
        return self._data[key]

    def __contains__(self, key: Path) -> bool:
        """
        Check that a file exists.
        """
        return key.exists()

    def __delitem__(self, key: Path):
        """
        Remove a file. If its parent directories are empty, these are also
        removed.
        """
        key.unlink()
        parent = key.parent
        while list(parent.iterdir()) == []:
            parent.rmdir()
            parent = parent.parent
        if key in self._data:
            del self._data[key]

    def write(self, key: Path, new_content: str, mode: int | None = None):
        """
        Write contents to a file. If `new_content` has the same digest as the known
        contents, nothing is done. The entry is removed from the cache afterward.

        Nothing is done to prevent overwriting an existing file.
        """
        if key in self:
            new_digest = hexdigest(new_content)
            if new_digest == self[key].stat.hexdigest:
                return
            del self._data[key]

        key.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(key, new_content, mode)

    def reset(self):
        """
        Reset the cache. Doesn't perform any IO.
        """
        self._data = {}
