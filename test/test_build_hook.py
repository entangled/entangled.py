from contextlib import chdir
import subprocess

from entangled.config import config
from entangled.commands import tangle

from uuid import uuid4
from time import sleep
from pathlib import Path


md_input = """
Create a file:

``` {{.python file=script.py}}
print("{message}", end="")
```

``` {{.bash .build target="test.dat" deps="script.py"}}
python script.py > test.dat
```
"""


def test_build(tmp_path):
    message = uuid4().hex
    with chdir(tmp_path):
        with open("test.md", "w") as f:
            f.write(md_input.format(message=message))

        with config(hooks=["build"]):
            tangle()

        sleep(0.1)
        with open(".entangled/build/Makefile", "r") as f_in:
            for l in f_in.readlines():
                print(l, end="")

        subprocess.call(["make", "-f", ".entangled/build/Makefile"])
        sleep(0.1)

        tgt = Path("test.dat")
        assert tgt.exists()
        contents = open(tgt, "r").read()
        assert contents == message
