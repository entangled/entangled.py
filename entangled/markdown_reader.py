from typing import Optional
from dataclasses import dataclass
from copy import copy
from pathlib import Path

import re
import mawk

from .config import config
from .utility import first
from .document import TextLocation, CodeBlock, ReferenceMap, Content, PlainText
from .properties import read_properties, get_attribute, get_classes, get_id
from .hooks.base import HookBase


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

    def __init__(self, filename: str, refs: Optional[ReferenceMap] = None, hooks: Optional[list[HookBase]] = None):
        self.location = TextLocation(filename)
        self.reference_map = refs or ReferenceMap()
        self.content: list[Content] = []
        self.inside_codeblock: bool = False
        self.current_content: list[str] = []
        self.hooks = hooks or []

    def flush_plain_text(self):
        self.content.append(PlainText("\n".join(self.current_content)))
        self.current_content = []

    @mawk.always
    def on_next_line(self, _):
        self.location.line_number += 1

    @mawk.on_match(config.markers.open)
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

    @mawk.on_match(config.markers.close)
    def on_close_codeblock(self, m: re.Match):
        if not self.inside_codeblock:
            return
        
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
            code = CodeBlock(
                language,
                self.current_codeblock_properties,
                self.current_codeblock_indent,
                "\n".join(self.current_content),
                self.current_codeblock_location,
            )
            self.reference_map[ref] = code
            if target_file is not None:
                self.reference_map.targets.add(target_file)
            self.content.append(ref)
            self.current_content = []

            for h in self.hooks:
                if h.condition(self.current_codeblock_properties):
                    h.on_read(ref, code)
            
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
        path_str = str(path.resolve().relative_to(Path.cwd()))
        md = MarkdownReader(path_str)
        md.run(f.read())
    return md.reference_map, md.content
