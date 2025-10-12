"""Properties of code blocks. These properties are the same as CSS selector
properties: id, class and attribute."""

from __future__ import annotations

from typing import Any, cast, override
from collections.abc import Iterable
from dataclasses import dataclass


from .parsing import (
    Parser,
    many,
    tokenize,
    matching,
    splat,
)


@dataclass
class Id:
    value: str

    @override
    def __str__(self):
        return f"#{self.value}"


id_p: Parser[Id] = cast(Parser[tuple[str]], matching(r"#([a-zA-Z]\S*)")) >> splat(Id)


@dataclass
class Class:
    value: str

    @override
    def __str__(self):
        return f".{self.value}"


class_p: Parser[Class] = cast(Parser[tuple[str]], matching(r"\.?([a-zA-Z]\S*)")) >> splat(Class)


@dataclass
class Attribute:
    key: str
    value: Any  # pyright: ignore[reportExplicitAny]

    @override
    def __str__(self):
        return f'{self.key}="{self.value}"'  # pyright: ignore[reportAny]


attribute_p: Parser[Attribute] = cast(Parser[tuple[str, str]],
        matching(r"([a-zA-Z]\S*)\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"") |
        matching(r"([a-zA-Z]\S*)\s*=\s*(\S+)")) >> splat(Attribute)


Property = Attribute | Class | Id


def read_properties(inp: str) -> list[Property]:
    """Read properties from a string. Example:

    >>> read_properties(".python #foo file=bar.py")
    [Id("python"), Class("foo"), Attribute("file", "bar.py")]
    """
    # Explicit typing is needed to convince MyPy of correctness
    # parsers: list[Parser[Property]] = [Id, Class, Attribute]
    result, _ = many(tokenize(id_p | attribute_p | class_p)).read(inp)
    return result


def get_id(props: list[Property]) -> str | None:
    """Get the first given Id in a property list."""
    try:
        return next(p.value for p in props if isinstance(p, Id))
    except StopIteration:
        return None


def get_classes(props: list[Property]) -> Iterable[str]:
    """Get all given Classes in a property list."""
    return (p.value for p in props if isinstance(p, Class))


def get_attribute(props: list[Property], key: str) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """Get the value of an Attribute in a property list."""
    try:
        return next(p.value for p in props if isinstance(p, Attribute) and p.key == key)  # pyright: ignore[reportAny]
    except StopIteration:
        return None
