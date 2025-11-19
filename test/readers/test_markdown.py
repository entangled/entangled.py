from functools import partial
from pathlib import PurePath

import pytest
import logging

from entangled.config.namespace_default import NamespaceDefault
from entangled.errors.user import ParseError, IndentationError, CodeAttributeError
from entangled.model import PlainText, CodeBlock, ReferenceId, ReferenceMap, ReferenceName, tangle_ref
from entangled.readers.markdown import code_block, collect_plain_text, ignore_block, markdown, raw_markdown
from entangled.iterators import Peekable, run_generator
from entangled.config import AnnotationMethod, Config, ConfigUpdate
from entangled.readers import run_reader


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


