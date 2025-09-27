from functools import cached_property
from typing import Self, override
from msgspec import Struct, convert, field
from dataclasses import dataclass

from entangled.from_str import FromStr, dec_hook


@dataclass
class Pt(FromStr):
    x: int
    y: int

    @override
    def to_str(self) -> str:
        return f"{self.x},{self.y}"

    @override
    @classmethod
    def from_str(cls, s: str) -> Self:
        x, y = map(int, s.split(","))
        return cls(x=x, y=y)


class Spec(Struct, dict=True):
    _pt: str = field(name = "pt")

    @cached_property
    def pt(self) -> Pt:
        return Pt.from_str(self._pt)


def test_from_str_msgspec():
    assert convert({ "pt": "3,4" }, type=Spec, dec_hook=dec_hook).pt == Pt(3, 4)
