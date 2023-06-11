from entangled.markdown_reader import MarkdownReader
from entangled.commands.stitch import stitch_markdown
from entangled.main import configure


def test_retrieve_same_content(data):
    file = data / "hello-world" / "hello-world.md"
    with open(file, "r") as f:
        md = MarkdownReader(str(file))
        markdown = f.read()
        md.run(markdown)
        assert stitch_markdown(md.reference_map, md.content) == markdown


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
    mr = MarkdownReader("-")
    mr.run(md_ignore)

    assert "hello" not in mr.reference_map
    assert "goodbye" in mr.reference_map


md_backtics = """
``` {.python #hello}
  ```
```
"""


def test_backtic_content():
    mr = MarkdownReader("-")
    mr.run(md_backtics)
    assert next(mr.reference_map["hello"]).source == "  ```"


md_unknown_lang = """
``` {.too_obscure #hello}
```
"""


def test_unknown_language():
    mr = MarkdownReader("-")
    mr.run(md_unknown_lang)
    assert len(mr.reference_map.map) == 0
