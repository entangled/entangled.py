from typing import cast
from .types import InputStream, MarkdownStream
from .yaml_header import get_config, read_yaml_header
from ..document import PlainText, CodeBlock, ReferenceMap
from ..config import Config, config


def read_markdown(input: InputStream, refs: ReferenceMap | None = None) -> MarkdownStream[ReferenceMap]:
    refs = refs or ReferenceMap()
    header = yield from read_yaml_header(input)
    config = get_config(header)

    return refs
