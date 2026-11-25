from pathlib import Path

from entangled.interface import Document
from entangled.interface.context import Context
from entangled.io import VirtualFS, transaction, TransactionMode


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


def make_fs() -> VirtualFS:
    return VirtualFS.from_dict({
        "entangled.toml": config,
        "chapters/a.md": chapter_a,
        "chapters/b.md": chapter_b,
    })


def tangle(fs: VirtualFS) -> Document:
    doc = Document(context=Context(fs))
    with transaction(fs=fs) as t:
        doc.load(t)
        doc.tangle(t)
    return doc


def strip_annotations(text: str) -> str:
    return "".join(l for l in text.splitlines(keepends=True) if "~/~" not in l)


def test_docs_hook():
    fs = make_fs()
    _ = tangle(fs)

    # code inside a docs div is not tangled
    assert fs[Path("score.py")].content == '# ~/~ begin <<chapters/a.md#score.py>>[init]\nprint("score")\n# ~/~ end\n'
    text = fs[Path("reference.md")].content
    assert text.startswith("<!-- ~/~ begin <<reference.md#entangled-docs::reference.md>>[init] -->")
    assert "<!-- ~/~ begin <<chapters/a.md#" in text
    assert strip_annotations(text) == expected_naked

    # Chapters are not changed by a tangle
    assert fs[Path("chapters/a.md")].content == chapter_a


def test_docs_hook_stitch():
    fs = make_fs()
    _ = tangle(fs)

    ref = Path("reference.md")
    fs.write(ref, fs[ref].content.replace("defined with", "made with"))

    doc = Document(context=Context(fs))
    with transaction(TransactionMode.FAIL, fs=fs) as t:
        doc.load(t)
        doc.load_all_code(t)
        doc.stitch(t)

    assert fs[Path("chapters/a.md")].content == chapter_a.replace("defined with", "made with")
    assert fs[Path("chapters/b.md")].content == chapter_b


def test_divs_ignored_without_hook():
    fs = VirtualFS.from_dict({
        "entangled.toml": 'version = "2.7"\n',
        "a.md": "::: {.docs file=reference.md}\n``` {.python file=x.py}\nx = 1\n```\n:::\n",
    })
    _ = tangle(fs)
    assert Path("x.py") in fs
    assert Path("reference.md") not in fs
