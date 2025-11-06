from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import override


from ..errors.internal import InternalError

from .code_block import CodeBlock
from .properties import get_attribute_string
from .reference_id import ReferenceId
from .reference_name import ReferenceName


def length[T](seq: Iterable[T]) -> int:
    """Compute the length of an iterable."""
    i = 0
    for _ in seq:
        i += 1
    return i


@dataclass
class ReferenceMap(MutableMapping[ReferenceId, CodeBlock]):
    """
    Members:
        `map`: maps references to actual code block content
        `root`: namespace root
        `targets`: lists filenames; a target should be in `index`

    The `ReferenceMap` implements `Mapping[ReferenceId, CodeBlock]`. In
    addition to that, we keep an index on `ReferenceName`.
    """

    _map: dict[ReferenceId, CodeBlock] = field(default_factory=dict)
    _index: defaultdict[ReferenceName, list[ReferenceId]] \
        = field(default_factory=lambda: defaultdict(list))
    _targets: dict[PurePath, ReferenceName] = field(default_factory=dict)

    def select_by_name(self, name: ReferenceName) -> list[ReferenceId]:
        """Return a list of references with the same name."""
        return self._index[name]

    def has_name(self, key: ReferenceName) -> bool:
        """Check that a name is present."""
        return key in self._index

    def new_id(self, filename: PurePath, name: ReferenceName) -> ReferenceId:
        """Create a new `ReferenceId` with a `ref_count` succeeding the last one
        by the same name."""
        c = length(filter(lambda r: r.file == filename, self._index[name]))
        return ReferenceId(name, filename, c)

    def select_by_target(self, target: PurePath) -> ReferenceName:
        return self._targets[target]

    def register_target(self, target: PurePath, ref_name: ReferenceName):
        self._targets[target] = ref_name

    @override
    def __contains__(self, key: object) -> bool:
        return key in self._map

    @override
    def __setitem__(self, key: ReferenceId, value: CodeBlock):
        if key in self._map:
            raise InternalError("Duplicate key in ReferenceMap", [key])
        self._map[key] = value
        self._index[key.name].append(key)

        if filename := get_attribute_string(value.properties, "file"):
            self._targets[PurePath(filename)] = key.name

    @override
    def __getitem__(self, key: ReferenceId) -> CodeBlock:
        return self._map[key]

    @override
    def __delitem__(self, key: ReferenceId):
        if key not in self:
            return

        value = self._map[key]
        if filename := get_attribute_string(value.properties, "file"):
            del self._targets[PurePath(filename)]
        self._index[key.name].remove(key)
        del self._map[key]

    @override
    def __len__(self) -> int:
        return len(self._map)

    @override
    def __iter__(self) -> Iterator[ReferenceId]:
        return iter(self._map)

    def __bool__(self) -> bool:
        return bool(self._map)
