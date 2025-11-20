# ~/~ begin <<README.md#deck>>[init]
from collections.abc import Iterator
from itertools import starmap, product
import random

from .card import Suit, Kind, Card

def sorted_deck() -> Iterator[Card]:
    return starmap(Card, product(Suit, Kind))
# ~/~ end
# ~/~ begin <<README.md#deck>>[1]
def shuffled_deck() -> list[Card]:
    deck = list(sorted_deck())
    random.shuffle(deck)
    return deck
# ~/~ end
