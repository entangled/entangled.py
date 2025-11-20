from dataclasses import dataclass
from typing import Any, override, Callable
from pathlib import Path

import logging
import sys

from ..text_location import TextLocation


class UserError(Exception):
    def __str__(self) -> str:
        return "Unknown user error."

    def handle(self):
        pass

@dataclass
class ConfigError(UserError):
    expected: str
    got: Any

    def __str__(self):
        return f"Expected {self.expected}, got: {self.got}"


@dataclass
class HelpfulUserError(UserError):
    """Raise a user error with a message."""
    msg: str
    action: Callable[[], None] = lambda: None

    def __str__(self):
        return f"error: {self.msg}"

    @override
    def handle(self):
        self.action()
        logging.error(str(self))
        sys.exit(-1)
        

@dataclass
class FileError(UserError):
    filename: Path

    def __str__(self):
        return f"file not found `{self.filename}`"


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
class CodeAttributeError(UserError):
    origin: TextLocation
    msg: str

    @override
    def __str__(self) -> str:
        return f"{self.origin}: Attribute error: {self.msg}"
