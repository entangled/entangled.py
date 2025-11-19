from entangled.interface import Document
from entangled.io import transaction
from entangled.logging import configure
from contextlib import chdir

import subprocess
import pytest
import sys

from uuid import uuid4
from pathlib import Path


md_input = """
---
entangled:
    version: "2.4"
    hooks:
        - build
---

Create a file:

``` {{.python file=script.py}}
print("{message}", end="")
```

``` {{.bash .build target="test.dat" deps="script.py"}}
python script.py > test.dat
```
""".lstrip()


@pytest.mark.skipif(sys.platform == "win32", reason="Skipped on Windows")
def test_build(tmp_path):
    configure(debug=True)
    message = uuid4().hex
    with chdir(tmp_path):
        Path("test.md").write_text(md_input.format(message=message), encoding="utf-8")

        doc = Document()
        with transaction() as t:
            doc.context |= doc.load_source(t, Path("test.md"))
            doc.tangle(t)

        for h in doc.context.hooks:
            h.post_tangle(doc.reference_map)

        print(Path(".entangled/build/Makefile").read_text())
        subprocess.call(["make", "-f", ".entangled/build/Makefile"])

        tgt = Path("test.dat")
        assert tgt.exists()
        assert tgt.read_text() == message
