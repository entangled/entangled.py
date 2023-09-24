from dataclasses import dataclass

from ..properties import Property
from ..document import ReferenceMap, ReferenceId, CodeBlock


@dataclass
class PrerequisitesFailed(Exception):
    msg: str

    def __str__(self):
        return self.msg


class HookBase:
    @staticmethod
    def check_prerequisites():
        """When prerequisites aren't met, raise PrerequisitesFailed."""
        return

    def condition(self, props: list[Property]):
        raise NotImplementedError()

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, code: CodeBlock):
        raise NotImplementedError()

    def pre_tangle(self, refs: ReferenceMap):
        pass

    def post_tangle(self, refs: ReferenceMap):
        pass
