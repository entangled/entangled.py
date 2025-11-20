// ~/~ begin <<docs/index.md#src/prime_sieve.cpp>>[init]
#include <iostream>
#include <vector>
#include <cstdlib>

int main() {
    // ~/~ begin <<docs/index.md#sieve>>[init]
    std::vector<bool> sieve(100, true);
    sieve[0] = false;
    sieve[1] = false;
    // ~/~ end
    // ~/~ begin <<docs/index.md#sieve>>[1]
    for (size_t i = 0; i < 50; ++i) {
        // ~/~ begin <<docs/index.md#deselect-multiples>>[init]
        if (!sieve[i]) {
            continue;
        }
        // ~/~ end
        // ~/~ begin <<docs/index.md#deselect-multiples>>[1]
        std::cout << i << std::endl;
        
        for (size_t j = i*2; j < 100; j += i) {
            sieve[j] = false;
        }
        // ~/~ end
    }
    // ~/~ end
    return EXIT_SUCCESS;
}
// ~/~ end
