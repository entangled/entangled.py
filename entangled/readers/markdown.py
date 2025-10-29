from typing import cast
from .types import InputStream, MarkdownStream
from .yaml_header import read_yaml_header
from ..document import PlainText, CodeBlock, ReferenceMap
from ..config import Config, config

import msgspec

def get_path(d: object, path: str) -> object:
    for element in path.split("."):
        if not isinstance(d, dict):
            raise ValueError("expected object")
        d = cast(dict[str, object], d).get(element, None)
        if d is None:
            return None
    return d


def read_markdown(input: InputStream, refs: ReferenceMap | None = None) -> MarkdownStream[ReferenceMap]:
    refs = refs or ReferenceMap()
    header = yield from read_yaml_header(input)
    if isinstance(header, dict):
        header = cast(dict[str, object], header)
        extra_config = msgspec.convert(header.get("entangled", None), Config)
    elif header is None:
        extra_config = None


    return refs
