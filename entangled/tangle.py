from typing import Optional, Iterable, TypeVar
from dataclasses import dataclass, field
from functools import singledispatch
from copy import copy
from pathlib import Path
from textwrap import indent
import re
import mawk


from .document import (
    ReferenceMap,
    ReferenceId,
    CodeBlock,
    TextLocation,
    Content,
    PlainText,
)
from .properties import read_properties, get_id, get_attribute, get_classes
from .config import Language, config
from .error import CyclicReference

T = TypeVar("T")


def first(it: Iterable[T]) -> Optional[T]:
    try:
        return next(iter(it))
    except StopIteration:
        return None


@dataclass
class MarkdownError(Exception):
    location: TextLocation
    what: str

    def __str__(self):
        return self.what


class MarkdownReader(mawk.RuleSet):
    """Reads a Markdown file, and splits it up into code blocks and other
    content. The contents of the code blocks get stored in `reference_map`.
    """

    def __init__(self, filename: str):
        self.location = TextLocation(filename)
        self.reference_map = ReferenceMap()
        self.content: list[Content] = []
        self.inside_codeblock: bool = False
        self.current_content: list[str] = []

    def flush_plain_text(self):
        self.content.append(PlainText("\n".join(self.current_content)))
        self.current_content = []

    @mawk.always
    def on_next_line(self, _):
        self.location.line_number += 1

    @mawk.on_match(r"^(?P<indent>\s*)```\s*{(?P<properties>[^{}]*)}\s*$")
    def on_open_codeblock(self, m: re.Match) -> Optional[list[str]]:
        if self.inside_codeblock:
            return None
        self.current_codeblock_indent = m["indent"]
        self.current_codeblock_location = copy(self.location)
        self.current_codeblock_properties = read_properties(m["properties"])
        self.current_content.append(m[0])
        self.flush_plain_text()
        self.inside_codeblock = True
        return []

    @mawk.on_match(r"^(?P<indent>\s*)```\s*$")
    def on_close_codeblock(self, m: re.Match):
        if len(m["indent"]) < len(self.current_codeblock_indent):
            raise MarkdownError(self.location, "indentation error")

        if m["indent"] != self.current_codeblock_indent:
            return  # treat this as code-block content

        # add block to reference-map
        language_class = first(get_classes(self.current_codeblock_properties))
        block_id = get_id(self.current_codeblock_properties)
        target_file = get_attribute(self.current_codeblock_properties, "file")
        ref_name = block_id or target_file
        language = config.get_language(language_class) if language_class else None

        if ref_name is None or language is None:
            self.flush_plain_text()
        else:
            ref = self.reference_map.new_id(
                self.current_codeblock_location.filename, ref_name
            )
            self.reference_map[ref] = CodeBlock(
                language,
                self.current_codeblock_properties,
                self.current_codeblock_indent,
                "\n".join(self.current_content),
                self.current_codeblock_location,
            )
            self.content.append(ref)
            self.current_content = []
        self.current_content.append(m[0])
        self.inside_codeblock = False
        return []

    @mawk.always
    def add_line(self, line: str):
        self.current_content.append(line)
        return []

    def on_eof(self):
        self.flush_plain_text()
        return []


def read_markdown(path: Path) -> tuple[ReferenceMap, list[Content]]:
    with open(path, "r") as f:
        md = MarkdownReader(str(path))
        md.run(f.read())
    return md.reference_map, md.content


@dataclass
class Tangler(mawk.RuleSet):
    reference_map: ReferenceMap
    visited: set[str]

    @mawk.on_match(r"^(?P<indent>\s*)<<(?P<refname>[\w-]+)>>\s*$")
    def on_noweb(self, m: re.Match):
        if m["refname"] in self.visited:
            raise CyclicReference(m["refname"])
        return [
            indent(tangle(self.reference_map, m["refname"], self.visited), m["indent"])
        ]


def tangle(
    reference_map: ReferenceMap, ref_name: str, _visited: Optional[set[str]] = None
) -> str:
    visited = _visited or set()
    visited.add(ref_name)
    source = "\n".join(cb.source for cb in reference_map[ref_name])
    return Tangler(reference_map, visited).run(source)
