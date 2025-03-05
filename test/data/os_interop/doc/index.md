---
title: Testing Windows/Linux interop
subtitle: a story of a mangled path
author: Johan Hidding
---

Paths on Windows are spelled with backslashes in between them, for example:

```
C:\Program Files\I have no clue\WhatImDoing.exe
```

On UNIXes (Linux and to and extend MacOS), paths are separated using slashes:

```
/usr/share/doc/man-pages/still-have-no-clue
```

Entangled uses Python's `Path` API throughout to deal with this difference transparently. Paths find a representation in the comment annotations left in tangled files, so that the markdown source of a piece of code can be found. We want consistent behaviour when using Entangled between different OS, so all paths should be encoded UNIX style.

This test creates a source file in a different path from this markdown source.

## Euler's number

We'll compute Euler's number in C. Euler's number is the exponential base for which the differential equation,

$$y_t = y,$$

holds. With a Taylor expansion we may see that the constant $e$ in the solution $A e^t$ can be computed as,

$$e = \sum_{n=0}^{\infty} \frac{1}{n!} = 1 + \frac{1}{1!} + \frac{1}{2!} + \dots$$

In C, we can compute this number, here to the 9th term:

``` {.c #series-expansion}
double euler_number = 1.0;
int factorial = 1;
for (int i = 1; i < 10; ++i) {
  factorial *= i;
  euler_number += 1.0 / factorial;
}
```

Wrapping this in an example program:

``` {.c file=src/euler_number.c}
#include <stdlib.h>
#include <stdio.h>

int main() {
  <<series-expansion>>
  printf("Euler's number e = %e\n", euler_number);
  return EXIT_SUCCESS;
}
```

To build this program, the following `Makefile` can be used:

``` {.make file=Makefile}
.RECIPEPREFIX = >
.PHONY: clean

build_dir = ./build
source_files = src/euler_number.cc

obj_files = $(source_files:%.cc=$(build_dir)/%.o)
dep_files = $(obj_files:%.o=%.d)

euler: $(obj_files)
> @echo -e "Linking \e[32;1m$@\e[m"
> @gcc $^ -o $@

$(build_dir)/%.o: %.c
> @echo -e "Compiling \e[33m$@\e[m"
> @mkdir -p $(@D)
> @gcc -MMD -c $< -o $@

clean:
> rm -rf build euler

-include $(dep_files)
```

I know, overkill.

## Expected output

When we tangle this program, this looks like:

```c
/* ~/~ begin <<doc/index.md#src/euler_number.c>>[init] */
#include <stdlib.h>
#include <stdio.h>

int main() {
  /* ~/~ begin <<doc/index.md#series-expansion>>[init] */
  double euler_number = 1.0;
  int factorial = 1;
  for (int i = 1; i < 10; ++i) {
    factorial *= i;
    euler_number += 1.0 / factorial;
  }
  /* ~/~ end */
  printf("Euler's number e = %e\n", euler_number);
  return EXIT_SUCCESS;
}
/* ~/~ end */
```

Notice, the forward slashes in the paths.
