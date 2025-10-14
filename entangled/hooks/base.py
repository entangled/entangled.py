from dataclasses import dataclass
from typing import override
from msgspec import Struct

from ..document import ReferenceMap, CodeBlock
from ..io import Transaction


@dataclass
class PrerequisitesFailed(Exception):
    msg: str

    @override
    def __str__(self):
        return self.msg


class HookBase:
    class Config(Struct):
        pass

    def __init__(self, config: Config):
        pass

    def check_prerequisites(self):
        """When prerequisites aren't met, raise PrerequisitesFailed."""
        pass

    def on_read(self, code: CodeBlock):  # pyright: ignore[reportUnusedParameter]
        """Called when the Markdown is being read, before the assembling of
        the reference map."""
        pass

    def pre_tangle(self, refs: ReferenceMap):  # pyright: ignore[reportUnusedParameter]
        """Executed after reading Markdown, but before actually tangling files.
        This allows the opportunity to add more targets to the reference map.
        """
        pass

    def on_tangle(self, t: Transaction, refs: ReferenceMap):  # pyright: ignore[reportUnusedParameter]
        """Executed after other targets were tangled, but during the same
        transaction. If you want to write a file, consider doing so as part of
        the transaction."""
        pass

    def post_tangle(self, refs: ReferenceMap):  # pyright: ignore[reportUnusedParameter]
        """Called after the tangle transaction is finished."""
        pass
