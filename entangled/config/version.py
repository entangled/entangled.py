from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    numbers: tuple[int, ...]

    def to_str(self) -> str:
        return ".".join(str(i) for i in self.numbers)

    @classmethod
    def from_str(cls, s: str) -> Version:
        return Version(tuple(int(sv) for sv in s.split(".")))

    def __lt__(self, other: Version) -> bool:
        return self.numbers < other.numbers
