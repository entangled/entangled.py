from copy import copy
from dataclasses import dataclass, field
from pathlib import Path

import re
from typing import override
import mawk
import logging

from entangled.config.language import Language

from .config import config
from .utility import first
from .text_location import TextLocation
from .document import CodeBlock, ReferenceMap, Content, PlainText, RawContent
from .properties import Property, read_properties, get_attribute, get_classes, get_id
from .hooks.base import HookBase
from .errors.user import IndentationError
from . import parsing


@dataclass
class PartialCodeBlock:
    indent: str
    open_line: str
    origin: TextLocation
    properties: list[Property] = field(default_factory=list)
    close_line: str | None = None
    source: str | None = None
    language: Language | None = None
    header: str | None = None
    mode: int | None = None

    def finalize(self) -> CodeBlock:
        assert self.close_line is not None
        assert self.source is not None

        return CodeBlock(
            properties = self.properties,
            indent = self.indent,
            open_line = self.open_line,
            close_line = self.close_line,
            source = self.source,
            origin = self.origin,
            language = self.language,
            header = self.header,
            mode = self.mode
        )


class MarkdownLexer(mawk.RuleSet):
    """Reads a Markdown file, and splits it up into code blocks and other
    content."""
    def __init__(
        self,
        filename: Path
    ):
        self.location: TextLocation = TextLocation(filename)
        self.raw_content: list[RawContent] = []
        self.inside_codeblock: bool = False
        self.current_content: list[str] = []
        self.current_codeblock: PartialCodeBlock | None = None
        self.ignore: bool = False

    def flush_plain_text(self):
        if self.current_content:
            self.raw_content.append(PlainText("\n".join(self.current_content)))
        self.current_content = []

    @mawk.always
    def on_next_line(self, _):
        self.location.line_number += 1

    @mawk.on_match(config.get.markers.begin_ignore)
    def on_begin_ignore(self, _):
        self.ignore = True
        logging.debug("ignoring markdown block %s", self.location)

    @mawk.on_match(config.get.markers.end_ignore)
    def on_end_ignore(self, _):
        self.ignore = False
        logging.debug("end of ignore")

    @mawk.on_match(config.get.markers.open)
    def on_open_codeblock(self, m: re.Match[str]) -> list[str] | None:
        if self.ignore:
            return None
        if self.inside_codeblock:
            return None
        logging.debug("triggered on codeblock: %s", m.group(0))
        self.current_codeblock = PartialCodeBlock(
            indent = m["indent"],
            origin = copy(self.location),
            open_line = m[0].removeprefix(m["indent"])
        )
        try:
            self.current_codeblock.properties.extend(read_properties(m["properties"]))
            logging.debug("properties: %s", self.current_codeblock.properties)
            self.flush_plain_text()
            self.inside_codeblock = True
        except parsing.Failure as f:
            logging.error("%s: Parsing error: %s", self.location, f)
            logging.error("Continuing parsing rest of document.")
        return []

    @mawk.on_match(config.get.markers.close)
    def on_close_codeblock(self, m: re.Match[str]) -> list[str] | None:
        if self.ignore:
            return None
        if not self.inside_codeblock or self.current_codeblock is None:
            return None

        if len(m["indent"]) < len(self.current_codeblock.indent):
            raise IndentationError(self.location)

        if m["indent"] != self.current_codeblock.indent:
            return None  # treat this as code-block content

        language_class = first(get_classes(self.current_codeblock.properties))
        language = config.get_language(language_class) if language_class else None
        if language_class and not language:
            logging.warning(f"`{self.location}`: language `{language_class}` unknown.")
        self.current_codeblock.language = language

        self.current_codeblock.source = "\n".join(
            line.removeprefix(self.current_codeblock.indent)
            for line in self.current_content
        )

        self.current_codeblock.close_line = m[0].removeprefix(self.current_codeblock.indent)

        self.raw_content.append(self.current_codeblock.finalize())
        self.current_content = []

        self.current_codeblock = None
        self.inside_codeblock = False
        return []

    @mawk.always
    def add_line(self, line: str) -> list[str]:
        self.current_content.append(line)
        return []

    @override
    def on_eof(self) -> list[str]:
        self.flush_plain_text()
        return []


def read_markdown_file(
    path: Path,
    refs: ReferenceMap | None = None,
    hooks: list[HookBase] | None = None) \
    -> tuple[ReferenceMap, list[Content]]:
    """
    Read a Markdown file.

    Args:
        path: Path to the file.
        refs: If given, references are added to this existing reference map.
        hooks: List of hooks to be processed.

    Returns:
        A reference map and a list of content.

    This splits the Markdown file into code blocks and other text. The resulting
    content is a list of `PlainText | ReferenceId`. Each `ReferenceId` can be
    looked up in the reference map.
    """
    with open(path, "r") as f:
        rel_path = path.resolve().relative_to(Path.cwd())
        return read_markdown_string(f.read(), rel_path, refs, hooks)


def read_markdown_string(
        text: str,
        path_str: Path | None = None,
        refs: ReferenceMap | None = None,
        hooks: list[HookBase] | None = None) \
        -> tuple[ReferenceMap, list[Content]]:
    """
    Parse Markdown from a string.

    Args:
        text: Input string.
        path: Path to the file from which the string was read, used for printing
              error messages.
        refs: If given, references are added to this existing reference map.
        hooks: List of hooks to be processed.

    Returns:
        A reference map and a list of content.
    """
    path_str = path_str or Path("-")
    md = MarkdownLexer(path_str)
    _ = md.run(text)

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
