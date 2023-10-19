from dataclasses import dataclass
from typing import Any, Callable

from ..text_location import TextLocation


class UserError(Exception):
    def __str__(self):
        return "Unknown user error."


@dataclass
class ConfigError(UserError):
    expected: str
    got: Any

    def __str__(self):
        return f"Expected {self.expected}, got: {self.got}"


@dataclass
class HelpfulUserError(UserError):
    """Raise a user error and supply an optional function `func` for context.

    Make sure to also execute e.func() in your error handling."""

    msg: str
    func: Callable = lambda: None

    def __str__(self):
        return f"error: {self.msg}"


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


@dataclass
class MissingReference(UserError):
    ref_name: str
    location: TextLocation

    def __str__(self):
        return f"Missing reference `{self.ref_name}` at `{self.location}`"
