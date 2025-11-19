from entangled.config import ConfigUpdate
from entangled.interface import Document
from entangled.model import ReferenceName, ReferenceId
from entangled.io import VirtualFS, transaction

from pathlib import PurePath, Path
from os import linesep as eol

fs = VirtualFS.from_dict({
    "input.md": """
A script with a she-bang!

``` {.bash file=test.sh}
#!/bin/bash

echo "Hello, World!"
```
""",

    "test.sh": """#!/bin/bash
# ~/~ begin <<input.md#test.sh>>[init]

echo "Hello, World!"
# ~/~ end
""",

    "test.sh.modified": """#!/bin/bash
# ~/~ begin <<input.md#test.sh>>[init]

echo "Hello, Universe!"
# ~/~ end
""",

    "input.md.modified": """
A script with a she-bang!

``` {.bash file=test.sh}
#!/bin/bash

echo "Hello, Universe!"
```
"""})


def test_shebang():
    doc = Document()
    doc.config |= ConfigUpdate(version="2.4", hooks=["shebang"])

    with transaction(fs=fs) as t:
        doc.load_source(t, Path("input.md"))

        ref = ReferenceId(ReferenceName((), "test.sh"), PurePath("input.md"), 0)
        assert ref in doc.reference_map

        assert doc.reference_map[ref].header == "#!/bin/bash" + eol
        code_content, _ = doc.target_text(PurePath("test.sh"))
        assert code_content.strip() == t.fs[Path("test.sh")].content.strip()

        doc.load_code(t, Path("test.sh.modified"))
        md_content, _ = doc.source_text(Path("input.md"))
        assert md_content.strip() == t.fs[Path("input.md.modified")].content.strip()

