from functools import partial

from entangled.model import PlainText, CodeBlock, ReferenceId, ReferenceMap, ReferenceName
from entangled.readers.markdown import code_block, collect_plain_text, ignore_block, raw_markdown
from entangled.iterators import Peekable, run_generator
from entangled.config import Config
from entangled.readers import run_reader
from entangled.interface import markdown, Context


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
    ol, _ = run_reader(partial(markdown, Context(), refs), test0)
    assert len(ol) == 1
    assert ol[0] == PlainText("abcdefg")
    assert not refs

    ol, _ = run_reader(partial(markdown, Context(), refs), test3)
    assert isinstance(ol[-1], ReferenceId)
    assert ol[-1].name.name == "test"
    assert refs
    assert refs.has_name(ReferenceName.from_str("test"))
    assert ol[-1] in refs



