# Entangled
Entangled is a solution for Literate Programming, a technique in which the programmer writes a human narrative first, then implementing the program in code blocks.
Literate programming was introduced by Donald Knuth in 1984 and has since then found several surges in popularity. One thing holding back the popularity of literate programming is the lack of maintainability under increasing program complexity. Entangled solves this issue by offering a two-way synchronisation mechanism. You can edit and debug your code as normal in your favourite IDE or text editor. Entangled will make sure that your Markdown files stay up-to-date with your code and vice-versa. Because Entangled works with Markdown, you can use it with most static document generators. To summarise, you keep using:

- your favourite **editor**: Entangled runs as a daemon in the background, keeping your text files synchronised.
- your favourite **programming language**: Entangled is agnostic to programming languages.
- your favourite **document generator**: Entangled is configurable to any dialect of Markdown.

## Get started
To install Entangled, all you need is a Python installation. If you use [`poetry`](https://python-poetry.org),

```
poetry add entangled-cli[rich]
```

Or, if you prefer `pip`,

```
pip install entangled-cli[rich]
```

## Use

> :warning: **This version of Entangled is still in alpha. Configuration is not yet implemented.**

Run the `entangled watch` daemon in the root of your project folder. By default all Markdown files are monitored for fenced code blocks like so:

~~~markdown
``` {.rust #hello file="src/world.rs"}
...
```
~~~

The syntax of code block properties is the same as CSS properties: `#hello` gives the block the `hello` identifier, `.rust` adds the `rust` class and the `file` attribute is set to `src/world.rs` (quotes are optional). For Entangled to know how to tangle this block, you need to specify a language and a target file. However, now comes the cool stuff. We can split our code in meaningful components by cross-refrences.

### Hello World in C++
The combined code-blocks in this example compose a compilable source code for "Hello World". For didactic reasons we don't always give the listing of an entire source file in one go. In stead, we use a system of references known as *noweb* (after Ramsey 1994).

Inside source fragments you may encounter a line with `<<...>>` marks like,

~~~markdown
``` {.cpp file=hello_world.cc}
#include <cstdlib>
#include <iostream>

<<example-main-function>>
```
~~~

which is then elsewhere specified. Order doesn't matter,

~~~markdown
``` {.cpp #hello-world}
std::cout << "Hello, World!" << std::endl;
```
~~~

So we can reference the `<<hello-world>>` code block later on.

~~~markdown
``` {.cpp #example-main-function}
int main(int argc, char **argv)
{
    <<hello-world>>
}
```
~~~

A definition can be appended with more code as follows (in this case, order does matter!):

~~~markdown
``` {.cpp #hello-world}
return EXIT_SUCCESS;
```
~~~

These blocks of code can be *tangled* into source files.

## History
This is a rewrite of Entangled in Python. Older versions were written in Haskell. The rewrite in Python was motivated by ease of installation, larger community and quite frankly, a fit of mental derangement.

## Contributing
If you have an idea for improving Entangled, please file an issue before creating a pull request. Code in this repository is formatted using `black` and type checked using `mypy`.

## License
Copyright 2023 Netherlands eScience Center, written by Johan Hidding, licensed under the Apache 2 license, see LICENSE.
