---
title: Prime numbers
entangled:
  version: "2.0"
  hooks: ["repl"]
  hook:
    repl:
      config:
        Python:
          backend: jupyter
          kernel: python3
---

# Prime numbers

We write a module that computes prime numbers using the Sieve of Eratosthenes.

``` {.python file=primes.py}
def primes(n: int) -> list[int]:
    """All prime numbers below `n`."""
    <<sieve>>
    return [i for i, is_prime in enumerate(sieve) if is_prime]
```

Every multiple of a prime is crossed out, starting at its square.

``` {.python #sieve}
sieve = [False, False] + [True] * (n - 2)
for i in range(2, int(n**0.5) + 1):
    if sieve[i]:
        sieve[i*i::i] = [False] * len(sieve[i*i::i])
```

## Usage

We can now use this module in a Python session.

``` {.python .repl #demo session=session.json}
from primes import primes
primes(30)
```

Output to standard out is shown separately from the result.

``` {.python .repl #demo}
for p in primes(10):
    print(p, p**2)
```

Rich output, like Markdown, is included as is.

``` {.python .repl #demo}
from IPython.display import Markdown
Markdown(f"There are **{len(primes(1000))}** primes below 1000.")
```
