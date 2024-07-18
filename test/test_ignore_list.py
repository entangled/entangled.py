from entangled.config import config
from entangled.status import find_watch_dirs, list_input_files
from contextlib import chdir
from entangled.commands.tangle import tangle
from pathlib import Path

readme_md = """
# README
```{.python file=src/test.py}
print("test")
```
"""

index_md_1 = """
# Test

``` {.c file=src/test.c}
#include <stdio.h>
int main() { printf("Hello, World!\\n"); return 0; }
```
"""

index_md_2 = """
``` {.makefile file=Makefile}
.RECIPEPREFIX = >

%.o: %.c
> gcc -c $< -o $@

hello: test.o
> gcc $^ -o $@
```
"""

data_md = """
Don't tangle me!
```{.python file=src/test2.py}
print("test2")
```
"""


def test_watch_dirs(tmp_path):
    with chdir(tmp_path):
        Path("./docs").mkdir()
        Path("./docs/data").mkdir()
        Path("./docs/index.md").write_text(index_md_1)
        Path("./docs/data/data.md").write_text(data_md)
        Path("./docs/README.md").write_text(readme_md)
        with config(watch_list=["**/*.md"], ignore_list=["**/data/*", "**/README.md"]):
            tangle()
            # data.md and README.md should not be entangled cause they are part
            # of the ignore list while index.md should be so test2.py, test.py
            # should not be created while test.c should be created.
            assert not Path.exists(Path("./src/test2.py"))
            assert not Path.exists(Path("./src/test.py"))
            assert Path.exists(Path("./src/test.c"))
