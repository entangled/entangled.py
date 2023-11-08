from dataclasses import dataclass


from ..properties import Property
from ..document import ReferenceMap, ReferenceId, CodeBlock
from ..transaction import Transaction


@dataclass
class PrerequisitesFailed(Exception):
    msg: str

    def __str__(self):
        return self.msg


class HookBase:
    class Config:
        pass

    def __init__(self, config: Config):
        pass

    def check_prerequisites(self):
        """When prerequisites aren't met, raise PrerequisitesFailed."""
        return

    def condition(self, props: list[Property]):
        """Condition upon which the `on_read` is triggered. Maybe a bit superfluous
        could be removed in the future."""
        return True

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, code: CodeBlock):
        """Called when the Markdown is being read, during the assembling of
        the reference map."""
        pass

    def pre_tangle(self, refs: ReferenceMap):
        """Executed after reading Markdown, but before actually tangling files.
        This allows the opportunity to add more targets to the reference map.
        """
        pass

    def on_tangle(self, t: Transaction, refs: ReferenceMap):
        """Executed after other targets were tangled, but during the same
        transaction. If you want to write a file, consider doing so as part of
        the transaction."""
        pass

    def post_tangle(self, refs: ReferenceMap):
        """Called after the tangle transaction is finished."""
        pass
