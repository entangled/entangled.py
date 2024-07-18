from typing import Optional
from copy import copy
from pathlib import Path

import re
import mawk
import logging

from .config import config
from .utility import first
from .document import TextLocation, CodeBlock, ReferenceMap, Content, PlainText, RawContent
from .properties import read_properties, get_attribute, get_classes, get_id
from .hooks.base import HookBase
from .errors.user import ParseError, IndentationError
from . import parsing


class MarkdownLexer(mawk.RuleSet):
    """Reads a Markdown file, and splits it up into code blocks and other
    content."""
    def __init__(
        self,
        filename: str
    ):
        self.location = TextLocation(filename)
        self.raw_content: list[RawContent] = []
        self.inside_codeblock: bool = False
        self.current_content: list[str] = []
        self.ignore = False

    def flush_plain_text(self):
        self.raw_content.append(PlainText("\n".join(self.current_content)))
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
        logging.debug("triggered on codeblock: %s", m.group(0))
        self.current_codeblock_indent = m["indent"]
        self.current_codeblock_location = copy(self.location)
        self.current_content.append(m[0])
        try:
            self.current_codeblock_properties = read_properties(m["properties"])
            logging.debug("properties: %s", self.current_codeblock_properties)
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

        language_class = first(get_classes(self.current_codeblock_properties))
        language = config.get_language(language_class) if language_class else None
        if language_class and not language:
            logging.warning(f"Language `{language_class}` unknown at `{self.location}`.")


        content = "\n".join(
            line.removeprefix(self.current_codeblock_indent)
            for line in self.current_content
        )

        code = CodeBlock(
            self.current_codeblock_properties,
            self.current_codeblock_indent,
            content,
            self.current_codeblock_location,
            language
        )

        self.raw_content.append(code)
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


def read_markdown_file(
    path: Path,
    refs: ReferenceMap | None = None,
    hooks: list[HookBase] | None = None) \
    -> tuple[ReferenceMap, list[Content]]:

    with open(path, "r") as f:
        path_str = str(path.resolve().relative_to(Path.cwd()))
        return read_markdown_string(f.read(), path_str, refs, hooks)


def read_markdown_string(
        text: str,
        path_str: str = "-",
        refs: ReferenceMap | None = None,
        hooks: list[HookBase] | None = None) \
        -> tuple[ReferenceMap, list[Content]]:
    md = MarkdownLexer(path_str)
    md.run(text)

    hooks = hooks if hooks is not None else []
    refs = refs if refs is not None else ReferenceMap()

    def process(r: RawContent) -> Content:
        match r:
            case CodeBlock():
                for h in hooks: h.on_read(r)
                block_id = get_id(r.properties)
                target_file = get_attribute(r.properties, "file")

                if mode := get_attribute(r.properties, "mode"):
                    r.mode = int(mode, 8)

                ref_name = block_id or target_file
                if ref_name is None:
                    ref_name = f"unnamed-{r.origin}"
                ref = refs.new_id(r.origin.filename, ref_name)

                refs[ref] = r
                if target_file is not None:
                    refs.targets.add(target_file)
                if target_file is not None and block_id is not None:
                    refs.alias[target_file] = block_id

                return ref

            case PlainText(): return r

    content = list(map(process, md.raw_content))
    logging.debug("found ids: %s", list(refs.map.keys()))
    return refs, content
