// ~/~ begin <<doc/index.md#src/euler_number.c>>[init]
#include <stdlib.h>
#include <stdio.h>

int main() {
  // ~/~ begin <<doc/index.md#series-expansion>>[init]
  double euler_number = 1.0;
  int factorial = 1;
  for (int i = 1; i < 10; ++i) {
    factorial *= i;
    euler_number += 1.0 / factorial;
  }
  // ~/~ end
  printf("Euler's number e = %e\n", euler_number);
  return EXIT_SUCCESS;
}
// ~/~ end
