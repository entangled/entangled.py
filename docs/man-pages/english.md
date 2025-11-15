% entangled(1) version {__version__} | User Commands

NAME
====

Entangled - Your literate programming toolkit.

SYNOPSIS
========

`entangled [options] [command] [arguments]...`

DESCRIPTION
===========

Entangled helps you write Literate Programs in Markdown. You put all your code inside Markdown code blocks. Entangled automatically extracts the code and writes it to more traditional source files. You can then edit these generated files, and the changes are being fed back to the Markdown.

OPTIONS
=======

`--help`

: Show the help message and exit.

`-v, --version`

: Show version and exit.

`-d, --debug`

: Print debug messages.

COMMANDS
========

Each command has its own arguments and flags that can be inspected using `entangled <command> --help`.

`brei <target>`

: Build one of the configured targets. Entangled has an integrated build system called `brei` (https://entangled.github.io/brei) that can be used to produce figures, or other artifacts. Targets and their dependencies can be specified in code blocks using the `brei` hook.

`new <template> <project-path>`

: Create a new entangled project from a template in the given project path.

`reset`

: Reset the file database. 

`status`

: Print a status overview.

`stitch`

: Stitch code changes back into the documentation.

`sync`

: Automatically detects ifBe smart wether to tangle or stich

`tangle`

: Tangle codes from the documentation.

`watch`

: Keep a loop running, watching for changes in the file system.

WRITING PROGRAMS
================

Entangled enables a **documentation first** approach to programming. To write programs using Entangled, you start by writing documentation and in Markdown and then add code blocks. The code blocks can be marked with attributes to indicate where code should be written.

HELLO WORLD
-----------

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

These blocks of code can be **tangled** into source files.

DEFAULT SYNTAX
--------------

The standard syntax is aimed to work well together with Pandoc. Every code block is delimited with three back ticks. Added to the opening line is a sequence of space separated **code properties**. These properties align with the CSS attributes that would end up in the generated HTML. For those unfamiliar with CSS:

- `#identifier`; a name prefixed with a `#` (sharp), identifies the object, only one of these should be present per item
- `.class`; a name prefixed with `.` (period), assigns the object to a class, a object can belong to any number of classes
- `key=value`; a name suffixed with `=` (equals), optionally followed by a value, adds any meta-data attribute to the object

The complete syntax of a code block then looks like:

~~~markdown
``` {[#<reference>|.<language>|<key>=<value>] ...}
<code> ...
```
~~~

The first class in the code properties is always interpreted to give the **programming language** of the code block. In Entangled, any code block is one of the following:
    
- A **referable** block: has exactly one **reference id** (`#<reference>`) and a class giving the language of the code block (`.<language>`). Example:

  ~~~markdown
  ``` {.rust #hello-rust}
  println!("Hello, Rust!");
  ```
  ~~~
 
  In some cases you may want to have additional classes to trigger hooks or a specific filter. Always the first class is interpreted to identify the language.
- A **file** block: has a key-value pair giving the path to the file (`file=<path>`), absolute or relative to the directory in which `entangled` runs. Again, there should be one class giving the language of the block (`.<language>`). Example:

  ~~~markdown
  ``` {.rust file=src/main.rs}
  fn main() {
     <<hello-rust>>
  }
  ```
  ~~~

  The identifier in a file block is optional. If it is left out, the identifier will silently be taken to be the file name.
- An **ignored** block: anything not matching the previous two.

TANGLED CODE
------------

Entangled recognizes three parameters for every code block. These parameters are extracted from an opening line may be [configured using regular expressions](#MARKERS). Formally, every code block has three properties:

- `Language`
- `Identifier`
- `Optional Filename`

Entangled should tangle your code following these rules:

1. If an **identifier** is repeated the contents of the code blocks is concatenated in the order that they appear in the Markdown. If an identifier appears in multiple files, the order is dependent on the order by which the files appear in the configuration, or if they result from a glob-pattern expansion, alphabetical order.

3. **Noweb references** are **expanded**. A noweb reference in Entangled should occupy a single line of code by itself, and is enclosed with double angle brackets, and maybe indented with white space. Space at the end of the line is ignored.

   ~~~txt
   +--- indentation ---+--- reference  ---+--- possible space ---+
                       <<noweb-reference>>
   ~~~

   The reference is expanded recursively, after which the indentation is prefixed to every line in the expanded reference content.

4. **Annotation**; Expanded and concatenated code blocks are annotated using comment lines. These lines should not be touched when editing the generated files. The default method of annotation follows an opening comment with `~\~ begin <<filename#identifier>>[n]`, and a closing comment with `~\~ end`. For example

   ~~~rust
   // ~\~ begin <<lit/index.md|main>>[1]
   println!("hello");
   // ~\~ end
   ~~~

CONFIGURATION
=============

Global configuration is loaded from `entangled.toml` in the current working directory, or from the YAML header of the Markdown file, if there is only one input file. In the case of multiple input files, the YAML header is local to that input file.

Configuration should match the following scheme:

`version`

: (`string`) the minimum version of Entangled.

`style`

: (`string`: `default` | `basic`) (default: `default`) a configuration preset. See STYLES.

`languages`

: (`list[Language]`) additional language settings.

`markers`

: (`Markers`) override marker expressions for extracting code blocks.

`watch_list`

: (`list[string]`) sets a list of glob patterns for files to read.

`ignore_list`

: (`list[string]`) sets a list of glob patterns to exclude from reading.

`annotation`

: (`string`: `standard` | `naked` | `supplemented`) sets the method for annotating tangled files.

`annotation_format`

: (`string`) set a format string for `supplemented` annotation (not yet implemented).

`use_line_directives`

: (`bool`) wether to include line directives to point compilers to the Markdown input source (not yet implemented).

`namespace`

: (`string`) set the namespace for the current input file. Namespaces are separated with double colons `::`.

`namespace_default`

: (`string`: `global` | `private`) if the namespace is absent, this controls the scope of code block identifiers.

`hooks`

: (`list[string]`) set the hooks used. Prepend a hook name with a tilde `~` to disable a hook locally.

`hook`

: (`object`) additional settings for enabled hooks.

`brei`

: (`Program`) create more Brei targets that are not listed in code blocks. The `Program` API is specified by the `brei` package.

LANGUAGE
--------

We can configure how a language is treated by setting comment characters. For example:

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

`name`

: (`string`) a unique name for the language.

`identifiers`

: (`list[string]`) a set of identifiers that are admissable as language classes for a code block using this language.

`comment`

: (`object[open: string, close: string = ""]`) how to write comments in this language.

MARKERS
-------

This configures how code blocks are detected.

`open`

: (`string`) opening regex for a code block. Python's regex engine supports named groups using `(?P<name>...)` syntax. This expression should contain an `indent` group and a `properties` group. The returned indentation should contain only spaces, and `properties` should at the minimum have the language identifier for the code block.

`close`

: (`string`) closing regex for a code block. This should contain a named pattern group `indent`.

STYLES
======

There are two configuration styles available: `default` and `basic`.

DEFAULT
-------

The default is to read code blocks with three back-tics and attributes grouped in curly braces. For example:

~~~markdown
This is a code block:

``` {.c #print-hello}
printf("Hello, World!");
```
~~~

BASIC
-----

The basic style is less expressive but has better compatability with most standard Markdown syntaxes like Github.In this style only the language identifier is given after three back-tics. Other attributes are passed using the `quarto_attributes` hook. For example:

~~~markdown
This is a code block:

```c
//| id: print-hello
printf("Hello, World!");
```
~~~

HOOKS
=====

BREI
----

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

QUARTO ATTRIBUTES
-----------------

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

Using these attributes it is possible to write in Entangled using completely standard Markdown syntax. 

The `id` attribute is reserved for the code's identifier (normally indicated with `#`) and the `classes` attribute can be used to indicate a list of classes in addition to the language class already given.

REPL (experimental)
-------------------

The `repl` hook enables running code blocks in REPL sessions. The hook extracts these code blocks into a separate JSON session file that can be evaluated using the `repl-session` tool (https://entangled.github.io/repl-session). The output needs to be processed by the documentation rendering system. The `mkdocs-entangled-plugin` package handles `repl` sessions and integrates the output into the rendered HTML.

SHEBANG
-------

If a code block starts with `#!...` on the first line. This line is brought to the top of the tangled file. Together with the use of a `mode` attribute, this enables coding executable scripts in Entangled. Example:

~~~markdown
A first Bash script:

``` {.bash file=cowsay mode=0755}
#!/bin/bash
echo "Mooo!"
```
~~~

SPDX_LICENSE
------------

If a code block starts with a line containing the string "SPDX-License-Identifier". That line is put above the first annotation comment, similar to the `shebang` hook.

BUGS
====

Bugs can be reported at https://github.com/entangled/entangled.py/issues.

