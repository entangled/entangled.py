from collections.abc import Generator, Iterator
from pathlib import PurePath

from ..config.namespace_default import NamespaceDefault

from ..document import CodeBlock, Content, RawContent, PlainText, ReferenceId, ReferenceMap
from ..config import Config
from ..errors.user import CodeAttributeError, IndentationError
from ..properties import get_attribute_string, read_properties, get_classes
from ..utility import first
from ..hooks import get_hooks, HookBase
from ..properties import get_id

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


def code_block(config: Config, filename: PurePath) -> Reader[RawContent, bool]:
    get_raw_token = delimited_token_getter(
        config.markers.open, config.markers.close, code_block_guard)
    if config.namespace is None:
        match config.namespace_default:
            case NamespaceDefault.GLOBAL:
                namespace = ()
            case NamespaceDefault.PRIVATE:
                namespace = (filename.as_posix(),)
    else:
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
            language,
            namespace = namespace
        )

        return True

    return code_block_reader


def raw_markdown(config: Config, input: InputStream) -> RawMarkdownStream[None]:
    if not input:
        return

    filename = input.peek()[0].filename
    ignore_block_reader = ignore_block(config)
    code_block_reader = code_block(config, filename)

    while input:
        if (yield from ignore_block_reader(input)):
            continue
        if (yield from code_block_reader(input)):
            continue

        _, line = next(input)
        yield PlainText(line)


def process(hooks: list[HookBase], refs: ReferenceMap, code_block: CodeBlock) -> ReferenceId:
    for h in hooks:
        h.on_read(code_block)

    block_id = get_id(code_block.properties)

    try:
        target_file = get_attribute_string(code_block.properties, "file")
    except TypeError:
        raise CodeAttributeError(code_block.origin, "`file` attribute should have string type")

    try:
        if mode := get_attribute_string(code_block.properties, "mode"):
            code_block.mode = int(mode, 8)
    except TypeError:
        raise CodeAttributeError(code_block.origin, "`mode` attribute should have string type")

    ref_name = block_id or target_file
    if ref_name is None:
        ref_name = f"unnamed-{code_block.origin}"
    ref = refs.new_id(code_block.origin.filename, code_block.namespace, ref_name)

    refs[ref] = code_block
    if target_file is not None:
        refs.targets.add(target_file)
    if target_file is not None and block_id is not None:
        refs.alias[target_file] = block_id

    return ref


def refine(hooks: list[HookBase], refs: ReferenceMap, raw: Iterator[RawContent]) -> Generator[Content, None, ReferenceMap]:
    plain_content: list[str] = []
    for token in raw:
        match token:
            case PlainText(t):
                plain_content.append(t)
            case CodeBlock():
                if plain_content:
                    yield PlainText("".join(plain_content))
                    plain_content = []
                    yield process(hooks, refs, token)

    return refs


def markdown(refs: ReferenceMap, input: InputStream) -> Generator[Content, None, ReferenceMap]:
    header = yield from read_yaml_header(input)
    config = get_config(header)
    hooks = get_hooks(config)
    refs = yield from refine(hooks, refs, raw_markdown(config, input))
    return refs
