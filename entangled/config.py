from __future__ import annotations

from typing import Optional, ClassVar, TypeVar
from enum import Enum
from dataclasses import dataclass
from .parsing import Parser, Parsable, fullmatch, fmap


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


class AnnotationMethod(Enum):
    Standard = 1
    Naked = 2
    Supplemented = 3


@dataclass
class Comment:
    open: str
    close: Optional[str] = None


@dataclass
class Language:
    name: str
    identifiers: list[str]
    comment: Comment
    line_directive: Optional[str] = None


T = TypeVar("T")


@dataclass
class Markers:
    open: str
    close: str
    class_: str
    id: str
    attribute: str


markers = Markers(
    r"^(?P<indent>\s*)```\s*{(?P<properties>[^{}]*)}\s*$",
    r"^(?P<indent>\s*)```\s*$",
    r"\.([a-zA-Z]\S*)",
    r"#([a-zA-Z]\S*)",
    r"([a-zA-Z]\S*)\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"",
)


@dataclass
class Config:
    version: Version
    languages: list[Language]
    markers: Markers
    watch_list: list[str]
    annotation_format: Optional[str] = None
    annotation: AnnotationMethod = AnnotationMethod.Standard
    use_line_directives: bool = False

    def __post_init__(self):
        self.language_index = dict()
        for l in self.languages:
            for i in l.identifiers:
                self.language_index[i] = l

    def get_language(self, lang_name: str) -> Optional[Language]:
        return self.language_index.get(lang_name, None)


languages = [
    Language("C", ["c", "cpp", "c++"], Comment("/*", "*/")),
    Language("Python", ["python"], Comment("#")),
    Language("Rust", ["rust"], Comment("//")),
    Language("Haskell", ["haskell"], Comment("--")),
    Language(
        "Lisp", ["scheme", "r5rs", "r6rs", "r7rs", "racket", "clojure"], Comment(";")
    ),
    Language("Julia", ["julia"], Comment("#")),
    Language("Java", ["java"], Comment("//")),
    Language("CSS", ["css"], Comment("/*", "*/")),
    Language("Lua", ["lua"], Comment("--")),
]

default = Config(
    Version.from_string("2.0"), languages, markers, ["README.md", "docs/**/*.md"]
)

config = default
