from __future__ import annotations
from dataclasses import dataclass
from itertools import takewhile

from ..properties import Attribute
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

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, cb: CodeBlock):
        trigger = f"{cb.language.comment.open}|"
        header = (line[len(trigger):] for line in cb.source.splitlines() if line.startswith(trigger))
        attrs = [Attribute(k.strip(), v.strip()) for k, v in map(lambda line: line.split(":"), header)]
        cb.properties.extend(attrs)
        log.debug(f"quarto attrs on {ref}: {attrs}")

