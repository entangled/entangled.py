Computing Primes
================

We setup a sieve of size 100, and set 0 and 1 not to be primes:

``` {.cpp #sieve}
std::vector<bool> sieve(100, true);
sieve[0] = false;
sieve[1] = false;
```

Then we loop over half the numbers to deselect multiples of any prime:

``` {.cpp #sieve}
for (size_t i = 0; i < 50; ++i) {
    <<deselect-multiples>>
}
```

If a number is not a prime, we skip.

``` {.cpp #deselect-multiples}
if (!sieve[i]) {
    continue;
}
```

Otherwise, we print the number, and loop over all its multiples:

``` {.cpp #deselect-multiples}
std::cout << i << std::endl;

for (size_t j = i*2; j < 100; j += i) {
    sieve[j] = false;
}
```

## Main

``` {.cpp file=src/prime_sieve.cpp}
#include <iostream>
#include <vector>
#include <cstdlib>

int main() {
    <<sieve>>
    return EXIT_SUCCESS;
}
```

