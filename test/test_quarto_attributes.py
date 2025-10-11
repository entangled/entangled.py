from pathlib import PurePath
from entangled.code_reader import CodeReader
from entangled.commands.stitch import stitch_markdown
from entangled.config import AnnotationMethod, Markers, config
from entangled.hooks import get_hooks
from entangled.markdown_reader import read_markdown_string
from entangled.tangle import tangle_ref
from entangled.properties import Attribute, get_attribute


md_in = """
``` {.scheme}
; | id: hello
; | foo: bar
(display "hello") (newline)
```

``` {.scheme}
;| file: hello.scm
<<hello>>
(display "goodbye") (newline)
```
"""


scm_out = """
(display "hello") (newline)
(display "goodbye") (newline)
"""


def test_quarto_attributes():
    with config(
        hooks=["quarto_attributes"]):
        # it is currently not possible to change markers at run-time,
        # because the config is passed to MarkdownLexer at module load time
        # markers=Markers(
        #     open=r"^(?P<indent>\s*)```(?P<properties>.*)$",
        #     close=r"^(?P<indent>\s*)```\s*$")):
        hooks = get_hooks()

    print(hooks)
    refs, _ = read_markdown_string(md_in, hooks=hooks)
    assert get_attribute(next(iter(refs.by_name("hello"))).properties, "foo") == "bar"
    result, _ = tangle_ref(refs, "hello.scm", AnnotationMethod.NAKED)
    assert result.strip() == scm_out.strip()


def test_quarto_attributes_stitch():
    with config(hooks=["quarto_attributes"]):
        hooks = get_hooks()

    refs, content = read_markdown_string(md_in, hooks=hooks)
    source, _ = tangle_ref(refs, "hello.scm")
    _ = CodeReader(PurePath("-"), refs).run(source)
    assert stitch_markdown(refs, content) == md_in


malformed_attrs = """
Test after issue 55

``` {.scheme #test}
;|blah:nospace
42
```
"""


def test_malformed_quarto_attributes():
    with config(
            hooks=["quarto_attributes"]):
            # it is currently not possible to change markers at run-time,
            # because the config is passed to MarkdownLexer at module load time
            # markers=Markers(
            #     open=r"^(?P<indent>\s*)```(?P<properties>.*)$",
            #     close=r"^(?P<indent>\s*)```\s*$")):
            hooks = get_hooks()

    refs, _ = read_markdown_string(malformed_attrs, hooks=hooks)
    assert "test" in refs
    codeblock = next(refs["test"])
    assert not any(isinstance(p, Attribute) for p in codeblock.properties)
