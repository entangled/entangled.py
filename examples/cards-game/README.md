---
entangled:
    version: "2.4"
    style: basic
---

A Silly Card Game
=================

Implements a silly game, counting how many cards we need to draw before reaching a Black Jack score of 42, counting aces as one point. This example uses principles from functional programming to solve this problem. Often introductions to functional programming emphasise the concept of immutability but not that of expressibility.

This code demonstrates several principles (not all isolated to functional programming!):

- **No illegal data.** Choose a type to represent your data that makes it
  illegal to express illegal states. In this case we go the extra mile to
  implement a `Card` data type composed of a `Suit` and `Kind` enum.
- **Use dataclasses.** we define types to combine data meaningfully.
  Preferably, a dataclass should be `frozen` to enforce immutability.
- **Small functions that are (mostly) pure.** every function has a single
  responsibility.
- **Use iterators/generators to compute sequences lazily.** This is part of a
  general tendency in functional programming to blur the boundary between
  data and code. Generators are data masquerading as code. Python's
  generator syntax makes this sort of programming particularly pretty.
- **Encapsulated mutability.** In the `shuffled_deck` function, we use in-place
  mutability of a list of cards, but this mutability is encapsulated to
  that function.
- **Use generic elemental functions that combine into more complex behaviour.**
  Specifically, we use `accumulate`, `zip`, `map` and `enumerate` to
  manipulate iterators.

The game
--------

The problem is as follows: we have a stack of playing cards. Numbered cards have the value of their number (one through ten), and picture cards (Jack, Queen and King) have a value of ten. We keep drawing cards from the deck until we reach a value of 42 or higher. How many times do you need to draw a card?

The following Python code sets up a Monte-Carlo experiment:

```python
import random

def run_game() -> int:
    deck = list(range(52))
    random.shuffle(deck)
    total = 0
    count = 0

    for card in deck:
        count += 1

        if card % 13 >= 10:
            value = 10
        else:
            value = card % 13 + 1

        total += value

        if total >= 42:
            return count
```

We can run the `run_game` function multiple times to build statistics. This code has several issues. For one, it comes straight out of the Fortran programmers handbook! Jokes asside, what are the problems here?

- The code is hard to read. What do we mean by that? Some would claim that this is some of the most readable code out there! Well, the control-flow and logic are very clear, however not so our intent.
- The code is hard to test. If there is an issue with this code somewhere, it is not so easy to spot, and since the function is monolithic, we can't test different parts for their logic.

We might modularize the code and use better variable names to improve things a bit. Also, we can use some of the idioms in Python.

```python
def shuffled_deck() -> list[int]:
    deck = range(52)
    random.shuffle(deck)
    return deck

def card_value(card: int) -> int:
    if card % 13 >= 10:
        return 10
    else:
        return card % 13 + 1

def run_game_2() -> int:
    deck = shuffled_deck()

    total = 0
    for i, card in enumerate(deck, start=1):
        total += card_value(card)
        if total >= 42:
            return i
```

Here we've used the `enumerate` function to create an enumerated for-loop, instead of hand-counting the number of cards, and moved some parts to separate functions. Things have improved now, but this is still nowhere near what a functional programmer would do. What follows now will feel silly for this problem, but it isn't there to solve the problem, it is there to teach you ways to think that you might not have seen before.

Data representation
-------------------

In the previous example we represented our cards as integers. This is efficient, but it doesn't communicate what the logic in our program is about. You should prefer data structures that make it obvious what the data means and that make it impossible to represent states that should not exist. Enters the `enum` and the `dataclass`.

```python
#| file: src/cards_game/card.py
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
```

Yes, this is extremely verbose, but hey, now you can reuse the `Card` type when you feel like programming other card games! This demonstrates two types of enum in Python: the classic numeric enum, and the `StrEnum` that is backed by internal string values. Python has a way of optimizing short strings that are used as identifiers, so don't worry about efficiency here, worry about what makes sense!

We could've implemented a method on the `Card` type to give us a card's value in the game of Black Jack, but this value is more a property of the game of Black Jack than that of the card itself. We keep the class empty and clean.

### Note on using `__repr__`

The `Suit`, `Kind`, and `Card` classes implement the `__repr__` method to get a nice representation in a Python REPL. In production code it is desirable that the `__repr__` method returns a representation of an
object that would evaluate back to the original object, so:

```python
assert eval(repr(obj)) == obj
```

should always hold. Here that principle is violated for convenience.

Encapsulating mutable state
---------------------------

Next we need to generate a deck of cards and shuffle it.

```python
def sorted_deck() -> Generator[Card]:
    for suit in Suit:
        for kind in Kind:
            yield Card(suit, kind)
```

The `sorted_deck` function is a little **gem** of the Python language. In as few words as it would take to describe what it does, we have an implementation that is both readable and efficient. Seeing and writing functions like this should release a small dose of dopamine in your brain. If we would write this function in completely functional style, we get a function that is short, powerful, but arguably less "Pythonic".

```python
#| id: deck
#| file: src/cards_game/deck.py
from collections.abc import Iterator
from itertools import starmap, product
import random

from .card import Suit, Kind, Card

def sorted_deck() -> Iterator[Card]:
    return starmap(Card, product(Suit, Kind))
```

To shuffle the deck we need to store it in a list, then call `random.shuffle`, which shuffles items in a list in-place, and return it.

```python
#| id: deck
def shuffled_deck() -> list[Card]:
    deck = list(sorted_deck())
    random.shuffle(deck)
    return deck
```

Here we used a mutating procedure, but it is encapsulated in a small function, so it won't affect the logic beyond the confines of this function.

Higher order functions
----------------------

The `map`, `reduce` (better known as *fold*), `filter`, and similar functions are collectively known as *higher order functions*. This means that they take smaller functions as their input to produce more complex behaviour.

The advantages of this approach are not as self-evident as some of the others in this tutorial. Often, writing code in terms of simple for-loops can be more readable. In a sense this is a good thing. The designers of Python found these patterns so important that they made syntax like list-comprehensions and generators, just to make this easier. What is important is that, as a programmer, you learn to think in terms of these abstract operations on sequences. Then, when you need to handle data that is a bit larger, you can abstract over these operations.

Advantages of `itertools` functions over hand-rolling a loop:

- **robustness**. You have a smaller chance of introducing subtle bugs.
- **scalability**. If you need to scale up, you can consider using libraries like Dask to handle the computation.
- **composability**. These routines form a kind of mini-language (also known as a domain-specific language or DSL) that allow for components to be reused and combined in new ways.

Disadvantages or possible traps are:

- **readability**. This can go either way. The danger is that when you start using `itertools` and relatives in earnest, you'll be tempted to go all-the-way, resulting in code that is very hard to read, especially for peers that don't use `itertools` every day.
- **mental overhead**. For many programmers, remembering what each and every iterator adaptor is doing can be a burden. In this tutorial we use only a few functions, but checkout the [`more-itertools` package](https://more-itertools.readthedocs.io/en/stable/).
- **off-by-one**. Many of these functions are variations on a theme. For instance, we'll use the `takewhile` function from `itertools`, but you might also want a version of that function that also includes the first item that fails the test. There is a `takewhile_inclusive` variant in `more-itertools`, but you don't need that if you roll your own generator.

With that discussion out of the way, we'll now implement the rest of the game with maximum utilisation of the `itertools` library.

One-liners
----------

```python
#| id: forty-two
#| file: src/cards_game/forty_two.py
from .card import Card
from collections.abc import Generator, Iterable
from functools import reduce
from dataclasses import dataclass
from enum import Enum, StrEnum
from itertools import accumulate, takewhile, repeat, starmap, product
from collections import defaultdict
```

The functional programmer prefers all their functions to be one liners. This is also why they detest any control-flow like `for` loops and `if` statements. Sometimes though, it can't be helped: the `if` statement is a necessary part of any Turing complete system. Luckily, we have the ternary expression (no matter how ugly it is in Python).

```python
#| id: forty-two
def black_jack_min_value(card: Card) -> int:
    return card.kind.value if card.kind.value < 10 else 10
```

We'll define a little accumulator function to keep the score:

```python
#| id: forty-two
def keep_score(score: int, card: Card) -> int:
    return score + black_jack_min_value(card)
```

And a predicate (a function of one argument returning a `bool`) to indicate the end of the game:

```python
#| id: forty-two
def game_continues(score: int) -> bool:
    return score < 42
```

Now, to run the game, we have another one-liner:

```python
#| id: forty-two
def run_game(deck: Iterable[Card]) -> Iterable[int]:
    return takewhile(game_continues, accumulate(deck, keep_score, initial=0))
```

Now, that almost reads as plain English!

Folding
-------

The `run_game` function is a one-liner. This is only possible because we carefully designed the `keep_score` function to fit in the *foldable* design pattern. The `keep_score` function takes a state and an update as input, and returns a new state:

```python
def update(s: State, ds: Delta) -> State:
    pass
```

When we can model the progress of a game in such a function, we gain access to a plethora of *reducing* or *folding* functions:

```python
def fold[S, D](update: Callable[[S, D], S], iter: Iterable[D], state: S) -> S:
    for item in iter:
        state = update(state, item)
    return state
```

In this case, we can use `itertools.accumulate` that yields intermediate results as well.

Getting answers
---------------

To get a usable answer, we need two more one-liners.

```python
#| id: forty-two
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
```

The exact answer
----------------

As a little extra: what are the complete statistics of this game? We have 52 cards. At a minimum we need to draw five of them to get to 42 points, and at most 17 cards ($4 \times (1 + 2 + 3 + 4) + 5 = 45$), so that leaves between 311875200 and 7805769880904240998072320000 combinations to compute!

Problems like these lend themselves really well to a technique called *dynamic programming*. That sounds fancy, but what it means is that we cache computations (also known as *memoization*) to speed things up. The `functools` library has a `cache` decorator.

As a first example, we look at the factorial function. We put a print-statement in there to see when the function is being evaluated:

```python
from functools import cache

@cache
def factorial(x):
    print(f"computing {x}!")
    if n == 0:
        return 1
    return n * factorial(n - 1)
```

> [!TIP]
> ### Exercise: compute the binomial coefficient
> The binomial coefficient can be defined by the recursion,
>
> $$\binom{n}{k} = \binom{n-1}{k-1} + \binom{n-1}{k},$$
>
> with the base cases,
>
> $$\binom{n}{0} = 1\quad\textrm{and}\binom{n}{n} = 1.$$
>
> Implement this recursion with a cached function. Tip: the binomial coefficent has a symmetry that can make your implementation even more efficient,
>
> $$\binom{n}{k} = \binom{n}{n - k}.$$
>
> <details markdown=1><summary>Solution</summary>
>
> ```python
> @cache
> def binomial_coefficient(a: int, b: int) -> int:
>     if b > a:
>         return 0
>     if a == 0:
>         return 1
>     if b > (a // 2):
>         return binomial_coefficient(a, a - b)
>     return binomial_coefficient(a-1, b-1) + binomial_coefficient(a-1, b)
> ```
>
> </details>

```python
#| file: src/cards_game/exact.py
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
```

Conclusion
----------

Python is a very flexible language, and it allows us to write some beautiful functional code. However, the language was not designed to be functional to this extend. Overuse of these techniques will negatively affect readability. The conclusion should be: there are times when to use and times when not to use this, and there is no golden rule that can tell you when that is. Go, and scroll up towards the crappy quasi-fortran discombobulation that we started with, and compare with the exquisite beauty we have crafted from it. Somehow, I'm still not sure which is better or worse.

