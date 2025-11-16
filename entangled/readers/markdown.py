from collections.abc import Generator, Iterator
from functools import partial

from ..config.namespace_default import NamespaceDefault

from ..model import CodeBlock, Content, RawContent, PlainText, ReferenceId, ReferenceMap, ReferenceName
from ..model.properties import get_attribute_string, get_attribute, read_properties, get_classes, get_id
from ..config import Config
from ..errors.user import CodeAttributeError, IndentationError
from ..utility import first
from ..hooks import get_hooks, HookBase
from ..iterators.lines import lines
from ..text_location import TextLocation

from .types import InputStream, Reader, RawMarkdownStream
from .delimiters import delimited_token_getter
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


def dedent_line(location: TextLocation, indent: str, line: str):
    if line.startswith(indent) or line.strip() == "":
        return line.removeprefix(indent)
    raise IndentationError(location)


def dedent(location: TextLocation, source: str, indent: str) -> str:
    return "".join(dedent_line(location, indent, line) for line in lines(source))


def code_block(config: Config) -> Reader[RawContent, bool]:
    get_raw_token = delimited_token_getter(
        config.markers.open, config.markers.close, code_block_guard)

    def code_block_reader(input: InputStream) -> RawMarkdownStream[bool]:
        if not input:
            return False

        block = get_raw_token(input)
        if block is None:
            return False

        if config.namespace is None:
            match config.namespace_default:
                case NamespaceDefault.GLOBAL:
                    namespace = ()
                case NamespaceDefault.PRIVATE:
                    namespace = (block.origin.filename.as_posix(),)
        else:
            namespace = config.namespace

        indent = block.open_match["indent"]
        properties = read_properties(block.open_match["properties"])
        language_class = first(get_classes(properties))
        language = config.get_language(language_class) if language_class else None
        if language_class and not language:
            logging.warning(f"`{block.origin}`: language `{language_class}` unknown.")
        source = dedent(block.origin, block.content, indent)

        yield CodeBlock(
            properties,
            indent,
            block.open_line.removeprefix(indent),
            block.close_line.removeprefix(indent),
            source,
            block.origin,
            language,
            namespace = namespace
        )

        return True

    return code_block_reader


def raw_markdown(config: Config, input: InputStream) -> RawMarkdownStream[None]:
    if not input:
        return

    ignore_block_reader = ignore_block(config)
    code_block_reader = code_block(config)

    while input:
        if (yield from ignore_block_reader(input)):
            continue
        if (yield from code_block_reader(input)):
            continue

        _, line = next(input)
        yield PlainText(line)


def process_code_block(hooks: list[HookBase], refs: ReferenceMap, code_block: CodeBlock) -> ReferenceId:
    for h in hooks:
        h.on_read(code_block)

    block_id = get_id(code_block.properties)

    try:
        target_file = get_attribute_string(code_block.properties, "file")
    except TypeError:
        raise CodeAttributeError(code_block.origin, "`file` attribute should have string type")

    if mode := get_attribute(code_block.properties, "mode"):
        if type(mode) is int:   # bool is a subtype of int, and we really want an int
            code_block.mode = mode
        elif isinstance(mode, str):
            code_block.mode = int(mode, 8)
        else:
            raise CodeAttributeError(code_block.origin, "`mode` attribute should have string or integer type")

    ref_name = block_id or target_file
    if ref_name is None:
        ref_name = f"unnamed-{code_block.origin}"
    ref = refs.new_id(code_block.origin.filename, ReferenceName(code_block.namespace, ref_name))
    refs[ref] = code_block

    return ref


def process_token(hooks: list[HookBase], refs: ReferenceMap, token: RawContent) -> Content:
    match token:
        case CodeBlock():
            return process_code_block(hooks, refs, token)
        case _:
            return token


def collect_plain_text[T](inp: Iterator[PlainText | T]) -> Generator[PlainText | T, None, None]:
    plain_content: list[str] = []

    def flush():
        nonlocal plain_content
        if plain_content:
            yield(PlainText("".join(plain_content)))
            plain_content = []

    for token in inp:
        match token:
            case PlainText(t):
                plain_content.append(t)
            case _:
                yield from flush()
                yield token

    yield from flush()


def markdown(config: Config, refs: ReferenceMap, input: InputStream) -> Generator[Content, None, Config]:
    header = yield from read_yaml_header(input)
    config |= get_config(header)
    hooks = get_hooks(config)

    yield from map(
        partial(process_token, hooks, refs),
        collect_plain_text(raw_markdown(config, input)))

    return config
