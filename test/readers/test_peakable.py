from collections.abc import Generator
import pytest
from entangled.readers.peekable import Peekable, peekable


def test_peekable_class():
    p = Peekable(iter(range(5)))
    assert p
    assert p.peek() == 0
    assert next(p) == 0
    assert p.peek() == 1
    assert list(p) == [1, 2, 3, 4]
    assert not p

    with pytest.raises(StopIteration):
        _ = p.peek()


def test_peekable_decorator():
    @peekable
    def counter() -> Generator[int]:
        yield from range(10)

    assert isinstance(counter(), Peekable)
