from collections.abc import Iterable
from typing import TypeVar, TypeGuard
from pathlib import Path


T = TypeVar("T")


def first(it: Iterable[T]) -> T | None:
    try:
        return next(iter(it))
    except StopIteration:
        return None


def normal_relative(path: Path) -> Path:
    return path.resolve().relative_to(Path.cwd())


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cat_maybes(it: Iterable[T | None]) -> Iterable[T]:
    def pred(x: T | None) -> TypeGuard[T]:
        return x is not None

    return filter(pred, it)
