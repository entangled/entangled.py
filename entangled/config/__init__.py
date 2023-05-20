"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

from typing import Optional, ClassVar, TypeVar
from enum import Enum
from dataclasses import dataclass, field
from copy import copy
from pathlib import Path

from ..construct import construct
from .version import Version
from .language import Language, languages

import tomllib


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
class Markers:
    """Markers can be used to configure the Markdown dialect. Currently not used."""

    open: str
    close: str
    begin_ignore: str
    end_ignore: str


markers = Markers(
    r"^(?P<indent>\s*)```\s*{(?P<properties>[^{}]*)}\s*$",
    r"^(?P<indent>\s*)```\s*$",
    r"^\s*\~\~\~markdown\s*$",
    r"^\s*\~\~\~\s*$"
)


@dataclass
class Config:
    """Main config class."""

    version: Version
    languages: list[Language] = field(default_factory=list)
    markers: Markers = field(default_factory=lambda: copy(markers))
    watch_list: list[str] = field(default_factory=lambda: ["**/*.md"])
    annotation_format: Optional[str] = None
    annotation: AnnotationMethod = AnnotationMethod.STANDARD
    use_line_directives: bool = False
    hooks: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.languages = languages + self.languages
        self.make_language_index()

    def make_language_index(self):
        self.language_index = dict()
        for l in self.languages:
            for i in l.identifiers:
                self.language_index[i] = l

    def get_language(self, lang_name: str) -> Optional[Language]:
        return self.language_index.get(lang_name, None)


default = Config(Version.from_string("2.0"))


def read_config():
    if not Path("./entangled.toml").exists():
        return default
    with open(Path("./entangled.toml"), "rb") as f:
        json = tomllib.load(f)
    return construct(Config, json)


config = read_config()
"""The `config.config` variable is changed when the `config` module is loaded.
Config is read from `entangled.toml` file."""
