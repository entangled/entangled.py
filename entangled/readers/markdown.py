from ..document import CodeBlock, RawContent, PlainText
from ..config import Config
from ..errors.user import IndentationError
from ..properties import read_properties, get_classes
from ..utility import first

from .types import InputStream, Reader, RawMarkdownStream
from .lines import lines
from .delimiters import delimited_token_getter
from .text_location import TextLocation
from .yaml_header import read_yaml_header, get_config

import re
import logging


def ignore_block(config: Config) -> Reader[RawContent, bool]:
    get_raw_token = delimited_token_getter(
        config.markers.begin_ignore, config.markers.end_ignore
    )

    def ignore_block_reader(input: InputStream) -> RawMarkdownStream[bool]:
        block = get_raw_token(input)
        if block is None:
            return False
        yield PlainText(block.string)
        return True

    return ignore_block_reader


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


def code_block(config: Config) -> Reader[RawContent, bool]:
    get_raw_token = delimited_token_getter(
        config.markers.open, config.markers.close, code_block_guard)
    namespace = config.namespace

    def code_block_reader(input: InputStream) -> RawMarkdownStream[bool]:
        block = get_raw_token(input)
        if block is None:
            return False

        indent = block.open_match["indent"]
        properties = read_properties(block.open_match["properties"])
        language_class = first(get_classes(properties))
        language = config.get_language(language_class) if language_class else None
        if language_class and not language:
            logging.warning(f"`{block.origin}`: language `{language_class}` unknown.")
        source = dedent(block.content, indent)

        yield CodeBlock(
            properties,
            indent,
            block.open_line,
            block.close_line,
            source,
            block.origin,
            language
        )

        return True

    return code_block_reader


def raw_markdown(input: InputStream) -> RawMarkdownStream[None]:
    header = yield from read_yaml_header(input)
    config = get_config(header)

    ignore_block_reader = ignore_block(config)
    code_block_reader = code_block(config)

    while input:
        if (yield from ignore_block_reader(input)):
            continue
        if (yield from code_block_reader(input)):
            continue

        _, line = next(input)
        yield PlainText(line)
