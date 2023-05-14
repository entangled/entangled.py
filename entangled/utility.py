from typing import Iterable, Optional, TypeVar
from contextlib import contextmanager
import os
from pathlib import Path


T = TypeVar("T")

@contextmanager
def pushd(wd: Path):
    olddir = os.getcwd()
    os.chdir(wd)
    yield wd
    os.chdir(olddir)


def first(it: Iterable[T]) -> Optional[T]:
    try:
        return next(iter(it))
    except StopIteration:
        return None


def normal_relative(path: Path) -> Path:
    return path.resolve().relative_to(Path.cwd())
