from __future__ import annotations
from dataclasses import dataclass
from itertools import takewhile
import yaml

from ..properties import Attribute, Class, Id
from ..document import ReferenceId, ReferenceMap, CodeBlock
from .base import HookBase
from ..logging import logger


log = logger()


class Hook(HookBase):
    @dataclass
    class Config(HookBase.Config):
        pass

    def __init__(self, config: Hook.Config):
        self.config = config

    def on_read(self, code: CodeBlock):
        log.debug("quarto filter: %s", code)

        if code.language is None:
            return

        trigger = f"{code.language.comment.open}|"
        header = "\n".join(
            line[len(trigger):] for line in code.source.splitlines()
            if line.startswith(trigger))

        attrs = yaml.safe_load(header)
        if attrs is None:
            return
        if not isinstance(attrs, dict):
            log.warning("quarto attributes do not evaluate to dictionary; skipping")
            log.warning(f"tried to parse: {header}")
            return

        if "id" in attrs.keys():
            code.properties.append(Id(attrs["id"]))

        if "classes" in attrs.keys():
            code.properties.extend(Class(c) for c in attrs["classes"])

        code.properties.extend(Attribute(k, v) for k, v in attrs.items()
                                               if k not in ("id", "classes"))

        log.debug("quarto attributes: %s", attrs)
