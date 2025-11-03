from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Namespace[T]:
    sep: str = "::"
    subspace: defaultdict[str, Namespace[T]] = field(
        default_factory=lambda: defaultdict(Namespace)
    )
    index: dict[str, T] = field(default_factory=dict)

    def sub(self, namespace: tuple[str, ...]) -> Namespace[T]:
        dir = self
        for i, s in enumerate(namespace):
            if s not in self.subspace:
                raise KeyError(f"no subspace `{s}` found in namespace `{self.sep.join(namespace[:i])}`")
            dir = dir.subspace[s]
        return dir

    def make_sub(self, namespace: tuple[str, ...]) -> Namespace[T]:
        dir = self
        for s in namespace:
            dir = dir.subspace[s]
        return dir

    def get(self, namespace: tuple[str, ...], name: str) -> T:
        dir = self.sub(namespace)

        if name in dir.index:
            return dir.index[name]

        raise KeyError(f"no reference `{name}` found in namespace `{self.sep.join(namespace)}`")

    def __getitem__(self, key: str | tuple[str, ...]) -> T:
        match key:
            case str():
                path = key.split(self.sep)
                return self.get((*path[:-1],), path[-1])
            case tuple():
                return self.get(key[:-1], key[-1])

    def __setitem__(self, key: str, value: T):
        path = key.split(self.sep)
        dir = self.make_sub((*path[:-1],))
        dir.index[key] = value

    def __contains__(self, key: str) -> bool:
        path = key.split(self.sep)
        dir = self.sub((*path[:-1],))
        return path[-1] in dir.index
