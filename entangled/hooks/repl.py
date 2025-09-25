from .base import HookBase


class Hook(HookBase):
    @dataclass
    class Config:
        pass

    def on_read(self, code: CodeBlock):
        """Called when the Markdown is being read, before the assembling of
        the reference map."""
        pass

    def on_tangle(self, t: Transaction, refs: ReferenceMap):
        """Executed after other targets were tangled, but during the same
        transaction. If you want to write a file, consider doing so as part of
        the transaction."""
        pass
