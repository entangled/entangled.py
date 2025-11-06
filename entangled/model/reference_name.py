from __future__ import annotations

from dataclasses import dataclass
from typing import override


@dataclass(frozen=True)
class ReferenceName:
    """
    Collects the concepts of a namespace and name into one object.
    """
    namespace: tuple[str, ...]
    name: str

    @override
    def __hash__(self) -> int:
        return hash((*self.namespace, self.name))

    @override
    def __str__(self):
        return "::".join(self.namespace) + "::" + self.name

    @staticmethod
    def from_str(name: str, namespace: tuple[str, ...] = ()) -> ReferenceName:
        path = name.split("::")
        if len(path) == 1:
            return ReferenceName(namespace, name)
        else:
            return ReferenceName(tuple(path[:-1]), path[-1])
