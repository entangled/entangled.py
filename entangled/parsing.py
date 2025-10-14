"""Monadic recursive descent parser combinator. This is used to custom
light weight parsing within Entangled, mainly parsing the class, id and
attribute properties of code blocks in markdown."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Never,
    Callable,
    override,
)
import re


@dataclass
class Failure(Exception):
    """Base class for parser failures."""

    msg: str

    @override
    def __str__(self):
        return self.msg


class EndOfInput(Failure):
    """Raised at end of input."""

    def __init__(self):
        super().__init__("end of input")


@dataclass
class Expected(Failure):
    """Input was different than expected."""

    inp: str

    @property
    def expected(self):
        return self.msg

    @override
    def __str__(self):
        if len(self.inp) > 20:
            inp = f"{self.inp[:20]} ..."
        else:
            inp = self.inp
        return f'expected: {self.expected}, got: "{inp}"'


@dataclass
class ChoiceFailure(Expected):
    """All options of a choice parser failed."""

    failures: list[Failure]

    @property
    @override
    def expected(self):
        return " | ".join(str(f) for f in self.failures)


class Parser[T](ABC):
    """Base class for parsers."""

    @abstractmethod
    def read(self, inp: str) -> tuple[T, str]:
        """Read a string and return an object and the remainder of the string."""
        raise NotImplementedError()

    def __rshift__[U](self, f: Callable[[T], Parser[U]]) -> Parser[U]:
        return bind(self, f)

    def then[U](self, p: Parser[U]) -> Parser[U]:
        return bind(self, lambda _: p)

    def __or__[U](self, other: Parser[U]) -> Choice[T, U]:
        return Choice(self, other)


def splat[*Args, U](f: Callable[[*Args], U]) -> Callable[[tuple[*Args]], Parser[U]]:
    def wrapper(args: tuple[*Args]) -> Parser[U]:
        return pure(f(*args))
    return wrapper


@dataclass
class ParserWrapper[T](Parser[T]):
    """Wrapper class for functional parser."""

    f: Callable[[str], tuple[T, str]]

    @override
    def read(self, inp: str) -> tuple[T, str]:
        return self.f(inp)


def fmap[T, U](f: Callable[[T], U]) -> Callable[[T], Parser[U]]:
    """Map a parser action over a function."""
    return lambda x: pure(f(x))


def parser[T](f: Callable[[str], tuple[T, str]]) -> Parser[T]:
    """Parser decorator."""
    return ParserWrapper(f)


def pure[T](x: T) -> Parser[T]:
    """Parser that always succeeds and returns value `x`."""
    return parser(lambda inp: (x, inp))


def fail(msg: str) -> Parser[Never]:
    """Parser that always fails with a message `msg`."""

    @parser
    def _fail(_: str) -> tuple[Never, str]:
        raise Failure(msg)

    return _fail


@parser
def item(inp: str) -> tuple[str, str]:
    """Parser that takes a single character from a string."""
    if len(inp) == 0:
        raise EndOfInput
    return inp[0], inp[1:]


def bind[T, U](p: Parser[T], f: Callable[[T], Parser[U]]) -> Parser[U]:
    """Fundamental monadic combinator. First parses `p`, then passes
    the value to `f`, giving a new parser that also knows the result
    of the first one."""

    @parser
    def bound(inp: str):
        x, inp = p.read(inp)
        return f(x).read(inp)

    return bound


# class Sequence(Generic[*Ts], ParserWrapper[tuple[*Ts]]):
#     """Parses a sequence of parsers to a tuple of results. A Sequence
#     parser can be extended using the `*` operator."""
#     def __mul__(self, q: Parser[U]):
#         return Sequence(self >> (lambda t: q >> (lambda x: pure(t + (x,)))))

# seq = Sequence(pure(()))

@dataclass
class Choice[T, U](Parser[T | U]):
    first: Parser[T]
    second: Parser[U]

    @override
    def read(self, inp: str) -> tuple[T | U, str]:
        failures: list[Failure]

        try:
            return self.first.read(inp)
        except ChoiceFailure as f:
            failures = f.failures
        except Failure as f:
            failures = [f]

        try:
            return self.second.read(inp)
        except ChoiceFailure as f:
            failures.extend(f.failures)
        except Failure as f:
            failures.append(f)

        raise ChoiceFailure("", inp, failures)


def optional[T, U](p: Parser[T], default: U | None = None) -> Choice[T, U | None]:
    return p | pure(default)


def many[T](p: Parser[T]) -> Parser[list[T]]:
    @parser
    def _many(inp: str) -> tuple[list[T], str]:
        result: list[T] = []
        while True:
            try:
                value, inp = p.read(inp)
                result.append(value)
            except Failure:
                break
        return result, inp

    return _many


def matching(regex: str) -> Parser[tuple[str, ...]]:
    pattern = re.compile(f"^{regex}")

    @parser
    def _matching(inp: str) -> tuple[tuple[str, ...], str]:
        if m := pattern.match(inp):
            return m.groups(), inp[m.end() :]
        raise Expected(f"/^{regex}/", inp)

    return _matching


def fullmatch(regex: str) -> Parser[str]:
    pattern = re.compile(f"^{regex}")

    @parser
    def _fullmatch(inp: str):
        if m := pattern.match(inp):
            return m[0], inp[m.end() :]
        raise Expected(f"/^{regex}/", inp)

    return _fullmatch


space: Parser[str] = fullmatch(r"\s+")


def tokenize[T](p: Parser[T]) -> Parser[T]:
    return optional(space).then(p)
