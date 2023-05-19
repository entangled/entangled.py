from __future__ import annotations
from typing import ClassVar
from dataclasses import dataclass

from ..parsing import Parser, Parsable, fmap, fullmatch


@dataclass
class Version(Parsable):
    numbers: tuple[int, ...]
    _pattern: ClassVar[Parser] = fullmatch(r"[0-9]+(\.[0-9]+)*")

    def __str__(self):
        return ".".join(str(i) for i in self.numbers)

    @staticmethod
    def from_string(s: str) -> Version:
        return Version(tuple(int(sv) for sv in s.split(".")))

    @staticmethod
    def __parser__() -> Parser[Version]:
        return Version._pattern >> fmap(Version.from_string)
