from entangled.interface import Document
from entangled.io import VirtualFS, transaction
from entangled.config import AnnotationMethod
from entangled.model.tangle import tangle_ref, MissingReference
from entangled.model import ReferenceName

import pytest
from pathlib import Path


fs = VirtualFS.from_dict({
    "input.md": """
``` {.scheme #hello}
(display "hello") (newline)
<<goodbye>>
```
""".lstrip()})


def test_missing_ref():
    doc = Document()
    with transaction(fs=fs) as t:
        doc.load_source(t, Path("input.md"))

    refs = doc.reference_map
    with pytest.raises(MissingReference) as excinfo:
        _ = tangle_ref(refs, ReferenceName((), "hello"), AnnotationMethod.NAKED)
    assert "goodbye" in str(excinfo.value)
