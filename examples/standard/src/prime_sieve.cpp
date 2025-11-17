// ~/~ begin <<docs/index.md#src/prime_sieve.cpp>>[init]
#include <iostream>
#include <vector>
#include <cstdlib>

int main() {
    std::vector<bool> sieve(100, true);
    sieve[0] = false;
    sieve[1] = false;
    for (size_t i = 0; i < 100; ++i) {
        if (!sieve[i]) {
            continue;
        }

        std::cout << i << std::endl;

        for (size_t j = i*2; j < 100; j += i) {
            sieve[j] = false;
        }
    }
    return EXIT_SUCCESS;
}
// ~/~ end
