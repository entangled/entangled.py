from entangled.config import AnnotationMethod
from entangled.io import VirtualFS, transaction
from entangled.interface import Document
from entangled.model import ReferenceName
from pathlib import Path

fs = VirtualFS.from_dict({
    "q.md": """
---
entangled:
    version: "2.4"
    namespace: q
---

``` {.python #hello}
print("hello")
```
""".strip(),

    "p.md": """
---
entangled:
    version: "2.4"
    namespace: p
---

``` {.python #hello}
print("world")
```

``` {.python file=combined.py}
<<q::hello>>
<<hello>>
```
""".strip()})

def test_yaml_namespace():
    doc = Document()
    with transaction(fs=fs) as t:
        update = doc.load_source(t, Path("q.md"))
        assert update and update.namespace == "q"
        update = doc.load_source(t, Path("p.md"))
        assert update and update.namespace == "p"

        refs = doc.reference_map
        refq = ReferenceName.from_str("q::hello")
        assert refs.has_name(refq)
        cb = [refs[r] for r in refs.select_by_name(refq)]
        assert cb[0].source == "print(\"hello\")\n"

        refp = ReferenceName.from_str("p::hello")
        assert refs.has_name(refp)
        cb = [refs[r] for r in refs.select_by_name(refp)]
        assert cb[0].source == "print(\"world\")\n"

        doc.tangle(t, AnnotationMethod.NAKED)

    assert fs[Path("combined.py")].content == "print(\"hello\")\nprint(\"world\")\n"

