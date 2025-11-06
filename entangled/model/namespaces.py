from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from .reference_name import ReferenceName


@dataclass
class Namespace[T]:
    """
    A structure of nested namespaces containing objects of type `T`.
    """
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

    def get(self, name: ReferenceName) -> T:
        dir = self.sub(name.namespace)

        if name in dir.index:
            return dir.index[name.name]

        raise KeyError(f"no reference `{name.name}` found in namespace `{self.sep.join(name.namespace)}`")

    def __getitem__(self, key: str | ReferenceName) -> T:
        match key:
            case ReferenceName():
                return self.get(key)

            case str():
                return self.get(ReferenceName.from_str(key))

    def __setitem__(self, key: ReferenceName, value: T):
        dir = self.make_sub(key.namespace)
        dir.index[key.name] = value

    def __contains__(self, key: ReferenceName) -> bool:
        dir = self.sub(key.namespace)
        return key.name in dir.index
