from typing import cast

import logging
import yaml
import msgspec

from ..config import Config
from ..document import PlainText
from ..errors.user import ParseError
from .types import InputStream, MarkdownStream
from .delimiters import delimited_token_getter


get_yaml_header_token = delimited_token_getter("---", "---")


def read_yaml_header(input: InputStream) -> MarkdownStream[object]:
    """
    Reads the YAML header that can be found at the top of a Markdown document.
    """
    delimited_token = get_yaml_header_token(input)
    if delimited_token is None:
        return None

    yield PlainText(delimited_token.string)
    try:
        return yaml.safe_load(delimited_token.content)
    except yaml.YAMLError as e:
        raise ParseError(delimited_token.origin, str(e))


def get_config(header: object) -> Config | None:
    """
    Get the `entangled` component from the unstructured header data,
    and convert it to a `Config` object.

    If there was no YAML header or it contained no `entangled` member,
    this will return `None`. If the given YAML header evaluated to something
    other than an object/dictionary or the conversion to `Config` failed,
    a `TypeError` is raised.
    """
    if isinstance(header, dict):
        header = cast(dict[str, object], header)
        try:
            return msgspec.convert(header.get("entangled", None), Config)
        except msgspec.ValidationError as e:
            logging.error(e)
            raise TypeError()

    elif header is None:
        return None
    else:
        raise TypeError()
