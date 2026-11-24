from contextlib import chdir
from pathlib import Path

from entangled.interface import Document
from entangled.io import transaction, TransactionMode


config = """
version = "2.7"
watch_list = ["chapters/*.md"]
hooks = ["docs"]
""".lstrip()

chapter_a = """
# Score

::: {.docs file=reference.md section="Patches" order=20}
Patches are defined with `patch`.
:::

::: {.docs file=reference.md section="The mel language" order=10}
`mel("...")` reads a melody from text.

```python
mel("g4:q bb4 d5")
```

::: {.callout}
Nested divs are copied too.
:::
:::

``` {.python file=score.py}
print("score")
```
""".lstrip()

chapter_b = """
# Tracks

``` {.markdown .docs file=reference.md section="The mel language" order=5}
Melodies are read by `mel`.
```

::: {.docs file=reference.md}
Introduction to the reference.
:::
""".lstrip()

expected_naked = """
Introduction to the reference.

## The mel language

Melodies are read by `mel`.

`mel("...")` reads a melody from text.

```python
mel("g4:q bb4 d5")
```

::: {.callout}
Nested divs are copied too.
:::

## Patches

Patches are defined with `patch`.
""".lstrip()


def setup(tmp_path: Path):
    Path("entangled.toml").write_text(config)
    Path("chapters").mkdir()
    Path("chapters/a.md").write_text(chapter_a)
    Path("chapters/b.md").write_text(chapter_b)


def tangle():
    doc = Document()
    with transaction() as t:
        doc.load(t)
        doc.tangle(t)
    return doc


def strip_annotations(text: str) -> str:
    return "".join(l for l in text.splitlines(keepends=True) if "~/~" not in l)


def test_docs_hook(tmp_path: Path):
    with chdir(tmp_path):
        setup(tmp_path)
        _ = tangle()

        # code inside a docs div is not tangled
        assert Path("score.py").read_text() == '# ~/~ begin <<chapters/a.md#score.py>>[init]\nprint("score")\n# ~/~ end\n'
        text = Path("reference.md").read_text()
        assert text.startswith("<!-- ~/~ begin <<reference.md#entangled-docs::reference.md>>[init] -->")
        assert "<!-- ~/~ begin <<chapters/a.md#" in text
        assert strip_annotations(text) == expected_naked

        # Chapters are not changed by a tangle
        assert Path("chapters/a.md").read_text() == chapter_a


def test_docs_hook_stitch(tmp_path: Path):
    with chdir(tmp_path):
        setup(tmp_path)
        _ = tangle()

        ref = Path("reference.md")
        ref.write_text(ref.read_text().replace("defined with", "made with"))

        doc = Document()
        with transaction(TransactionMode.FAIL) as t:
            doc.load(t)
            doc.load_all_code(t)
            doc.stitch(t)

        assert Path("chapters/a.md").read_text() == chapter_a.replace("defined with", "made with")
        assert Path("chapters/b.md").read_text() == chapter_b


def test_divs_ignored_without_hook(tmp_path: Path):
    with chdir(tmp_path):
        Path("entangled.toml").write_text('version = "2.7"\n')
        Path("a.md").write_text(
            "::: {.docs file=reference.md}\n``` {.python file=x.py}\nx = 1\n```\n:::\n")
        _ = tangle()
        assert Path("x.py").exists()
        assert not Path("reference.md").exists()
