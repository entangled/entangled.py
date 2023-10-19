from typing import Any
from dataclasses import dataclass, field
from textwrap import wrap
import logging


@dataclass
class InternalError(Exception):
    msg: str
    irritants: list[Any] = field(default_factory=list)

    def __str__(self):
        return f"Internal error: {self.msg}"


def bug_contact(e: Exception):
    logging.error(
        "This error is due to an internal bug in Entangled. Please file an "
        "issue including the above stack trace "
        "and example content to "
        "reproduce the exception at https://github.com/entangled/entangled.py/."
    )
