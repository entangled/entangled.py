from entangled.config import ConfigUpdate
from entangled.interface import Document
from entangled.model import ReferenceName, ReferenceId
from entangled.io import VirtualFS, transaction

from pathlib import PurePath, Path

eol = "\n"

fs = VirtualFS.from_dict({
    "input.md": """
A C file with a license!

``` {.c file=test.c}
// SPDX-License-Identifier: MIT
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
```
""",

    "output_test.c": """// SPDX-License-Identifier: MIT
// ~/~ begin <<input.md#test.c>>[init]
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
// ~/~ end
""",

    "output_test.c.modified": """// SPDX-License-Identifier: MIT
// ~/~ begin <<input.md#test.c>>[init]

int main() {
    printf("Hello, World!\n");
    return 0;
}
// ~/~ end
""",

    "input.md.modified": """
A C file with a license!

``` {.c file=test.c}
// SPDX-License-Identifier: MIT

int main() {
    printf("Hello, World!\n");
    return 0;
}
```
"""})


def test_spdx_license():
    doc = Document()
    doc.config |= ConfigUpdate(version="2.4", hooks=["spdx_license"])

    with transaction(fs=fs) as t:
        doc.load_source(t, Path("input.md"))

        ref = ReferenceId(ReferenceName((), "test.c"), PurePath("input.md"), 0)
        assert ref in doc.reference_map

        assert doc.reference_map[ref].header == "// SPDX-License-Identifier: MIT" + eol
        code_content, _ = doc.target_text(PurePath("test.c"))
        assert code_content.strip() == t.fs[Path("output_test.c")].content.strip()

        doc.load_code(t, Path("output_test.c.modified"))
        md_content, _ = doc.source_text(Path("input.md"))
        assert md_content.strip() == t.fs[Path("input.md.modified")].content.strip()

