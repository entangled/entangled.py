from entangled.interface import Document
from entangled.io import VirtualFS, transaction
from entangled.errors.user import CodeAttributeError
from entangled.model import ReferenceName, ReferenceId

from pathlib import Path
import pytest


fs = VirtualFS.from_dict({
    "wrongly_typed_attribute1.md": """
---
entangled:
    version: "2.4"
    style: basic
---

```python
#| file: 3
```
""".lstrip(),


    "octal_mode_attribute2.md": """
---
entangled:
    version: "2.4"
    style: basic
---

Note, the mode here is given in octal, and the YAML reader understands this, so this is
supported.

```python
#| file: hello.py
#| mode: 0755
#!/usr/bin/env python
print("Hello, World!")
```
""".lstrip(),


    "octal_mode_attribute1.md": """
``` {.python file=hello.py mode=0755}
print("Hello, World!")
```
""".lstrip(),

    "wrongly_typed_mode_attribute.md": """
---
entangled:
    version: "2.4"
    style: basic
---

```python
#| file: hello.py
#| mode: true
print("Hello, World!")
```
""".lstrip()})


def test_file_attribute_type():
    doc = Document()
    with transaction(fs=fs) as t:
        refs = doc.reference_map

        with pytest.raises(CodeAttributeError):
            doc.load_source(t, Path("wrongly_typed_attribute1.md"))

        with pytest.raises(CodeAttributeError):
            doc.load_source(t, Path("wrongly_typed_mode_attribute.md"))

        for i in range(1, 3):
            src = Path(f"octal_mode_attribute{i}.md")
            doc.load_source(t, src)
            ref = ReferenceId(ReferenceName((), "hello.py"), src, 0)
            assert ref in refs
            assert refs[ref].mode == 0o755
        

