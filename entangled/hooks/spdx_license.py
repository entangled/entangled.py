from typing import final, override
from ..model import CodeBlock
from .base import HookBase


@final
class Hook(HookBase):
    @override
    def on_read(self, code: CodeBlock):
        lines = code.source.splitlines(keepends=True)
        if lines and "SPDX-License-Identifier" in lines[0]:
            code.header = (code.header or "") + lines[0]
            code.source = "".join(lines[1:])
