from entangled.interface import Document
from entangled.config import ConfigUpdate, NamespaceDefault, AnnotationMethod
from entangled.model import ReferenceName
from entangled.io import VirtualFS, transaction

from pathlib import Path


fs = VirtualFS.from_dict({
    "a.md": """
First input:

``` {.python #a}
# part a
```

``` {.python file=a.py}
<<a>>
```
""".strip(),

    "b.md": """
Second input

``` {.python #a}
# part b
```

``` {.python file=b.py}
<<a>>
```
""".strip()})


def test_global_namespace():
    doc = Document()

    with transaction(fs=fs) as t:
        doc.config |= ConfigUpdate(
            version="2.4",
            namespace_default=NamespaceDefault.GLOBAL,
            annotation=AnnotationMethod.NAKED)

        doc.load_source(t, Path("a.md"))
        doc.load_source(t, Path("b.md"))

        refs = doc.reference_map
        cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("a"))]
        assert len(cb) == 2
        assert cb[0].source.strip() == "# part a"
        assert cb[1].source.strip() == "# part b"

        source, _ = doc.target_text(Path("a.py"))
        assert source.splitlines() == ["# part a", "# part b"]


def test_private_namespace():
    doc = Document()

    with transaction(fs=fs) as t:
        doc.config |= ConfigUpdate(
            version="2.4",
            namespace_default=NamespaceDefault.PRIVATE,
            annotation=AnnotationMethod.NAKED)

        doc.load_source(t, Path("a.md"))
        doc.load_source(t, Path("b.md"))
        
        refs = doc.reference_map

        cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("a.md::a"))]
        assert len(cb) == 1
        assert cb[0].source.strip() == "# part a"

        cb = [refs[r] for r in refs.select_by_name(ReferenceName.from_str("b.md::a"))]
        assert len(cb) == 1
        assert cb[0].source.strip() == "# part b"

        source, _ = doc.target_text(Path("a.py"))
        assert source.splitlines() == ["# part a"]

        source, _ = doc.target_text(Path("b.py"))
        assert source.splitlines() == ["# part b"]

