from entangled.config import config
from entangled.status import find_watch_dirs, list_input_files
from contextlib import chdir
from entangled.commands.tangle import tangle
from pathlib import Path

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
"""

def test_watch_dirs(tmp_path):
    with chdir(tmp_path):
        Path("./docs").mkdir()
        Path("./data").mkdir()
        Path("./docs/index.md").write_text(index_md_1)
        Path("./data/data.md").write_text(data_md)
        with config(watch_list=["docs/*.md"]):
            assert set(find_watch_dirs()) == set([Path("./docs")])
            tangle()
            assert set(find_watch_dirs()) == set([Path("./docs"), Path("./src")])
            Path("./docs/index.md").write_text(index_md_1 + "\n" + index_md_2)
            tangle()
            assert set(find_watch_dirs()) == set([Path("."), Path("./docs"), Path("./src")])

            assert sorted(list_input_files()) == [Path("./docs/index.md")]
    
