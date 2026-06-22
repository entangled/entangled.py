from pathlib import Path

from entangled.io import VirtualFS, transaction
from entangled.interface import Document

fs = VirtualFS.from_dict({
    "test.md": """
---
entangled:
  version: "2.4"
  tangle_path: "a/b/c"
---

This prints Hello, World from C.

``` {.c file=hello.c}
#include <stdio.h>
int main() {
    printf("Hello, World!\n");
    return 0;
}
```
""".lstrip()})

def test_tangle_path():
    doc = Document()
    with transaction(fs = fs) as t:
        doc.load(t)
        doc.tangle(t)

    target = Path("a/b/c/hello.c")
    assert target in fs
    new_content = fs[target].content.replace("World", "Universe")
    fs.write(target, new_content)
    assert "Universe" in fs[target].content

    print(fs._data.keys())
    print(fs[Path(".entangled/filedb.json")].content)

    with transaction(fs = fs) as t:
        doc.load_all_code(t)
        doc.stitch(t)

    assert "Universe" in fs[Path("test.md")].content
