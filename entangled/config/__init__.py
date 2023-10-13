"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

from typing import Any, Optional, ClassVar, TypeVar
from enum import Enum
from dataclasses import dataclass, field
from copy import copy
from pathlib import Path
from contextlib import contextmanager

from ..construct import construct
from .version import Version
from .language import Language, languages

import threading
import tomllib
import logging


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
    r"^\s*\~\~\~\s*$",
)


@dataclass
class Config(threading.local):
    """Main config class. This class is made thread-local to make
    it possible to test in parallel."""

    version: Version
    languages: list[Language] = field(default_factory=list)
    markers: Markers = field(default_factory=lambda: copy(markers))
    watch_list: list[str] = field(default_factory=lambda: ["**/*.md"])
    annotation_format: Optional[str] = None
    annotation: AnnotationMethod = AnnotationMethod.STANDARD
    use_line_directives: bool = False
    hooks: list[str] = field(default_factory=list)
    hook: dict = field(default_factory=dict)

    def __post_init__(self):
        self.languages = languages + self.languages
        self.make_language_index()

    def make_language_index(self):
        self.language_index = dict()
        for l in self.languages:
            for i in l.identifiers:
                self.language_index[i] = l


default = Config(Version.from_string("2.0"))


def read_config_from_toml(
    path: Path, section: Optional[str] = None
) -> Optional[Config]:
    """Read a config from given `path` in given `section`. The path should refer to
    a TOML file that should decode to a `Config` object. If `section` is given, only
    that section is decoded to a `Config` object. The `section` string may contain
    periods to indicate deeper nesting.

    Example:

    ```python
    read_config_from_toml(Path("./pyproject.toml"), "tool.entangled")
    ```
    """
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            json = tomllib.load(f)
            if section is not None:
                for s in section.split("."):
                    json = json[s]
            return construct(Config, json)
    except ValueError as e:
        logging.error("Could not read config: %s", e)
        return None
    except KeyError as e:
        logging.debug("%s", e)
        logging.debug("The config file %s should contain a section %s", path, section)
        return None


def read_config():
    if Path("./entangled.toml").exists():
        return read_config_from_toml(Path("./entangled.toml")) or default
    if Path("./pyproject.toml").exists():
        return (
            read_config_from_toml(Path("./pyproject.toml"), "tool.entangled") or default
        )
    return default


class ConfigWrapper:
    def __init__(self, config):
        self.config = config

    def read(self):
        self.config = read_config()

    def __getattr__(self, attr):
        return getattr(self.config, attr)

    @contextmanager
    def __call__(self, **kwargs):
        backup = {k: getattr(self.config, k) for k in kwargs}
        for k, v in kwargs.items():
            setattr(self.config, k, v)
        yield
        for k in kwargs.keys():
            setattr(self.config, k, backup[k])

    def get_language(self, lang_name: str) -> Optional[Language]:
        return self.config.language_index.get(lang_name, None)


config = ConfigWrapper(read_config())
"""The `config.config` variable is changed when the `config` module is loaded.
Config is read from `entangled.toml` file."""
