"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

from typing import Optional, ClassVar, TypeVar
from enum import Enum
from dataclasses import dataclass
from .parsing import Parser, Parsable, fullmatch, fmap


@dataclass
class Version(Parsable):
    """Dataclass that manages version strings."""

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
    """Annotation methods.

    - `STANDARD` is the default. Comments tell where a piece of code
       came from in enough detail to reconstruct the markdown if some
       of the code is changed.
    - `NAKED` adds no comments to the tangled files. Stitching is not
       possible with this setting.
    - `SUPPLEMENTED` adds extra information to the comment lines.
    """

    STANDARD = 1
    NAKED = 2
    SUPPLEMENTED = 3


@dataclass
class Comment:
    """Comment method for a language. For example: `Comment("/*", "*/")` works
    for C/C++ etc, `Comment("#")` works for Python, and so on.
    """

    open: str
    close: Optional[str] = None


@dataclass
class Language:
    """Language information. Given a language we may have any number of short-hands
    to indicate a code block is written in that language. If a language supports
    line directives this can be used to redirect compiler messages directly to the
    markdown files."""

    name: str
    identifiers: list[str]
    comment: Comment
    line_directive: Optional[str] = None


T = TypeVar("T")


@dataclass
class Markers:
    """Markers can be used to configure the Markdown dialect. Currently not used."""

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
    """Main config class."""

    version: Version
    languages: list[Language]
    markers: Markers
    watch_list: list[str]
    annotation_format: Optional[str] = None
    annotation: AnnotationMethod = AnnotationMethod.STANDARD
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

default = Config(Version.from_string("2.0"), languages, markers, ["**/*.md"])

config = default
"""The `config.config` variable is changed when the `config` module is loaded.
Config is read from `entangled.toml` file."""
