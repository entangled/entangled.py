"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from itertools import chain

import msgspec
import tomllib

from .annotation_method import AnnotationMethod
from .language import Language
from .markers import Markers
from .config_data import Config
from .config_update import ConfigUpdate
from ..logging import logger
from ..version import __version__

log = logger()


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
            update = msgspec.convert(json, type=ConfigUpdate)
            return Config() | update

    except ValueError as e:
        log.error("Could not read config: %s", e)
        return None
    except KeyError as e:
        log.debug("%s", str(e))
        log.debug("The config file %s should contain a section %s", path, section)
        return None


def read_config():
    if Path("./entangled.toml").exists():
        return read_config_from_toml(Path("./entangled.toml")) or Config()
    if Path("./pyproject.toml").exists():
        return (
            read_config_from_toml(Path("./pyproject.toml"), "tool.entangled") or Config()
        )
    return Config()


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
        self.config = (self.config if self.config is not None else Config()) \
            | ConfigUpdate(version=__version__, **kwargs)

        yield

        self.config = backup

    def get_language(self, lang_name: str) -> Language | None:
        if self.config is None:
            raise ValueError("No config loaded.")
        return self.config.languages.get(lang_name, None)


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


__all__ = ["config", "AnnotationMethod", "Markers"]
