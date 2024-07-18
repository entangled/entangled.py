from entangled.markdown_reader import read_markdown_file, read_markdown_string
from entangled.commands.stitch import stitch_markdown
from entangled.main import configure


def test_retrieve_same_content(data):
    file = data / "hello-world" / "hello-world.md"
    with open(file, "r") as f:
        markdown = f.read()
        refs, content = read_markdown_string(markdown)
        assert stitch_markdown(refs, content) == markdown


md_ignore = """
hello

~~~markdown
This should be ignored.

``` {.python #hello}
```
~~~

This shouldn't

``` {.python #goodbye}
```
"""


def test_ignore():
    refs, _ = read_markdown_string(md_ignore)
    assert "hello" not in refs
    assert "goodbye" in refs


md_backtics = """
``` {.python #hello}
  ```
```
"""


def test_backtic_content():
    refs, _ = read_markdown_string(md_backtics)
    assert next(refs["hello"]).source == "  ```"


md_unknown_lang = """
``` {.too_obscure #hello}
```
"""


def test_unknown_language():
    refs, _ = read_markdown_string(md_unknown_lang)
    # assert len(refs.map) == 0
