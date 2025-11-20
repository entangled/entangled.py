Entangled Architecture
======================

Entangled is organised into several sub-modules with clearly defined responsibilities:

- `commands`, all sub-commands for the command line.
- `config`, all data types related to configuring Entangled.
- `hooks`, the hook subsystem.
- `interface`, interfaces the model and io with commands.
- `io`, manages file I/O.
- `iterators`, support functions for iterators.
- `model`, the data model for Entangled, also contains the tangler.
- `readers`, reading data into the model.

Imports in Python need to be acyclical, as follows:

``` mermaid
graph TD;
    iterators --> model;
    config --> hooks;
    config --> interface;
    config --> model;
    config --> readers;
    hooks --> readers;
    iterators --> readers;
    model --> readers;
    readers --> interface;
    io --> interface;
    hooks --> interface;
    interface --> commands;
```

Commands
--------

We use `click` to make the command line interface, and `rich` and `rich-click` to make it pretty. Every command is encapsulated in a transaction:

```python
with transaction() as t:
    ...
```

This transaction is the front-end for all I/O based operations. Communication with the user is all handled through the `logging` system.

Note: in the past we used `argh` to parse arguments, but this package doesn't have the same level of support from the community.

Config
------

Config is read from `entangled.toml` using the `msgspec` package. The config is separated into an in-memory representation `Config`, and a loadable structure `ConfigUpdate`. We load an update from `entangled.toml` or from a YAML header at the top of a Markdown file. This `ConfigUpdate` is merged with an existing `Config` using the `|` operator. This way we can stack different layers of configuration on top of each other. We can even have different Markdown dialects between files working together.

Hooks
-----

A hook is a class derived from `HookBase`, where you can override the following. A nested `Config` class that can be loaded by `msgspec`:

```python
class Config(msgspec.Struct):
    pass
```

An `__init__` method:

```python
def __init__(self, config: Config):
    super().__init__(config)
```

The `check_prerequisites` method checks that prerequisites are met. For instance, the build hook can use this to see that GNU Make is available.

```python
def check_prerequisites(self):
    pass
```

The `on_read` method is called right after a code block is being read. Example: `quarto_attributes` uses this method to translate the YAML mini header into code block attributes.

```python
def on_read(self, code: CodeBlock):
    pass
```

The `pre_tangle` method is run after all the Markdown is read, but before any output is written. Here you can define any additional output targets or modify the reference map in place.

```python
def pre_tangle(self, refs: ReferenceMap):
    pass
```

The `on_tangle` method lets you add actions to the I/O transaction.

```python
def on_tangle(self, t: Transaction, refs: ReferenceMap):
    pass
```

Lastly, `post_tangle` lets you do clean-up after tangle is complete. I've never used this.

```python
def post_tangle(self, refs: ReferenceMap):
    pass
```

Hooks can be used to implement many things that feel to the user like features.

I/O
---

Offers a virtualization layer on top of all file IO. All IO in Entangled is organized into transactions. When conflicts are found that could endanger your data integrity, Entangled will fail to run the entire transaction. For instance, if you have a markdown file called `model.md` which generates a file called `model.py`, and you have edits in both of them, either `entangled tangle` or `entangled stitch` will see that and refuse to overwrite changes, unless you run with `-f/--force`.

A file database is kept containing MD5 hashes of all input files, to check that content hasn't changed without Entangled knowing about it. All input (and their hashes) are cached in `entangled.virtual.FileCache`.

On the top level, all I/O is encapsulated in transactions:

```python
with transaction() as t:
    t.read(...)
    t.write(...)
    ...
```

Iterators
---------

Internally, Entangled makes heavy use of generators to read files and process text line-by-line. Because both the `model` and `readers` modules use these operations, they need to be in a separate module. Crucially, this module contains the `Peekable` iterator, which allows us to peek into the future of an iterator by caching a single element.

Model
-----

The `model`  contains some of the core functionality of Entangled. It defines the in-memory representation of a Markdown document, as well as the graph representing the code blocks and their references.

- `ReferenceName` contains a `namespace: tuple[str, ...]` and `name: str`, representing a named code entity that may consist of multiple linked code blocks by the same name.
- `ReferenceId` is a unique identifier for every code block. This stores the reference `name`, but also its Markdown source `file` and a `ref_count` for when there are multiple code blocks of the same name.
- `Content` is either `PlainText` which is ignored by Entangled unless stitching, or a `ReferenceId`.
- `CodeBlock` contains all information on a code block including enclosing lines (i.e. the lines containing the three back-tics), its attributes, indentation and the origin of the content.
- `ReferenceMap` fundamentally acts as a `Mapping[ReferenceId, CodeBlock]`, but also contains an index for searching by `ReferenceName` or target file.
- `Document` collects configuration, a dictionary of content and the reference map for ease of use.

Readers
-------

Readers are implemented as `Callable[[InputStream], Generator[RawContent, None, T]]`. Here, `RawContent` is a form of `Content` where we're still dealing with `CodeBlock`s directly instead of `ReferenceId`. The third type-argument to `Generator` is kept abstract here. We can use it to pass values from one generator to the other. For instance (a simplified version):

```python
def read_yaml_header(inp: InputStream) -> Generator[RawContent, None, ConfigUpdate]:
    ...
    yield plain_text
    return config_update

def read_markdown(inp: InputStream, refs: ReferenceMap) -> Generator[RawContent, None, Config]:
    config_update = yield from read_yaml_header(inp)
    config = Config() | config_update
    yield from rest_of_markdown(config, inp, refs)
    return config
```

Here we have a `read_yaml_header` reader that emits `PlainText`, but also parses the YAML header into a `ConfigUpdate`. We subsequently use that configuration to determine how to further read the rest of the Markdown file. This way we can completely process a Markdown file in a single pass, buffering only a single line at a time.

Test Coverage
=============

Unit tests for each module should cover most of that module. The `Makefile` contains test targets for every module that measure only the coverage on that module.

