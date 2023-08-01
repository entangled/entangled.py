from contextlib import chdir

from entangled.config import config
from entangled.commands import tangle

from uuid import uuid4
from time import sleep
from pathlib import Path

import os

md_input = """
Create a file:

``` {{.python file=script.py}}
print("{message}", end="")
```

``` {{.makefile #build target=test.dat}}
test.dat: script.py
> python $< > $@
```
"""


def test_build(tmp_path):
    message = uuid4().hex
    with chdir(tmp_path):
        with open("test.md", "w") as f:
            f.write(md_input.format(message=message))

        with config(hooks=["build"]):
            # normally, build hooks are disabled in CI,
            # here we need to make an exception
            if "CI" in os.environ:
                del os.environ["CI"]
                tangle()
                os.environ["CI"] = "true"
            else:
                tangle()

        sleep(0.1)
        tgt = Path("test.dat")
        assert tgt.exists()
        contents = open(tgt, "r").read()
        assert contents == message
