from typing import Union
from dataclasses import is_dataclass
from enum import Enum

import typing
import types

from .parsing import Parser


def isgeneric(annot):
    return hasattr(annot, "__origin__") \
        and hasattr(annot, "__args__")


def construct(annot, json):
    """Construct an object from a given type from a JSON stream.

    The `annot` type should be one of: str, int, list[T], Optional[T],
    or a dataclass, and the JSON data should match exactly the given
    definitions in the dataclass hierarchy.
    """
    if annot is str:
        assert isinstance(json, str)
        return json
    if annot is int:
        assert isinstance(json, int)
        return json
    if isinstance(json, str) and isinstance(annot, Parser):
        result, _ = annot.read(json)
        return result
    if isgeneric(annot) and typing.get_origin(annot) is list:
        assert isinstance(json, list)
        return [construct(typing.get_args(annot)[0], item) for item in json]
    if isgeneric(annot) and typing.get_origin(annot) is Union \
        and typing.get_args(annot)[1] is types.NoneType:
        if json is None:
            return None
        else:
            return construct(typing.get_args(annot)[0], json)
    if is_dataclass(annot):
        assert isinstance(json, dict)
        arg_annot = typing.get_type_hints(annot)
        # assert all(k in json for k in arg_annot)
        args = { k: construct(arg_annot[k], json[k])
                 for k in json }
        return annot(**args)
    if isinstance(json, str) and issubclass(annot, Enum):
        options = {opt.name.lower(): opt for opt in annot}
        assert json.lower() in options
        return options[json.lower()]
    raise ValueError(f"Couldn't construct {annot} from {repr(json)}")