"""Monadic recursive descent parser combinator. This is used to custom 
light weight parsing within Entangled, mainly parsing the class, id and
attribute properties of code blocks in markdown."""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TypeVar,
    TypeVarTuple,
    Generic,
    Callable,
    Union,
    Any,
    Optional,
    ParamSpec,
)
import re


T = TypeVar("T")
Ts = TypeVarTuple("Ts")
U = TypeVar("U")
P = ParamSpec("P")
T_co = TypeVar("T_co", covariant=True)


@dataclass
class Failure(Exception):
    """Base class for parser failures."""

    msg: str

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

    def __str__(self):
        if len(self.inp) > 20:
            inp = f"{self.inp[:20]} ..."
        return f'expected: {self.expected}, got: "{self.inp}"'


@dataclass
class ChoiceFailure(Expected):
    """All options of a choice parser failed."""

    failures: list[Failure]

    @property
    def expected(self):
        return " | ".join(str(f) for f in self.failures)


class Parser(Generic[T]):
    """Base class for parsers."""

    def read(self, _: str) -> tuple[T, str]:
        """Read a string and return an object the remainder of the string."""
        raise NotImplementedError()

    def __rshift__(self, f: Callable[[T], Parser[U]]) -> Parser[U]:
        return bind(self, f)

    def then(self, p: Parser[U]) -> Parser[U]:
        return bind(self, lambda _: p)


def starmap(f: Callable[..., U]) -> Callable[[tuple], Parser[U]]:
    return lambda args: pure(f(*args))


class ParserMeta(Generic[T], Parser[T], type):
    def read(cls, inp: str) -> tuple[T, str]:
        return cls.__parser__().read(inp)  # type: ignore


class Parsable(Generic[T], metaclass=ParserMeta):
    """Base class for Parsable objects. Parsables need to define a
    `__parser__()` method that should return a `Parser[Self]`. That
    way a Parsable class is also a `Parser` object for itself.
    This allows for nicely expressive grammars."""

    pass


@dataclass
class ParserWrapper(Generic[T], Parser[T]):
    """Wrapper class for functional parser."""

    f: Callable[[str], tuple[T, str]]

    def read(self, inp: str) -> tuple[T, str]:
        return self.f(inp)


def fmap(f: Callable[[T], U]) -> Callable[[T], Parser[U]]:
    """Map a parser action over a function."""
    return lambda x: pure(f(x))


def parser(f: Callable[[str], tuple[T, str]]) -> Parser[T]:
    """Parser decorator."""
    return ParserWrapper(f)


def pure(x: T) -> Parser[T]:
    """Parser that always succeeds and returns value `x`."""
    return parser(lambda inp: (x, inp))


def fail(msg: str) -> Parser[Any]:
    """Parser that always fails with a message `msg`."""

    @parser
    def _fail(_: str) -> tuple[Any, str]:
        raise Failure(msg)

    return _fail


@parser
def item(inp: str) -> tuple[str, str]:
    """Parser that takes a single character from a string."""
    if len(inp) == 0:
        raise EndOfInput
    return inp[0], inp[1:]


def bind(p: Parser[T], f: Callable[[T], Parser[U]]) -> Parser[U]:
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


def choice(*options: Parser[Any]) -> Parser[Any]:
    @parser
    def _choice(inp: str) -> tuple[Any, str]:
        failures = []

        for o in options:
            try:
                return o.read(inp)
            except Failure as f:
                failures.append(f)
                continue

        raise ChoiceFailure("", inp, failures)

    return _choice


def optional(p: Parser[T], default: Optional[U] = None) -> Parser[Union[T, U]]:
    return choice(p, pure(default))


def many(p: Parser[T]) -> Parser[list[T]]:
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


def matching(regex: str) -> Parser[tuple[str | Any, ...]]:
    pattern = re.compile(f"^{regex}")

    @parser
    def _matching(inp: str) -> tuple[tuple[str | Any, ...], str]:
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


space = matching(r"\s+")


def tokenize(p: Parser[T]) -> Parser[T]:
    return optional(space).then(p)
