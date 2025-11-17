from entangled.config import AnnotationMethod, Config
from entangled.readers import run_reader, markdown
from entangled.model.tangle import tangle_ref, MissingReference
from entangled.model import ReferenceName, ReferenceMap

from functools import partial
import pytest

md_source = """
``` {.scheme #hello}
(display "hello") (newline)
<<goodbye>>
```
""".lstrip()


def test_missing_ref():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Config(), refs), md_source)
    with pytest.raises(MissingReference) as excinfo:
        _ = tangle_ref(refs, ReferenceName((), "hello"), AnnotationMethod.NAKED)
    assert "goodbye" in str(excinfo.value)
