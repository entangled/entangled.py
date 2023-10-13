from dataclasses import dataclass, field
from pathlib import Path

import mawk
import re

from .document import ReferenceId, TextLocation, ReferenceMap
from .errors.user import IndentationError


@dataclass
class Frame:
    ref: ReferenceId
    indent: str
    content: list[str] = field(default_factory=list)


class CodeReader(mawk.RuleSet):
    """Reads an annotated code file."""

    def __init__(self, path: str, refs: ReferenceMap):
        self.location = TextLocation(path, 0)
        self.stack: list[Frame] = [Frame(ReferenceId("#root#", "", -1), "")]
        self.refs: ReferenceMap = refs

    @property
    def current(self) -> Frame:
        return self.stack[-1]

    @mawk.always
    def increase_line_number(self, _):
        self.location.line_number += 1

    @mawk.on_match(
        r"^(?P<indent>\s*).* ~/~ begin <<(?P<source>[^#<>]+)#(?P<ref_name>[^#<>]+)>>\[(?P<ref_count>init|\d+)\]"
    )
    def on_block_begin(self, m: re.Match):
        ref_name = m["ref_name"]

        # When there are lines above the first ref, say a shebang, swap
        # them into the first block.
        if len(self.stack) == 1 and len(self.stack[0].content) > 0:
            content = self.stack[0].content
            self.stack[0].content = []
        else:
            content = []

        if m["ref_count"] == "init":
            ref_count = 0
            if not m["indent"].startswith(self.current.indent):
                raise IndentationError(self.location)
            indent = m["indent"].removeprefix(self.current.indent)
            self.current.content.append(f"{indent}<<{ref_name}>>")
        else:
            ref_count = int(m["ref_count"])

        self.stack.append(
            Frame(
                ReferenceId(m["ref_name"], m["source"], ref_count), m["indent"], content
            )
        )
        return []

    @mawk.on_match(r"^(?P<indent>\s*).* ~/~ end")
    def on_block_end(self, m: re.Match):
        if m["indent"] != self.current.indent:
            raise IndentationError(self.location)
        self.refs[self.current.ref].source = "\n".join(self.current.content)
        self.stack.pop()
        return []

    @mawk.always
    def otherwise(self, line: str):
        if line.strip() == "":
            self.current.content.append("")
            return []
        if not line.startswith(self.current.indent):
            raise IndentationError(self.location)
        self.current.content.append(line.removeprefix(self.current.indent))
        return []
