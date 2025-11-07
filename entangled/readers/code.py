from collections.abc import Generator, Mapping
from dataclasses import dataclass
from pathlib import PurePath
from os import linesep as eol

import re

from .types import InputStream
from ..model import ReferenceId, ReferenceName


@dataclass
class Block:
    reference_id: ReferenceId
    indent: str
    content: str


OPEN_BLOCK_EXPR = r"^(?P<indent>\s*).* ~/~ begin <<(?P<source>[^#<>]+)#(?P<ref_name>[^#<>]+)>>\[(?P<ref_count>\d+)\]"
CLOSE_BLOCK_EXPR = r"^(?P<indent>\s*).* ~/~ end"



def read_content(namespace_map: Mapping[PurePath, tuple[str, ...]], block: Block, input: InputStream) -> Generator[Block]:

    for _, line in input:
        if m := re.match(CLOSE_BLOCK_EXPR, line):
            assert m["indent"] == block.indent
            yield block
            return

        elif m := re.match(OPEN_BLOCK_EXPR, line):
            assert m["indent"] <= block.indent
            ref_name = ReferenceName.from_str(m["ref_name"])
            md_source = PurePath(m["source"])
            ref_count = int(m["ref_count"])
            if ref_name != block.ref_name:
                namespace = namespace_map[md_source]
                ref_str = ref_name.name if ref_name.namespace == namespace else str(ref_name)
                block.content += m["indent"].removeprefix(block.indent) + "<<" + ref_str + ">>" + eol
            new_block = Block(ReferenceId(ref_name, md_source, ref_count), m["indent"], "")
            yield from read_content(namespace_map, new_block, input)

        else:
            block.content += line.removeprefix(block.indent)

