import typing
from typing import Any, Self, Union, TypeVar, TypeGuard, Type, Optional, cast
import types

import tomllib
import json

from dataclasses import is_dataclass
from enum import Enum
from pathlib import Path

from .errors.user import HelpfulUserError, ConfigError

T = TypeVar("T")


def isgeneric(annot):
    return typing.get_origin(annot) and hasattr(annot, "__args__")


class FromStr:
    @classmethod
    def from_str(cls, _: str) -> Self:
        raise NotImplementedError()


def construct(annot: Any, json: Any) -> Any:
    try:
        return _construct(annot, json)
    except (AssertionError, ValueError, KeyError, TypeError) as e:
        raise ConfigError(annot, json) from e


def is_object_type(dtype: Type[Any]) -> TypeGuard[Type[dict[str, Any]]]:
    return (
        isgeneric(dtype)
        and typing.get_origin(dtype) is dict
        and typing.get_args(dtype)[0] is str
    )


def is_optional_type(dtype: Type[Any]) -> TypeGuard[Type[Optional[Any]]]:
    return (
        isgeneric(dtype)
        and typing.get_origin(dtype) is Union
        and typing.get_args(dtype)[1] is types.NoneType
    )


def normalize_enum(x: str):
    return x.upper().replace("-", "_")


def _construct(annot: Type[T], json: Any) -> T:
    """Construct an object from a given type from a JSON stream.

    The `annot` type should be one of: str, int, list[T], Optional[T],
    or a dataclass, and the JSON data should match exactly the given
    definitions in the dataclass hierarchy.
    """
    if annot is bool:
        assert isinstance(json, bool)
        return cast(T, json)
    if annot is str:
        assert isinstance(json, str)
        return cast(T, json)
    if annot is int:
        assert isinstance(json, int)
        return cast(T, json)
    if is_object_type(annot):
        assert isinstance(json, dict)
        return cast(
            T, {k: construct(typing.get_args(annot)[1], v) for k, v in json.items()}
        )
    if annot is Any:
        return cast(T, json)
    
    # dicts
    if isgeneric(annot) and typing.get_origin(annot) is dict:
        assert isinstance(json, dict)
        return cast(T, {construct(typing.get_args(annot)[0], k): construct(typing.get_args(annot)[1], v)
                        for k, v in json.items()})
    if annot is dict:
        assert isinstance(json, dict)
        return cast(T, json)
    
    # lists
    if isgeneric(annot) and typing.get_origin(annot) is list:
        assert isinstance(json, list)
        return cast(T, [construct(typing.get_args(annot)[0], item) for item in json])
    if annot is list:
        assert isinstance(json, list)
        return cast(T, json)

    # sets
    if isgeneric(annot) and typing.get_origin(annot) is set:
        assert isinstance(json, list)
        return cast(T, {construct(typing.get_args(annot)[0], item) for item in json})
    if annot is set:
        assert isinstance(json, list)
        return cast(T, set(json))

    if annot is Path and isinstance(json, str):
        return cast(T, Path(json))
    
    if is_optional_type(annot):
        if json is None:
            return cast(T, None)
        else:
            return cast(T, construct(typing.get_args(annot)[0], json))
    if isgeneric(annot) and typing.get_origin(annot) is types.UnionType:
        for dtype in typing.get_args(annot):
            try:
                return cast(T, _construct(dtype, json))
            except ValueError:
                continue
            except AssertionError:
                continue
        raise ValueError("None of the choices in type union match data.")
    if type(annot) is type and issubclass(annot, FromStr) and isinstance(json, str):
        return cast(T, annot.from_str(json))
    if is_dataclass(annot):
        assert isinstance(json, dict)
        arg_annot = typing.get_type_hints(annot)
        args = {k: construct(arg_annot[k], json[k]) for k in json}
        return cast(T, annot(**args))
    if isinstance(json, str) and isinstance(annot, type) and issubclass(annot, Enum):
        options = {normalize_enum(e.name): e for e in annot}
        assert isinstance(json, str)
        assert normalize_enum(json) in options
        return cast(T, options[normalize_enum(json)])
    raise ValueError(f"Couldn't construct {annot} from {repr(json)}")


def read_from_file(data_type: Type[T], path: Path, section: Optional[str] = None) -> T:
    """Read a config from given `path` in given `section`. The path should refer to
    a TOML or JSON file that should decode to a `Config` object. If `section` is given, only
    that section is decoded to a `Config` object. The `section` string may contain
    periods to indicate deeper nesting.

    Example:

    ```python
    read_from_file(Config, Path("./pyproject.toml"), "tool.loom")
    ```
    """
    if not path.exists():
        raise HelpfulUserError(f"File not found: {path}")
    with open(path, "rb") as f:
        if path.suffix == ".toml":
            data: Any = tomllib.load(f)
        elif path.suffix == ".json":
            data = json.load(f)
        else:
            raise HelpfulUserError(f"Unrecognized file format: {path}")

    try:
        if section is not None:
            for s in section.split("."):
                data = data[s]
    except KeyError as e:
        raise HelpfulUserError(
            f"Data file `{path}` should contain section `{section}`."
        ) from e

    return construct(data_type, data)

