from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, TypeVar, Generic, Any, Sequence, Union
import re


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

class Parser(Protocol[T_co]):
    def read(self, inp: str) -> Optional[tuple[T_co, str]]:
        ...

@dataclass
class Id:
    value: str

    def __str__(self):
        return f"#{self.value}"

    @staticmethod
    def read(inp: str) -> Optional[tuple[Id, str]]:
        if m := re.match("#([^ {}]+)", inp):
            return Id(m[1]), inp[m.end():]
        return None


@dataclass
class Class:
    value: str

    def __str__(self):
        return f".{self.value}"

    @staticmethod
    def read(inp: str) -> Optional[tuple[Class, str]]:
        if m := re.match("\\.([^ {}]+)", inp):
            return Class(m[1]), inp[m.end():]
        return None


@dataclass
class Attribute:
    key: str
    value: str

    def __str__(self):
        return f"{self.key}=\"{self.value}\""
    
    @staticmethod
    def read(inp: str) -> Optional[tuple[Attribute, str]]:
        if m := re.match("([^ {}]+) *= *([^ {}\"]+)", inp):
            return Attribute(m[1], m[2]), inp[m.end():]
        if m := re.match("([^ {}]+) *= *\"([^\"]*)\"", inp):
            return Attribute(m[1], m[2]), inp[m.end():]
        return None


Property = Union[Attribute, Class, Id]

@dataclass
class Choice(Generic[T]):
    options: Sequence[Parser[T]]

    def read(self, inp: str) -> Optional[tuple[T, str]]:
        for o in self.options:
            rv = o.read(inp)
            if rv is None:
                continue
            else:
                return rv
        return None


@dataclass
class Many(Generic[T]):
    parser: Parser[T]

    def read(self, inp: str) -> tuple[list[T], str]:
        result: list[T] = []
        while True:
            rv = self.parser.read(inp)
            if rv is None:
                return result, inp
            else:
                value, rest = rv
                result.append(value)
                inp = rest


@dataclass
class Skip:
    what: str

    def read(self, inp: str) -> Optional[tuple[None, str]]:
        if m := re.match(self.what, inp):
            return None, inp[m.end():]
        return None


@dataclass
class Last(Generic[T]):
    first: Parser[Any]
    second: Parser[T]

    def read(self, inp: str) -> Optional[tuple[T, str]]:
        rv = self.first.read(inp)
        if rv is None:
            return None
        else:
            _, rest = rv
            return self.second.read(rest)


def tokenize(p: Parser[T]) -> Parser[T]:
    return Last(Skip(" *"), p)


def read_properties(inp: str) -> list[Property]:
    # Explicit typing is needed to convince MyPy of correctness
    parsers: list[Parser[Property]] = [Id, Class, Attribute]
    result, _ = Many(tokenize(Choice(parsers))).read(inp) 
    return result
