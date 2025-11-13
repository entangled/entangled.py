# ~/~ begin <<README.md#forty-two>>[init]
from .card import Card
from collections.abc import Generator, Iterable
from functools import reduce
from dataclasses import dataclass
from enum import Enum, StrEnum
from itertools import accumulate, takewhile, repeat, starmap, product
from collections import defaultdict
# ~/~ end
# ~/~ begin <<README.md#forty-two>>[1]
def black_jack_min_value(card: Card) -> int:
    return card.kind.value if card.kind.value < 10 else 10
# ~/~ end
# ~/~ begin <<README.md#forty-two>>[2]
def keep_score(score: int, card: Card) -> int:
    return score + black_jack_min_value(card)
# ~/~ end
# ~/~ begin <<README.md#forty-two>>[3]
def game_continues(score: int) -> bool:
    return score < 42
# ~/~ end
# ~/~ begin <<README.md#forty-two>>[4]
def run_game(deck: Iterable[Card]) -> Iterable[int]:
    return takewhile(game_continues, accumulate(deck, keep_score, initial=0))
# ~/~ end
# ~/~ begin <<README.md#forty-two>>[5]
def length[T](iter: Iterable[T]) -> int:
    return sum(1 for _ in iter)
     
def trace_game(deck: Iterable[Card]) -> list[tuple[Card, int]]:
    return list(zip(deck, run_game(deck)))

def trial() -> int:
    return length(run_game(shuffled_deck()))

def experiment(n: int) -> Iterable[int]:
    return starmap(trial, repeat((), n))

def histogram[T](iter: Iterable[T]) -> defaultdict[T, int]:
    def tally[T](hist: defaultdict[T, int], item: T) -> defaultdict[T, int]:
        hist[item] += 1
        return hist

    return reduce(tally, iter, defaultdict(lambda: 0))
# ~/~ end
