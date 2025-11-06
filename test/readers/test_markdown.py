from functools import partial
from pathlib import PurePath

import pytest
import logging

from entangled.config.namespace_default import NamespaceDefault
from entangled.errors.user import ParseError, IndentationError, CodeAttributeError
from entangled.model import Document, PlainText, CodeBlock, ReferenceId, ReferenceMap, ReferenceName
from entangled.model.tangle import tangle_ref
from entangled.readers.markdown import code_block, collect_plain_text, ignore_block, markdown, raw_markdown
from entangled.readers.lines import numbered_lines
from entangled.readers.peekable import Peekable
from entangled.config import AnnotationMethod, Config, ConfigUpdate
from entangled.readers.types import run_generator, Reader


empty_stream = Peekable(iter([]))


test0 = """
abcdefg
""".strip()


test1 = """
~~~markdown
``` {.python}
# this code block is ignored
```
~~~
""".strip()


def run_reader[O, T](reader: Reader[O, T], inp: str, filename: str = "-") -> tuple[list[O], T]:
    return run_generator(reader(numbered_lines(PurePath(filename), inp)))


def test_ignore_block():
    ol, _ = run_generator(ignore_block(Config())(empty_stream))
    assert not ol

    ol, rv = run_reader(ignore_block(Config()), test0)
    assert not rv and not ol

    ol, rv = run_reader(ignore_block(Config()), test1)
    assert rv
    assert ol == [PlainText(test1)]


test2 = """
``` {.python}
# this code block should be read
```
""".strip()


test3 = """
First we have some other input

``` {.python #test}
# so this should not be read directly by the `code_block` function
# once we read with `raw_markdown` that should change
```
""".strip()


def test_code_block():
    ol, _ = run_generator(code_block(Config())(empty_stream))
    assert not ol

    ol, rv = run_reader(code_block(Config()), test0)
    assert not rv and not ol

    ol, rv = run_reader(code_block(Config()), test2)
    assert rv

    assert len(ol) == 1
    assert isinstance(ol[0], CodeBlock)
    assert ol[0].source.strip() == "# this code block should be read"

    ol, rv = run_reader(code_block(Config()), test3)
    assert not rv and not ol


def test_raw_markdown():
    ol, _ = run_generator(raw_markdown(Config(), empty_stream))
    assert not ol

    ol, _ = run_reader(partial(raw_markdown, Config()), test0)
    assert len(ol) == 1
    assert ol[0] == PlainText("abcdefg")

    ol, _ = run_reader(partial(raw_markdown, Config()), test1)
    assert not any(isinstance(x, CodeBlock) for x in ol)

    ol, _ = run_reader(partial(raw_markdown, Config()), test2)
    assert len(ol) == 1
    assert isinstance(ol[0], CodeBlock)
    assert ol[0].source.strip() == "# this code block should be read"

    ol, _ = run_reader(partial(raw_markdown, Config()), test3)
    assert isinstance(ol[0], PlainText)
    assert ol[0].content.strip() == "First we have some other input"
    assert isinstance(ol[-1], CodeBlock)


def test_collect_plain_text():
    assert list(collect_plain_text(iter([]))) == []
    assert list(collect_plain_text(iter([PlainText("a"), PlainText("b"), 4, PlainText("c")]))) == \
        [PlainText("ab"), 4, PlainText("c")]


def test_markdown():
    refs = ReferenceMap()
    ol, _ = run_reader(partial(markdown, Config(), refs), test0)
    assert len(ol) == 1
    assert ol[0] == PlainText("abcdefg")
    assert not refs

    ol, _ = run_reader(partial(markdown, Config(), refs), test3)
    assert isinstance(ol[-1], ReferenceId)
    assert ol[-1].name.name == "test"
    assert refs
    assert refs.has_name(ReferenceName.from_str("test"))
    assert ol[-1] in refs


test_indent1 = """
This code block is indented:

    ``` {.python}
    hello

    goodbye
    ```

Note the lack of indentation due to a blank line.
""".strip()


test_indent_error1 = """
This code is indented, but contains a line that is not correctly indented:

    ``` {.python}
hello
    ```
""".strip()

test_indent_error2 = """
This code is indented, but the closing fence indent doesn't match the opening:

    ``` {.python}
    hello
      ```

This should raise an `unexpected end of file`.
""".strip()

test_indent_error3 = """
This code is indented, but the closing fence indent doesn't match the opening:

    ``` {.python}
    hello
  ```

This should raise an `indentation error`.
"""

def test_indentation():
    refs = ReferenceMap()
    ol, _ = run_reader(partial(markdown, Config(), refs), test_indent1)
    doc = Document(Config(), refs, {PurePath("a.md"): ol})

    assert isinstance(ol[1], ReferenceId)
    assert refs[ol[1]].indent == "    "
    assert doc.source_text(PurePath("a.md")) == test_indent1

    with pytest.raises(IndentationError):
        _ = run_reader(partial(markdown, Config(), refs), test_indent_error1)

    with pytest.raises(ParseError):
        _ = run_reader(partial(markdown, Config(), refs), test_indent_error2)

    with pytest.raises(IndentationError):
        _ = run_reader(partial(markdown, Config(), refs), test_indent_error3)


test_ns_a = """
First input:

``` {.python #a}
# part a
```

``` {.python file=a.py}
<<a>>
```
""".strip()


test_ns_b = """
Second input

``` {.python #a}
# part b
```

``` {.python file=b.py}
<<a>>
```
""".strip()


def test_global_namespace():
    refs = ReferenceMap()
    config = Config() | ConfigUpdate(
        version="2.4",
        namespace_default=NamespaceDefault.GLOBAL,
        annotation=AnnotationMethod.NAKED)
    doca, _ = run_reader(partial(markdown, config, refs), test_ns_a, "a.md")
    docb, _ = run_reader(partial(markdown, config, refs), test_ns_b, "b.md")
    doc = Document(config, refs, { PurePath("a.md"): doca, PurePath("b.md"): docb })

    cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("a"))]
    assert len(cb) == 2
    assert cb[0].source.strip() == "# part a"
    assert cb[1].source.strip() == "# part b"

    source, _ = doc.target_text(PurePath("a.py"))
    assert source.splitlines() == ["# part a", "# part b"]


def test_private_namespace():
    refs = ReferenceMap()
    config = Config() | ConfigUpdate(
        version="2.4",
        namespace_default=NamespaceDefault.PRIVATE,
        annotation=AnnotationMethod.NAKED)
    doca, _ = run_reader(partial(markdown, config, refs), test_ns_a, "a.md")
    docb, _ = run_reader(partial(markdown, config, refs), test_ns_b, "b.md")
    doc = Document(config, refs, { PurePath("a.md"): doca, PurePath("b.md"): docb })

    cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("a.md::a"))]
    assert len(cb) == 1
    assert cb[0].source.strip() == "# part a"

    cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("b.md::a"))]
    assert len(cb) == 1
    assert cb[0].source.strip() == "# part b"

    source, _ = doc.target_text(PurePath("a.py"))
    assert source.splitlines() == ["# part a"]

    source, _ = doc.target_text(PurePath("b.py"))
    assert source.splitlines() == ["# part b"]


test_ns_yaml1 = """
---
entangled:
    version: "2.4"
    namespace: q
---

``` {.python #hello}
print("hello")
```
""".strip()

test_ns_yaml2 = """
---
entangled:
    version: "2.4"
    namespace: p
---

``` {.python #hello}
print("world")
```

``` {.python #combined}
<<q::hello>>
<<hello>>
```
""".strip()

def test_yaml_namespace():
    refs = ReferenceMap()
    _, config = run_reader(partial(markdown, Config(), refs), test_ns_yaml1, "a.md")
    assert config.namespace == ("q",)
    _, config = run_reader(partial(markdown, Config(), refs), test_ns_yaml2, "b.md")
    assert config.namespace == ("p",)

    refq = ReferenceName.from_str("q::hello")
    assert refs.has_name(refq)
    cb = [refs[r] for r in refs.select_by_name(refq)]
    assert cb[0].source == "print(\"hello\")\n"

    refp = ReferenceName.from_str("p::hello")
    assert refs.has_name(refp)
    cb = [refs[r] for r in refs.select_by_name(refp)]
    assert cb[0].source == "print(\"world\")\n"

    src, _ = tangle_ref(refs, ReferenceName.from_str("p::combined"), annotation=AnnotationMethod.NAKED)
    assert src == "print(\"hello\")\nprint(\"world\")\n"


wrongly_typed_attribute1 = """
---
entangled:
    version: "2.4"
    style: basic
---

```python
#| file: 3
```
""".strip()


octal_mode_attribute2 = """
---
entangled:
    version: "2.4"
    style: basic
---

Note, the mode here is given in octal, and the YAML reader understands this, so this is
supported.

```python
#| file: hello.py
#| mode: 0755
#!/usr/bin/env python
print("Hello, World!")
```
""".strip()


octal_mode_attribute1 = """
``` {.python file=hello.py mode=0755}
print("Hello, World!")
```
""".strip()

wrongly_typed_mode_attribute = """
---
entangled:
    version: "2.4"
    style: basic
---

```python
#| file: hello.py
#| mode: true
print("Hello, World!")
```
""".strip()


def test_file_attribute_type():
    refs = ReferenceMap()

    with pytest.raises(CodeAttributeError):
        _ = run_reader(partial(markdown, Config(), refs), wrongly_typed_attribute1, "a.md")

    with pytest.raises(CodeAttributeError):
        _ = run_reader(partial(markdown, Config(), refs), wrongly_typed_mode_attribute, "a.md")
        ref = ReferenceId(ReferenceName((), "hello.py"), PurePath("a.md"), 0)
        print(refs[ref])

    for md in [octal_mode_attribute1, octal_mode_attribute2]:
        _ = run_reader(partial(markdown, Config(), refs), md, "hello.md")
        ref = ReferenceId(ReferenceName((), "hello.py"), PurePath("hello.md"), 0)
        assert ref in refs
        assert refs[ref].mode == 0o755
    

unknown_language = """
``` {.brainfuck #hello-world}
>++++++++[<+++++++++>-]<.>++++[<+++++++>-]<+.+++++++..+++.>>++++++[<+++++++>-]<+
+.------------.>++++++[<+++++++++>-]<+.<.+++.------.--------.>>>++++[<++++++++>-
]<+.
```
""".strip()


def test_unknown_language(caplog):
    refs = ReferenceMap()

    with caplog.at_level(logging.WARNING):
        _ = run_reader(partial(markdown, Config(), refs), unknown_language, "a.md")
    assert "language `brainfuck` unknown" in caplog.text


