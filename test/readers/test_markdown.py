from functools import partial
from pathlib import PurePath

from entangled.config.namespace_default import NamespaceDefault
from entangled.document import PlainText, CodeBlock, ReferenceId, ReferenceMap
from entangled.readers.markdown import code_block, collect_plain_text, ignore_block, markdown, raw_markdown
from entangled.readers.lines import numbered_lines
from entangled.config import AnnotationMethod, Config, config
from entangled.readers.types import run_generator, Reader
from entangled.tangle import tangle_ref


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
    ol, refs = run_reader(partial(markdown, refs), test0)
    assert len(ol) == 1
    assert ol[0] == PlainText("abcdefg")
    assert not refs.map

    ol, refs = run_reader(partial(markdown, refs), test3)
    assert isinstance(ol[-1], ReferenceId)
    assert ol[-1].name == "test"
    assert "test" in refs


test_ns_a = """
First input:

``` {.python #a}
# part a
```

``` {.python #refers-to-a}
<<a>>
```
""".strip()


test_ns_b = """
Second input

``` {.python #a}
# part b
```
""".strip()


def test_global_namespace():
    refs = ReferenceMap()

    with config(namespace_default=NamespaceDefault.GLOBAL):
        _, refs = run_reader(partial(markdown, refs), test_ns_a, "a.md")
        _, refs = run_reader(partial(markdown, refs), test_ns_b, "b.md")

    cb = list(refs.by_name("a"))
    assert len(cb) == 2
    assert cb[0].source.strip() == "# part a"
    assert cb[1].source.strip() == "# part b"

    source, _ = tangle_ref(refs, "refers-to-a", AnnotationMethod.NAKED)
    assert source.splitlines() == ["# part a", "# part b"]


def test_private_namespace():
    refs = ReferenceMap()

    with config(namespace_default=NamespaceDefault.PRIVATE):
        _, refs = run_reader(partial(markdown, refs), test_ns_a, "a.md")
        _, refs = run_reader(partial(markdown, refs), test_ns_b, "b.md")

    print(refs.map)

    cb = list(refs.by_name("a"))
    assert len(cb) == 2
    assert cb[0].source.strip() == "# part a"
    assert cb[1].source.strip() == "# part b"

    source, _ = tangle_ref(refs, "a.md::refers-to-a", AnnotationMethod.NAKED)
    assert source.splitlines() == ["# part a"]
