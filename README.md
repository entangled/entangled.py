# Entangled
[![Upload Python Package](https://github.com/entangled/entangled.py/actions/workflows/deploy.yml/badge.svg)](https://github.com/entangled/entangled.py/actions/workflows/deploy.yml)
[![Python package](https://github.com/entangled/entangled.py/actions/workflows/python-package.yml/badge.svg)](https://github.com/entangled/entangled.py/actions/workflows/python-package.yml)

Entangled is a solution for Literate Programming, a technique in which the programmer writes a human narrative first, then implementing the program in code blocks.
Literate programming was introduced by Donald Knuth in 1984 and has since then found several surges in popularity. One thing holding back the popularity of literate programming is the lack of maintainability under increasing program complexity. Entangled solves this issue by offering a two-way synchronisation mechanism. You can edit and debug your code as normal in your favourite IDE or text editor. Entangled will make sure that your Markdown files stay up-to-date with your code and vice-versa. Because Entangled works with Markdown, you can use it with most static document generators. To summarise, you keep using:

- your favourite **editor**: Entangled runs as a daemon in the background, keeping your text files synchronised.
- your favourite **programming language**: Entangled is agnostic to programming languages.
- your favourite **document generator**: Entangled is configurable to any dialect of Markdown.

We’re trying to increase the visibility of Entangled. If you like Entangled, please consider adding this badge [![Entangled badge](https://img.shields.io/badge/entangled-Use%20the%20source!-%2300aeff)](https://entangled.github.io/) to the appropriate location in your project:

```markdown
[![Entangled badge](https://img.shields.io/badge/entangled-Use%20the%20source!-%2300aeff)](https://entangled.github.io/)
```

## Get started
To install Entangled, all you need is a Python (version &ge;3.11) installation. If you use [`poetry`](https://python-poetry.org), and you start a new project,

```
poetry init 
poetry add entangled-cli
```

The `poetry init` command will create a `pyproject.toml` file and a virtual environment to install Python dependencies in. To activate the virtual environment, run `poetry shell` inside the project directory.

Or, if you prefer plain old `pip`,

```
pip install entangled-cli
```

## Use

> :warning: **This version of Entangled is still in beta.** In general things are working as they should, but there may still be some rough edges in the user experience.

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

### Configuring
Entangled is configured by putting a `entangled.toml` in the root of your project.

```toml
# required: the minimum version of Entangled
version = "2.0"            

# default watch_list is ["**/*.md"]
watch_list = ["docs/**/*.md"]

# default ignore_list is ["**/README.md"]
ignore_list = ["docs/**/examples.md"]
```

You may add languages as follows:

```toml
[[languages]]
name = "Java"
identifiers = ["java"]
comment = { open = "//" }

# Some languages have comments that are not terminated by
# newlines, like XML or CSS.
[[languages]]
name = "XML"
identifiers = ["xml", "html", "svg"]
comment = { open = "<!--", close = "-->" }
```

The `identifiers` are the tags that you may use in your code block header to identify the language. Using the above config, you should be able to write:

~~~markdown
``` {.html file=index.html}
<!DOCTYPE html>
<html lang="en">
    <<header>>
    <<body>>
</html>
```

And so on...
~~~

If you have a `pyproject.toml` file, either because you use `poetry` to setup Entangled or because you're actually developing a Python project, you may want to put the configuration in `pyproject.toml` instead. Add a section `tools.entangled` like so:

```toml
[[tools.entangled]]
version = "2.0"
watch_list = ["docs/**/*.md"]
```

## Hooks
Entangled has a system of *hooks*: these add actions to the tangling process:

- `build` trigger actions in a generated `Makefile`
- `brei` trigger actions (or tasks) using [Brei](https://entangled.github.io/brei), which is automatically installed along with Entangled. This is now prefered over the `build` hook.
- `quatro_attributes` add attributes to the code block in Quatro style with `#|` comments at the top of the code block.

## `build` hook
You can enable this hook in `entangled.toml`:

```toml
version = "2.0"
watch_list = ["docs/**/*.md"]
hooks = ["build"]
```

Then in your Markdown, you may enter code tagged with the `.build` tag.

~~~markdown
``` {.python .build target=docs/fig/plot.svg}
from matplotlib import pyplot as plt
import numpy as np

x = np.linspace(-np.pi, np.pi, 100)
y = np.sin(x)
plt.plot(x, y)
plt.savefig("docs/fig/plot.svg")
```
~~~

This code will be saved into a Python script in the `.entangled/build` directory, or if you specify the `file=` attribute some other location. Second, a `Makefile` is generated in `.entangled/build`, that can be invoked as,

```shell
make -f .entangled/build/Makefile
```

You may configure how code from different languages is evaluated in `entangled.toml`. For example, to add Gnuplot support, and also make Julia code run through `DaemonMode.jl`, you may do the following:

```toml
[hook.build.runners]
Gnuplot = "gnuplot {script}"
Julia = "julia --project=. --startup-file=no -e 'using DaemonMode; runargs()' {script}"
```

Once you have the code in place to generate figures and markdown tables, you can use the syntax at your disposal to include those into your Markdown. In this example that would be

~~~markdown
![My awesome plot](fig/plot.svg)
~~~

In the case of tables or other rich content, Standard Markdown (or CommonMark) has no syntax for including other Markdown files, so you'll have to check with your own document generator how to do that. In MkDocs, you could use `mkdocs-macro-plugin`, Pandoc has `pandoc-include`, etc.

You can also specify intermediate data generation like so:

~~~markdown
``` {.python .build target="data/result.csv"}
import numpy as np
import pandas as pd

result = np.random.normal(0.0, 1.0, (100, 2))
df = pd.DataFrame(result, columns=["x", "y"])
df.to_csv("data/result.csv")
```

``` {.python .build target="fig/plot.svg" deps="data/result.csv"}
import pandas as pd

df = pd.read_csv("data/result.csv")
plot = df.plot()
plot.savefig("fig/plot.svg")
```
~~~

The snippet for generating the data is given as a dependency for that data; to generate the figure, both `result.csv` and the code snippet are dependencies.

### `quarto_attributes` hook
Sometimes using the `build` hook (or the `brei` hook, see below), leads to long header lines. It is then better to specify attributes in a header section of your code. The Quarto project came up with a syntax, having the header be indicated by a comment with a vertical bar, e.g. `#|` or `//|` etc. The `quarto_attributes` hook reads those attributes and adds them to the properties of the code block.

Example with the `brei` hook:

~~~markdown
``` {.python .task}
#| description: Draw a triangle
#| creates: docs/fig/triangle.svg
#| collect: figures
from matplotlib import pyplot as plt
plt.plot([[-1, -0.5], [1, -0.5], [0, 1], [-1, -0.5]])
plt.savefig("docs/fig/triangle.svg")
```

![](fig/triangle.svg)
~~~

## Brei
Entangled has a small build engine (similar to GNU Make) embedded, called Brei. You may give it a list of tasks (specified in TOML) that may depend on one another. Brei will run these when dependencies are newer than the target. Execution is lazy and in parallel. Brei supports:

- Running tasks by passing a script to any configured interpreter, e.g. Bash, Python, Lua etc.
- Redirecting `stdout` or `stdin` to or from files.
- Defining so called "phony" targets.
- Define `template` for programmable reuse.
- `include` other Brei files, even ones that need to be generated by another `task`.
- Variable substitution, including writing `stdout` to variables.

Brei is available as a separate package, see [the Brei documentation](https://entangled.github.io/brei).

### Examples
To write out "Hello, World!" to a file `msg.txt`, we may do the following,

```toml
[[task]]
stdout = "secret.txt"
language = "Python"
script = """
print("Uryyb, Jbeyq!")
"""
```

To have this message decoded define a pattern,

```toml
[pattern.rot13]
stdout = "{stdout}"
stdin = "{stdin}"
language = "Bash"
script = """
tr a-zA-Z n-za-mN-ZA-M
"""

[[call]]
pattern = "rot13"
  [call.args]
  stdin = "secret.txt"
  stdout = "msg.txt"
```

To define a phony target "all",

```toml
[[task]]
name = "all"
requires = ["msg.txt"]
```

### The `brei` hook
The following example uses both `brei` and `quatro_attributes` hooks. To add a Brei task, tag a code block with the `.task` class. 

~~~markdown
First we generate some data.

``` {.python #some-functions}
# define some functions
```

Now we show what that data would look like:

``` {.python .task}
#| description: Generate data
#| creates: data/data.npy

<<some-functions>>

# generate and save data
```

Then we plot in another task.

``` {.python .task}
#| description: Plot data
#| creates: docs/fig/plot.svg
#| requires: data/data.npy
#| collect: figures

# load data and plot
```
~~~

The `collect` attribute tells the Brei hook to add the `docs/fig/plot.svg` target to the `figures` collection. All figures can then be rendered as follows, having in `entangled.toml`

```toml
version = "2.0"
watch_list = ["docs/**/*.md"]
hooks = ["quatro_attributes", "brei"]

[brei]
include = [".entangled/tasks.json"]
```

And run

```bash
entangled brei figures
```

You can use `${variable}` syntax inside Brei tasks just as you would in a stand-alone Brei script.

## Support for Document Generators
Entangled has been used successfully with the following document generators. Note that some of these examples were built using older versions of Entangled, but they should work just the same.

### Pandoc
[Pandoc](https://pandoc.org/) is a very versatile tool for converting documents in any format. It specifically has very wide support for different forms of Markdown syntax out in the wild, including a filter system that lets you extend the workings of Pandoc. Those filters can be written in any language through an API, for instance Python filters can be written using `panflute`, but there is also native support for Lua.

To work with Entangled style literate documents, there is a set of [Pandoc filters](https://github.com/entangled/filters) available. The major downside of Pandoc, is that it offers no help in making your output HTML look beautiful. One option is to use the [Bootstrap template](https://github.com/entangled/bootstrap), but you may wan't to try out others as well, or design your own. These days a lot can be done with a single well designed CSS file.

- :heavy_plus_sign: dynamic
- :heavy_plus_sign: supports most Markdown syntax out of the box
- :heavy_plus_sign: excellent for science: citation, numbered figures, tables and equations
- :heavy_plus_sign: support for LaTeX
- :heavy_minus_sign: harder to setup
- :heavy_minus_sign: takes work to make look good

Example: [Hello World in C++](https://entangled.github.io/examples/hello-world.html)

### MkDocs
[MkDocs](https://www.mkdocs.org/) is specifically taylored towards converting Markdown into good looking, easy to navigate HTML, especially when used in combination with the [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material/) theme. To use Entangled style code blocks with MkDocs, you'll need to install the [`mkdocs-entangled-plugin`](https://github.com/entangled/mkdocs-plugin) as well.

- :heavy_plus_sign: specifically designed for Markdown to HTML, i.e. software documentation
- :heavy_plus_sign: pretty output, out of the box
- :heavy_plus_sign: easy to install
- :heavy_minus_sign: not intended for scientific use: numbering and referencing equations, figures and tables is hard to setup
- :heavy_minus_sign: documentation is on par with most Python projects: Ok for most things, but really hard if you want specifics

Example: TBD

### Documenter.jl
[Documenter.jl]() is the standard tool to write Julia documention in. It has internal support for evaluating code block contents.

Example: [Intro to code generation in Julia](https://jhidding.github.io/MacroExercises.jl/dev/)

### PDoc
[PDoc]() is a tool for documenting smaller Python projects. It grabs all documentation from the doc-strings in your Python library and generates a page from that. To have it include its own literate source, I had to use some very ugly hacks.

Example: [check-deps, a Universal dependency checker in Python](https://jhidding.github.io/check-deps/checkdeps.html)

### Docsify
[Docsify](https://docsify.js.org/#/) serves the markdown files and does the conversion to HTML in a Javascript library (in browser).

Example: [Guide to C++ on the web through WASM](https://nlesc-jcer.github.io/cpp2wasm/#/)

## History
This is a rewrite of Entangled in Python. Older versions were written in Haskell. The rewrite in Python was motivated by ease of installation, larger community and quite frankly, a fit of mental derangement.

## Contributing
If you have an idea for improving Entangled, please file an issue before creating a pull request. Code in this repository is formatted using `black` and type checked using `mypy`.

## License
Copyright 2023 Netherlands eScience Center, written by Johan Hidding, licensed under the Apache 2 license, see LICENSE.

