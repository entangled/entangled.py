from collections.abc import Generator
from dataclasses import dataclass
from pathlib import PurePath
from os import linesep as eol

import re

from .types import InputStream
from ..model import ReferenceId, ReferenceName
from ..errors.user import ParseError, IndentationError


@dataclass
class Block:
    reference_id: ReferenceId
    content: str


OPEN_BLOCK_EXPR = r"^(?P<indent>\s*).* ~/~ begin <<(?P<source>[^#<>]+)#(?P<ref_name>[^#<>]+)>>\[(?P<ref_count>\d+|init)\]"


@dataclass
class OpenBlockData:
    ref: ReferenceId
    is_init: bool
    indent: str


def open_block(line: str) -> OpenBlockData | None:
    if not (m := re.match(OPEN_BLOCK_EXPR, line)):
        return None

    ref_name = ReferenceName.from_str(m["ref_name"])
    md_source = PurePath(m["source"])
    is_init = m["ref_count"] == "init"
    ref_count = 0 if is_init else int(m["ref_count"])
    return OpenBlockData(ReferenceId(ref_name, md_source, ref_count), is_init, m["indent"])


CLOSE_BLOCK_EXPR = r"^(?P<indent>\s*).* ~/~ end"


@dataclass
class CloseBlockData:
    indent: str


def close_block(line: str) -> CloseBlockData | None:
    if not (m := re.match(CLOSE_BLOCK_EXPR, line)):
        return None
    return CloseBlockData(m["indent"])


def read_top_level(input: InputStream) -> Generator[Block]:
    if not input:
        return

    while input:
        r = yield from read_block((), "", input)
        if r is None:
            _ = next(input)


def read_block(namespace: tuple[str, ...], indent: str, input: InputStream) -> Generator[Block, None, str | None]:
    if not input:
        return None

    pos, line1 = input.peek()
    if (block_data := open_block(line1)) is None:
        return None
    _ = next(input)
    if block_data.indent < indent:
        raise IndentationError(pos)

    content = ""
    while input:
        line = yield from read_block(block_data.ref.name.namespace, block_data.indent, input)
        if line is not None:
            content += line
            continue

        pos, line = next(input)
        if (close_block_data := close_block(line)) is None:
            if not line.startswith(block_data.indent):
                raise IndentationError(pos)
            content += line.removeprefix(block_data.indent)
        else:
            if close_block_data.indent != block_data.indent:
                raise IndentationError(pos)
            yield Block(block_data.ref, content)

            if block_data.is_init:
                extra_indent = block_data.indent.removeprefix(indent)
                ref = block_data.ref
                ref_str = ref.name if ref.name.namespace == namespace else str(ref.name)
                return f"{extra_indent}<<{ref_str}>>{eol}"
            else:
                return ""

    raise ParseError(pos, "unexpected end of file")

