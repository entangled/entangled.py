from dataclasses import dataclass, field
from collections.abc import Iterator, Callable
import functools


@dataclass
class Peekable[T]:
    """
    An iterator that allows peeking one element into the future.
    """
    iterator: Iterator[T]
    head: list[T] = field(default_factory=list)

    def peek(self) -> T:
        if not self.head:
            try:
                self.head.append(next(self.iterator))
            except StopIteration:
                raise
        return self.head[0]

    def __bool__(self):
        if not self.head:
            try:
                _ = self.peek()
            except StopIteration:
                return False
        return True

    def __next__(self):
        if self.head:
            return self.head.pop()
        return next(self.iterator)

    def __iter__(self):
        return self


def peekable[**P, T](f: Callable[P, Iterator[T]]) -> Callable[P, Peekable[T]]:
    @functools.wraps(f)
    def peekabled(*args: P.args, **kwargs: P.kwargs) -> Peekable[T]:
        return Peekable(f(*args, **kwargs))
    return peekabled
