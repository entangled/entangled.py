---
title: Literate programming
author: Johan Hidding
bibliography: lit/ref.bib
reference-section-title: References
version: 1.0.0
footer: "Literate Programming made easy by [Entangled](https://entangled.github.io)!"
license:  "[Apache 2](https://www.apache.org/licenses/LICENSE-2.0)"
---

This example is written in a style of *literate programming* [@Knuth1984]. The combined code-blocks in this example compose a compilable source code for "Hello World". For didactic reasons we don't always give the listing of an entire source file in one go. In stead, we use a system of references known as *noweb* [@Ramsey1994].

Inside source fragments you may encounter a line with `<<...>>` marks like,

``` {.cpp file=hello_world.cc}
#include <cstdlib>
#include <iostream>

<<example-main-function>>
```

which is then elsewhere specified. Order doesn't matter,

``` {.cpp #hello-world}
std::cout << "Hello, World!" << std::endl;
```

So we can reference the `<<hello-world>>` code block later on.

``` {.cpp #example-main-function}
int main(int argc, char **argv)
{
    <<hello-world>>
}
```

A definition can be appended with more code as follows (in this case, order does matter!):

``` {.cpp #hello-world}
return EXIT_SUCCESS;
```

These blocks of code can be *tangled* into source files.

