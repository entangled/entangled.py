"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

from functools import cached_property
import threading
from contextlib import contextmanager
from copy import copy, deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any
from itertools import chain

import msgspec
from msgspec import Struct, field
import tomllib

from brei import Program

from entangled import from_str
from .language import Language, languages
from .version import Version
from ..logging import logger


log = logger()


class AnnotationMethod(StrEnum):
    """Annotation methods.

    - `STANDARD` is the default. Comments tell where a piece of code
       came from in enough detail to reconstruct the markdown if some
       of the code is changed.
    - `NAKED` adds no comments to the tangled files. Stitching is not
       possible with this setting.
    - `SUPPLEMENTED` adds extra information to the comment lines.
    """

    STANDARD = "standard"
    NAKED = "naked"
    SUPPLEMENTED = "supplemented"


class Markers(Struct):
    """Markers can be used to configure the Markdown dialect. Currently not used."""

    open: str
    close: str
    begin_ignore: str = r"^\s*\~\~\~markdown\s*$"
    end_ignore: str = r"^\s*\~\~\~\s*$"


markers = Markers(
    r"^(?P<indent>\s*)```\s*{(?P<properties>[^{}]*)}\s*$", r"^(?P<indent>\s*)```\s*$"
)


class Config(Struct, dict=True):
    """Main config class.

    Attributes:
        version: Version of Entangled for which this config was created.
            Entangled should read all versions lower than its own.
        languages: List of programming languages and their comment styles.
        markers: Regexes for detecting open and close of code blocks.
        watch_list: List of glob-expressions indicating files to include
            for tangling.
        annotation: Style of annotation.
        annotation_format: Extra annotation.
        use_line_directives: Wether to print pragmas in source code for
            indicating markdown source locations.
        hooks: List of enabled hooks.
        hook: Sub-config of hooks.
        loom: Sub-config of loom.

    This class is made thread-local to make it possible to test in parallel."""

    _version: str = field(name = "version")
    languages: list[Language] = field(default_factory=list)
    markers: Markers = field(default_factory=lambda: copy(markers))
    watch_list: list[str] = field(default_factory=lambda: ["**/*.md"])
    ignore_list: list[str] = field(default_factory=list)
    annotation_format: str | None = None
    annotation: AnnotationMethod = AnnotationMethod.STANDARD
    use_line_directives: bool = False
    hooks: list[str] = field(default_factory=lambda: ["shebang"])
    hook: dict[str, Any] = field(default_factory=dict)  # pyright: ignore[reportExplicitAny]
    brei: Program = field(default_factory=Program)

    language_index: dict[str, Language] = field(default_factory=dict)

    @cached_property
    def version(self) -> Version:
        return Version.from_str(self._version)

    def __post_init__(self):
        self.languages = languages + self.languages
        self.make_language_index()

    def make_language_index(self):
        for l in self.languages:
            for i in l.identifiers:
                self.language_index[i] = l


default = Config("2.0")  # Version.from_str("2.0"))


def read_config_from_toml(
    path: Path, section: str | None = None
) -> Config | None:
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
            json: Any = tomllib.load(f)  # pyright: ignore[reportExplicitAny]
            if section is not None:
                for s in section.split("."):
                    json = json[s]  # pyright: ignore[reportAny]
            return msgspec.convert(json, type=Config, dec_hook=from_str.dec_hook)

    except ValueError as e:
        log.error("Could not read config: %s", e)
        return None
    except KeyError as e:
        log.debug("%s", str(e))
        log.debug("The config file %s should contain a section %s", path, section)
        return None


def read_config():
    if Path("./entangled.toml").exists():
        return read_config_from_toml(Path("./entangled.toml")) or default
    if Path("./pyproject.toml").exists():
        return (
            read_config_from_toml(Path("./pyproject.toml"), "tool.entangled") or default
        )
    return default


class ConfigWrapper(threading.local):
    def __init__(self, config: Config | None = None):
        self.config: Config | None = config

    def read(self, force: bool = False):
        if self.config is None or force:
            self.config = read_config()

    @property
    def get(self) -> Config:
        if self.config is None:
            raise ValueError("No config loaded.")
        return self.config

    @contextmanager
    def __call__(self, **kwargs):
        backup = self.config
        new_config = deepcopy(self.config)
        for k, v in kwargs.items():
            setattr(new_config, k, v)
        self.config = new_config

        yield

        self.config = backup

    def get_language(self, lang_name: str) -> Language | None:
        if self.config is None:
            raise ValueError("No config loaded.")
        return self.config.language_index.get(lang_name, None)


config = ConfigWrapper()
"""The `config.config` variable is changed when the `config` module is loaded.
Config is read from `entangled.toml` file."""


def get_input_files() -> list[Path]:
    include_file_list = chain.from_iterable(map(Path(".").glob, config.get.watch_list))
    input_file_list = [
        path for path in include_file_list
        if not any(path.match(pat) for pat in config.get.ignore_list)
    ]
    return sorted(input_file_list)
