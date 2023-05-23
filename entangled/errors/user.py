from dataclasses import dataclass
from textwrap import wrap

from ..document import TextLocation


class UserError(Exception):
    def __str__(self):
        return "Unknown user error."


@dataclass
class IndentationError(UserError):
    location: TextLocation

    def __str__(self):
        return f"indentation error at `{self.location}`"


@dataclass
class ParseError(UserError):
    location: TextLocation
    msg: str

    def __str__(self):
        return f"parse error at {self.location}: {self.msg}"


@dataclass
class CyclicReference(UserError):
    ref_name: str
    cycle: list[str]

    def __str__(self):
        cycle_str = " -> ".join(self.cycle)
        return f"Cyclic reference in <<{self.ref_name}>>: {cycle_str}"

