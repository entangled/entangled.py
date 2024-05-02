from __future__ import annotations

from entangled.construct import (construct, FromStr)
from entangled.errors.user import ConfigError
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import pytest


def test_primitives():
    assert construct(dict, {"a": 3}) == {"a": 3}
    assert construct(bool, True) == True
    assert construct(str, "hello") == "hello"
    assert construct(list, [1, 2, 3, 3]) == [1, 2, 3, 3]
    assert construct(set, [1, 2, 3, 3]) == {1, 2, 3}

    with pytest.raises(ConfigError):
        construct(str, True)
    with pytest.raises(ConfigError):
        construct(list, {"a": 3})


def test_typed_primitives():
    assert construct(dict[str, int], {"a": 3}) == {"a": 3}
    assert construct(list[int], [1, 2, 3, 3]) == [1, 2, 3, 3]
    assert construct(set[int], [1, 2, 3, 3]) == {1, 2, 3}

    with pytest.raises(ConfigError):
        construct(list[int], ["1", "2", "3"])


def test_paths():
    assert construct(Path, "/usr/bin/python") == Path("/usr/bin/python")


@dataclass
class Email(FromStr):
    user: str
    domain: str

    @classmethod
    def from_str(cls, s: str) -> Email:
        parts = s.split("@")
        assert len(parts) == 2
        user, domain = parts
        return Email(user, domain)
    

def test_email():
    assert construct(Email, "john@doe") == Email("john", "doe")
    assert construct(Email, {"user": "john", "domain": "doe"}) == Email("john", "doe")

    with pytest.raises(ConfigError):
        construct(Email, "john")
    with pytest.raises(ConfigError):
        construct(Email, 3)


@dataclass
class Opus:
    title: str
    composer: str
    form: str | None = None
    poet: str | None = None


def test_optional():
    assert construct(Opus, {"title": "Jesu, meine Freude", "composer": "Bach", "form": "motet"}) \
            == Opus("Jesu, meine Freude", "Bach", form="motet")
    assert construct(Opus, {"title": "Estampes", "composer": "Debussy"}) \
            == Opus("Estampes", "Debussy")

    with pytest.raises(ConfigError):
        construct(Opus, {"title": "Mondschein Sonata"})
    with pytest.raises(ConfigError):
        construct(Opus, {"title": "Die Forelle", "composer": 3})


@dataclass
class User:
    username: str
    email: Email


def test_nested_object():
    assert construct(User, {"username": "john", "email": "john@doe"}) \
            == User("john", Email("john", "doe"))
    with pytest.raises(ConfigError):
        construct(User, {"username": "john", "email": 4})


class TeaType(Enum):
    WHITE = 1
    YELLOW = 2
    GREEN = 3
    OOLONG = 4
    BLACK = 5
    POST_FERMENTED = 6
    SCENTED = 7


def test_enum():
    assert construct(TeaType, "white") == TeaType.WHITE
    assert construct(TeaType, "post-fermented") == TeaType.POST_FERMENTED
    assert construct(TeaType, "post_fermented") == TeaType.POST_FERMENTED
    assert construct(TeaType, "POST_FERMENTED") == TeaType.POST_FERMENTED

    with pytest.raises(ConfigError):
        construct(TeaType, 1)
    with pytest.raises(ConfigError):
        construct(TeaType, "English-breakfast")
