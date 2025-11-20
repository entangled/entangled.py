"""Configuration. The variable `config` should be automatically populated with
defaults and config loaded from `entangled.toml` in the work directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from itertools import chain

import msgspec
import tomllib

from .annotation_method import AnnotationMethod
from .markers import Markers
from .config_data import Config
from .config_update import ConfigUpdate
from .namespace_default import NamespaceDefault

from ..logging import logger
from ..version import __version__
from ..errors.user import HelpfulUserError


log = logger()


def read_config_from_toml(
    path: Path, section: str | None = None
) -> ConfigUpdate | None:
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
            log.debug("Read config from `%s`", path)
            return update

    except (msgspec.ValidationError, tomllib.TOMLDecodeError) as e:
        raise HelpfulUserError(f"Could not read config: {e}")
    except KeyError as e:
        log.debug("%s", str(e))
        log.debug("The config file %s should contain a section %s", path, section)
        return None


def read_config() -> ConfigUpdate | None:
    if Path("./entangled.toml").exists():
        return read_config_from_toml(Path("./entangled.toml"))
    if Path("./pyproject.toml").exists():
        return (
            read_config_from_toml(Path("./pyproject.toml"), "tool.entangled")
        )
    return None


def get_input_files(cfg: Config) -> list[Path]:
    log.debug("watch list: %s; ignoring: %s", cfg.watch_list, cfg.ignore_list)
    include_file_list = chain.from_iterable(map(Path(".").glob, cfg.watch_list))
    input_file_list = [
        path for path in include_file_list
        if not any(path.match(pat) for pat in cfg.ignore_list) and path.is_file()
    ]
    log.debug("input file list %s", input_file_list)
    return sorted(input_file_list)


__all__ = ["Config", "ConfigUpdate", "AnnotationMethod", "Markers", "NamespaceDefault"]
