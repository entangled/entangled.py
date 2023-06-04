from entangled.tangle import tangle_ref
from entangled.config import AnnotationMethod
from entangled.markdown_reader import MarkdownReader
from entangled.errors.user import MissingReference

import pytest

md_source = """
``` {.scheme #hello}
(display "hello") (newline)
<<goodbye>>
```
"""


def test_missing_ref(tmp_path):
    with pytest.raises(MissingReference):
        mr = MarkdownReader("-")
        mr.run(md_source)
        tangle_ref(mr.reference_map, "hello", AnnotationMethod.NAKED)
