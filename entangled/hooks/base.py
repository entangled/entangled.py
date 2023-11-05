from dataclasses import dataclass

from ..properties import Property
from ..document import ReferenceMap, ReferenceId, CodeBlock


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
        return True

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, code: CodeBlock):
        pass

    def pre_tangle(self, refs: ReferenceMap):
        pass

    def post_tangle(self, refs: ReferenceMap):
        pass
