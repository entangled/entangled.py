from __future__ import annotations
import re
import textwrap
from typing import Any, final, override
import yaml

from entangled.config.language import Language

from ..properties import Attribute, Class, Id, Property
from ..document import CodeBlock
from .base import HookBase
from ..logging import logger


log = logger()


def split_yaml_header(language: Language, source: str) -> tuple[str, str, object]:
    """Split source into YAML header and body."""
    trigger = re.escape(language.comment.open) + r"\s*\|(.*)"
    lines = source.splitlines()
    header_lines: list[str] = []
    body_start: int = 0

    for i, line in enumerate(lines):
        if m := re.match(trigger, line):
            header_lines.append(m.group(1))
            continue

        body_start = i
        break

    return "\n".join(lines[:body_start]), "\n".join(lines[body_start:]), yaml.safe_load("\n".join(header_lines))


def amend_code_properties(code_block: CodeBlock):
    language = code_block.language
    if not language:
        return

    source = code_block.source
    props: list[Property] = []

    header, body, attrs = split_yaml_header(language, source)

    if attrs is None:
        return

    if not isinstance(attrs, dict):
        log.warning(f"{code_block.origin}: Quarto attributes do not evaluate to dictionary; skipping")
        log.warning(f"tried to parse:\n{header}")
        return

    if "id" in attrs.keys():
        if not isinstance(attrs["id"], str):
            log.warning(f"{code_block.origin}: Quarto id does not evaluate to string; skipping")
            log.warning(f"tried to parse:\n{header}")
            return
        props.append(Id(attrs["id"]))

    if "classes" in attrs.keys():
        classes = attrs["classes"]
        if not all(isinstance(c, str) for c in classes):
            log.warning(f"{code_block.origin}: Quarto classes do not evaluate to strings; skipping")
            log.warning(f"tried to parse:\n{header}")
            return
        props.extend(Class(c) for c in classes)

    props.extend(Attribute(str(k), v) for k, v in attrs.items()
                 if k not in ("id", "classes"))

    code_block.source = body
    code_block.open_line += "\n" + header
    code_block.properties.extend(props)


@final
class Hook(HookBase):
    def __init__(self, config: Hook.Config):
        super().__init__(config)
        self.config = config

    @override
    def on_read(self, code: CodeBlock):
        log.debug("quarto filter: %s", code)
        amend_code_properties(code)
