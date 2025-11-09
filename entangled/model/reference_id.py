from dataclasses import dataclass
from pathlib import PurePath
from typing import override

from .reference_name import ReferenceName


@dataclass(frozen=True)
class ReferenceId:
    """
    The `ReferenceId` is the main key type into the `ReferenceMap`, and
    uniquely identifies a single code block.

    Attributes:
        name: Full qualified name of the reference.
        file: The markup source file of this reference.
        ref_count: The index within the source file, in case of repeated entries.
            This index starts at 0 for each input file using the same name.
    """
    name: ReferenceName
    file: PurePath
    ref_count: int

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.file, self.ref_count))

    @override
    def __str__(self) -> str:
        return f"{self.name}[{self.ref_count}]"

