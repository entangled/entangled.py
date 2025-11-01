from ..document import CodeBlock, Content
from ..config import Config
from ..errors.user import IndentationError
from ..properties import read_properties, get_classes
from ..utility import first

from .types import InputStream, Reader, MarkdownStream
from .lines import lines
from .delimiters import delimited_token_getter
from .text_location import TextLocation

import re
import logging


def code_block_guard(origin: TextLocation, open_match: re.Match[str], close_match: re.Match[str]) -> bool:
    open_indent = open_match["indent"]
    close_indent = close_match["indent"]
    if len(close_indent) < len(open_indent):
        raise IndentationError(origin)
    if open_indent != close_indent:
        return False
    return True


def dedent(source: str, indent: str) -> str:
    return "".join(line.removeprefix(indent) for line in lines(source))


def code_block(config: Config) -> Reader[Content, None, CodeBlock]:
    get_raw_token = delimited_token_getter(
        config.markers.open, config.markers.close, code_block_guard)

    def code_block_reader(input: InputStream) -> MarkdownStream[CodeBlock]:
        block = get_raw_token(input)
        if block is None:
            return None

        indent = block.open_match["indent"]
        properties = read_properties(block.open_match["properties"])
        language_class = first(get_classes(properties))
        language = config.get_language(language_class) if language_class else None
        if language_class and not language:
            logging.warning(f"`{block.origin}`: language `{language_class}` unknown.")
        source = dedent(block.content, indent)

        return CodeBlock(
            properties,
            indent,
            block.open_line,
            block.close_line,
            source,
            block.origin,
            language
        )

        yield None  # pyright: ignore[reportUnreachable]


    return code_block_reader
