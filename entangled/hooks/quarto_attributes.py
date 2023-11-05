from __future__ import annotations
from dataclasses import dataclass
from itertools import takewhile

from ..properties import Attribute
from ..document import ReferenceId, ReferenceMap, CodeBlock
from .base import HookBase

class Hook(HookBase):
    @dataclass
    class Config(HookBase.Config):
        pass

    def __init__(self, config: Hook.Config):
        self.config = config

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, cb: CodeBlock):
        header = takewhile(lambda line: line[1] == "|", cb.source.splitlines())
        attrs = [Attribute(k.strip(), v.strip()) for k, v in map(lambda line: line.split(":"), header)]
        cb.properties.extend(attrs)

