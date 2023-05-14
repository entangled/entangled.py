from typing import Any
from dataclasses import dataclass, field
from textwrap import wrap


@dataclass
class InternalError(Exception):
    msg: str
    irritants: list[Any] = field(default_factory=list)

    def __str__(self):
        return f"Internal error: {self.msg}"


@dataclass
class CyclicReference(Exception):
    ref_name: str

    def __str__(self):
        return f"Cyclic reference in <<{self.ref_name}>>"


def bug_contact():
    print(
        wrap(
            "This error is due to an internal bug in Entangled. "
            "Please file an issue including the above stack trace "
            "and example content to reproduce the exception "
            "at https://github.com/entangled/entangled.py/."
        )
    )
