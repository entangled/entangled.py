from entangled.config import AnnotationMethod, Markers, config
from entangled.hooks import get_hooks
from entangled.markdown_reader import read_markdown_string
from entangled.tangle import tangle_ref


md_in = """
``` {.scheme}
;| id: hello
(display "hello") (newline)
```

``` {.scheme}
;| file: hello.scm
<<hello>>
(display "goodbye") (newline)
```
"""


scm_out = """
;| file: hello.scm
;| id: hello
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
    result, _ = tangle_ref(refs, "hello.scm", AnnotationMethod.NAKED)
    assert result.strip() == scm_out.strip()
