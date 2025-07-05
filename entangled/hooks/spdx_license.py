from ..document import CodeBlock
from .base import HookBase


class Hook(HookBase):
    def on_read(self, code: CodeBlock):
        lines = code.source.splitlines()
        if lines and "SPDX-License-Identifier" in lines[0]:
            code.header = lines[0]
            code.source = "\n".join(lines[1:])
