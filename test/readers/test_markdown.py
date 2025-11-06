from functools import partial
from pathlib import PurePath

from entangled.config.namespace_default import NamespaceDefault
from entangled.config.version import Version
from entangled.model import Document, PlainText, CodeBlock, ReferenceId, ReferenceMap, ReferenceName, tangle_ref
from entangled.readers.markdown import code_block, collect_plain_text, ignore_block, markdown, raw_markdown
from entangled.readers.lines import numbered_lines
from entangled.config import AnnotationMethod, Config, ConfigUpdate
from entangled.readers.types import run_generator, Reader


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
    ol, _ = run_reader(partial(raw_markdown, Config()), test0)
    assert len(ol) == 1
    assert ol[0] == PlainText("abcdefg")

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
    doca, config = run_reader(partial(markdown, Config(), refs), test_ns_yaml1, "a.md")
    assert config.namespace == ("q",)
    docb, config = run_reader(partial(markdown, Config(), refs), test_ns_yaml2, "b.md")
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
