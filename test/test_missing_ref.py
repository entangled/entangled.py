from entangled.tangle import tangle_ref
from entangled.config import AnnotationMethod
from entangled.markdown_reader import read_markdown_string
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
        refs, _ = read_markdown_string(md_source)
        tangle_ref(refs, "hello", AnnotationMethod.NAKED)
