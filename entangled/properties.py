"""Properties of code blocks. These properties are the same as CSS selector
properties: id, class and attribute."""

from __future__ import annotations

from typing import Optional, Union, ClassVar, Iterable
from dataclasses import dataclass
import re

from .parsing import (
    Parser,
    many,
    choice,
    tokenize,
    matching,
    Parsable,
    starmap,
    Failure,
)


@dataclass
class Id(Parsable):
    value: str
    _pattern: ClassVar[Parser] = matching(r"#([a-zA-Z]\S*)")

    def __str__(self):
        return f"#{self.value}"

    @staticmethod
    def __parser__():
        return Id._pattern >> starmap(Id)


@dataclass
class Class(Parsable):
    value: str
    _pattern: ClassVar[Parser] = matching(r"\.([a-zA-Z]\S*)")

    def __str__(self):
        return f".{self.value}"

    @staticmethod
    def __parser__():
        return Class._pattern >> starmap(Class)


@dataclass
class Attribute(Parsable):
    key: str
    value: str

    _pattern1: ClassVar[Parser] = matching(
        r"([a-zA-Z]\S*)\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\""
    )
    _pattern2: ClassVar[Parser] = matching(r"([a-zA-Z]\S*)\s*=\s*(\S+)")

    def __str__(self):
        return f'{self.key}="{self.value}"'

    @staticmethod
    def __parser__():
        return choice(Attribute._pattern1, Attribute._pattern2) >> starmap(Attribute)


Property = Union[Attribute, Class, Id]


def read_properties(inp: str) -> list[Property]:
    """Read properties from a string. Example:

    >>> read_properties(".python #foo file=bar.py")
    [Id("python"), Class("foo"), Attribute("file", "bar.py")]
    """
    # Explicit typing is needed to convince MyPy of correctness
    # parsers: list[Parser[Property]] = [Id, Class, Attribute]
    result, _ = many(tokenize(choice(Id, Class, Attribute))).read(inp)
    return result


def get_id(props: list[Property]) -> Optional[str]:
    """Get the first given Id in a property list."""
    try:
        return next(p.value for p in props if isinstance(p, Id))
    except StopIteration:
        return None


def get_classes(props: list[Property]) -> Iterable[str]:
    """Get all given Classes in a property list."""
    return (p.value for p in props if isinstance(p, Class))


def get_attribute(props: list[Property], key: str) -> Optional[str]:
    """Get the value of an Attribute in a property list."""
    try:
        return next(p.value for p in props if isinstance(p, Attribute) and p.key == key)
    except StopIteration:
        return None
