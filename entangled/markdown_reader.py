from typing import Optional
from copy import copy
from pathlib import Path

import re
import mawk
import logging

from .config import config
from .utility import first
from .document import TextLocation, CodeBlock, ReferenceMap, Content, PlainText
from .properties import read_properties, get_attribute, get_classes, get_id
from .hooks.base import HookBase
from .errors.user import ParseError, IndentationError
from . import parsing


class MarkdownReader(mawk.RuleSet):
    """Reads a Markdown file, and splits it up into code blocks and other
    content. The contents of the code blocks get stored in `reference_map`.
    """

    def __init__(
        self,
        filename: str,
        refs: Optional[ReferenceMap] = None,
        hooks: Optional[list[HookBase]] = None,
    ):
        self.location = TextLocation(filename)
        self.reference_map = refs or ReferenceMap()
        self.content: list[Content] = []
        self.inside_codeblock: bool = False
        self.current_content: list[str] = []
        self.current_header: list[str] = []
        self.ignore = False
        self.hooks = hooks or []

    def flush_plain_text(self):
        self.content.append(PlainText("\n".join(self.current_content)))
        self.current_content = []

    @mawk.always
    def on_next_line(self, _):
        self.location.line_number += 1

    @mawk.on_match(config.markers.begin_ignore)
    def on_begin_ignore(self, _):
        self.ignore = True
        logging.debug("ignoring markdown block %s", self.location)

    @mawk.on_match(config.markers.end_ignore)
    def on_end_ignore(self, _):
        self.ignore = False
        logging.debug("end of ignore")

    @mawk.on_match(config.markers.open)
    def on_open_codeblock(self, m: re.Match) -> Optional[list[str]]:
        if self.ignore:
            return None
        if self.inside_codeblock:
            return None
        self.current_codeblock_indent = m["indent"]
        self.current_codeblock_location = copy(self.location)
        self.current_content.append(m[0])
        try:
            self.current_codeblock_properties = read_properties(m["properties"])
            self.flush_plain_text()
            self.inside_codeblock = True
        except parsing.Failure as f:
            logging.error("Parsing error at %s: %s", self.location, f)
            logging.error("Continuing parsing rest of document.")
        return []

    @mawk.on_match(config.markers.close)
    def on_close_codeblock(self, m: re.Match):
        if self.ignore:
            return
        if not self.inside_codeblock:
            return

        if len(m["indent"]) < len(self.current_codeblock_indent):
            raise IndentationError(self.location)

        if m["indent"] != self.current_codeblock_indent:
            return  # treat this as code-block content

        # add block to reference-map
        language_class = first(get_classes(self.current_codeblock_properties))
        block_id = get_id(self.current_codeblock_properties)
        target_file = get_attribute(self.current_codeblock_properties, "file")
        language = config.get_language(language_class) if language_class else None

        if language_class and not language:
            logging.warning(f"Language `{language_class}` unknown at `{self.location}`.")

        header = (
            "\n".join(
                line.removeprefix(self.current_codeblock_indent)
                for line in self.current_header
            )
            if self.current_header
            else None
        )
        content = "\n".join(
            line.removeprefix(self.current_codeblock_indent)
            for line in self.current_content
        )

        ref_name = block_id or target_file
        if ref_name is None:
            ref_name = f"unnamed-{self.location}"

        if language is None:
            self.flush_plain_text()
        else:
            ref = self.reference_map.new_id(
                self.current_codeblock_location.filename, ref_name
            )
            mode = get_attribute(self.current_codeblock_properties, "mode")
            code = CodeBlock(
                language,
                self.current_codeblock_properties,
                self.current_codeblock_indent,
                header,
                content,
                self.current_codeblock_location,
                int(mode, 8) if mode else None
            )
            # logging.debug(repr(code))
            self.reference_map[ref] = code
            if target_file is not None:
                self.reference_map.targets.add(target_file)
            self.content.append(ref)
            self.current_content = []

            for h in self.hooks:
                if h.condition(self.current_codeblock_properties):
                    h.on_read(self.reference_map, ref, code)

        self.current_content.append(m[0])
        self.inside_codeblock = False
        return []

    @mawk.on_match(r"^\s*#!.*$")
    def on_shebang(self, m: re.Match):
        if self.inside_codeblock and not self.current_content:
            self.current_header.append(m[0])
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
