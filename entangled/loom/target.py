from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar
from pathlib import Path
from ..parsing import Parsable, Parser, matching, starmap, fmap, fullmatch, choice


@dataclass
class Phony(Parsable):
    """A Phony is a target that does not correspond to a file."""
    _pattern: ClassVar[Parser] = matching(r"phony\(([^()\s]+)\)")
    name: str

    @staticmethod
    def __parser__() -> Parser[Phony]:
        return Phony._pattern >> starmap(lambda n: Phony(n))

    def __str__(self):
        return f"phony({self.name})"

    def __hash__(self):
        return hash(f"#{self.name}#")


@dataclass
class Target(Parsable):
    """A Target is either a Phony or a Path."""
    phony_or_path: Phony | Path

    @staticmethod
    def __parser__() -> Parser[Target]:
        return choice(Phony, fullmatch(".*") >> fmap(Path)) >> fmap(Target)

    @staticmethod
    def from_str(s: str) -> Target:
        result: Target = Target.__parser__().read(s)[0]
        return result

    def __str__(self):
        return f"Target({self.phony_or_path})"

    def __hash__(self):
        return hash(self.phony_or_path)

    def is_phony(self) -> bool:
        return isinstance(self.phony_or_path, Phony)

    def is_path(self) -> bool:
        return isinstance(self.phony_or_path, Path)

    @property
    def path(self) -> Path:
        if not isinstance(self.phony_or_path, Path):
            raise ValueError("Not a path")
        return self.phony_or_path


