# ~/~ begin <<README.md#src/cards_game/exact.py>>[init]
from __future__ import annotations

from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from functools import cache
from copy import copy
import numpy as np
import numpy.typing as npt


type UIntArray = npt.NDArray[np.uint64]
type FloatArray = npt.NDArray[np.float64]


MAX_HAND: UIntArray = np.array([4] * 9 + [16], dtype=np.uint64)
HIST_SIZE: int = 13
HIST_OFFSET: int = 5


def histogram_zero() -> FloatArray:
    return np.zeros(HIST_SIZE, dtype=np.float64)


def histogram_singleton(n: int) -> FloatArray:
    h = histogram_zero()
    h[n - HIST_OFFSET] = 1
    return h


@dataclass
class Hand:
    n_cards: int = 0
    score: int = 0
    counts: IntArray = field(default_factory=lambda: np.zeros(10, dtype=np.uint64))

    def __hash__(self) -> int:
        h = 0
        for (i, n) in enumerate(self.counts):
            h |= int(n) << (3 * i)
        return h

    def __eq__(self, other) -> bool:
        return (self.counts == other.counts).all()

    def draw(self) -> Generator[tuple[int, Hand]]:
        """Generates new hands with multiplicity."""
        for i in range(len(self.counts)):
            n = self.counts[i]
            m = MAX_HAND[i]
            if n < m:
                c = copy(self.counts)
                c[i] += 1
                yield (m - n, Hand(self.n_cards + 1, self.score + i + 1, c))


def compute_dist():
    cache: dict[int, FloatArray] = dict()

    def run(h: Hand) -> FloatArray:
        x = hash(h)
        if x not in cache:
            if h.score >= 42:
                cache[x] = histogram_singleton(h.n_cards)
            else:
                cache[x] = (1.0 / (52 - h.n_cards)) * sum((m * compute_dist(x, h2) \
                    for (m, h2) in h.draw()), histogram_zero())
        return cache[x]

    return run(Hand())
# ~/~ end
