from contextlib import chdir
from pathlib import Path
import sys

import pytest
from entangled.loom.file_task import Phony, Target
from entangled.loom.program import LoomProgram, resolve_tasks


hello_world_loom = """
[[task]]
targets = ["phony(all)"]
dependencies = ["hello.txt"]

[[task]]
targets = ["hello.txt"]
stdout = "hello.txt"
language = "Bash"
script = "echo 'Hello, World'"
"""


@pytest.mark.asyncio
async def test_loom(tmp_path):
    with chdir(tmp_path):
        src = Path("hello.toml")
        tgt = Path("hello.txt")
        src.write_text(hello_world_loom)
        prg = LoomProgram.read(src)
        db = await resolve_tasks(prg)
        assert db.index[Target(tgt)].stdout == tgt
        await db.run(Target(Phony("all")))
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World\n"


include_loom = """
include = [
    "generated_wf.toml"
] 

[[task]]
targets = ["generated_wf.toml"]
stdout = "generated_wf.toml"
language = "Python"
script = '''
print(\"\"\"
[[task]]
targets = ["hello.txt"]
stdout = "hello.txt"
language = "Bash"
script = "echo 'Hello, World'"
\"\"\")
'''

[[task]]
targets = ["phony(all)"]
dependencies = ["hello.txt"]
"""


@pytest.mark.asyncio
async def test_include(tmp_path):
    with chdir(tmp_path):
        src = Path("hello.toml")
        tgt = Path("hello.txt")
        src.write_text(include_loom)
        prg = LoomProgram.read(src)
        db = await resolve_tasks(prg)
        assert db.index[Target(tgt)].stdout == tgt
        await db.run(Target(Phony("all")))
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World\n"


pattern_loom = """
[pattern.echo]
targets = ["{stdout}"]
stdout = "{stdout}"
language = "Python"
script = '''
print("{text}")
'''

[[task]]
targets = ["phony(all)"]
dependencies = ["hello.txt"]

[[call]]
pattern = "echo"
args = { stdout = "hello.txt", text = "Hello, World" }
"""


@pytest.mark.asyncio
async def test_pattern(tmp_path):
    with chdir(tmp_path):
        src = Path("hello.toml")
        tgt = Path("hello.txt")
        src.write_text(pattern_loom)
        prg = LoomProgram.read(src)
        db = await resolve_tasks(prg)
        assert db.index[Target(tgt)].stdout == tgt
        await db.run(Target(Phony("all")))
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World\n"


rot_13_loom = """
[[task]]
targets = ["secret.txt"]
stdout = "secret.txt"
language = "Python"
script = \"\"\"
print("Uryyb, Jbeyq!")
\"\"\"

[pattern.rot13]
targets = ["{stdout}"]
dependencies = ["{stdin}"]
stdout = "{stdout}"
stdin = "{stdin}"
language = "Bash"
script = \"\"\"
tr a-zA-Z n-za-mN-ZA-M
\"\"\"

[[call]]
pattern = "rot13"
  [call.args]
  stdin = "secret.txt"
  stdout = "hello.txt"

[[task]]
targets = ["phony(all)"]
dependencies = ["hello.txt"]
"""


@pytest.mark.skipif(sys.platform == "win32", reason="no `tr` on windows")
@pytest.mark.asyncio
async def test_rot13(tmp_path):
    with chdir(tmp_path):
        src = Path("hello.toml")
        tgt = Path("hello.txt")
        src.write_text(rot_13_loom)
        prg = LoomProgram.read(src)
        db = await resolve_tasks(prg)
        assert db.index[Target(tgt)].stdout == tgt
        await db.run(Target(Phony("all")))
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"
