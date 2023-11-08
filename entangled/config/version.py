from __future__ import annotations
from dataclasses import dataclass

from ..construct import FromStr

@dataclass
class Version(FromStr):
    numbers: tuple[int, ...]

    def __str__(self):
        return ".".join(str(i) for i in self.numbers)

    @classmethod
    def from_str(cls, s: str) -> Version:
        return Version(tuple(int(sv) for sv in s.split(".")))

