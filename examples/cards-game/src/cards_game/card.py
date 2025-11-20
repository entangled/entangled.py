# ~/~ begin <<README.md#src/cards_game/card.py>>[init]
from enum import Enum, StrEnum
from dataclasses import dataclass


class Suit(StrEnum):
    SPADES = "spades"
    CLOVES = "cloves"
    HEARTS = "hearts"
    DIAMONDS = "diamonds"

    def __repr__(self) -> str:
        return self.name[0]


class Kind(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13

    def __repr__(self) -> str:
        if self.value <= 10:
            return str(self.value)
        else:
            return self.name[0]


@dataclass(frozen = True)
class Card:
    suit: Suit
    kind: Kind

    def __repr__(self) -> str:
        return repr(self.suit) + repr(self.kind)
# ~/~ end
